#!/usr/bin/env python3
"""Build references/docs_official.db from a clone of PrefectHQ/fastmcp's docs/.

Stdlib-only, Python 3.10+. Selects the ~180 current-version FastMCP docs (the
ten core folders plus python-sdk and integrations), rewrites the five Mintlify
JSX snippet components to plain text (or drops them), parses changelog.mdx into a
structured `changelog` table, and writes a single SQLite file with an FTS5 index.

Forked from Skills-for-Langchain v1.2.0's build_docs_db.py and adapted to the
FastMCP docs dialect (docs/plans/initial-build/02-db-and-build-script.md):
  - FastMCP docs sit directly under --src (no src/oss/ nesting).
  - Snippets here are JSX component *definitions*, not content fragments, so the
    LangChain recursive `expand_body()` inliner is replaced by per-component
    transform/drop substitution (D9). There are no `:::python`/`:::js` language
    conditionals in FastMCP docs, so that machinery is deleted (D10).
  - Schema gains `section` and `description`; changelog is (version, date, body).

Usage:
    python3 scripts/build_docs_db.py \
        --src .tmp/docs_fastmcp \
        --out .claude/skills/fastmcp/references/docs_official.db \
        [--commit <sha>] [--mirror <path/to/mirror.db>]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

# --- Corpus selection (01-corpus.md) ---------------------------------------

# Top-level folders under --src, recursed for *.mdx. Order is display-only.
# updates.mdx, v2/, apps/, snippets/ are deliberately NOT here: asserting their
# absence in validate_docs_db.py is cheaper than special-casing them here.
INCLUDE = [
    "getting-started",
    "servers",
    "clients",
    "deployment",
    "development",
    "patterns",
    "cli",
    "tutorials",
    "community",
    "more",
    "python-sdk",
    "integrations",
]

DOC_COUNT_MIN, DOC_COUNT_MAX = 150, 220
CHANGELOG_MIN = 80


def log(msg: str) -> None:
    print(msg, flush=True)


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# --- Preflight -------------------------------------------------------------

def assert_fts5() -> None:
    con = sqlite3.connect(":memory:")
    try:
        opts = {row[0] for row in con.execute("PRAGMA compile_options;")}
    finally:
        con.close()
    if "ENABLE_FTS5" not in opts:
        die("this Python's bundled SQLite lacks FTS5 (ENABLE_FTS5). "
            "Use a Python whose sqlite3 has FTS5 (system CPython on macOS/Linux normally does).")


# --- Frontmatter -----------------------------------------------------------

def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter_dict, body) splitting a leading --- ... --- block."""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}, text
    fm_raw = m.group(1)
    body = text[m.end():]
    fm: dict[str, str] = {}
    for line in fm_raw.splitlines():
        km = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not km:
            continue
        key, val = km.group(1), km.group(2).strip()
        if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
            val = val[1:-1]
        fm[key] = val
    return fm, body


# --- Snippet handling (D9: transform/drop, not recursive inlining) ---------

# FastMCP's five snippets are JSX component *definitions* under /snippets/. Each
# import line is stripped; each rendered tag is rewritten per the rules below.
# Import forms both appear in the corpus and must both be accepted:
#   named:   import { VersionBadge } from '/snippets/version-badge.mdx'
#   default: import PrefabPinWarning from '/snippets/prefab-pin-warning.mdx'
# Scoped to module paths containing /snippets/ so Python `import ...` lines
# inside code blocks are never matched.
IMPORT_RE = re.compile(
    r"""^import\s+(?:\{\s*(?P<named>[^}]+?)\s*\}|(?P<default>[A-Za-z_][A-Za-z0-9_]*))"""
    r"""\s+from\s+['"](?P<path>[^'"]*/snippets/[^'"]+)['"]\s*;?\s*$""",
    re.MULTILINE,
)

# Static Tip text, hardcoded from the snippet definitions (their source is
# .tmp/docs_fastmcp/snippets/{prefab-pin-warning,local-focus}.mdx). One sentence
# each; carrying the text keeps the guidance in the DB after the tag is gone.
PREFAB_PIN_TEXT = (
    "**Note:** [Prefab](https://prefab.prefect.io) is under active development "
    "with frequent breaking changes. FastMCP sets a minimum `prefab-ui` version "
    "but does not pin an upper bound — pin `prefab-ui` to a specific version in "
    "your own dependencies before deploying."
)
LOCAL_FOCUS_TEXT = (
    "**Note:** This integration focuses on running local FastMCP server files "
    "with STDIO transport. For remote servers running with HTTP or SSE transport, "
    "use your client's native configuration — FastMCP's integrations focus on "
    "simplifying the complex local setup with dependencies and `uv` commands."
)


def _sub_version_badge(body: str) -> str:
    # <VersionBadge version="3.0.0" /> -> *New in version 3.0.0* (semantic info
    # that must survive into the DB). Tolerate quote/spacing variants.
    body = re.sub(
        r"""<VersionBadge\s+version=["']([^"']+)["']\s*/>""",
        lambda m: f"*New in version {m.group(1)}*",
        body,
    )
    # Bare <VersionBadge /> only appears once, inside an inline-code span in prose
    # *about* the component (development/contributing.mdx). Collapse to the two
    # lowercase words so the sentence still reads AND no `versionbadge` FTS token
    # is left behind (validate: MATCH 'VersionBadge' stays at zero rows).
    body = re.sub(r"<VersionBadge\s*/>", "version badge", body)
    return body


def _sub_static_tip(name: str, text: str):
    def _apply(body: str) -> str:
        return re.sub(r"<%s\s*/>" % re.escape(name), lambda _m: text, body)
    return _apply


def _drop_tag(name: str):
    # Delete the component tag, including multi-line self-closing bodies
    # (YouTubeEmbed spans several lines). Non-greedy up to the first "/>".
    def _apply(body: str) -> str:
        return re.sub(r"<%s\b.*?/>" % re.escape(name), "", body, flags=re.DOTALL)
    return _apply


# name -> substitution function. An imported name absent here is an unknown
# snippet added upstream: fail loud so the script is taught about it consciously.
SUBSTITUTIONS = {
    "VersionBadge": _sub_version_badge,
    "PrefabPinWarning": _sub_static_tip("PrefabPinWarning", PREFAB_PIN_TEXT),
    "LocalFocusTip": _sub_static_tip("LocalFocusTip", LOCAL_FOCUS_TEXT),
    "PrefabDemoFrame": _drop_tag("PrefabDemoFrame"),
    "YouTubeEmbed": _drop_tag("YouTubeEmbed"),
}

SUP_RE = re.compile(r"<sup>.*?</sup>", re.DOTALL)


def tag_present(body: str, name: str) -> bool:
    return re.search(r"<%s\b" % re.escape(name), body) is not None


def process_snippets(body: str, origin: str) -> str:
    """Strip /snippets import lines and rewrite the component tags to text."""
    names: set[str] = set()
    kept: list[str] = []
    for line in body.splitlines(keepends=True):
        m = IMPORT_RE.match(line.rstrip("\n"))
        if m:
            if m.group("named"):
                for nm in m.group("named").split(","):
                    nm = nm.strip()
                    if nm:
                        names.add(nm)
            else:
                names.add(m.group("default"))
        else:
            kept.append(line)
    body = "".join(kept)

    # Fail loud on an imported snippet we have no rule for — upstream added one
    # and the script must be taught about it consciously.
    for name in sorted(names):
        if name not in SUBSTITUTIONS and tag_present(body, name):
            die(f"{origin}: imported snippet {name!r} has no substitution rule "
                f"(upstream added a snippet — add it to SUBSTITUTIONS)")

    # Apply every known transform unconditionally. These component tags carry a
    # fixed meaning wherever they occur, and a few appear in docs that document
    # the component without importing it (e.g. contributing.mdx shows a bare
    # `<VersionBadge />` in prose); the import-scoped substitution used by the
    # LangChain fork base would miss those, and validate_docs_db.py's regression
    # check (zero `<VersionBadge` rows) would then fail. A handler is a no-op
    # when its tag is absent.
    for handler in SUBSTITUTIONS.values():
        body = handler(body)

    # Residual: no /snippets import line and no imported-snippet tag may survive.
    if re.search(r"^import\s+.*/snippets/", body, re.MULTILINE):
        die(f"{origin}: unresolved /snippets import line remains after substitution")
    stray = sorted(n for n in names if tag_present(body, n))
    if stray:
        die(f"{origin}: unresolved snippet render tags remain: {stray}")
    return body


# --- Per-file processing ---------------------------------------------------

def process_file(abspath: str, rel_path: str, section: str) -> dict:
    with open(abspath, encoding="utf-8") as fh:
        text = fh.read()

    fm, body = split_frontmatter(text)
    body = process_snippets(body, rel_path)

    # Optional python-sdk cleanup: strip the <sup><a…><Icon github/></a></sup>
    # GitHub-source link decorations after every symbol heading (01). Reduces FTS
    # noise; nice-to-have, so it is scoped to the section that carries them.
    if section == "python-sdk":
        body = SUP_RE.sub("", body)

    path = rel_path[: -len(".mdx")] if rel_path.endswith(".mdx") else rel_path
    title = fm.get("title") or fm.get("sidebarTitle") or os.path.basename(path)
    return {
        "path": path,
        "title": title,
        "description": fm.get("description"),
        "section": section,
        "body": body.strip() + "\n",
    }


def collect_records(src: str) -> tuple[list[dict], dict[str, int]]:
    records: list[dict] = []
    per_section: dict[str, int] = {}
    for section in INCLUDE:
        base = os.path.join(src, section)
        if not os.path.isdir(base):
            die(f"expected corpus dir at {base}")
        for dirpath, _dirs, files in sorted(os.walk(base)):
            for name in sorted(files):
                if not name.endswith(".mdx"):
                    continue
                abspath = os.path.join(dirpath, name)
                rel_path = os.path.relpath(abspath, src).replace(os.sep, "/")
                records.append(process_file(abspath, rel_path, section))
                per_section[section] = per_section.get(section, 0) + 1
    return records, per_section


# --- Changelog -------------------------------------------------------------

def parse_changelog(src: str) -> list[dict]:
    """Parse changelog.mdx into one row per <Update> block: (version, date, body).

    Attributes are parsed order-independently so a block that carries an extra
    `date="…"` between `label` and `description` (one ancient v0.x entry does)
    is still captured. date prefers an explicit `date` attribute, falling back
    to `description` — which, for every current-version entry, IS the ISO date.
    """
    path = os.path.join(src, "changelog.mdx")
    if not os.path.isfile(path):
        die(f"expected changelog at {path}")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    rows: list[dict] = []
    for block in re.finditer(r"<Update\b([^>]*)>(.*?)</Update>", text, re.DOTALL):
        attrs, inner = block.group(1), block.group(2)
        lm = re.search(r'\blabel="([^"]+)"', attrs)
        if not lm:
            continue
        version = lm.group(1)
        dm = re.search(r'\bdate="([^"]+)"', attrs)
        desc = re.search(r'\bdescription="([^"]+)"', attrs)
        date = dm.group(1) if dm else (desc.group(1) if desc else None)
        rows.append({
            "version": version,
            "date": date,
            "body": inner.strip(),
        })
    if len(rows) < CHANGELOG_MIN:
        die(f"changelog: parsed only {len(rows)} <Update> blocks (< {CHANGELOG_MIN}); "
            "format changed upstream?")
    return rows


# --- Database --------------------------------------------------------------

SCHEMA = """
CREATE TABLE docs (
    path        TEXT PRIMARY KEY,
    title       TEXT,
    description TEXT,
    section     TEXT,
    body        TEXT NOT NULL
);
CREATE INDEX idx_docs_section ON docs(section);

CREATE VIRTUAL TABLE docs_fts USING fts5(
    title, description, body,
    content='docs', content_rowid='rowid',
    tokenize='porter unicode61'
);
CREATE TRIGGER docs_ai AFTER INSERT ON docs BEGIN
    INSERT INTO docs_fts(rowid, title, description, body)
        VALUES (new.rowid, new.title, new.description, new.body);
END;
CREATE TRIGGER docs_ad AFTER DELETE ON docs BEGIN
    INSERT INTO docs_fts(docs_fts, rowid, title, description, body)
        VALUES('delete', old.rowid, old.title, old.description, old.body);
END;
CREATE TRIGGER docs_au AFTER UPDATE ON docs BEGIN
    INSERT INTO docs_fts(docs_fts, rowid, title, description, body)
        VALUES('delete', old.rowid, old.title, old.description, old.body);
    INSERT INTO docs_fts(rowid, title, description, body)
        VALUES (new.rowid, new.title, new.description, new.body);
END;

CREATE TABLE changelog (
    version TEXT,
    date    TEXT,
    body    TEXT
);
CREATE INDEX idx_changelog_date ON changelog(date);

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def resolve_commit(src: str, override: str | None) -> str | None:
    if override:
        return override
    # The snapshot dir is a plain copy without .git; a --commit is normally
    # passed. Best-effort read only if a .git happens to be present.
    if not os.path.exists(os.path.join(src, ".git")):
        return None
    try:
        import subprocess
        out = subprocess.run(["git", "-C", src, "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip() or None
    except Exception:
        return None


def write_db(db_path: str, records: list[dict], changelog: list[dict],
             meta: dict[str, str]) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.executemany(
            "INSERT INTO docs(path, title, description, section, body) VALUES (?,?,?,?,?)",
            [(r["path"], r["title"], r["description"], r["section"], r["body"]) for r in records],
        )
        con.executemany(
            "INSERT INTO changelog(version, date, body) VALUES (?,?,?)",
            [(c["version"], c["date"], c["body"]) for c in changelog],
        )
        con.executemany("INSERT INTO meta(key, value) VALUES (?,?)", list(meta.items()))
        con.execute("INSERT INTO docs_fts(docs_fts) VALUES('optimize');")
        con.commit()
        con.execute("PRAGMA optimize;")
        con.commit()
        con.execute("VACUUM;")
        con.commit()
    finally:
        con.close()


def self_validate(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        for t in ("docs", "docs_fts", "changelog", "meta"):
            if t not in tables:
                die(f"self-validate: missing table {t}")
        (doc_count,) = con.execute("SELECT count(*) FROM docs").fetchone()
        if not (DOC_COUNT_MIN <= doc_count <= DOC_COUNT_MAX):
            die(f"self-validate: doc_count {doc_count} outside band "
                f"{DOC_COUNT_MIN}..{DOC_COUNT_MAX}")
        (cl,) = con.execute("SELECT count(*) FROM changelog").fetchone()
        if cl < CHANGELOG_MIN:
            die(f"self-validate: changelog {cl} rows (< {CHANGELOG_MIN})")
        (hits,) = con.execute(
            "SELECT count(*) FROM docs_fts WHERE docs_fts MATCH 'provider'").fetchone()
        if hits == 0:
            die("self-validate: FTS MATCH 'provider' returned no rows")
        meta_keys = {r[0] for r in con.execute("SELECT key FROM meta")}
        for k in ("snapshot_date", "built_at", "source_repo", "source_commit",
                  "doc_count", "schema_version"):
            if k not in meta_keys:
                die(f"self-validate: meta missing key {k}")
    finally:
        con.close()


# --- Main ------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="path to the FastMCP docs/ snapshot")
    ap.add_argument("--out", required=True, help="output .db path")
    ap.add_argument("--commit", default=None, help="source commit sha for meta (else read from --src/.git)")
    ap.add_argument("--mirror", default=None, help="also copy the finished .db to this path")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    if not os.path.isdir(os.path.join(src, "servers")):
        die(f"--src {src} does not look like a FastMCP docs snapshot (no servers/)")

    assert_fts5()

    log("[1/5] processing corpus files ...")
    records, per_section = collect_records(src)
    log(f"      {len(records)} docs")
    for section in INCLUDE:
        if section in per_section:
            log(f"        {section:16s} {per_section[section]}")

    log("[2/5] parsing changelog ...")
    changelog = parse_changelog(src)
    log(f"      {len(changelog)} changelog rows "
        f"(newest {changelog[0]['version']} {changelog[0]['date']})")

    snapshot_date = next((c["date"] for c in changelog if c["date"]), None)
    commit = resolve_commit(src, args.commit)
    meta = {
        "snapshot_date": snapshot_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_repo": "https://github.com/PrefectHQ/fastmcp",
        "source_commit": commit or "unknown (hand-copied snapshot, 2026-07-18)",
        "doc_count": str(len(records)),
        "schema_version": "1",
    }

    log("[3/5] writing database (temp) ...")
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db", dir=out_dir)
    os.close(tmp_fd)
    os.remove(tmp_path)  # let sqlite create it fresh
    try:
        write_db(tmp_path, records, changelog, meta)
        log("[4/5] self-validating ...")
        self_validate(tmp_path)
        shutil.move(tmp_path, args.out)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if args.mirror:
        os.makedirs(os.path.dirname(os.path.abspath(args.mirror)), exist_ok=True)
        shutil.copyfile(args.out, args.mirror)
        log(f"      mirrored to {args.mirror}")

    size = os.path.getsize(args.out)
    log("[5/5] done.")
    log(f"      out: {args.out}  ({size/1_000_000:.2f} MB)")
    log(f"      snapshot_date={meta['snapshot_date']}  commit={meta['source_commit'][:12]}")
    if size > 8_000_000:
        log("      WARNING: .db larger than 8 MB — inspect for accidentally ingested non-doc content.")


if __name__ == "__main__":
    main()

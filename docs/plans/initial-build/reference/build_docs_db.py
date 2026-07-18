#!/usr/bin/env python3
"""Build references/docs_official.db from a clone of langchain-ai/docs.

Stdlib-only. Selects the core ~187 docs (langchain, langgraph, deepagents,
concepts, reference, python/migrate, python/releases), inlines every
`/snippets/...` import, strips `:::js` conditional blocks (keeps `:::python`),
parses the changelog, and writes a single SQLite file with an FTS5 index.

See docs/plans/docs-db/ for the design (02 corpus, 03 schema, 04 build).

Usage:
    python scripts/build_docs_db.py \
        --src .tmp/docs_langchain \
        --out .claude/skills/langchain/references/docs_official.db \
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

# --- Corpus selection (02-corpus-and-clone.md) -----------------------------

# (relative dir under src/oss, package tag). Recursed for *.mdx.
INCLUDE = [
    ("langchain", "langchain"),
    ("langgraph", "langgraph"),
    ("deepagents", "deepagents"),
    ("concepts", "concepts"),
    ("reference", "reference"),
    ("python/migrate", "migrate"),
    ("python/releases", "releases"),
]

MONTHS = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
    "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}

IMPORT_RE = re.compile(r"""^import\s+([A-Za-z_][A-Za-z0-9_]*)\s+from\s+['"]([^'"]+)['"];?\s*$""")


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


# --- Snippet index ---------------------------------------------------------

def build_snippet_index(src: str) -> dict[str, str]:
    """Map '/snippets/<rel>' -> file content for every file under src/snippets/."""
    root = os.path.join(src, "src", "snippets")
    if not os.path.isdir(root):
        die(f"expected snippets dir at {root}")
    index: dict[str, str] = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            abspath = os.path.join(dirpath, name)
            rel = os.path.relpath(abspath, os.path.join(src, "src"))
            key = "/" + rel.replace(os.sep, "/")  # e.g. /snippets/code-samples/foo.mdx
            with open(abspath, encoding="utf-8") as fh:
                index[key] = fh.read()
    return index


# --- Per-file processing ---------------------------------------------------

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


FENCE_RE = re.compile(r"^(:{3,})(python|js)?\s*$")


def strip_lang_conditionals(body: str) -> str:
    """Remove `:::js ... :::` spans entirely; unwrap `:::python ... :::`.

    Nesting-aware and indentation-insensitive. Mintlify wraps nested
    conditionals with progressively MORE colons (e.g. an outer `::::::js`
    around inner `:::python`/`:::js`), so a bare closing fence is matched to
    its open by colon count. A line is kept iff no `js` block encloses it.
    """
    out: list[str] = []
    stack: list[tuple[int, str]] = []  # (colon_count, lang)
    for line in body.splitlines(keepends=True):
        m = FENCE_RE.match(line.strip())
        if m:
            colons, lang = len(m.group(1)), m.group(2)
            if lang:  # opening fence
                stack.append((colons, lang))
            else:      # closing fence: pop the matching (nearest same-count) open
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][0] == colons:
                        del stack[i]
                        break
                else:
                    if stack:
                        stack.pop()
            continue
        if not any(lang == "js" for _c, lang in stack):
            out.append(line)
    return "".join(out)


def tag_present(body: str, name: str) -> bool:
    return re.search(r"<%s\s*/>" % re.escape(name), body) is not None


IMPORT_LINE_RE = re.compile(r"^import\s+[A-Za-z_][A-Za-z0-9_]*\s+from\s+['\"]/snippets/", re.MULTILINE)
MAX_DEPTH = 8


def expand_body(text: str, snippet_index: dict[str, str], origin: str,
                seen: frozenset[str], depth: int, names: set[str]) -> tuple[str, int]:
    """Recursively inline `/snippets/...` imports and strip `:::js`.

    A snippet can itself import and render further snippets; each level is
    expanded before substitution so no nested render tag survives. `names`
    accumulates every imported component name seen (for the residual check).
    Returns (expanded_text, substitution_count). Missing target/cycle -> error.
    """
    if depth > MAX_DEPTH:
        die(f"{origin}: snippet nesting exceeded depth {MAX_DEPTH} (cycle?)")

    # 1. Collect and drop import lines.
    imports: dict[str, str] = {}
    kept: list[str] = []
    for line in text.splitlines(keepends=True):
        m = IMPORT_RE.match(line.rstrip("\n"))
        if m:
            imports[m.group(1)] = m.group(2)
            names.add(m.group(1))
        else:
            kept.append(line)
    text = "".join(kept)

    # 2. Strip js / unwrap python at this level.
    text = strip_lang_conditionals(text)

    # 3. Resolve every imported tag that survived, recursing into its content.
    count = 0
    for name, path in imports.items():
        if not tag_present(text, name):
            continue
        if path not in snippet_index:
            die(f"{origin}: import {name} -> {path} has no matching file under src/snippets/")
        if path in seen:
            die(f"{origin}: snippet import cycle through {path}")
        resolved, sub = expand_body(snippet_index[path], snippet_index, path,
                                    seen | {path}, depth + 1, names)
        text = re.sub(r"<%s\s*/>" % re.escape(name), lambda _m: resolved, text)
        count += 1 + sub
    return text, count


def compute_url(rest: str) -> str:
    """`<rest>` is the path with src/oss/ and .mdx stripped."""
    if rest.endswith("/index"):
        rest = rest[: -len("/index")]
    return f"https://docs.langchain.com/oss/{rest}"


def process_file(abspath: str, rel_path: str, package: str,
                 snippet_index: dict[str, str]) -> tuple[dict, int]:
    with open(abspath, encoding="utf-8") as fh:
        text = fh.read()

    fm, body = split_frontmatter(text)

    # Recursively strip :::js, unwrap :::python, and inline every snippet
    # (including snippets that themselves import further snippets).
    names: set[str] = set()
    body, subs = expand_body(body, snippet_index, rel_path, frozenset(), 0, names)

    # Residual check (D5): no /snippets import line survives, and no *imported*
    # component name remains as a render tag. Scoped to imported names so legit
    # self-closing JSX in code examples (e.g. `<LoadingIndicator />`) is kept.
    if IMPORT_LINE_RE.search(body):
        die(f"{rel_path}: unresolved /snippets import line remains after expansion")
    stray = sorted(n for n in names if tag_present(body, n))
    if stray:
        die(f"{rel_path}: unresolved snippet render tags remain: {stray}")

    rest = rel_path[: -len(".mdx")] if rel_path.endswith(".mdx") else rel_path
    record = {
        "path": rel_path,
        "package": package,
        "title": fm.get("title"),
        "tag": fm.get("tag"),
        "url": compute_url(rest),
        "body": body.strip() + "\n",
    }
    return record, subs


def collect_records(src: str, snippet_index: dict[str, str]) -> tuple[list[dict], dict[str, int], int]:
    records: list[dict] = []
    per_pkg: dict[str, int] = {}
    total_subs = 0
    oss = os.path.join(src, "src", "oss")
    for subdir, package in INCLUDE:
        base = os.path.join(oss, subdir)
        if not os.path.isdir(base):
            die(f"expected corpus dir at {base}")
        for dirpath, _dirs, files in sorted(os.walk(base)):
            for name in sorted(files):
                if not name.endswith(".mdx"):
                    continue
                abspath = os.path.join(dirpath, name)
                rel_path = os.path.relpath(abspath, oss).replace(os.sep, "/")
                record, subs = process_file(abspath, rel_path, package, snippet_index)
                records.append(record)
                per_pkg[package] = per_pkg.get(package, 0) + 1
                total_subs += subs
    return records, per_pkg, total_subs


# --- Changelog -------------------------------------------------------------

def to_iso_date(label: str) -> str | None:
    m = re.match(r"([A-Za-z]{3})\w*\s+(\d{1,2}),\s*(\d{4})", label.strip())
    if not m:
        return None
    mon = MONTHS.get(m.group(1)[:3].title())
    if not mon:
        return None
    return f"{m.group(3)}-{mon}-{int(m.group(2)):02d}"


def parse_changelog(src: str) -> list[dict]:
    path = os.path.join(src, "src", "oss", "python", "releases", "changelog.mdx")
    if not os.path.isfile(path):
        die(f"expected changelog at {path}")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    rows: list[dict] = []
    for block in re.finditer(r"<Update\b([^>]*)>(.*?)</Update>", text, re.DOTALL):
        attrs, inner = block.group(1), block.group(2)
        lm = re.search(r'label="([^"]+)"', attrs)
        date = to_iso_date(lm.group(1)) if lm else None
        tm = re.search(r"tags=\{\[([^\]]*)\]\}", attrs)
        tag_pkgs = re.findall(r'"([^"]+)"', tm.group(1)) if tm else []

        # One row per `## `pkg` vX.Y.Z` heading (usually exactly one).
        headings = list(re.finditer(r"^\s*##\s+`([^`]+)`\s+v?([^\s]+)\s*$", inner, re.MULTILINE))
        if not headings:
            continue
        for i, hm in enumerate(headings):
            pkg = hm.group(1)
            version = hm.group(2)
            start = hm.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(inner)
            summary = re.sub(r"\n{3,}", "\n\n", inner[start:end]).strip()
            rows.append({
                "date": date,
                "package": pkg or (tag_pkgs[0] if tag_pkgs else None),
                "version": version,
                "summary": summary,
            })
    return rows


# --- Database --------------------------------------------------------------

SCHEMA = """
CREATE TABLE docs (
    id       INTEGER PRIMARY KEY,
    path     TEXT NOT NULL UNIQUE,
    package  TEXT NOT NULL,
    title    TEXT,
    tag      TEXT,
    url      TEXT,
    body     TEXT NOT NULL
);
CREATE INDEX idx_docs_package ON docs(package);

CREATE VIRTUAL TABLE docs_fts USING fts5(
    title, body,
    content='docs', content_rowid='id',
    tokenize='porter unicode61'
);
CREATE TRIGGER docs_ai AFTER INSERT ON docs BEGIN
    INSERT INTO docs_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TRIGGER docs_ad AFTER DELETE ON docs BEGIN
    INSERT INTO docs_fts(docs_fts, rowid, title, body) VALUES('delete', old.id, old.title, old.body);
END;
CREATE TRIGGER docs_au AFTER UPDATE ON docs BEGIN
    INSERT INTO docs_fts(docs_fts, rowid, title, body) VALUES('delete', old.id, old.title, old.body);
    INSERT INTO docs_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;

CREATE TABLE changelog (
    id       INTEGER PRIMARY KEY,
    date     TEXT,
    package  TEXT,
    version  TEXT,
    summary  TEXT
);
CREATE INDEX idx_changelog_pkg ON changelog(package, date);

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def resolve_commit(src: str, override: str | None) -> str | None:
    if override:
        return override
    head = os.path.join(src, ".git")
    if not os.path.exists(head):
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
            "INSERT INTO docs(path, package, title, tag, url, body) VALUES (?,?,?,?,?,?)",
            [(r["path"], r["package"], r["title"], r["tag"], r["url"], r["body"]) for r in records],
        )
        con.executemany(
            "INSERT INTO changelog(date, package, version, summary) VALUES (?,?,?,?)",
            [(c["date"], c["package"], c["version"], c["summary"]) for c in changelog],
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
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        for t in ("docs", "docs_fts", "changelog", "meta"):
            if t not in tables:
                die(f"self-validate: missing table {t}")
        (doc_count,) = con.execute("SELECT count(*) FROM docs").fetchone()
        if not (150 <= doc_count <= 250):
            die(f"self-validate: doc_count {doc_count} outside sane band 150..250")
        (cl,) = con.execute("SELECT count(*) FROM changelog").fetchone()
        if cl == 0:
            die("self-validate: changelog is empty")
        (hits,) = con.execute("SELECT count(*) FROM docs_fts WHERE docs_fts MATCH 'agent'").fetchone()
        if hits == 0:
            die("self-validate: FTS MATCH 'agent' returned no rows")
        meta_keys = {r[0] for r in con.execute("SELECT key FROM meta")}
        for k in ("snapshot_date", "built_at", "source_repo", "source_commit", "doc_count", "schema_version"):
            if k not in meta_keys:
                die(f"self-validate: meta missing key {k}")
    finally:
        con.close()


# --- Main ------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="path to the langchain-ai/docs clone")
    ap.add_argument("--out", required=True, help="output .db path")
    ap.add_argument("--commit", default=None, help="source commit sha for meta (else read from --src/.git)")
    ap.add_argument("--mirror", default=None, help="also copy the finished .db to this path")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    if not os.path.isdir(os.path.join(src, "src", "oss")):
        die(f"--src {src} does not contain src/oss/")

    assert_fts5()

    log(f"[1/6] indexing snippets under {src}/src/snippets ...")
    snippet_index = build_snippet_index(src)
    log(f"      indexed {len(snippet_index)} snippet files")

    log("[2/6] processing corpus files ...")
    records, per_pkg, total_subs = collect_records(src, snippet_index)
    log(f"      {len(records)} docs, {total_subs} snippet substitutions")
    for _subdir, pkg in INCLUDE:
        if pkg in per_pkg:
            log(f"        {pkg:12s} {per_pkg[pkg]}")

    log("[3/6] parsing changelog ...")
    changelog = parse_changelog(src)
    log(f"      {len(changelog)} changelog rows")

    snapshot_date = max((c["date"] for c in changelog if c["date"]), default=None)
    commit = resolve_commit(src, args.commit)
    meta = {
        "snapshot_date": snapshot_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_repo": "https://github.com/langchain-ai/docs",
        "source_commit": commit or "unknown",
        "doc_count": str(len(records)),
        "schema_version": "1",
    }

    log("[4/6] writing database (temp) ...")
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db", dir=os.path.dirname(os.path.abspath(args.out)) or ".")
    os.close(tmp_fd)
    os.remove(tmp_path)  # let sqlite create it fresh
    try:
        write_db(tmp_path, records, changelog, meta)
        log("[5/6] self-validating ...")
        self_validate(tmp_path)
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        shutil.move(tmp_path, args.out)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if args.mirror:
        os.makedirs(os.path.dirname(os.path.abspath(args.mirror)), exist_ok=True)
        shutil.copyfile(args.out, args.mirror)
        log(f"      mirrored to {args.mirror}")

    size = os.path.getsize(args.out)
    log("[6/6] done.")
    log(f"      out: {args.out}  ({size/1_000_000:.2f} MB)")
    log(f"      snapshot_date={meta['snapshot_date']}  commit={meta['source_commit'][:12]}")
    if size > 20_000_000:
        log("      WARNING: .db larger than 20 MB — did integrations leak into the corpus?")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Standalone validation for references/docs_official.db (plan doc 02).

Opens the shipped artifact read-only and asserts the invariants that make it
trustworthy — schema present, row counts in band, snippet substitution actually
happened, no v2/apps/import leakage, key content survived, FTS answers, meta
fully populated. Exits non-zero on any failure. Run by CI and after every rebuild.

Usage:
    python3 scripts/validate_docs_db.py [--db <path>]
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys

DEFAULT_DB = ".claude/skills/fastmcp/references/docs_official.db"
REQUIRED_TABLES = ("docs", "docs_fts", "changelog", "meta")
REQUIRED_META = ("snapshot_date", "built_at", "source_repo", "source_commit",
                 "doc_count", "schema_version")

failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    status = "ok  " if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        failures.append(msg)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DEFAULT_DB, help=f"path to the db (default {DEFAULT_DB})")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print(f"ERROR: no db at {args.db}", file=sys.stderr)
        return 2

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    print(f"Validating {args.db}")

    # 1. Schema.
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    for t in REQUIRED_TABLES:
        check(t in tables, f"table `{t}` present")

    # 2. Row counts.
    (doc_count,) = con.execute("SELECT count(*) FROM docs").fetchone()
    check(150 <= doc_count <= 220, f"doc_count {doc_count} within band 150..220")
    meta = dict(con.execute("SELECT key, value FROM meta"))
    check(meta.get("doc_count") == str(doc_count),
          f"meta.doc_count ({meta.get('doc_count')}) equals count(*) ({doc_count})")

    # 3. Changelog present and current-version on top.
    (cl,) = con.execute("SELECT count(*) FROM changelog").fetchone()
    check(cl >= 80, f"changelog has >= 80 rows ({cl})")
    newest = con.execute(
        "SELECT version FROM changelog ORDER BY date DESC LIMIT 1").fetchone()
    # Bump this assertion when v4 ships and the corpus is refreshed.
    check(newest is not None and newest[0].startswith("v3."),
          f"newest changelog version starts with v3. ({newest[0] if newest else None})")

    # 4. No leftover /snippets import lines (single-quote form, as in the docs).
    (imp,) = con.execute(
        "SELECT count(*) FROM docs WHERE body LIKE '%from ''/snippets/%'").fetchone()
    check(imp == 0, f"no leftover /snippets import lines ({imp})")

    # 5. No v2 or apps leakage into the corpus.
    (v2,) = con.execute("SELECT count(*) FROM docs WHERE path LIKE 'v2/%'").fetchone()
    check(v2 == 0, f"no v2/ leakage ({v2})")
    (apps,) = con.execute("SELECT count(*) FROM docs WHERE path LIKE 'apps/%'").fetchone()
    check(apps == 0, f"no apps/ leakage ({apps})")

    # 6. Regression — snippet substitution: no rendered VersionBadge tags survive.
    (vb,) = con.execute("SELECT count(*) FROM docs WHERE body LIKE '%<VersionBadge%'").fetchone()
    check(vb == 0, f"no leftover <VersionBadge tags ({vb})")

    # 7. Regression — key content survived the pipeline.
    skills = con.execute(
        "SELECT body FROM docs WHERE path = 'servers/providers/skills'").fetchone()
    check(skills is not None and "SkillsDirectoryProvider" in skills[0],
          "servers/providers/skills body contains SkillsDirectoryProvider")
    upg = con.execute(
        "SELECT body FROM docs WHERE path = 'getting-started/upgrading/from-fastmcp-2'").fetchone()
    check(upg is not None and "on_duplicate" in upg[0],
          "getting-started/upgrading/from-fastmcp-2 body contains on_duplicate")

    # 8. FTS answers.
    for term in ("provider", "elicitation"):
        (hits,) = con.execute(
            "SELECT count(*) FROM docs_fts WHERE docs_fts MATCH ?", (term,)).fetchone()
        check(hits > 0, f"FTS MATCH '{term}' returns rows ({hits})")

    # 9. Meta fully populated.
    for k in REQUIRED_META:
        check(bool(meta.get(k)), f"meta.{k} populated" + (f" = {meta[k]}" if meta.get(k) else ""))

    con.close()

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s) failed.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

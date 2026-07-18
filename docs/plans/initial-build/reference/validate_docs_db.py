#!/usr/bin/env python3
"""Lightweight validation for references/docs_official.db (docs/plans/docs-db/06).

Standalone: opens the shipped artifact and asserts the invariants that make it
trustworthy — schema present, row counts sane, snippets actually inlined (the
dynamic-subagents regression), no unresolved snippet tags or :::js leakage, FTS
returns hits, meta fully populated. Exits non-zero on the first failure.

Usage:
    python scripts/validate_docs_db.py [--db <path>]
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys

DEFAULT_DB = ".claude/skills/langchain/references/docs_official.db"
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

    # Schema.
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    for t in REQUIRED_TABLES:
        check(t in tables, f"table `{t}` present")

    # Row counts.
    (doc_count,) = con.execute("SELECT count(*) FROM docs").fetchone()
    check(150 <= doc_count <= 250, f"doc_count {doc_count} within band 150..250")
    (cl,) = con.execute("SELECT count(*) FROM changelog").fetchone()
    check(cl > 0, f"changelog non-empty ({cl} rows)")

    # No unresolved snippet render tags or leftover /snippets import lines.
    (imp,) = con.execute(
        "SELECT count(*) FROM docs WHERE body LIKE '%import %from ''/snippets/%'").fetchone()
    check(imp == 0, f"no leftover /snippets import lines ({imp})")
    (js,) = con.execute("SELECT count(*) FROM docs WHERE body LIKE '%:::js%'").fetchone()
    check(js == 0, f"no :::js leakage ({js})")

    # Snippets inlined — the dynamic-subagents regression this whole DB exists for.
    row = con.execute(
        "SELECT body FROM docs WHERE path LIKE '%dynamic-subagents%'").fetchone()
    check(row is not None and "create_deep_agent(" in row[0],
          "dynamic-subagents body contains inlined Python (create_deep_agent()")

    # FTS answers.
    (hits,) = con.execute(
        "SELECT count(*) FROM docs_fts WHERE docs_fts MATCH 'agent'").fetchone()
    check(hits > 0, f"FTS MATCH 'agent' returns rows ({hits})")

    # Meta fully populated.
    meta = dict(con.execute("SELECT key, value FROM meta"))
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

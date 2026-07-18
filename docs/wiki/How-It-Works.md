# How It Works

## The forcing function

Model pretrained knowledge of FastMCP is dominated by the **2.x** era and the old
`mcp` SDK's bundled FastMCP 1.0. The framework is now **3.x**, with a rewritten
provider system, transforms, background tasks, and a moved repository
(`PrefectHQ/fastmcp`). Code that "looks right" from memory is frequently 2.x and
wrong in 3.x.

`SKILL.md` opens by declaring that pretrained knowledge stale and routing every
API question to a queryable source of truth: before Claude proposes an
architecture or writes/edits/reviews any `fastmcp` code, it runs a read-only query
against `references/docs_official.db` for every API it is about to rely on, and
builds against what it reads. The one thing it internalizes directly is the
**gotchas table** — removed/renamed APIs that a search over *current* docs cannot
surface, because absence is not searchable.

## The database

A single SQLite file, `references/docs_official.db`, built from the `docs/` folder
of `PrefectHQ/fastmcp` by `scripts/build_docs_db.py`.

```
docs(path, title, description, section, body)   -- one row per doc
docs_fts                                         -- FTS5(title, description, body), porter stemming
changelog(version, date, body)                   -- one row per release
meta(key, value)                                 -- snapshot_date, source_commit, doc_count, …
```

- `path` is the source-relative path without extension, e.g. `servers/providers/skills`.
- `section` is the top-level folder (`servers`, `clients`, `python-sdk`,
  `integrations`, …), so a query can scope to `WHERE section = 'python-sdk'`.
- `body` is Markdown with the five Mintlify JSX snippet components rewritten to
  text (e.g. `<VersionBadge version="3.0.0" />` → `*New in version 3.0.0*`) or
  dropped; there is no raw JSX badge/iframe left in the corpus.

## Query examples

```bash
# Concept search, ranked (prefer FTS over LIKE). snippet() column 2 = body.
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT d.path, snippet(docs_fts,2,'[',']','…',12) FROM docs_fts
   JOIN docs d ON d.rowid=docs_fts.rowid
   WHERE docs_fts MATCH 'openapi' ORDER BY rank LIMIT 5;"

# Proximity search — use the functional NEAR(...) form, not a bare NEAR.
#   docs_fts MATCH 'NEAR(skills provider, 10)'

# Exact signatures live in the python-sdk section.
#   SELECT path, title FROM docs WHERE section='python-sdk' AND path LIKE '%server%';

# How current is this snapshot?
#   SELECT key, value FROM meta;
```

FTS5 notes: multi-word means implicit AND; `OR` for alternatives; `"exact phrase"`
for phrases; wrap underscore/hyphen-heavy tokens in double quotes
(`'"on_duplicate"'`); porter stemming means `provider` also matches `providers`.

## The consultant flow

When the user describes something to expose as MCP rather than asking about
existing code, the skill loads `references/consultant.md` and runs an interview:

1. **Divergent open** — plain conversation to understand what to expose, who
   consumes it, and the constraints.
2. **Convergent** — AskUserQuestion over a **ten-dimension rubric** (tool source,
   tool surface, component fit, interactivity, state/lifecycle, auth, transport,
   composition, middleware, quality/hosts). Not every dimension is asked, but all
   ten are self-checked before a design is presented; each carries its *why* and a
   *Find in the DB* pointer.
3. **Propose → revise** — a concrete architecture with every API verified in the
   DB, mapped back to the dimension that drove each choice.
4. **Agreement gate** — nothing is written until the user says build, and the
   build scope is agreed per case.

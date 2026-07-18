---
name: fastmcp
description: >-
  Current-API guidance and architecture consulting for FastMCP 3.x, the Python framework for building MCP servers. Load this whenever writing, editing, or reviewing Python that imports `fastmcp`; whenever building or designing an MCP server; and whenever a user asks to expose something as MCP — an API, a skills folder, files, a database, or a whole toolchain — even when they name no framework and show no code. It carries a version-stamped snapshot of the official docs that you query for exact current APIs (the 3.x provider system, transforms, tasks, auth, composition) instead of trusting pretrained memory, which is dominated by the stale FastMCP 2.x / bundled-1.0 API. It also acts as a consultant that interviews the user about what they want to expose and proposes a concrete FastMCP server architecture grounded in those docs. Do NOT load this for configuring MCP servers inside a host (`.mcp.json`, `claude mcp add`, connector setup) — that is host product knowledge, not the FastMCP framework.
---

# FastMCP: MCP-server architecture consultant + current-API guide

This skill has two behaviors over one shared knowledge base — a searchable database of the current official FastMCP docs (`references/docs_official.db`). When the user wants to **expose something as an MCP server**, it acts as a **consultant**: it interviews, proposes a concrete current-API architecture, and — only on agreement — builds. When the user has **concrete FastMCP code or a specific API question**, it stays a **current-API guide**: it answers directly, grounding every API name in a DB query. Both behaviors query the DB for the facts rather than trusting memory.

## Query the DB before you rely on any API

You do **not** reliably know the current FastMCP API. Your pretrained knowledge is dominated by FastMCP **2.x** and the old `mcp` SDK's bundled FastMCP 1.0; the framework is now **3.x** (v3.4.4 at snapshot time) with a rewritten provider system, transforms, background tasks, and a moved repository (`PrefectHQ/fastmcp`, formerly `jlowin/fastmcp`). Memory is precisely the thing that is stale here.

**Before you write, edit, or review any code that touches `fastmcp`, or propose any architecture, query `references/docs_official.db`** for every API you are about to rely on, and treat the DB — not your memory — as ground truth. The full body of every current doc is in the DB, including exact signatures in the `python-sdk` section; the substance is there to be read, not guessed.

A v4 built on the MCP Python SDK v2 is already documented (snake_case protocol fields, an `mcp_types` package, a pydantic ≥ 2.12 floor). When user code mixes eras, the migration guides in the DB (`getting-started/upgrading/*`) are authoritative — read them rather than guessing which era a symbol belongs to.

## Consult or answer — decide which behavior you are in

- If the user is describing **something they want to expose as MCP** — an API, a folder of skills, a harness, a database, a workflow, "make X an MCP" — **act as the consultant**: read `references/consultant.md` and run that process. The user typically knows *what they want exposed*, not *what FastMCP can do*; bridging that gap is the job.
- If the user has **concrete FastMCP code or a specific API question** — **do not launch an interview**. Query the DB for the APIs in play, apply the gotchas below, and answer.
- When it is genuinely ambiguous, ask **one** short clarifying question rather than assuming — a single line, not a full interview.

**Near-miss boundary.** Configuring MCP servers *inside a host* — editing `.mcp.json`, running `claude mcp add`, wiring up a connector in Claude Code / Claude Desktop / Cursor — is **not** this skill's job. That is host product knowledge. This skill is for *building servers with the FastMCP Python framework*. The one overlap: when a FastMCP server you built needs host-side install steps, the DB's `integrations/claude-code` and `integrations/mcp-json-configuration` docs cover that — use them.

## Gotchas the DB can't surface

These are stale 2.x-era reflexes that *look* plausible and compiled in 2.x but are wrong in 3.x — the residue a search over *current* docs cannot correct, because it can only show you what still exists. The authoritative list is `getting-started/upgrading/from-fastmcp-2` (in the DB); apply these directly, and read that doc when touching 2.x code:

- **Transport/network kwargs left the constructor.** `FastMCP("srv", host=…, port=…)` now raises `TypeError` (also `log_level`, `debug`, `sse_path`, `stateless_http`, …). Pass them to `run()` / `run_http_async()`: `mcp.run(transport="http", host="0.0.0.0", port=8080)`.
- **Decorators return the original function**, not a component object. `@mcp.tool`/`@mcp.resource`/`@mcp.prompt` no longer give you something with `.name`/`.description` — that access raises `AttributeError`. Get the component via the server: `await mcp.get_tool("name")`.
- **`get_tools()`/`get_resources()`/`get_prompts()` are gone** → `list_tools()`/`list_resources()`/`list_prompts()` (and `list_resource_templates()`), which return **lists, not dicts**.
- **`tool.enable()`/`tool.disable()` moved to the server**: `server.disable(names={"tool_name"}, components={"tool"})` or `server.disable(tags={"tag"})`; `server.enable(...)` likewise.
- **`ctx.set_state()`/`ctx.get_state()` are now async** (must be awaited). State must be JSON-serializable unless `serializable=False` is passed.
- **Prompt returns are typed now.** `PromptMessage(role=…, content=TextContent(…))` → `fastmcp.prompts.Message("Hello")` or a plain string; v3 no longer silently coerces raw dicts.
- **Composition renamed.** `mount(prefix="x")` → `mount(namespace="x")`; `import_server(sub)` → `mount(sub)`.
- **Proxying moved.** `FastMCP.as_proxy(url)` → `from fastmcp.server import create_proxy; create_proxy(url)`.
- **The provider system is how 3.x sources components.** `from fastmcp.server.openapi import FastMCPOpenAPI` → `OpenAPIProvider`, passed via `FastMCP("name", providers=[…])`. Providers (local functions, `OpenAPIProvider`, `FileSystemProvider`, `SkillsDirectoryProvider`, proxies) are the 3.x way to populate a server.
- **Auth providers no longer auto-load credentials from env vars** — pass `client_id`/`client_secret` explicitly.
- **Repo/packaging shifts.** Homepage/repo is `PrefectHQ/fastmcp`, not `jlowin/fastmcp`; `pip install fastmcp` alone won't upgrade an existing 2.x install (`--upgrade` is required); background tasks need the `fastmcp[tasks]` extra.
- **Era detection for v4.** camelCase protocol fields (`inputSchema`, `mimeType`) are pre-v4 style; v4 (MCP SDK v2) renames them to snake_case with a deprecation bridge. Before "fixing" either direction, read `getting-started/upgrading/from-fastmcp-3`.

## How to query the DB

The DB is a single SQLite file at `references/docs_official.db` (in this repo, `.claude/skills/fastmcp/references/docs_official.db`; if that path isn't present you are running from a plugin install — locate `references/docs_official.db` next to this SKILL.md). Query it read-only through the `sqlite3` CLI in Bash. Schema:

- `docs(path, title, description, section, body)` — one row per doc; `path` is the source-relative path without extension (e.g. `servers/providers/skills`); `section` is the top-level folder (`servers`, `clients`, `python-sdk`, `integrations`, …); `body` is Markdown with the JSX snippet components rewritten to text.
- `docs_fts` — FTS5 over `(title, description, body)`; join on `docs_fts.rowid = docs.rowid`. Column indices for `snippet()`: 0 = title, 1 = description, 2 = body.
- `changelog(version, date, body)` — one row per release, newest first in the file (sort explicitly).
- `meta(key, value)` — provenance: `snapshot_date`, `source_commit`, `doc_count`, `source_repo`, `built_at`, `schema_version`.

```sql
-- 1. Wrap an existing REST API as MCP.
SELECT d.path, d.title, snippet(docs_fts, 2, '[', ']', ' … ', 12) AS excerpt
FROM docs_fts JOIN docs d ON d.rowid = docs_fts.rowid
WHERE docs_fts MATCH 'openapi' ORDER BY rank LIMIT 5;

-- 2. Expose a skills folder (proximity search: skills near provider).
SELECT d.path, d.title
FROM docs_fts JOIN docs d ON d.rowid = docs_fts.rowid
WHERE docs_fts MATCH 'NEAR(skills provider, 10)' ORDER BY rank LIMIT 5;

-- 3. Mid-tool interactivity: ask the user or the model.
SELECT d.path, d.title
FROM docs_fts JOIN docs d ON d.rowid = docs_fts.rowid
WHERE docs_fts MATCH 'elicitation OR sampling' ORDER BY rank LIMIT 8;

-- 4. Read a full doc (after a search points you at it).
SELECT body FROM docs WHERE path = 'servers/composition';

-- 5. Exact signatures live in the python-sdk section.
SELECT path, title FROM docs WHERE section = 'python-sdk' AND path LIKE '%server%';

-- 6. What changed recently, and how current this DB is.
SELECT version, date FROM changelog ORDER BY date DESC LIMIT 5;
SELECT key, value FROM meta;
```

Invocation (always `-readonly`):

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT d.path, snippet(docs_fts, 2, '[', ']', '…', 20) FROM docs_fts JOIN docs d ON d.rowid=docs_fts.rowid WHERE docs_fts MATCH 'skills provider' ORDER BY rank LIMIT 5;"
```

FTS5 `MATCH` syntax notes (the one ergonomic cost of raw SQL):
- Multi-word `'skills provider'` means *both* terms (implicit AND); use `OR` for alternatives; `"exact phrase"` in double quotes for a phrase.
- Proximity uses the **functional** form `NEAR(termA termB, N)` — a bare `termA NEAR termB` is not the operator and matches nothing.
- Porter stemming is on, so `provider` also matches `providers`, `providing`.
- A token with a hyphen/parenthesis/underscore-heavy shape can be read as an operator — wrap odd tokens in double quotes, e.g. `'"on_duplicate"'`.

Workflow: FTS-search for the concept → read the promising `body` rows in full → build/edit against what you read. When a search returns nothing, broaden the terms (drop a word, try a synonym) before falling back to memory — and even then, flag the uncertainty.

## Coverage limits

- **Apps** (tools that return interactive UI) are a deliberate v1.0.0 scope cut — the `apps/` guide docs are not in the DB. If a consultation would genuinely benefit from an interactive-UI answer, say so and point at gofastmcp.com's Apps section rather than improvising the API. (The `python-sdk` API reference for the apps module is present, but treat it as raw signatures, not a consulting playbook.)
- **FastMCP 2.x** is not in the DB beyond the migration guide. For maintaining a 2.x codebase, offer the migration path (`getting-started/upgrading/from-fastmcp-2`) rather than 2.x-era answers from memory.
- The snapshot's date and source commit are in `meta` — quote them when the user asks how current the guidance is, and treat any release newer than `snapshot_date` as unverified.

## Staying current

The DB is a version-stamped snapshot (`SELECT value FROM meta WHERE key='snapshot_date'`), not a timeless encyclopedia. To refresh it, there is no manual re-curation:

1. `rm -rf .tmp/docs_fastmcp && git clone --no-checkout --depth 1 --filter=blob:none https://github.com/PrefectHQ/fastmcp.git .tmp/fastmcp_clone && (cd .tmp/fastmcp_clone && git sparse-checkout set docs && git checkout)` — then use `.tmp/fastmcp_clone/docs` as `--src` and its `git rev-parse HEAD` as `--commit`.
2. `python3 scripts/build_docs_db.py --src .tmp/fastmcp_clone/docs --out .claude/skills/fastmcp/references/docs_official.db --commit <sha> --mirror plugins/skills-for-fastmcp/skills/fastmcp/references/docs_official.db` — eyeball the per-section counts and changelog line.
3. `python3 scripts/validate_docs_db.py` — schema, row-count bands, no v2/apps/snippet leakage, content regressions, FTS hits, meta stamped.
4. **Re-verify the gotchas table above** against the refreshed `getting-started/upgrading/*` docs, then bump `plugin.json` + `CHANGELOG.md` and `diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp` clean.

**v4 tripwire:** when the `changelog` table's newest `version` starts with `v4.`, the gotchas section here and `validate_docs_db.py`'s `v3.` version assertion must be revisited **in the same refresh** — the 2→3 reflexes will be joined (or replaced) by 3→4 ones, and the corpus's excluded/migration set changes. The full procedure and design rationale are in `docs/plans/initial-build/`.

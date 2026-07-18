# 03 — SKILL.md specification

Target: `.claude/skills/fastmcp/SKILL.md` (canonical; byte-identical copy in the plugin mirror). Structural template: `docs/plans/initial-build/reference/SKILL.md` (the Skills-for-Langchain v1.2.0 SKILL.md) — reuse its section architecture, rewrite every sentence for FastMCP. Do not copy LangChain-specific prose.

## Frontmatter

- `name: fastmcp`
- `description`: must trigger on (a) any Python work that imports or mentions FastMCP, (b) building/wrapping anything as an MCP server ("make X an MCP", API→MCP, skills→MCP, harness→MCP), (c) MCP server design questions in Python. Draft:

  > Current-API guidance and architecture consulting for FastMCP 3.x (Python MCP server framework). Use when writing Python that imports fastmcp, when building or designing an MCP server, or when the user asks to expose an API, a skills folder, files, or a whole toolchain as MCP. Also acts as a consultant that interviews the user and proposes a FastMCP server architecture.

- **Near-miss boundary (critical, include as a line in the body, not the description):** configuring MCP servers *inside Claude Code* (`.mcp.json`, `claude mcp add`, connector setup) is NOT this skill's job — that is Claude Code product knowledge. This skill is for *building servers with the FastMCP Python framework*. The one overlap: `integrations/claude-code` and `integrations/mcp-json-configuration` docs in the DB cover installing a FastMCP server into hosts; use them when the user's FastMCP server needs host-side installation steps.

## Section 1 — The forcing function

Same posture as the reference SKILL.md, FastMCP-specific justification. Key sentences to convey:

- You (Claude) do not reliably know the current FastMCP API. Your pretrained knowledge is dominated by FastMCP 2.x and the old `mcp` SDK's bundled FastMCP 1.0; the framework is now 3.x (v3.4.4 at snapshot time) with a rewritten provider system, transforms, tasks, and a moved repository (PrefectHQ/fastmcp).
- Before writing or reviewing any code that touches fastmcp, query `references/docs_official.db`. Do not answer from memory; memory is precisely the thing that is stale here.
- A v4 built on MCP Python SDK v2 is already documented (snake_case protocol fields, `mcp_types` package). When user code mixes eras, the migration guides in the DB (`getting-started/upgrading/*`) are authoritative.

## Section 2 — Consult vs. answer decision

Mirror the reference structure: if the user is describing something they want to expose as MCP (an API, a folder of skills, a harness, a database, a workflow), enter the consultant flow (`references/consultant.md`). If they have a concrete API question or existing code, answer directly — grounded in DB queries. When in doubt between the two, one clarifying question decides it.

## Section 3 — Gotchas the DB can't surface

These are the stale reflexes a model with 2.x-era knowledge will produce that *look* plausible and compile in 2.x but are wrong in 3.x. Distill from `getting-started/upgrading/from-fastmcp-2.mdx` (in the DB; the full list lives there — SKILL.md carries only the reflex-correction table). Each entry: wrong reflex → current form.

1. `FastMCP("srv", host="0.0.0.0", port=8080)` → transport/network kwargs moved to `mcp.run(transport="http", host=…, port=…)`; the constructor raises `TypeError` on them now.
2. `@mcp.tool` returns the **original function**, not a component object — `.name`/`.description` access on the decorated result crashes. Get components via `await mcp.get_tool("name")`.
3. `get_tools()` / `get_resources()` / `get_prompts()` → `list_tools()` / `list_resources()` / `list_prompts()`, returning **lists, not dicts**.
4. `tool.enable()` / `tool.disable()` → `server.enable(...)` / `server.disable(names=…, tags=…)`.
5. `ctx.set_state()` / `ctx.get_state()` are now **async** and state must be JSON-serializable by default.
6. `PromptMessage(role=…, content=TextContent(…))` → `fastmcp.prompts.Message("Hello")`; raw dict returns from prompts are no longer coerced.
7. `mount(prefix="x")` → `mount(namespace="x")`; `import_server(sub)` → `mount(sub)`.
8. `FastMCP.as_proxy(url)` → `from fastmcp.server import create_proxy`.
9. `from fastmcp.server.openapi import FastMCPOpenAPI` → `OpenAPIProvider` passed via `FastMCP("name", providers=[…])` — the provider system is the 3.x way to source components (local functions, OpenAPI, filesystem, skills directories, proxies).
10. Auth providers no longer auto-load credentials from env vars — pass `client_id`/`client_secret` explicitly.
11. Repo/homepage: `PrefectHQ/fastmcp`, not `jlowin/fastmcp`; `pip install fastmcp` alone won't upgrade an existing 2.x install (`--upgrade` required); background tasks need `fastmcp[tasks]`.
12. Era-detection heads-up: if code reads `inputSchema`/`mimeType`-style camelCase protocol fields, it is pre-v4 style; v4 (MCP SDK v2) renames them to snake_case with a deprecation bridge. Check `getting-started/upgrading/from-fastmcp-3` before "fixing" either direction.

Implementation note: verify each of the twelve against the built DB (FTS query per item) before finalizing — the migration doc is the source; do not ship an item the DB cannot back.

## Section 4 — How to query the DB

Same shape as the reference SKILL.md: schema summary, invocation, and 5–6 worked FTS5 queries. Invocation:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT path, snippet(docs_fts, 2, '[', ']', '…', 20) FROM docs_fts WHERE docs_fts MATCH 'skills provider' ORDER BY rank LIMIT 5"
```

Worked examples to include (each mapped to a real consultation need):

- `MATCH 'openapi'` — wrap an existing REST API.
- `MATCH 'skills NEAR provider'` — expose a skills folder.
- `MATCH 'elicitation OR sampling'` — mid-tool interactivity.
- `MATCH 'middleware'` — cross-cutting request handling.
- `SELECT version, date FROM changelog ORDER BY date DESC LIMIT 5` — what changed recently.
- `SELECT path, title FROM docs WHERE section = 'python-sdk' AND path LIKE '%server%'` — exact signatures.

Include the FTS5 syntax notes from the reference (quote multi-word phrases, `OR`/`NEAR`, porter stemming) and the plugin-path variant of the DB path for plugin installs.

## Section 5 — Coverage limits

- **Apps** (tools returning interactive UI) are not in the DB — deliberate v1.0.0 scope cut. If a consultation would genuinely benefit from an interactive UI answer, say so and point at gofastmcp.com's Apps section; do not improvise the API.
- **FastMCP 2.x** is not in the DB beyond the migration guide. For maintaining a 2.x codebase, offer the migration path rather than 2.x-era answers from memory.
- Snapshot date and version are in `meta` — quote them when the user asks how current the guidance is.

## Section 6 — Staying current

DB-refresh workflow, mirroring the reference: re-clone docs → run build → run validators → re-verify the gotchas table against the new migration guides → bump plugin version + CHANGELOG → re-copy plugin mirror. Note the v4 tripwire explicitly: when the changelog table's newest version starts with `v4.`, the gotchas section and validate_docs_db.py's version assertion must be revisited in the same pass.

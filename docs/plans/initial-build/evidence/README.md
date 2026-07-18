# v1.0.0 release evidence

Validation evidence for the initial build, per `06-validation.md`. Full headless
transcripts are the `probe*.jsonl` files in this directory (stream-json).

## Layer 1 — mechanical (all green)

- `build_docs_db.py` — 180 docs, 94 changelog rows (newest v3.4.4 / 2026-07-08),
  self-validation passed, DB 2.43 MB, mirror written.
- `validate_docs_db.py` — 21/21 checks pass (schema, doc_count band, no v2/apps/
  snippet leakage, `SkillsDirectoryProvider` + `on_duplicate` content regressions,
  FTS answers, meta).
- `validate_evidence.py` — plugin/marketplace naming, `## [1.0.0]` CHANGELOG
  heading, plugin mirror byte-identical (3 files).
- Fail-fast confirmed: an injected unknown `/snippets/` import makes the build
  `die()` with exit 1 and ships no partial DB.

## Layer 2 — content spot checks

- Per-section counts match `01-corpus.md` exactly (getting-started 7, servers 44,
  clients 19, deployment 5, development 9, patterns 3, cli 7, tutorials 3,
  community 1, more 2, python-sdk 50, integrations 30).
- Snippet substitution: `MATCH 'VersionBadge'` → 0 rows; `MATCH '"New in version"'`
  → 95 rows.
- `changelog` newest three: v3.4.4 (2026-07-08), v3.4.3 (2026-07-05),
  v3.4.2 (2026-06-06).
- `from-fastmcp-2` migration doc contains every reflex-correction term
  (on_duplicate, get_tool, list_tools, set_state, mount, create_proxy,
  OpenAPIProvider); all 12 SKILL.md gotchas backed by DB queries.
- python-sdk bodies clean — no `<sup>` decorations, no import lines.

## Layer 3 — behavioral headless probes (all pass)

Run in isolated scratch dirs with `claude -p … --plugin-dir <plugin>
--dangerously-skip-permissions --output-format stream-json`, so the skill is
supplied only by the plugin.

| Probe | Prompt | Result |
|---|---|---|
| 1 | "FastMCP로 간단한 HTTP MCP 서버를 만들어줘. 포트는 8080." | **PASS** — skill loaded, queried the DB (`meta`, `running-server`), generated `FastMCP(name="MyServer")` with `mcp.run(transport="http", host="127.0.0.1", port=8080)`. No constructor host/port, no `jlowin/fastmcp`. |
| 2 | "내 .claude/skills 폴더를 MCP 서버로 노출하고 싶어." | **PASS** — full consultant posture: inspected the folder, queried `NEAR(skills provider, 10)` + read `servers/providers/skills`, cited `SkillsDirectoryProvider`/`ClaudeSkillsProvider`, surfaced skills-as-resources-not-tools, flagged the symlink-security risk honestly, proposed the smallest stdio design, asked the decisive consumer question, gated on agreement. Every cited API verified present in the DB. |
| 3 | "이 FastMCP 2.x 코드 좀 고쳐줘: `FastMCP('s', port=8080)`, `tool.disable()`, `ctx.set_state()`" | **PASS** — corrected all three reflexes: `port` → `run()`, `tool.disable()` → `mcp.disable(names={…})` (with the decorator-returns-function rationale), `ctx.set_state/get_state` → `async`/awaited + `serializable=False`; also flagged `--upgrade` and offered to fix `mount(prefix=)`/`as_proxy`/`import_server`/`PromptMessage`. |

Stale reflexes that must NOT appear (constructor `host`/`port`, `get_tools()`,
`tool.disable()` as a recommendation, `PromptMessage(role=…)`, `mount(prefix=…)`,
`FastMCP.as_proxy`, `import_server`, sync `ctx.set_state`) — none appeared in any
probe's recommended code.

# Skills for FastMCP

<p align="center">
  <img src="https://raw.githubusercontent.com/tjdwls101010/tjdwls101010/refs/heads/main/Images/skills%20for%20fastmcp.png" alt="Skills for FastMCP" width="640">
</p>

A Claude Code skill that makes Claude **build MCP servers with the current FastMCP
API instead of its stale memory** — and that acts as a consultant when you want to
expose something as an MCP server.

It does two things over one knowledge base — a version-stamped SQLite/FTS5 snapshot
of the official FastMCP 3.x docs:

- **Current-API guide.** When you write, edit, or review Python that imports
  `fastmcp`, the skill queries the docs database for the exact current API rather
  than trusting pretrained knowledge — which for FastMCP is dominated by the
  **2.x** era and the old `mcp` SDK's bundled 1.0.
- **MCP-server consultant.** When you describe something you want to expose as MCP
  — a REST API, a skills folder, files, a whole toolchain — it interviews you over
  a ten-dimension rubric, reaches explicit agreement, and proposes a concrete
  FastMCP server architecture with every API grounded in the docs database.

It transplants the proven architecture of
[Skills-for-Langchain](https://github.com/tjdwls101010/Skills-for-Langchain) v1.2.0.

> [!IMPORTANT]
> Model pretrained knowledge of FastMCP is mostly **2.x**. FastMCP is now **3.x**
> (v3.4.4 at snapshot time) under PrefectHQ, with a rewritten provider system,
> transforms, tasks, and a moved repository (`PrefectHQ/fastmcp`). Code that
> "looks right" from memory — constructor `host`/`port`, `get_tools()`,
> `tool.disable()`, `mount(prefix=…)`, `FastMCP.as_proxy` — is 2.x and wrong in
> 3.x. This skill exists to correct exactly that.

## Install

**Marketplace**

```
/plugin marketplace add tjdwls101010/Skills-for-FastMCP
/plugin install skills-for-fastmcp
```

**Local plugin dir (no marketplace)**

```
claude --plugin-dir /path/to/Skills-for-FastMCP/plugins/skills-for-fastmcp
```

**Manual copy** — copy `.claude/skills/fastmcp/` into your project's or user
`.claude/skills/` directory. The skill is self-contained (SKILL.md, the consultant
reference, and the docs database).

## How it works

```
.claude/skills/fastmcp/
├── SKILL.md                     # forcing function, gotchas table, how to query
└── references/
    ├── consultant.md            # the interview protocol + ten-dimension rubric
    └── docs_official.db         # SQLite/FTS5 snapshot of the current docs
```

The loop: the skill declares that pretrained FastMCP knowledge is stale, then
before proposing an architecture or writing any `fastmcp` code, Claude runs a
read-only FTS5 query against `docs_official.db` for every API it is about to rely
on and builds against what it reads. The database holds the full body of ~180
current docs (the core folders, the `python-sdk` API reference with exact
signatures, and integrations) plus a structured `changelog` table.

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT d.path, d.title FROM docs_fts JOIN docs d ON d.rowid=docs_fts.rowid \
   WHERE docs_fts MATCH 'openapi' ORDER BY rank LIMIT 5;"
```

## Coverage and limits

- **FastMCP 3.x snapshot.** The exact version and source commit are stamped in the
  database's `meta` table — `SELECT value FROM meta WHERE key='snapshot_date'`.
  Treat any release newer than that date as unverified.
- **Apps excluded.** The Apps subsystem (tools that return interactive UI) is a
  deliberate v1.0.0 scope cut; the skill says so and points at gofastmcp.com.
- **FastMCP 2.x excluded** beyond the official 2→3 migration guide, which is the
  sanctioned way to reason about 2.x code.

## Maintenance

Refreshing the database from a newer docs snapshot is a scripted, validated
operation, not a re-curation — see the
[wiki](https://github.com/tjdwls101010/Skills-for-FastMCP/wiki) for the refresh
workflow, the SemVer/CHANGELOG coupling, and the plugin-mirror rule, and
[`docs/plans/initial-build/`](docs/plans/initial-build/) for the full design
rationale.

## License

[MIT](LICENSE).

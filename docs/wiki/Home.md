# Skills for FastMCP — wiki

A Claude Code skill that makes Claude build MCP servers with the **current**
FastMCP 3.x API instead of its stale pretrained memory, and that acts as a
consultant when you want to expose something as an MCP server.

Two behaviors over one knowledge base — a version-stamped SQLite/FTS5 snapshot of
the official FastMCP docs:

- **Current-API guide** — every `fastmcp` API is looked up in the database before
  it is used, so 2.x-era reflexes (constructor `host`/`port`, `get_tools()`,
  `tool.disable()`, `mount(prefix=…)`) get corrected instead of shipped.
- **MCP-server consultant** — when you describe something to expose as MCP, it
  interviews you over a ten-dimension rubric, agrees on the design, and proposes a
  concrete FastMCP architecture grounded in the docs.

## Pages

- **[How It Works](How-It-Works.md)** — the forcing function, the database schema,
  query examples, and the consultant flow.
- **[Coverage and Limits](Coverage-and-Limits.md)** — what is in the corpus and
  what is deliberately left out, snapshot provenance, and the v4 tripwire.
- **[Customization](Customization.md)** — changing the corpus, adding sections,
  rebuilding, and editing the consultant's dimensions.
- **[Maintenance and Release](Maintenance-and-Release.md)** — the refresh
  workflow, SemVer/CHANGELOG coupling, the plugin-mirror rule, and release steps.

The full design rationale (every decision, with its why) lives in the repo at
[`docs/plans/initial-build/`](../plans/initial-build/), starting at
`00-goals-and-decisions.md`.

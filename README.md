<p align="center">
  <img src="https://raw.githubusercontent.com/tjdwls101010/tjdwls101010/refs/heads/main/Images/skills%20for%20fastmcp.png" alt="Skills for FastMCP" width="640">
</p>

<h1 align="center">Skills for FastMCP</h1>

<p align="center">
  A Claude Code skill that makes Claude build MCP servers with the <strong>current</strong> FastMCP 3.x API — and consult with you on the architecture before it writes a line.
</p>

<p align="center">
  <a href="https://github.com/tjdwls101010/Skills-for-FastMCP/actions/workflows/validate.yml"><img src="https://github.com/tjdwls101010/Skills-for-FastMCP/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
</p>

## What & why

Ask any AI assistant to build an MCP server with FastMCP and it will confidently write code
that no longer runs. Its training data is dominated by FastMCP **2.x** and the old `mcp` SDK's
bundled FastMCP 1.0, while the framework has since moved to **3.x** under PrefectHQ with a
rewritten provider system, renamed composition APIs, and constructor arguments that now raise
`TypeError`. The code looks right, reads right, and fails on the first run.

Skills for FastMCP fixes that at the source. It ships a **version-stamped, searchable snapshot
of the official FastMCP documentation** and a skill that requires Claude to query it before
relying on any API — so answers come from the current docs, not from memory. On top of the same
knowledge base it also acts as a **consultant**: describe something you want to expose as MCP,
and it interviews you across a ten-dimension design rubric, agrees the scope with you, and only
then proposes an architecture.

## Key features

- **Current-API guidance.** Every FastMCP class, decorator, and keyword argument is checked
  against the shipped docs database before it appears in an answer.
- **Twelve stale-reflex corrections.** A table of the 2.x habits that a search over *current*
  docs can never catch — because absence is not searchable. See
  [FastMCP-3-Gotchas](docs/wiki/FastMCP-3-Gotchas.md).
- **An MCP-server consultant.** A ten-dimension rubric covering tool sourcing, context
  efficiency, interactivity, auth, transport, composition and more — run as a checklist before
  any architecture is proposed, never as an interrogation.
- **Honest boundaries.** The snapshot's version, date, and source commit are stamped into the
  database and quoted on request; excluded areas are declared rather than improvised.
- **Reproducible, not hand-curated.** The database is built by a script and guarded by 22
  automated checks plus a byte-identity rule on the packaged copy, so refreshing it is an
  operation rather than a rewrite.

## Quick start

**Prerequisites** — [Claude Code](https://claude.com/claude-code), and `sqlite3` with FTS5
(the system `sqlite3` on macOS and most Linux distributions already has it).

**Install** (marketplace):

```
/plugin marketplace add tjdwls101010/Skills-for-FastMCP
/plugin install skills-for-fastmcp
```

**Verify it works.** Start Claude Code in any project and ask:

```
Write a FastMCP server that exposes one tool and serves it over HTTP on port 8080.
```

You should see Claude query the docs database before writing, and the result should pass
network settings to `run()` — never to the constructor:

```python
mcp.run(transport="http", host="0.0.0.0", port=8080)   # correct in 3.x
# FastMCP("srv", port=8080)  ← the 2.x reflex; raises TypeError today
```

That difference is the whole point of the project. Two other install methods (local plugin
directory, manual copy) and a fuller verification walkthrough are in
[Getting-Started](docs/wiki/Getting-Started.md).

## Usage overview

The skill loads itself when it is relevant, and picks one of two behaviors:

| You say | It does |
|---|---|
| "Make our REST API an MCP server" | **Consults** — interviews you over the rubric, agrees scope, proposes an architecture |
| "Why does `mount(prefix=…)` fail?" | **Answers** — queries the database and replies directly, no interview |

You can also query the shipped database yourself; it is an ordinary read-only SQLite file:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT d.path, d.title FROM docs_fts JOIN docs d ON d.rowid=docs_fts.rowid \
   WHERE docs_fts MATCH 'openapi' ORDER BY rank LIMIT 5;"
```

More recipes in [Usage-Guides](docs/wiki/Usage-Guides.md).

## Documentation

The full documentation lives in **[`docs/wiki/`](docs/wiki/README.md)**:

| | |
|---|---|
| [Overview](docs/wiki/Overview.md) | What it is, who it's for, and what it deliberately does not do |
| [Getting-Started](docs/wiki/Getting-Started.md) | Install, first use, and how to confirm the skill fired |
| [Concepts](docs/wiki/Concepts.md) | MCP, skills, plugins, the forcing function, FTS5 |
| [Architecture](docs/wiki/Architecture.md) | Components, the build pipeline, and why it is shaped this way |
| [Usage-Guides](docs/wiki/Usage-Guides.md) | Querying the database, and both behavior modes |
| [Consultant-Rubric](docs/wiki/Consultant-Rubric.md) | The ten design dimensions, explained |
| [FastMCP-3-Gotchas](docs/wiki/FastMCP-3-Gotchas.md) | The twelve 2.x → 3.x reflex corrections |
| [Coverage-and-Limits](docs/wiki/Coverage-and-Limits.md) | What's in the corpus, what isn't, and why |
| [Customization](docs/wiki/Customization.md) | Forking and adapting it to another framework |
| [Maintenance-and-Release](docs/wiki/Maintenance-and-Release.md) | Refreshing the snapshot and shipping a release |
| [Troubleshooting](docs/wiki/Troubleshooting.md) | Failure modes mapped to fixes |

Design rationale for every decision made during the initial build is preserved in
[`docs/plans/initial-build/`](docs/plans/initial-build/).

## Project status

**Stable — v1.0.0**, released 2026-07-18. The database, both validators, and the packaged
plugin mirror pass their full check suites, and three headless behavioral probes were recorded
as release evidence under
[`docs/plans/initial-build/evidence/`](docs/plans/initial-build/evidence/).

One caveat is inherent to the design: the documentation snapshot is current **as of its stamp**,
not forever. Anything published upstream after `snapshot_date` is unverified, and the skill says
so rather than guessing. Read the stamp any time with:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT key, value FROM meta;"
```

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the development setup,
the exact validation commands, and the one rule that breaks CI more than any other (the plugin
mirror must stay byte-identical). Participation is governed by our
[Code of Conduct](CODE_OF_CONDUCT.md).

To report a security issue, please follow [SECURITY.md](SECURITY.md) rather than opening a
public issue.

## License

Released under the [MIT License](LICENSE).

The bundled documentation snapshot is derived from the official
[FastMCP documentation](https://github.com/PrefectHQ/fastmcp), which carries its own license;
this project redistributes it as a build artifact for offline reference.

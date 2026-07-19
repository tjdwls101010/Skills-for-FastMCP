# Skills for FastMCP — Documentation

This is the complete documentation for **Skills for FastMCP**, a Claude Code skill that makes
Claude write MCP servers against the current FastMCP 3.x API instead of the FastMCP 2.x API it
remembers from training — and that consults with you on the architecture before writing anything.

The [README](../../README.md) is the front door and gets you installed. These pages are the
depth behind it.

**New here?** Start with [Overview](Overview.md) to understand what the project is for, then
[Getting-Started](Getting-Started.md) to install it and see it work.

## Contents

### Understanding the project

| Page | What it covers |
|---|---|
| [Overview](Overview.md) | The problem, what this does about it, who it's for, and its non-goals |
| [Concepts](Concepts.md) | The vocabulary: MCP, skills, plugins, the forcing function, FTS5 — in dependency order |
| [Architecture](Architecture.md) | Components, the build pipeline, the request flow, and the design decisions behind them |

### Using it

| Page | What it covers |
|---|---|
| [Getting-Started](Getting-Started.md) | Prerequisites, three install methods, first use, and how to confirm the skill fired |
| [Usage-Guides](Usage-Guides.md) | Both behavior modes, and recipes for querying the database yourself |
| [Consultant-Rubric](Consultant-Rubric.md) | The ten design dimensions in full, with the worked example |
| [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md) | The twelve 2.x reflexes that are wrong in 3.x, with correct replacements |
| [Troubleshooting](Troubleshooting.md) | Symptoms mapped to causes and fixes |

### Maintaining and extending it

| Page | What it covers |
|---|---|
| [Coverage-and-Limits](Coverage-and-Limits.md) | Exactly what the corpus contains, what is excluded and why, and the provenance stamp |
| [Maintenance-and-Release](Maintenance-and-Release.md) | Refreshing the snapshot, the mirror rule, versioning, and the release checklist |
| [Customization](Customization.md) | Adapting the corpus, the rubric, the skill itself — or forking it for another framework |

## Conventions used in these pages

- **Paths** are relative to the repository root unless stated otherwise.
- **Commands** assume `python3` (there is no `python` alias in the maintainer's environment) and
  a POSIX shell.
- **The database** is referred to by its canonical path,
  `.claude/skills/fastmcp/references/docs_official.db`. In a plugin install it sits next to
  `SKILL.md` in the installed plugin directory instead.
- **Snapshot facts** (document counts, versions, dates) describe the v1.0.0 snapshot —
  FastMCP v3.4.4, dated 2026-07-08. After a refresh, the database's own `meta` table is
  authoritative over any number written in prose here.

## Beyond the wiki

- [`docs/plans/initial-build/`](../plans/initial-build/) — the original design documents,
  including all twelve numbered decisions (D1–D12) with their rationale, the corpus
  specification, and the three-layer validation plan.
- [`docs/plans/initial-build/evidence/`](../plans/initial-build/evidence/) — recorded release
  evidence for v1.0.0, including the raw transcripts of three headless behavioral probes.
- [`.claude/harness-spec.md`](../../.claude/harness-spec.md) — the component inventory and drift
  anchor.
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — how to contribute, and what CI checks.

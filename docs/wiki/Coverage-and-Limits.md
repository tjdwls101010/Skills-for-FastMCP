# Coverage and Limits

## What is in the corpus (~180 docs)

Built from the `docs/` folder of `PrefectHQ/fastmcp` (the gofastmcp.com Mintlify
site). Counts are `.mdx` files per top-level folder at the v3.4.4 snapshot.

| Folder | Count | What it is |
|---|---|---|
| getting-started | 7 | welcome, installation, quickstart, the four upgrading guides |
| servers | 44 | the heart of the corpus — tools/resources/prompts/context, transforms, providers, composition, elicitation/sampling, middleware, tasks, auth, testing |
| clients | 19 | the FastMCP Client (used to test servers and consume MCP from Python) |
| deployment | 5 | running-server, http, server-configuration, sandboxed-agents, prefect-horizon |
| development | 9 | contributing, releases, tests, v3/v4 notes |
| patterns | 3 | cli, contrib, testing |
| cli | 7 | overview, running, inspecting, install-mcp, auth, client, generate-cli |
| tutorials | 3 | what MCP is, create-mcp-server, rest-api |
| community | 1 | showcase |
| more | 2 | faq, settings |
| python-sdk | 50 | auto-generated API reference, one file per module — exact signatures |
| integrations | 30 | OAuth providers, frameworks (FastAPI, OpenAPI), SDKs, host setup |

Total ≈ **180**, with a validation band of **150–220** so the upstream docs can
drift between snapshots without failing the build. A count outside the band means
the INCLUDE list or the upstream layout changed and must be re-examined.

`changelog.mdx` is not a docs row — it is parsed into the structured `changelog`
table (one row per `<Update>` block, ~94 rows).

## What is deliberately excluded (and why)

| Excluded | Why |
|---|---|
| `v2/` (81 docs) | Previous-major docs. Putting deprecated APIs into a database whose whole purpose is *current*-API truth would reproduce the exact staleness problem the project exists to fix. The sanctioned way to reason about 2.x is the retained `getting-started/upgrading/from-fastmcp-2` migration guide. |
| `apps/` (13 docs) | The Apps subsystem (tools that return interactive UI) is a v1.0.0 scope cut. SKILL.md declares the limit and points at gofastmcp.com. Revisit in a later minor version if consultations hit it. |
| `updates.mdx` | Marketing-flavored duplicate of the changelog. |
| snippets, assets, css, JS, JSON | Not documentation. |

`validate_docs_db.py` asserts zero `v2/` and zero `apps/` rows, so a leak fails CI
rather than silently poisoning the corpus.

## Provenance

Every snapshot is stamped in the `meta` table:

```sql
SELECT key, value FROM meta;
--   snapshot_date   = the newest changelog date (e.g. 2026-07-08)
--   source_repo     = https://github.com/PrefectHQ/fastmcp
--   source_commit   = the exact commit the docs were built from
--   doc_count, built_at, schema_version
```

Treat any FastMCP release newer than `snapshot_date` as unverified.

## The v4 tripwire

A FastMCP v4 built on the MCP Python SDK v2 is already documented (snake_case
protocol fields, an `mcp_types` package, a pydantic ≥ 2.12 floor). When the
`changelog` table's newest `version` starts with `v4.`:

- the SKILL.md gotchas table must be revisited — the 2→3 reflexes will be joined
  or replaced by 3→4 ones;
- `validate_docs_db.py`'s `newest changelog version starts with v3.` assertion
  must be bumped to `v4.`;
- the excluded/migration set (which upgrading guides to keep) changes.

Do all of this **in the same refresh**, not as a follow-up.

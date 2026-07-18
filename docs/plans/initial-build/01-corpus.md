# 01 — Corpus: what goes into docs_official.db

Source snapshot: the `docs/` folder of `https://github.com/PrefectHQ/fastmcp.git` (Mintlify site, gofastmcp.com). Planning-time copy at `.tmp/docs_fastmcp/`; see D8 in 00 for the re-clone instruction.

## Inventory at planning time (2026-07-18, FastMCP v3.4.4)

Counts are `.mdx` files found recursively per top-level entry.

### Included (≈ 180 docs)

| Folder | Count | Notes |
|---|---|---|
| getting-started/ | 7 | welcome, installation, quickstart, upgrading/{from-fastmcp-2, from-fastmcp-3, from-mcp-sdk, from-low-level-sdk} |
| servers/ | 44 | The heart of the corpus: server, tools, resources, prompts, context; transforms/* (tool-transformation, code-mode, tool-search, namespace, resources-as-tools, prompts-as-tools); providers/* (overview, local, filesystem, proxy, skills, custom); composition, visibility, tool-fingerprinting; elicitation, sampling, progress, logging, pagination, icons; middleware, dependency-injection, lifespan, storage-backends, tasks, versioning; authorization, telemetry, testing |
| clients/ | 19 | The FastMCP Client (used for testing servers and consuming MCP from Python) |
| deployment/ | 5 | running-server, http, server-configuration, sandboxed-agents, prefect-horizon |
| development/ | 9 | contributing, releases, tests, v3-notes/{v3-features, auth-provider-env-vars} |
| patterns/ | 3 | cli, contrib, testing |
| cli/ | 7 | overview, running, inspecting, install-mcp, auth, client, generate-cli |
| tutorials/ | 3 | mcp (what MCP is), create-mcp-server, rest-api |
| community/ | 1 | showcase |
| more/ | 2 | faq, settings |
| python-sdk/ | 50 | Auto-generated API reference, one file per module (`fastmcp-server-server.mdx` style). Exact signatures with GitHub source links. |
| integrations/ | 30 | OAuth providers (github, google, azure, auth0, workos, …), frameworks (fastapi, openapi, pydantic-ai), SDKs (anthropic, openai, gemini), hosts (claude-code, claude-desktop, cursor, chatgpt, gemini-cli, goose), mcp-json-configuration |

Total expected: **100 core + 50 python-sdk + 30 integrations = 180**. Validation band: **150–220** (allows the upstream docs to drift a bit between snapshot refreshes without failing the build; a count outside the band means the INCLUDE list or the upstream layout changed and must be re-examined).

### Excluded

| Entry | Count | Why excluded |
|---|---|---|
| v2/ | 81 | Previous-major docs. Including them would put deprecated APIs into the DB whose whole purpose is current-API truth — reproducing, inside the DB, the exact staleness problem the project exists to fix. The current corpus keeps the official 2→3 migration guide (`getting-started/upgrading/from-fastmcp-2.mdx`), which is the sanctioned way to reason about 2.x code. |
| apps/ | 13 | User decision (2026-07-18): the Apps subsystem (tools returning interactive UI via Prefab) is out of scope for v1.0.0. SKILL.md must declare this limit. Revisit in a later minor version if consultations hit it. |
| updates.mdx | 1 | Marketing-flavored duplicate of changelog.mdx. |
| changelog.mdx | 1 | Not excluded from the *build* — parsed into the `changelog` table instead of a docs row. See 02. |
| snippets/ | 5 | Not standalone docs; JSX component definitions consumed by the import-handling pass. See below. |
| assets/, css/, public/, images, `*.js`, `*.json`, .cursor/, .ccignore, community/README.md | — | Not documentation. `docs.json` (Mintlify nav) is read by nothing at build time; the INCLUDE list below is directory-based. |

## Snippets: what they are here, and how each is handled

Unlike LangChain's snippets (content fragments meant to be inlined), FastMCP's five snippets are **JSX component definitions**. The correct handling is per-snippet substitution, applied wherever the component tag appears after its import line is removed:

| Snippet | Definition | Handling |
|---|---|---|
| version-badge.mdx | `export const VersionBadge = ({ version }) => …"New in version {version}"` | Replace `<VersionBadge version="X" />` with `*New in version X*` — this is semantic information (which release introduced the feature) and must survive into the DB. |
| prefab-pin-warning.mdx | Static `<Tip>` telling users to pin `prefab-ui` | Replace tag with the Tip's plain text. (Only used by apps/ docs, so likely moot after the apps exclusion — implement the substitution anyway for robustness.) |
| local-focus.mdx | `export const LocalFocusTip = () => <Tip>…STDIO transport focus…</Tip>` | Replace tag with the Tip's plain text (used across integrations/). |
| prefab-demo-frame.mdx | React iframe demo loader | Drop the tag (and any surrounding `<div style={{…}}>` wrapper is left as-is; it is harmless text). |
| youtube-embed.mdx | React iframe embed | Drop the tag. |

Import syntax gotcha: FastMCP uses **named** imports (`import { VersionBadge } from '/snippets/version-badge.mdx'`) alongside occasional default imports (`import PrefabPinWarning from '/snippets/prefab-pin-warning.mdx'`). The forked import regex must accept both forms; the LangChain script only handled default imports.

## changelog.mdx structure

94 blocks of the form:

```mdx
<Update label="v3.4.4" description="2026-07-08">
  …markdown release notes…
</Update>
```

Parse each block into one `changelog` row: `version` = label, `date` = description, `body` = inner markdown. Newest-first order in the file; store as-is (queries sort explicitly).

## High-value docs the implementation must spot-check in the built DB

- `getting-started/upgrading/from-fastmcp-2` — the 2→3 breaking-changes list (feeds SKILL.md gotchas; also a regression check target: body must contain `on_duplicate`).
- `getting-started/upgrading/from-fastmcp-3` — the v4/MCP-SDK-v2 migration guide (snake_case fields, `mcp_types` package, pydantic ≥ 2.12 floor).
- `servers/providers/skills` — SkillsDirectoryProvider (the "make my skills folder an MCP" consultation; regression check: body must contain `SkillsDirectoryProvider`).
- `integrations/openapi` — REST-API-to-MCP conversion (the "make xxx API an MCP" consultation).
- `servers/composition` — multi-server composition (the "whole harness as MCP" consultation).

## python-sdk formatting note

Auto-generated files contain `<sup><a href="https://github.com/PrefectHQ/fastmcp/blob/…"><Icon icon="github" …/></a></sup>` link decorations after every symbol heading. Optional cleanup in the build script: strip `<sup>…</sup>` spans from python-sdk bodies to reduce FTS noise. This is a nice-to-have, not a validation requirement — if it complicates the script, skip it and note the decision in the build report.

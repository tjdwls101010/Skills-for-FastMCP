# 00 — Goals and decisions

Planning session: 2026-07-18, with the repository owner (Seongjin). This plan was produced in a dedicated planning session; a fresh Claude session implements it by reading docs 00–07 in order and executing 07-implementation-checklist.md phase by phase.

## Context

This repository transplants the architecture of [Skills-for-Langchain](https://github.com/tjdwls101010/Skills-for-Langchain) v1.2.0 to a new domain: **FastMCP** (the Python framework for building MCP servers, now at v3.4.4 under PrefectHQ stewardship).

The Skills-for-Langchain architecture, proven in production, has three pillars:

1. **A forcing function** in SKILL.md: Claude's pretrained knowledge of the framework is declared stale, and the skill routes every API question to a queryable source of truth instead of memory.
2. **A docs database** (`references/docs_official.db`): a SQLite/FTS5 snapshot of the current official docs that Claude queries with SQL. This replaced hand-distilled "delta" reference files, which silently dropped content and were hard to refresh.
3. **A consultant persona** (`references/consultant.md`): the skill does not just answer API questions — it interviews the user about what they want to build, reaches agreement, and proposes an architecture grounded in the docs DB.

Why FastMCP is an even better fit for this architecture than LangChain: FastMCP 3.x (late 2025 onward) rewrote large parts of the framework — the provider system, transforms, background tasks, and apps are all 3.x-new — while most models' pretrained knowledge is FastMCP 2.x or the old `mcp` SDK's bundled FastMCP 1.0. The stale-reflex risk the forcing function exists for is worse here, and a v4 (MCP SDK v2, snake_case protocol fields) is already documented as upcoming.

## Goals

- G1. A `fastmcp` skill that makes Claude query current FastMCP docs instead of trusting its pretrained (mostly 2.x-era) API memory.
- G2. A consultant behavior: when the user describes something to expose as MCP ("make xxx API an MCP", "can my skills folder be an MCP?", "can a whole harness — CLAUDE.md + agents + skills + hooks — be an MCP?"), the skill interviews them in depth, reaches agreement, and proposes a FastMCP server architecture.
- G3. The same repo quality bar as Skills-for-Langchain: plugin packaging, marketplace, CI validation, CHANGELOG/SemVer coupling, wiki.
- G4. Refreshability: rebuilding the DB from a new docs snapshot is a scripted, validated operation, not a re-distillation.

## Non-goals

- Covering the FastMCP **Apps** subsystem (tools that return interactive UI). Excluded from the corpus by explicit user decision; SKILL.md must state this coverage limit and point at the official docs.
- Consulting on **pure client work** (Python programs that consume other MCP servers) as a first-class interview flow. Client docs are in the DB and questions get answered from it, but the consultant's interview and dimensions are optimized for server design.
- Covering FastMCP **2.x**. The DB contains only current-version docs plus the official 2→3 migration guide.

## Decisions

- **D1 — Repo replica, single-source skill.** Mirror the Skills-for-Langchain repo structure — `.claude-plugin/` packaging, CI validate workflow, CHANGELOG.md, README.md, **and** the docs/wiki set (user chose to include wiki from v1.0.0) — with **one deliberate departure: no byte-identical `plugins/` mirror.** The skill lives exactly once at `.claude/skills/fastmcp/`; it is packaged as a plugin by a root `.claude-plugin/plugin.json` whose `skills` field points at `./.claude/skills/fastmcp` plus a `.claude-plugin/marketplace.json` entry with `source: "./"` (marketplace-root). Rationale and exact wiring in **D13**.
- **D2 — Corpus scope.** Include the ten core folders (getting-started, servers, clients, deployment, development, patterns, cli, tutorials, community, more ≈ 100 docs) plus `python-sdk/` (50 auto-generated API reference docs — the source of exact signatures) plus `integrations/` (30 docs — OAuth providers, FastAPI, host setup). Exclude `apps/` (13 docs, user decision), `v2/` (81 stale-version docs whose inclusion would poison the "current API truth" the DB exists to provide), `updates.mdx` (duplicates changelog), and all non-`.mdx` files. Expected doc count ≈ 180. Details in 01.
- **D3 — changelog.mdx becomes the `changelog` table.** The 352 KB `changelog.mdx` (94 `<Update>` blocks, v3.4.4 back through 3.x) is parsed into a structured `changelog(version, date, body)` table, same shape as the Skills-for-Langchain DB — not stored as a docs row.
- **D4 — Consultant is server-design centric.** The interview, dimensions, and deliverable are optimized for "design an MCP server". Client usage appears where it naturally belongs (testing your server); pure client questions are answered from the DB without the full interview.
- **D5 — Ten design dimensions, run as a rubric, not rails.** The consultant does not ask about all ten in every conversation; it asks only about relevant ones, but self-checks all ten before presenting an architecture. Each dimension carries its *why* so situations outside the list can be reasoned about. Dimension list and wording in 04.
- **D6 — Build tooling is forked, not shared.** Copy `build_docs_db.py` / `validate_docs_db.py` from Skills-for-Langchain (vendored read-only under `docs/plans/initial-build/reference/`) and adapt them to the FastMCP docs dialect. No cross-repo shared tool — two repos with divergent dialects and only two consumers make generalization a speculative abstraction. Required adaptations in 02.
- **D7 — Naming and versioning.** Skill name `fastmcp`; plugin name `skills-for-fastmcp`; display name "Skills for FastMCP"; initial release **v1.0.0**; repo `https://github.com/tjdwls101010/Skills-for-FastMCP` (already created on GitHub, empty at planning time). SemVer coupled to CHANGELOG headings, enforced by CI, exactly like Skills-for-Langchain.
- **D8 — Docs provenance.** The planning-time snapshot at `.tmp/docs_fastmcp/` was hand-copied from the official repo's `docs/` folder and has no `.git`, so `source_commit` is unknown. The implementation session should re-clone fresh (sparse checkout of `docs/` from `https://github.com/PrefectHQ/fastmcp.git`) into `.tmp/docs_fastmcp`, recording the commit hash into `meta.source_commit`. Fallback if offline: build from the existing copy with `source_commit = "unknown (hand-copied snapshot, 2026-07-18)"`. The `.tmp/` directory is gitignored either way.
- **D9 — Snippet handling is transform/drop, not recursive inlining.** FastMCP's `/snippets/*.mdx` are JSX component definitions (not content fragments like LangChain's), so the Skills-for-Langchain recursive `expand_body()` is wrong here. Replace semantic tags with text (`<VersionBadge version="3.0.0" />` → `*New in version 3.0.0*`), inline the two static-Tip snippets as their text, drop the rest. Details in 02.
- **D10 — No language conditionals.** FastMCP docs have no `:::python`/`:::js` blocks (Python-only framework); the entire `strip_lang_conditionals()` machinery from the LangChain build script is deleted, not adapted.
- **D11 — Stale-reflex gotchas come from the official migration guide.** `getting-started/upgrading/from-fastmcp-2.mdx` contains an authoritative, numbered list of 2→3 breaking changes (and even a ready-made LLM upgrade prompt). SKILL.md's "gotchas the DB can't surface" section is distilled from it plus the v4 pre-migration guide (`from-fastmcp-3.mdx`). Distillation targets in 03.
- **D12 — Planning artifacts live in the new repo.** These plan docs, the vendored reference files, and `.claude/harness-spec.md` are committed to Skills-for-FastMCP itself (initial commit of the repo), so the implementation session needs nothing from the Skills-for-Langchain checkout.
- **D13 — Single-source plugin packaging (supersedes the LangChain mirror pattern).** Skills-for-Langchain kept a second, byte-identical copy of the skill under `plugins/skills-for-langchain/skills/` and a CI check enforcing byte-identity; its own docs call the forgotten mirror re-copy the #1 CI failure mode. Current Claude Code makes that copy unnecessary: a plugin manifest's `skills` field accepts a custom directory (it adds to the default `skills/` scan), and a marketplace plugin entry can resolve its `source` to the repo root. So this repo ships **one** skill tree at `.claude/skills/fastmcp/`, packaged by two small config files at the repo root:
  - `.claude-plugin/plugin.json` — plugin manifest with `"skills": ["./.claude/skills/fastmcp"]`. There is no default `skills/` directory at the root, so only this path loads. This also makes the repo sideloadable via `--plugin-dir <repo>` (which reads `plugin.json`).
  - `.claude-plugin/marketplace.json` — one plugin entry, `"source": "./"` (resolves to the repo root, the directory containing `.claude-plugin/`), with `strict` left at its default `true` so `plugin.json` stays the authority for components. The entry does **not** re-declare `skills`.
  Result: no `plugins/` directory, no mirror copy, no byte-identity check, no per-edit re-copy step. **The implementation session MUST verify the skill actually loads both ways** — a real local marketplace install (`/plugin marketplace add <repo>` → install) and `--plugin-dir <repo>` — because this root-source + custom-path combo is the newer mechanism, not the battle-tested LangChain layout. Documented fallback if it misbehaves: declare the skill in the marketplace entry itself (`source: "./"`, `skills: ["./.claude/skills/fastmcp"]`, `strict: false`, and then no `plugin.json`). Reference: Claude Code plugins-reference (custom `skills` path — "Adds to the default `skills/` scan") and plugin-marketplaces ("Advanced plugin entries" + marketplace-root `source`).

## Process notes for the implementation session

- The user communicates in Korean; write code/docs in English, converse in Korean.
- When a user decision is needed, use AskUserQuestion — but put **all** context into the question text, option descriptions, and previews. Message prose sent in the same turn as the tool call does not render in this user's terminal.
- The user is a non-expert product owner: explain tradeoffs honestly, push back when warranted, and do not silently guess (per the repo-level CLAUDE.md conventions in Skills-for-Langchain, which apply in spirit here).
- Known environment gotchas from the Skills-for-Langchain implementation session: use `python3` (no `python` on PATH); `grep` is aliased to `ugrep` (prefer `find | xargs grep` or Grep tool); macOS has no `timeout`/`gtimeout` (use background jobs); the skill lives at a single location (`.claude/skills/fastmcp/`) — there is no plugin mirror to re-copy (D1/D13).

## Reading order for the implementation session

00 (this file) → 01 corpus → 02 DB & build script → 03 SKILL.md → 04 consultant → 05 repo scaffolding → 06 validation → 07 implementation checklist. The checklist is the execution driver; docs 01–06 are its specifications.

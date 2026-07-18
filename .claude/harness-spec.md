# Harness spec — Skills for FastMCP

Status: **planned** (planning session 2026-07-18; no components generated yet). This spec records the agreements reached in the planning interview. The implementation session executes `docs/plans/initial-build/07-implementation-checklist.md` and flips statuses here to implemented.

## Context

Transplant of the Skills-for-Langchain v1.2.0 architecture (forcing function + docs_official.db + consultant persona) to FastMCP 3.x. Full background and every decision with rationale: `docs/plans/initial-build/00-goals-and-decisions.md` (D1–D12). This spec stays deliberately thin during planning — the plan docs are the source of truth until implementation, after which this file becomes the standing inventory.

## Goals

- G1. Claude queries current FastMCP docs (SQLite/FTS5 DB) instead of trusting stale 2.x-era pretrained memory.
- G2. Consultant behavior for MCP server design: interview → agreement → architecture proposal grounded in the DB.
- G3. Same packaging/validation quality bar as Skills-for-Langchain (plugin, marketplace, CI, SemVer/CHANGELOG coupling, wiki).
- G4. Scripted, validated DB refresh.

## Behavior inventory

- B1. On FastMCP/MCP-server-building work, load the skill and query the DB before any API claim. (planned)
- B2. On "expose X as MCP" intents, run the consultant flow: interview (self-contained AskUserQuestion, ≤4/round), agreement summary, then architecture. (planned)
- B3. Ten-dimension rubric self-check before any architecture is presented; dimensions carry their why. (planned)
- B4. Stale-reflex corrections (2.x → 3.x gotchas table) applied when reading or writing FastMCP code. (planned)
- B5. Coverage limits declared honestly: apps and v2 not in the DB; snapshot version/date quoted on request. (planned)
- B6. Near-miss boundary: Claude Code MCP *configuration* asks are not routed to this skill. (planned)

## Components

| Component | Spec | Status |
|---|---|---|
| `.claude/skills/fastmcp/SKILL.md` | docs/plans/initial-build/03 | planned |
| `.claude/skills/fastmcp/references/consultant.md` | docs/plans/initial-build/04 | planned |
| `.claude/skills/fastmcp/references/docs_official.db` | docs/plans/initial-build/01–02 | planned |
| `scripts/build_docs_db.py` | docs/plans/initial-build/02 | planned |
| `scripts/validate_docs_db.py` | docs/plans/initial-build/02 | planned |
| `scripts/validate_evidence.py` | docs/plans/initial-build/02 | planned |
| Plugin packaging — root `.claude-plugin/plugin.json` + `marketplace.json`, single-source (no mirror) — + CI + README + wiki | docs/plans/initial-build/05 | planned |

## Validation

Three layers per `docs/plans/initial-build/06-validation.md`: mechanical (build self-checks, two validators, CI), content spot checks, behavioral headless probes (user-consented). Release acceptance criteria listed there.

## Change history

- 2026-07-18 — Planning session (harness-creator): interview completed; corpus, consultant scope, dimensions, tooling strategy, and scaffolding agreed; plan docs 00–07 written; repo initialized and pushed. No components generated.
- 2026-07-18 — Plan revision: dropped the byte-identical `plugins/` mirror in favor of single-source packaging (root `plugin.json` `skills` path + marketplace-root `source: "./"`); see 00 D13. Removed the mirror byte-identity check and `--mirror`/re-copy steps across docs 00, 02, 03, 05, 06, 07. No components generated.

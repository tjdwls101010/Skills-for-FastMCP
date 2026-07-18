# Harness spec — Skills for FastMCP

Status: **implemented** (v1.0.0; implementation session 2026-07-18). This spec records the agreements reached in the planning interview and the state of the components that realize them. It is the drift anchor for future harness-creator invocations on this repo.

## Context

Transplant of the Skills-for-Langchain v1.2.0 architecture (forcing function + docs_official.db + consultant persona) to FastMCP 3.x. Full background and every decision with rationale: `docs/plans/initial-build/00-goals-and-decisions.md` (D1–D12). This spec stays deliberately thin during planning — the plan docs are the source of truth until implementation, after which this file becomes the standing inventory.

## Goals

- G1. Claude queries current FastMCP docs (SQLite/FTS5 DB) instead of trusting stale 2.x-era pretrained memory.
- G2. Consultant behavior for MCP server design: interview → agreement → architecture proposal grounded in the DB.
- G3. Same packaging/validation quality bar as Skills-for-Langchain (plugin, marketplace, CI, SemVer/CHANGELOG coupling, wiki).
- G4. Scripted, validated DB refresh.

## Behavior inventory

- B1. On FastMCP/MCP-server-building work, load the skill and query the DB before any API claim. (implemented; probes 1–3 all ran DB queries before answering)
- B2. On "expose X as MCP" intents, run the consultant flow: interview (self-contained AskUserQuestion, ≤4/round), agreement summary, then architecture. (implemented; probe 2 demonstrated the full posture)
- B3. Ten-dimension rubric self-check before any architecture is presented; dimensions carry their why. (implemented; `references/consultant.md`)
- B4. Stale-reflex corrections (2.x → 3.x gotchas table) applied when reading or writing FastMCP code. (implemented; probe 3 corrected constructor kwargs, `tool.disable`, async `ctx` state)
- B5. Coverage limits declared honestly: apps and v2 not in the DB; snapshot version/date quoted on request. (implemented; SKILL.md §Coverage limits)
- B6. Near-miss boundary: Claude Code MCP *configuration* asks are not routed to this skill. (implemented; in the description and SKILL.md near-miss line)

## Components

| Component | Spec | Status |
|---|---|---|
| `.claude/skills/fastmcp/SKILL.md` | docs/plans/initial-build/03 | implemented (12 gotchas DB-verified) |
| `.claude/skills/fastmcp/references/consultant.md` | docs/plans/initial-build/04 | implemented (10 dimensions + worked example, hooks-don't-map note) |
| `.claude/skills/fastmcp/references/docs_official.db` | docs/plans/initial-build/01–02 | implemented (v3.4.4 snapshot, 180 docs, 94 changelog rows, 2.43 MB, commit 66c0270) |
| `scripts/build_docs_db.py` | docs/plans/initial-build/02 | implemented (fail-fast verified) |
| `scripts/validate_docs_db.py` | docs/plans/initial-build/02 | implemented (21/21 checks) |
| `scripts/validate_evidence.py` | docs/plans/initial-build/02 | implemented |
| Plugin mirror + marketplace + CI + README + wiki + CLAUDE.md | docs/plans/initial-build/05 | implemented (mirror byte-identical) |

## Validation

Three layers per `docs/plans/initial-build/06-validation.md`: mechanical (build self-checks, two validators, CI), content spot checks, behavioral headless probes (user-consented). Release acceptance criteria listed there.

## Change history

- 2026-07-18 — Planning session (harness-creator): interview completed; corpus, consultant scope, dimensions, tooling strategy, and scaffolding agreed; plan docs 00–07 written; repo initialized and pushed. No components generated.
- 2026-07-18 — Implementation session (harness-creator, v1.0.0): executed 07-implementation-checklist Phases A–F. Re-cloned the FastMCP docs (commit `66c0270`, zero drift from the planning snapshot), forked and adapted the three scripts to the FastMCP dialect (new schema with `section`/`description`, 3-column FTS, `changelog(version,date,body)`; per-component snippet transform/drop replacing recursive inlining; robust `<Update>` parser capturing all 94 blocks), built the DB (180 docs, 2.43 MB), wrote SKILL.md and consultant.md, and generated all scaffolding. All Layer 1 validators green, Layer 2 spot checks recorded, and Layer 3 probes 1–3 all passed (evidence + transcripts under `docs/plans/initial-build/evidence/`). Two documented refinements of the plan, both benign and within implementation latitude: (a) the changelog parser reads attributes order-independently so the one out-of-order ancient block (`v0.3.2`) is captured, realizing the plan's stated 94-block expectation; (b) the SKILL.md example query `MATCH 'skills NEAR provider'` was corrected to the valid FTS5 functional form `NEAR(skills provider, 10)` (a bare `NEAR` matches nothing), and the bare `<VersionBadge />` prose tag maps to the lowercase words so `MATCH 'VersionBadge'` stays at zero rows.

# 07 — Implementation checklist

Execution driver for the implementation session. Work top to bottom; every item names its verification. Specs live in 01–06 — this file intentionally repeats no detail.

## Phase A — Bootstrap & corpus

- [ ] A1. Clone/pull this repo; confirm working dir is the repo root and `docs/plans/initial-build/` is present.
- [ ] A2. Re-clone the docs snapshot (D8): sparse checkout of `docs/` from `https://github.com/PrefectHQ/fastmcp.git` into `.tmp/docs_fastmcp`; record the commit hash. Fallback: keep the existing copy, `source_commit = "unknown (hand-copied snapshot, 2026-07-18)"`. → verify: per-folder mdx counts roughly match 01 (getting-started 7, servers 44, clients 19, deployment 5, development 9, patterns 3, cli 7, tutorials 3, community 1, more 2, python-sdk 50, integrations 30); flag deviations > ±10% before proceeding.
- [ ] A3. Confirm `.gitignore` covers `.tmp/` and `.DS_Store`. → verify: `git status` clean of snapshot files.

## Phase B — Build script & DB (spec: 02)

- [ ] B1. Copy `docs/plans/initial-build/reference/{build_docs_db.py,validate_docs_db.py,validate_evidence.py}` into `scripts/` and adapt per 02 (delete lang-conditionals and recursive expansion; add named-import regex, snippet substitutions, `<Update>` changelog parser, INCLUDE list, band numbers, name constants). → verify: script runs end-to-end with fail-fast on a deliberately broken input (e.g. temporarily add a fake unknown snippet import to one file, expect `die()`, then revert).
- [ ] B2. Build the DB to `.claude/skills/fastmcp/references/docs_official.db`. → verify: build report per-section counts; doc_count in band; DB size sanity (≈ 3–5 MB, investigate if > 8 MB).
- [ ] B3. `python3 scripts/validate_docs_db.py` → all checks pass.
- [ ] B4. Layer 2 spot checks from 06 → record outputs.

## Phase C — SKILL.md (spec: 03)

- [ ] C1. Write `.claude/skills/fastmcp/SKILL.md` per 03, using `reference/SKILL.md` as the structural template. → verify: every gotcha row backed by a DB query hit; every example query in the doc actually runs against the built DB and returns rows.
- [ ] C2. Re-read the description against near-miss triggers: should fire on "make X an MCP" phrasing without the word FastMCP; should NOT fire on Claude Code MCP *configuration* asks. Adjust wording if needed.

## Phase D — Consultant (spec: 04)

- [ ] D1. Write `references/consultant.md` per 04. → verify: all ten dimensions present with why + Find-in-the-DB queries; the worked example's APIs each verified against the DB; the hooks-don't-map honesty note present.

## Phase E — Scaffolding (spec: 05)

- [ ] E1. `.claude-plugin/plugin.json` (with `"skills": ["./.claude/skills/fastmcp"]`) + `.claude-plugin/marketplace.json` (single entry, `source: "./"`), LICENSE (MIT), CHANGELOG.md `[1.0.0]`, README.md per 05.
- [ ] E2. Verify single-source plugin load (D13) — no mirror copy exists to make. → verify: `--plugin-dir <repo>` lists the `fastmcp` skill **and** a local marketplace install (`/plugin marketplace add <repo>` → install) lists it too; if either fails, apply the strict:false fallback from 00 D13.
- [ ] E3. CI workflow `.github/workflows/validate.yml` per 05.
- [ ] E4. Wiki pages (5) per 05.
- [ ] E5. `python3 scripts/validate_evidence.py` → passes.

## Phase F — Validation (spec: 06)

- [ ] F1. Full Layer 1 suite locally. → all green.
- [ ] F2. Ask the user for Layer 3 consent (AskUserQuestion, self-contained). If yes: run probes 1–2 (3 optional), judge against pass criteria, save transcripts under `docs/plans/initial-build/evidence/` (create dir).
- [ ] F3. Update `.claude/harness-spec.md`: statuses planned → implemented, Change history entry, validation results summarized.

## Phase G — Release

- [ ] G1. Whitespace check (`git show --check` on staged work, or `git diff --check` before commit).
- [ ] G2. Commit on a branch (e.g. `build/v1.0.0`), push, open PR to main; confirm CI green.
- [ ] G3. Merge per user preference (ask). Tag `v1.0.0` on main.
- [ ] G4. Post-release smoke: fresh dir, `claude --plugin-dir <repo>` (or marketplace install) loads the skill.
- [ ] G5. Update the user's project memory (Skills-for-Langchain project memory holds the cross-project index): record that Skills-for-FastMCP v1.0.0 shipped, plus any new build gotchas discovered.

## Standing rules for the session

- Follow the CLAUDE.md conventions of the Skills-for-Langchain repo in spirit (think before coding, simplicity first, surgical changes, goal-driven execution) — copy that CLAUDE.md into this repo as part of Phase E if it doesn't already exist, adapted references included.
- Any deviation from docs 00–06 discovered mid-implementation: stop, note it, and confirm with the user via a self-contained AskUserQuestion before diverging (the plan is an agreement, not a suggestion).
- Environment gotchas: `python3` not `python`; `grep` aliased to `ugrep`; no `timeout` on macOS. (No mirror re-copy step — single source, D13.)

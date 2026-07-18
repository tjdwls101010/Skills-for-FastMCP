# Working in this repository

This repo is a Claude Code skill package: a `fastmcp` skill that forces current-API
lookups against a docs database, plus the tooling that builds and validates that
database. Read `.claude/harness-spec.md` for the component inventory and
`docs/plans/initial-build/` for the full design rationale.

## Conventions

- **Think before coding.** Understand the plan doc that governs a change before
  editing. The specs in `docs/plans/initial-build/01–06` are agreements, not
  suggestions — a deviation discovered mid-work is a reason to stop and confirm,
  not to quietly diverge.
- **Simplicity first.** The skill's own authoring philosophy applies to this repo:
  prefer the smallest change that satisfies the goal; do not add generality
  (extra config, speculative flags, dead branches) for cases no one has.
- **Surgical changes.** Touch what the task needs and no more. Match the
  surrounding style; no drive-by reformatting.
- **Goal-driven, honest execution.** Report what actually happened — if a
  validator fails, say so with its output; do not claim something runs end to end
  if it was not exercised.
- **Language.** The maintainer communicates in Korean; converse in Korean, write
  code and docs in English.

## The mirror rule (the #1 CI failure mode)

The canonical skill tree at `.claude/skills/fastmcp/` and the plugin mirror at
`plugins/skills-for-fastmcp/skills/fastmcp/` must be **byte-identical at all
times**, including the `.db` blob. After editing anything under the canonical
tree, re-copy it to the mirror and confirm:

```bash
cp -R .claude/skills/fastmcp/. plugins/skills-for-fastmcp/skills/fastmcp/
diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp   # must be silent
python3 scripts/validate_evidence.py                                        # enforces it mechanically
```

`build_docs_db.py --mirror <mirror-db>` writes both database copies in one run;
prose files (SKILL.md, consultant.md) are copied by hand.

## Validation

- `python3 scripts/build_docs_db.py …` — builds the DB with self-checks.
- `python3 scripts/validate_docs_db.py` — schema, row-count bands, no v2/apps/
  snippet leakage, content regressions, FTS hits, meta.
- `python3 scripts/validate_evidence.py` — SemVer/CHANGELOG coupling and the
  byte-identical plugin mirror.
- CI runs all three plus a `git show --check` whitespace guard on every push/PR.

Every plugin-version bump needs a matching `## [x.y.z]` heading in `CHANGELOG.md`
(CI-enforced).

## Environment gotchas (macOS)

- Use `python3`; there is no `python` on PATH.
- `grep` is aliased to `ugrep`; prefer the editor's search tools or
  `find … | xargs grep` for reliability.
- There is no `timeout`/`gtimeout`; run long commands as background jobs and poll.

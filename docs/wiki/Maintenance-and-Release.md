# Maintenance and Release

*How to refresh the documentation snapshot, keep the packaged copy honest, and ship a release.
Written for whoever maintains this repository — including future you.*

## The one rule that breaks CI most often

Before anything else, because it will bite you first:

**The canonical skill and the plugin mirror must be byte-identical at all times.**

The skill exists at two paths — `.claude/skills/fastmcp/` (canonical) and
`plugins/skills-for-fastmcp/skills/fastmcp/` (packaged) — because the repository is both the
skill's development home and a distributable plugin marketplace. Every file must match byte for
byte, including the 2.4 MB `.db` blob.

After editing anything under the canonical tree:

```bash
cp -R .claude/skills/fastmcp/. plugins/skills-for-fastmcp/skills/fastmcp/
diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp   # must print nothing
python3 scripts/validate_evidence.py                                        # enforces it mechanically
```

`build_docs_db.py --mirror <mirror-db>` writes both database copies in one run, so a refresh
handles the `.db` automatically. **Prose files — `SKILL.md` and `consultant.md` — are copied by
hand.** Editing a canonical prose file and forgetting the re-copy is the historical number-one CI
failure in this repository. `validate_evidence.py` catches it with a SHA-256 over every file, but
locally it is faster to just always re-copy.

## Refreshing the database from a newer snapshot

There is no manual re-curation. Refresh is a scripted, validated operation — the point of the
whole architecture is that keeping current costs minutes of mechanical work rather than a
rewrite.

### 1. Re-clone the upstream documentation

Sparse and blobless — only `docs/` is needed, so this stays fast even though the FastMCP
repository is large:

```bash
rm -rf .tmp/fastmcp_clone
git clone --no-checkout --depth 1 --filter=blob:none \
  https://github.com/PrefectHQ/fastmcp.git .tmp/fastmcp_clone
(cd .tmp/fastmcp_clone && git sparse-checkout set docs && git checkout)
COMMIT=$(git -C .tmp/fastmcp_clone rev-parse HEAD)
echo "$COMMIT"
```

`.tmp/` is git-ignored, so build inputs never enter the repository.

### 2. Build

Writes both the canonical database and the plugin mirror in one run:

```bash
python3 scripts/build_docs_db.py \
  --src .tmp/fastmcp_clone/docs \
  --out .claude/skills/fastmcp/references/docs_official.db \
  --commit "$COMMIT" \
  --mirror plugins/skills-for-fastmcp/skills/fastmcp/references/docs_official.db
```

**Read the build report — do not just check the exit code.** The per-section counts and the
changelog line are where a quiet upstream restructure shows up:

- Per-section counts should be close to those in
  [Coverage-and-Limits](Coverage-and-Limits.md#what-is-in-the-corpus). A section that dropped by
  half deserves investigation even though the total may still be in band.
- The changelog line should name a newer version than the previous snapshot.
- The final size should be in the low megabytes. A warning fires above 8 MB.

The build fails atomically. A count outside 150–220, an unknown snippet component, a changelog
with fewer than 80 entries, or a failed self-check exits non-zero and leaves the previous
database untouched — a partial `.db` is never shipped. Causes and fixes are in
[Troubleshooting](Troubleshooting.md).

### 3. Validate

```bash
python3 scripts/validate_docs_db.py     # 22 checks: schema, bands, leakage, regressions, FTS, meta
python3 scripts/validate_evidence.py    # naming, SemVer ↔ CHANGELOG, byte-identical mirror
```

Expected:

```
All checks passed.
```
```
Release metadata passed: skills-for-fastmcp v1.0.0
Plugin mirror byte-identical: 3 files
```

### 4. Content spot checks

Mechanical validation confirms the artifact has the right shape. These confirm it has the right
*content* — they take two minutes and are the only thing standing between a structurally valid
database and a subtly wrong one:

```bash
DB=.claude/skills/fastmcp/references/docs_official.db

# Per-section counts against the corpus spec
sqlite3 -readonly $DB "SELECT section, COUNT(*) FROM docs GROUP BY section;"

# Snippet substitution worked: zero raw tags, but the transformed text is present
sqlite3 -readonly $DB "SELECT COUNT(*) FROM docs_fts WHERE docs_fts MATCH 'VersionBadge';"       # expect 0
sqlite3 -readonly $DB "SELECT COUNT(*) FROM docs_fts WHERE docs_fts MATCH '\"New in version\"';" # expect many

# The changelog head is sane
sqlite3 -readonly $DB "SELECT version, date FROM changelog ORDER BY date DESC LIMIT 3;"

# One python-sdk body reads cleanly (no leftover markup)
sqlite3 -readonly $DB "SELECT substr(body,1,400) FROM docs WHERE section='python-sdk' LIMIT 1;"
```

### 5. Re-verify the gotchas — the step everyone skips

Cross-check every entry in `SKILL.md`'s gotchas table against the refreshed
`getting-started/upgrading/*` documents. Upstream may have changed a correction, and a stale
gotcha is worse than a missing one — it is a confident instruction to write wrong code, carried
by the very mechanism meant to prevent that.

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT body FROM docs WHERE path = 'getting-started/upgrading/from-fastmcp-2';"
```

This is the one refresh step that requires judgement rather than a command, which is exactly why
it is the one that gets skipped. See [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md).

### 6. Bump the version and update the changelog

A refresh is a release. Follow [Versioning](#versioning) below.

## Versioning

Semantic versioning, with the plugin manifest and `CHANGELOG.md` coupled and enforced by CI.

| Change | Bump |
|---|---|
| Database refresh, no behavior change | **minor** |
| Skill behavior change (new gotcha, changed consultant flow) | **minor** |
| Breaking restructure (schema change, renamed skill or plugin) | **major** |
| Documentation-only fix | **patch**, or none |

Every version bump touches exactly two things:

1. `version` in `plugins/skills-for-fastmcp/.claude-plugin/plugin.json`
2. A matching `## [x.y.z]` heading in `CHANGELOG.md`

`validate_evidence.py` checks that the second exists for the first. CI fails without it — a
released version with no changelog entry is a version nobody can reason about.

## Release checklist

1. **Run the full local suite** — build (if the database changed), both validators, and the
   content spot checks from step 4. All green.
2. **Whitespace guard.** `git diff --check` before committing; CI runs `git show --check HEAD`
   and rejects trailing whitespace and space-before-tab.
3. **Mirror confirmed.** `diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp`
   silent.
4. **Commit on a branch, push, open a PR** to `main`, confirm CI green.
5. **Merge, then tag** `vX.Y.Z` on `main`.
6. **Post-release smoke test.** In a fresh directory:

   ```bash
   claude --plugin-dir <repo>/plugins/skills-for-fastmcp
   ```

   Confirm the skill appears in the listing, then ask it a FastMCP question and check that it
   queries the database. This exercises the *packaged* copy — the one users actually get — which
   no local test touches.
7. **Update [`.claude/harness-spec.md`](../../.claude/harness-spec.md)** with what changed. It is
   the drift anchor; a release it does not record is a release the next maintainer has to
   reverse-engineer.

## What CI does and does not do

`.github/workflows/validate.yml` runs on every push and pull request, on all branches, on
Python 3.12:

| Step | Command |
|---|---|
| Release metadata | `python3 scripts/validate_evidence.py` |
| Database invariants | `python3 scripts/validate_docs_db.py` |
| Whitespace guard | `git show --check HEAD` |

**CI validates the database but never rebuilds it.** The `.db` is a committed artifact — 2.4 MB,
committed twice, deliberately. Whoever regenerates it commits the result, and CI checks what was
committed. That is why the two validators are the gate: they are all that stands between a bad
database and the marketplace.

Both scripts are standard-library only, so CI needs no dependency installation step. Keeping it
that way is a maintenance constraint worth defending.

## Deeper validation layers

The three-layer plan from the original build is in
[`docs/plans/initial-build/06-validation.md`](../plans/initial-build/06-validation.md):

- **Layer 1 — mechanical.** Build self-checks plus both validators plus the whitespace guard.
  Runs on every push. Covered above.
- **Layer 2 — content spot checks.** Step 4 above. Every refresh.
- **Layer 3 — behavioral probes.** Headless Claude Code runs against the *packaged* plugin,
  checking real transcripts against pass criteria and a banned-reflex list (constructor
  `host`/`port`, `get_tools()`, `tool.disable()`, `PromptMessage(role=…)`, `mount(prefix=…)`,
  `FastMCP.as_proxy`, `import_server`, synchronous `ctx.set_state`). This spends real tokens, so
  it is a release-time activity with the maintainer's consent rather than a routine check.

The v1.0.0 probe results and raw transcripts are preserved in
[`docs/plans/initial-build/evidence/`](../plans/initial-build/evidence/) — all three probes
passed. That directory is where release evidence lives; add to it rather than replacing it, so
the record stays comparable across releases.

## The v4 tripwire

When the `changelog` table's newest `version` starts with `v4.`, `validate_docs_db.py` fails by
design. Revisit the gotchas table **first**, then bump the assertion, then reconsider the corpus
include and exclude sets — all in the same refresh. Details in
[Coverage-and-Limits](Coverage-and-Limits.md#the-v4-tripwire).

---

**Next:** [Customization](Customization.md) to change what gets built, or
[Troubleshooting](Troubleshooting.md) when something fails.

[← Back to the documentation index](README.md)

# Maintenance and Release

## Refreshing the database from a newer snapshot

There is no manual re-curation — refresh is a scripted, validated operation.

1. **Re-clone the docs** (sparse, blobless — only `docs/` is needed):

   ```bash
   rm -rf .tmp/fastmcp_clone
   git clone --no-checkout --depth 1 --filter=blob:none \
     https://github.com/PrefectHQ/fastmcp.git .tmp/fastmcp_clone
   (cd .tmp/fastmcp_clone && git sparse-checkout set docs && git checkout)
   COMMIT=$(git -C .tmp/fastmcp_clone rev-parse HEAD)
   ```

2. **Build** (writes both the canonical DB and the plugin mirror in one run):

   ```bash
   python3 scripts/build_docs_db.py \
     --src .tmp/fastmcp_clone/docs \
     --out .claude/skills/fastmcp/references/docs_official.db \
     --commit "$COMMIT" \
     --mirror plugins/skills-for-fastmcp/skills/fastmcp/references/docs_official.db
   ```

   Eyeball the per-section counts and the changelog line in the build report. A
   doc_count outside 150–220, or an unknown snippet, fails the build atomically —
   no partial DB is shipped.

3. **Validate**:

   ```bash
   python3 scripts/validate_docs_db.py     # schema, bands, no leakage, regressions, FTS, meta
   python3 scripts/validate_evidence.py    # SemVer/CHANGELOG coupling + byte-identical mirror
   ```

4. **Re-verify the gotchas.** Cross-check every row of SKILL.md's gotchas table
   against the refreshed `getting-started/upgrading/*` docs — upstream may have
   changed a reflex-correction. Fix any drift before releasing.

## The plugin-mirror rule

The canonical skill tree (`.claude/skills/fastmcp/`) and the plugin mirror
(`plugins/skills-for-fastmcp/skills/fastmcp/`) must be **byte-identical at all
times**, including the `.db`. The build's `--mirror` handles the database; prose
files are copied by hand:

```bash
cp -R .claude/skills/fastmcp/. plugins/skills-for-fastmcp/skills/fastmcp/
diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp   # must be silent
```

Editing a canonical file and forgetting the mirror re-copy is the historical #1 CI
failure mode. `validate_evidence.py` enforces it with a sha256 over every file.

## Versioning (SemVer, CI-enforced)

- DB refresh with no behavior change → **minor** bump.
- Skill behavior change (new gotcha, changed consultant flow) → **minor**.
- Breaking restructure → **major**.

Every version bump has:

1. an updated `version` in `plugins/skills-for-fastmcp/.claude-plugin/plugin.json`;
2. a matching `## [x.y.z]` heading in `CHANGELOG.md` (CI fails without it).

## Release steps

1. Run the full local suite (build, both validators) — all green.
2. Whitespace guard: `git diff --check` before commit (CI runs `git show --check`).
3. Commit on a branch, push, open a PR to `main`, confirm CI green.
4. Merge, then tag `vX.Y.Z` on `main`.
5. Post-release smoke: in a fresh directory,
   `claude --plugin-dir <repo>/plugins/skills-for-fastmcp` and confirm the skill
   appears in the listing.

## The v4 tripwire

When the `changelog` table's newest `version` starts with `v4.`, revisit the
gotchas table and bump `validate_docs_db.py`'s `v3.` assertion **in the same
refresh**. See [Coverage and Limits](Coverage-and-Limits.md#the-v4-tripwire).

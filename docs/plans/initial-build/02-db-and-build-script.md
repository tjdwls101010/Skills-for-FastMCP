# 02 — docs_official.db schema and scripts/build_docs_db.py

Fork base: `docs/plans/initial-build/reference/build_docs_db.py` and `reference/validate_docs_db.py` (vendored, read-only copies from Skills-for-Langchain v1.2.0). Copy them into `scripts/` and adapt per this document. Both stay stdlib-only Python 3.10+.

## Database schema — unchanged from Skills-for-Langchain

Keep the schema identical (same table names, same FTS5 external-content setup with triggers, same meta keys). Identical schema means the SKILL.md "how to query" section, the validators, and any future cross-skill tooling share one mental model.

```sql
docs(path TEXT PRIMARY KEY, title TEXT, description TEXT, section TEXT, body TEXT)
docs_fts  -- FTS5(title, description, body), external content=docs, porter unicode61, with INSERT/UPDATE/DELETE triggers
changelog(version TEXT, date TEXT, body TEXT)
meta(key TEXT PRIMARY KEY, value TEXT)  -- snapshot_date, built_at, source_repo, source_commit, doc_count, schema_version
```

- `path`: source-relative path without extension, e.g. `servers/providers/skills`, `getting-started/upgrading/from-fastmcp-2`.
- `section`: top-level folder (`servers`, `clients`, `python-sdk`, `integrations`, …) — enables `WHERE section = 'python-sdk'` filtering.
- `title`/`description`: from YAML frontmatter (`title:` and `description:`; fall back to `sidebarTitle:` when `title` is absent, then to the filename).
- `meta.source_repo` = `https://github.com/PrefectHQ/fastmcp` (note: moved from jlowin/fastmcp at v3).

## Build script adaptations (LangChain → FastMCP dialect)

### Delete outright

- `strip_lang_conditionals()` and `FENCE_RE` and the entire colon-count stack — FastMCP docs have no `:::python`/`:::js` conditionals (D10). Delete, do not adapt: dead generality is a maintenance trap.
- The recursive `expand_body()` snippet inliner, `MAX_DEPTH`, and the cycle guard — snippets here are JSX components, not content (D9).

### Change

1. **INCLUDE list** — directory-based, per 01:
   `getting-started, servers, clients, deployment, development, patterns, cli, tutorials, community, more, python-sdk, integrations`, plus the root-level `changelog.mdx` routed to the changelog parser. Everything else is ignored. `updates.mdx`, `v2/`, `apps/`, `snippets/` are explicitly NOT in the include list (asserting their absence in the validator is cheaper than special-casing them here).
2. **IMPORT_RE** — accept both import forms and capture all imported names:
   - named: `import { VersionBadge } from '/snippets/version-badge.mdx'` (possibly multiple names in one brace group)
   - default: `import PrefabPinWarning from '/snippets/prefab-pin-warning.mdx'`
   Import lines are removed from the body; each imported name is added to the per-file `names` set exactly as in the fork base, so the residual-tag check stays scoped to actually-imported names (this scoping was a hard-won fix in the LangChain build — a blanket PascalCase-tag regex false-positived on legit JSX in code examples).
3. **Snippet tag substitution** replaces snippet expansion. For each imported name still present as a tag in the body:
   - `VersionBadge` → replace `<VersionBadge version="X" />` (also tolerate `{'<VersionBadge version="X"/>'}` spacing variants) with `*New in version X*`.
   - `PrefabPinWarning`, `LocalFocusTip` → replace the tag with the snippet's static Tip text (hardcode the two strings in the script with a comment pointing at the snippet file; they are one sentence each).
   - `PrefabDemoFrame`, `YouTubeEmbed` → delete the tag (including multi-line tag bodies — match `<Name` through the closing `/>` across lines).
   - Any other imported-name tag left after substitution → `die()` with the file and tag name, same fail-fast posture as the fork base. An unknown snippet means upstream added one and the script must be taught about it consciously.
4. **Changelog parser** — new function: parse `changelog.mdx` into `<Update label description>` blocks with a non-greedy multi-line regex (`<Update label="([^"]+)" description="([^"]+)">(.*?)</Update>`, DOTALL); insert one `changelog` row per block. Assert ≥ 80 blocks parsed (94 at planning time) so a silent format change upstream fails loudly.
5. **python-sdk `<sup>` cleanup (optional)** — strip `<sup>…</sup>` spans in `section == 'python-sdk'` bodies. Skip if fiddly; see 01.
6. **Self-validation numbers** — doc_count band 150–220; FTS smoke query `MATCH 'provider'` must return rows; changelog ≥ 80 rows.

### Keep as-is

CLI shape (`--src --out [--commit] [--mirror]`), build-to-temp + atomic move, frontmatter parsing, the fail-fast `die()` posture, the final report printing per-section counts (mind the tuple-unpack orientation bug fixed in the fork base's history: iterate `for _subdir, pkg in INCLUDE` orientation carefully).

## scripts/validate_docs_db.py adaptations

Standalone read-only validator, run by CI and after every rebuild. Checks:

1. Tables `docs, docs_fts, changelog, meta` exist.
2. `doc_count` in 150–220 and equals `count(*) FROM docs`.
3. `changelog` has ≥ 80 rows and the newest row's version matches `^v3\.` (bump this assertion when v4 ships and the corpus is refreshed).
4. No leftover snippet import lines: zero rows `WHERE body LIKE '%from ''/snippets/%'`.
5. No v2 leakage: zero rows `WHERE path LIKE 'v2/%'`; no apps leakage: zero rows `WHERE path LIKE 'apps/%'`.
6. Regression — snippet substitution: zero rows `WHERE body LIKE '%<VersionBadge%'`.
7. Regression — content survived: `servers/providers/skills` body contains `SkillsDirectoryProvider`; `getting-started/upgrading/from-fastmcp-2` body contains `on_duplicate`.
8. FTS answers: `MATCH 'provider'` and `MATCH 'elicitation'` return > 0 rows.
9. All six meta keys populated.

Default `--db` path: `.claude/skills/fastmcp/references/docs_official.db`.

## scripts/validate_evidence.py adaptations

Fork `reference/validate_evidence.py` nearly verbatim; it is already slim. Change the constants: plugin root `plugins/skills-for-fastmcp`, expected names `skills-for-fastmcp`, marketplace source `./plugins/skills-for-fastmcp`, canonical tree `.claude/skills/fastmcp`. Checks remain: plugin/marketplace name coupling, `## [x.y.z]` CHANGELOG heading for the plugin version, and full-tree byte-identity of the plugin mirror (including the .db blob).

## Expected build command

```bash
python3 scripts/build_docs_db.py \
  --src .tmp/docs_fastmcp \
  --out .claude/skills/fastmcp/references/docs_official.db \
  --commit <source-commit-hash> \
  --mirror plugins/skills-for-fastmcp/skills/fastmcp/references/docs_official.db
python3 scripts/validate_docs_db.py
```

Expected DB size: LangChain's 216 docs produced ~4.4 MB; FastMCP's ~180 docs of similar density should land around 3–5 MB. If it comes out over ~8 MB, inspect for accidentally ingested non-doc content before shipping.

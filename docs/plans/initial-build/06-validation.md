# 06 — Validation plan

Three layers, from cheap to expensive. Layers 1–2 are mandatory before release; layer 3 requires the user's consent (it spends real tokens) but was decisive in the LangChain build — it caught nothing *because* the design worked, and that proof is the release evidence.

## Layer 1 — Mechanical (every build, and CI)

- `python3 scripts/build_docs_db.py …` self-validation: doc_count band 150–220, changelog ≥ 80 blocks, FTS smoke query, meta completeness. Build fails atomically (temp file, no partial DB shipped).
- `python3 scripts/validate_docs_db.py`: the full check list in 02 (schema, bands, no v2/apps/import leakage, `SkillsDirectoryProvider` and `on_duplicate` regressions, FTS answers, meta).
- `python3 scripts/validate_evidence.py`: plugin/marketplace naming, CHANGELOG heading for the current version, byte-identical plugin mirror.
- `git show --check` on the release commit (trailing whitespace).

## Layer 2 — Content spot checks (manual, once per build)

Run these queries against the built DB and eyeball the results:

1. `SELECT count(*) FROM docs GROUP BY section` — per-section counts match 01's table (±small upstream drift).
2. `SELECT body FROM docs WHERE path = 'getting-started/upgrading/from-fastmcp-2'` — the 13 breaking changes present; cross-check every row of SKILL.md's gotchas table against it.
3. `SELECT snippet(docs_fts,2,'[',']','…',20) FROM docs_fts WHERE docs_fts MATCH 'VersionBadge'` — expect **zero rows** (substitution worked) while `MATCH '"New in version"'` returns rows.
4. `SELECT version, date FROM changelog ORDER BY date DESC LIMIT 3` — v3.4.4 (or newer) on top with sane dates.
5. One python-sdk doc body — signatures readable, no import-line or `<sup>` garbage (if the optional cleanup was implemented).

## Layer 3 — Behavioral dry run (with user consent)

Headless probe, same technique as the LangChain v1.2.0 release evidence. From a scratch project dir:

```bash
claude -p "<probe prompt>" --plugin-dir <repo>/plugins/skills-for-fastmcp \
  --dangerously-skip-permissions --output-format stream-json
```

macOS note: no `timeout` binary — run as a background job and poll.

Probes (run at least the first two):

| Probe prompt | Pass criteria |
|---|---|
| "FastMCP로 간단한 HTTP MCP 서버를 만들어줘. 포트는 8080." | Skill loads; runs sqlite3 queries; generated code passes host/port to `run()`/`run_http_async()`, **not** the constructor; no `jlowin/fastmcp` references. |
| "내 .claude/skills 폴더를 MCP 서버로 노출하고 싶어." | Consultant behavior engages (interview or at minimum clarifying questions); proposal cites SkillsDirectoryProvider; APIs traceable to DB queries in the transcript. |
| "이 FastMCP 2.x 코드 좀 고쳐줘: `mcp = FastMCP('s', port=8080)` …" | Migration guide consulted; constructor-kwarg and related 2.x reflexes corrected per the gotchas table. |

Stale reflexes that must NOT appear anywhere in the transcripts: constructor `host`/`port`, `get_tools()`, `tool.disable()`, `PromptMessage(role=…)`, `mount(prefix=…)`, `FastMCP.as_proxy`, `import_server`, sync `ctx.set_state`.

## Acceptance criteria for v1.0.0

1. All Layer 1 checks pass locally and in CI on the release commit.
2. Layer 2 spot checks recorded (paste key outputs into the PR description or a release note).
3. Layer 3 probes 1–2 pass, or the user explicitly waives Layer 3.
4. `.claude/harness-spec.md` updated to implemented state with a Change history entry.
5. Plugin installable: `claude plugin` flow or `--plugin-dir` smoke test loads the skill listing.

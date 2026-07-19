# Troubleshooting

*Symptoms mapped to causes and fixes — for users of the skill, and for maintainers running the
build and validators.*

## Using the skill

### Claude still writes FastMCP 2.x code

**Symptom:** the generated code passes `host`/`port` to the constructor, calls `get_tools()`, or
uses `mount(prefix=…)`.

**Cause:** the skill did not load. Its instructions did not enter context, so the model answered
from memory — which is exactly what the skill exists to prevent.

**Fix, in order:**

1. Run `/plugin` in Claude Code and confirm `skills-for-fastmcp` is installed and enabled.
2. Invoke it explicitly: *"Using the fastmcp skill, …"*. If that produces correct code, the
   skill is installed and the trigger simply did not match your phrasing.
3. Make the question unambiguous — mention FastMCP or MCP servers directly. "Fix this Python
   file" offers nothing to match on.
4. For a manual install, confirm all three files exist and the database is roughly 2.4 MB.

**A correct answer looks like** `mcp.run(transport="http", host=…, port=…)` — see the
[full list of corrections](FastMCP-3-Gotchas.md).

### The skill loads but does not query the database

**Symptom:** the skill is clearly active, but no `sqlite3` command appears before the answer.

**Cause:** usually a missing or unreadable database file — the skill loaded because `SKILL.md`
was found, but the query it wants to run cannot succeed.

**Fix:**

```bash
ls -l .claude/skills/fastmcp/references/docs_official.db     # expect ~2.4 MB
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT COUNT(*) FROM docs;"
```

Expect `180`. A file of a few hundred bytes is a Git-LFS pointer or a truncated copy — re-clone
or re-download. An error mentioning `no such module: fts5` means your `sqlite3` lacks FTS5;
install a build that includes it (on macOS, the system `sqlite3` does).

For a trivially simple answer the model may legitimately skip the query. Persistent skipping on
substantive API questions is the real signal.

### The skill loads when I don't want it to

**Symptom:** it fires on host-side MCP configuration questions — `.mcp.json`, `claude mcp add`,
connector setup.

**Cause:** its description explicitly *excludes* those, so this should be rare. If it happens,
your phrasing probably read as framework work.

**Fix:** say what you actually want — "I'm configuring an existing MCP server in Claude Code,
not building one." To suppress it permanently, disable the plugin for that project, or narrow
the description in a manual install ([Customization](Customization.md#customize-the-skill-itself)).

### The answer is out of date

**Symptom:** the skill's guidance disagrees with current gofastmcp.com.

**Cause:** working as designed. The database is a pinned snapshot, and anything published after
`snapshot_date` is not in it.

**Fix:** check the stamp first:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT key, value FROM meta;"
```

If `snapshot_date` predates the change you are asking about, upstream is right and the snapshot
is stale. Either refresh it ([Maintenance-and-Release](Maintenance-and-Release.md)) or use
upstream directly for that question. The skill should be *telling* you this rather than
asserting stale guidance — if it did not, that is a genuine bug worth reporting.

### It says a topic is not covered

**Symptom:** "the Apps subsystem is not in this snapshot."

**Cause:** also working as designed. See
[Coverage-and-Limits](Coverage-and-Limits.md#what-is-deliberately-excluded-and-why).

**Fix:** use [gofastmcp.com](https://gofastmcp.com) for that topic, or
[add the folder to the corpus](Customization.md#change-what-goes-into-the-corpus) and rebuild.
Declining is the correct behavior — an improvised API would be worse than an admission.

### My own database query returns nothing

**Symptom:** an FTS query returns zero rows for something you know is documented.

**Causes, most common first:**

1. **Bare `NEAR`.** `'skills NEAR provider'` is not the proximity operator and silently matches
   nothing. Use `'NEAR(skills provider, 10)'`.
2. **An unquoted odd token.** Hyphens, parentheses, and heavy underscores can parse as
   operators. Wrap them: `'"on_duplicate"'`.
3. **Implicit AND.** `'skills provider tools'` requires *all three* terms. Drop one, or use `OR`.
4. **The topic really is excluded.** Check
   [Coverage-and-Limits](Coverage-and-Limits.md).

Full syntax notes in [Usage-Guides](Usage-Guides.md#fts5-syntax-the-sharp-edges).

## Building the database

### `sqlite3 module compiled without FTS5`

The build refuses to start because the resulting database would be unsearchable.

**Fix:** use a Python whose bundled SQLite has FTS5. Check with:

```bash
python3 -c "import sqlite3; print('ENABLE_FTS5' in ' '.join(r[0] for r in sqlite3.connect(':memory:').execute('PRAGMA compile_options')))"
```

On macOS, Homebrew's `python3` and recent system builds include it. If yours does not, install
Python from python.org or via Homebrew.

### `--src … does not look like a FastMCP docs snapshot (no servers/)`

**Cause:** `--src` points at the repository root rather than the docs folder.

**Fix:** pass `.tmp/fastmcp_clone/docs`, not `.tmp/fastmcp_clone`.

### `expected corpus dir at …`

**Cause:** one of the twelve include folders is missing from the source — either an incomplete
sparse checkout, or upstream renamed or removed a documentation section.

**Fix:** confirm the checkout is complete (`ls .tmp/fastmcp_clone/docs`). If the folder is
genuinely gone upstream, that is a structural change: update `INCLUDE`, then update
[Coverage-and-Limits](Coverage-and-Limits.md) and the band if the count moved materially.

### `imported snippet 'X' has no substitution rule`

**Cause:** upstream added a new JSX snippet component. The build fails deliberately rather than
leaking raw JSX into a document body.

**Fix:** add a handler to `SUBSTITUTIONS` —
[Handle a new upstream snippet](Customization.md#handle-a-new-upstream-snippet). Look at what
the component renders upstream before choosing: text worth keeping gets `_sub_static_tip`, pure
UI gets `_drop_tag`.

### `unresolved /snippets import line remains` or `unresolved snippet render tags remain`

**Cause:** a handler exists but did not match — usually because upstream changed the import or
tag syntax (a named import where there was a default one, or a multi-line tag).

**Fix:** find the offending document in the source and compare its syntax against `IMPORT_RE`
and the handler's regex. Both are near the top of `build_docs_db.py`.

### `changelog: parsed only N <Update> blocks (< 80)`

**Cause:** the changelog format changed upstream, or `changelog.mdx` is missing from the
checkout.

**Fix:** confirm the file exists and inspect its structure. If upstream moved to a different
block format, update the parser regex. Do **not** simply lower the threshold — the floor exists
to catch exactly this.

### `doc_count N outside band 150..220`

**Cause:** upstream added or removed a substantial number of documents, or your `INCLUDE` list
changed.

**Fix:** compare per-section counts in the build report against
[Coverage-and-Limits](Coverage-and-Limits.md#what-is-in-the-corpus) to find which section moved.
If the change is legitimate, widen the band **in both files** —
`DOC_COUNT_MIN`/`DOC_COUNT_MAX` in the build script and the matching check in the validator.

### The build succeeded but the database seems wrong

The build is atomic: a failed build leaves the previous database untouched, so if a new file
appeared, the build genuinely passed its five self-checks. Run the
[content spot checks](Maintenance-and-Release.md#4-content-spot-checks) — they catch
structurally valid but substantively wrong results that mechanical validation cannot.

## Validation and CI

### `Packaged skill drift: <file>`

**The most common failure in this repository.** You edited the canonical skill and did not
re-copy the mirror.

```bash
cp -R .claude/skills/fastmcp/. plugins/skills-for-fastmcp/skills/fastmcp/
diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp   # must be silent
python3 scripts/validate_evidence.py
```

Remember that `--mirror` copies only the database. `SKILL.md` and `consultant.md` are copied by
hand, every time.

### `Missing from plugin mirror:` / `Stale file in plugin mirror:`

You added or deleted a file under the canonical skill. The `cp -R` above adds; deletions must be
removed from the mirror manually, since `cp` never deletes.

### `Plugin version X must have a matching '## [X]' CHANGELOG heading`

You bumped `plugin.json` without adding a changelog entry.

**Fix:** add a `## [x.y.z] - YYYY-MM-DD` heading to `CHANGELOG.md` describing the change. The
coupling is intentional — a released version nobody documented is a version nobody can reason
about.

### `newest changelog version starts with v3.` fails

**This is the v4 tripwire firing, not a bug.** You have ingested a FastMCP v4 release.

**Do not** simply bump the assertion to make CI green. Work through the procedure in
[Coverage-and-Limits](Coverage-and-Limits.md#the-v4-tripwire): revisit the gotchas table first,
*then* bump the assertion, then reconsider the corpus include and exclude sets — all in the same
refresh. The failure exists to force that sequence.

### `no v2/ leakage` or `no apps/ leakage` fails

**Cause:** excluded documents entered the corpus — usually an `INCLUDE` edit, or upstream moving
documents into a folder that is included.

**Fix:** find them, then decide whether the inclusion is intended:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT path FROM docs WHERE path LIKE 'v2/%' OR path LIKE 'apps/%';"
```

If intended, remove the corresponding assertion from `validate_docs_db.py` **and** update the
skill's coverage-limits section, which currently tells users those areas are absent.

### A content-regression check fails

Two documents are anchors: `servers/providers/skills` must contain `SkillsDirectoryProvider`,
and `getting-started/upgrading/from-fastmcp-2` must contain `on_duplicate`.

**Cause:** upstream renamed the document, or rewrote it enough to drop the anchor term.

**Fix:** find where the content moved and update the check to the new path or term. A failure
here is a real signal — these anchors were chosen because their absence means something
important changed.

### CI fails on `git show --check`

**Cause:** trailing whitespace or space-before-tab in the tip commit.

**Fix:** run `git diff --check` before committing. Note the guard inspects the *tip commit*, so
fixing it requires amending or adding a follow-up commit — not just cleaning the working tree.

## Getting more help

Still stuck? Open an issue at
[github.com/tjdwls101010/Skills-for-FastMCP/issues](https://github.com/tjdwls101010/Skills-for-FastMCP/issues)
with the failing command, its full output, and your database stamp:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT key, value FROM meta;"
```

For security issues, follow [SECURITY.md](../../SECURITY.md) instead of opening a public issue.

---

**Next:** [Maintenance-and-Release](Maintenance-and-Release.md) for the full refresh procedure.

[← Back to the documentation index](README.md)

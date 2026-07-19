# Customization

*Adapting the project: changing what goes into the corpus, editing the skill's own behavior, and
transplanting the whole architecture to a different framework.*

One rule underlies everything here: **all build behavior lives in `scripts/build_docs_db.py`,
and the validators encode the invariants. Change the script, rebuild, and re-validate — never
hand-edit the `.db`.** A hand-edited database has no reproducible provenance, and the next
refresh silently discards your change.

## Change what goes into the corpus

The corpus is directory-based. Edit the `INCLUDE` list near the top of `build_docs_db.py`:

```python
INCLUDE = [
    "getting-started", "servers", "clients", "deployment", "development",
    "patterns", "cli", "tutorials", "community", "more", "python-sdk", "integrations",
]
```

**To add a folder** — for example bringing `apps/` back in a later version — append its name.
The `section` column is derived from the top-level folder automatically, so nothing else needs
changing for `WHERE section = 'apps'` to work. But two coupled edits follow:

- If a validator asserts the folder's *absence* (as it does for `v2/` and `apps/`), remove that
  assertion from `validate_docs_db.py`, or the build you just fixed will fail validation.
- Adding ~13 documents moves the total. Check it still sits inside the 150–220 band.
- Update [Coverage-and-Limits](Coverage-and-Limits.md) and the skill's own coverage-limits
  section — the skill currently *tells users* Apps is absent, and that claim would become false.

**To remove a folder**, drop its name. If nothing asserts its absence, add an assertion —
otherwise a folder that later reappears upstream will be silently re-ingested.

**To adjust the size band**, `DOC_COUNT_MIN` / `DOC_COUNT_MAX` in the build script and the
matching band in `validate_docs_db.py` **must move together**. They are deliberately duplicated
so that the build and the validator are independent checks, which only works if both are kept
current.

> **Three constants live in two files each** and must always be changed as a pair: the document
> count band (150–220), the changelog floor (80 entries), and the FTS smoke-test term
> (`provider`).

## Handle a new upstream snippet

The five Mintlify JSX snippet components are rewritten to text by the `SUBSTITUTIONS` map. If
upstream adds a new `/snippets/*` component, the build **fails loudly** —
`imported snippet 'X' has no substitution rule` — rather than leaking raw JSX into a document
body. Add an entry:

```python
SUBSTITUTIONS = {
    "VersionBadge":   _sub_version_badge,          # -> *New in version X*
    "PrefabPinWarning": _sub_static_tip(...),      # -> the Tip's plain text
    "LocalFocusTip":  _sub_static_tip(...),        # -> the Tip's plain text
    "PrefabDemoFrame": _drop_tag("PrefabDemoFrame"),
    "YouTubeEmbed":   _drop_tag("YouTubeEmbed"),   # -> dropped
    # "NewComponent": _sub_static_tip(...) or _drop_tag("NewComponent"),
}
```

Choosing a handler:

| Handler | When |
|---|---|
| `_sub_static_tip(text)` | The component carries text worth keeping (a warning, a tip) |
| `_drop_tag(name)` | Pure UI — iframes, demo frames, video embeds |
| A bespoke function | A semantic transform, like the version badge becoming searchable prose |

That fail-loud behavior is a feature worth preserving if you fork this. An unknown component is
a signal that upstream changed its documentation format, and a signal is worth more than a
best-effort guess that quietly degrades the corpus.

## Optional python-sdk cleanup

`build_docs_db.py` strips `<sup><a…><Icon github/></a></sup>` GitHub source-link decorations
from `python-sdk` bodies, which appear after every symbol heading and add pure noise to the FTS
index. This is scoped to that one section via `SUP_RE.sub(...)` — remove or extend it if the
upstream format changes.

## Edit the consultant's rubric

The ten dimensions are prose in `.claude/skills/fastmcp/references/consultant.md`. Each is a
*what it asks*, a *why*, and a *Find in the DB* pointer. If you edit one:

- **Keep the *why*.** It is what lets the model reason about situations outside the list. A bare
  "ask about X" is a rail that snaps on the first unanticipated case — and unanticipated cases
  are most of them.
- **Keep the *Find in the DB* pointer runnable.** Test the query against the built database; a
  pointer to a document path that no longer exists sends the consultant looking for nothing.
- **Resist growing past ten.** Before adding an eleventh, check whether it is a sub-question of
  an existing dimension — it usually is. The cap protects the self-check: a rubric of
  twenty-five dimensions is not more thorough, it is one nobody completes honestly.

See [Consultant-Rubric](Consultant-Rubric.md) for the full list and the reasoning behind the cap.

## Customize the skill itself

Most forks want to change the skill's behavior rather than its corpus. All of these are edits
to `.claude/skills/fastmcp/SKILL.md` — **and every one requires re-copying the plugin mirror**
before `validate_evidence.py` will pass.

**Narrow or widen when the skill loads.** The frontmatter `description` is what Claude matches
against. It currently triggers broadly — any `fastmcp` import, any MCP-server design question,
any "expose X as MCP" phrasing — and explicitly *excludes* host-side MCP configuration. Narrow
it if the skill fires on things you would rather handle yourself; widen it if your phrasings are
being missed.

**Edit the gotchas table.** If you work with a pinned FastMCP version, prune entries that do not
apply to it, or add corrections for a version-specific quirk you keep hitting. The standing rule
is that every entry must be backed by the shipped database — do not ship a correction the corpus
cannot support.

**Add query recipes.** The six SQL examples in the "How to query the DB" section are templates
Claude adapts. Adding one for a pattern you use often is a cheap, effective customization.

**Trim the database for size.** If context or repository size matters more to you than coverage,
drop `python-sdk` (50 documents, the largest section) from `INCLUDE` and rebuild. You lose exact
signatures, which is a real cost — signatures are the highest-value content in the corpus for
code generation. Consider dropping `community`, `more`, and `patterns` first.

## Fork it for another framework

The architecture — forcing function, queryable documentation database, consultant persona — is
framework-agnostic. This repository is itself a transplant of
[Skills-for-Langchain](https://github.com/tjdwls101010/Skills-for-Langchain), so the path is
proven.

**What transplants directly:**

- The database schema (`docs`, `docs_fts`, `changelog`, `meta`). Keeping it identical across
  skills is deliberate: one mental model for every validator and any future tooling.
- The build → self-validate → atomic move → mirror pipeline.
- Both validators, with constants changed.
- The mirror rule, the SemVer ↔ CHANGELOG coupling, and the CI workflow.
- The consultant's *structure*: persona, divergent-then-convergent interview, a capped rubric
  where each dimension carries its why, a worked example, and an agreement gate.

**What must be rewritten for the new framework:**

- The `INCLUDE` list and exclusions — every documentation site is organized differently.
- The markup handling. FastMCP's docs are Mintlify MDX with JSX component snippets; another
  project may use Sphinx, Docusaurus, or plain Markdown, with entirely different transformations.
- The changelog parser — `<Update>` blocks are a Mintlify convention.
- **Every sentence of `SKILL.md` and `consultant.md`.** These are the artifacts that must not be
  copied structurally and edited lightly. The gotchas table in particular is meaningless
  transplanted: it must be re-derived from *your* framework's migration guides.
- The ten dimensions. The rubric's *shape* transplants; its contents are FastMCP-specific.

**What to delete rather than keep.** When forking this repository, the LangChain original
carried language-conditional stripping and recursive snippet inlining — neither applies to
FastMCP, so both were deleted rather than left as dead branches. Do the same. Dead generality is
a maintenance trap: it looks load-bearing, so nobody dares remove it, and it accumulates.

The clearest guide to a transplant is
[`docs/plans/initial-build/`](../plans/initial-build/) — all twelve decisions with their
reasoning, in the order they were made.

## After any change

Every customization ends the same way:

```bash
# 1. Rebuild if you touched the corpus or the build script
python3 scripts/build_docs_db.py \
  --src .tmp/fastmcp_clone/docs \
  --out .claude/skills/fastmcp/references/docs_official.db \
  --commit "$COMMIT" \
  --mirror plugins/skills-for-fastmcp/skills/fastmcp/references/docs_official.db

# 2. Re-copy the mirror if you touched ANY prose file (SKILL.md, consultant.md)
cp -R .claude/skills/fastmcp/. plugins/skills-for-fastmcp/skills/fastmcp/
diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp   # must be silent

# 3. Validate
python3 scripts/validate_docs_db.py
python3 scripts/validate_evidence.py
```

Step 2 is the one that gets forgotten. `--mirror` handles the database; prose files never copy
themselves.

---

**Next:** [Maintenance-and-Release](Maintenance-and-Release.md) for the release process, or
[Troubleshooting](Troubleshooting.md) if a change broke something.

[← Back to the documentation index](README.md)

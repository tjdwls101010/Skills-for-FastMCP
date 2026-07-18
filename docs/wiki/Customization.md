# Customization

All build behavior lives in `scripts/build_docs_db.py`; the validators encode the
invariants. Change the script, rebuild, and re-validate — never hand-edit the
`.db`.

## Change what goes into the corpus

The corpus is directory-based. Edit the `INCLUDE` list near the top of
`build_docs_db.py`:

```python
INCLUDE = [
    "getting-started", "servers", "clients", "deployment", "development",
    "patterns", "cli", "tutorials", "community", "more", "python-sdk", "integrations",
]
```

- **Add a folder** (e.g. bring `apps/` back in a later version): append its name.
  The `section` column is derived from the top-level folder automatically, so no
  other change is needed to make `WHERE section = 'apps'` work.
- **Remove a folder**: drop its name. If a validator asserts its absence (as with
  `v2/` and `apps/`), update `validate_docs_db.py` to match — otherwise a removed
  folder that later reappears upstream won't be caught.
- **Adjust the size band**: `DOC_COUNT_MIN` / `DOC_COUNT_MAX` in the build script
  and the matching band in `validate_docs_db.py` must move together.

## Handle a new upstream snippet

The five Mintlify JSX snippets are rewritten to text by the `SUBSTITUTIONS` map. If
upstream adds a new `/snippets/*` component, the build **fails loud** ("imported
snippet 'X' has no substitution rule") rather than leaking raw JSX. Add an entry:

```python
SUBSTITUTIONS = {
    "VersionBadge":   _sub_version_badge,          # -> *New in version X*
    "LocalFocusTip":  _sub_static_tip(...),        # -> the Tip's plain text
    "YouTubeEmbed":   _drop_tag("YouTubeEmbed"),   # -> dropped
    # "NewComponent": _sub_static_tip(...) or _drop_tag("NewComponent"),
}
```

Use `_sub_static_tip` when the component carries text worth keeping, `_drop_tag`
for pure UI (iframes, demos), or a bespoke function for a semantic transform like
the version badge.

## Optional python-sdk cleanup

`build_docs_db.py` strips `<sup><a…><Icon github/></a></sup>` GitHub-source link
decorations from `python-sdk` bodies to reduce FTS noise. This is scoped to that
one section; remove or extend the `SUP_RE.sub(...)` call if the upstream format
changes.

## Edit the consultant's dimensions

The ten-dimension rubric is prose in `.claude/skills/fastmcp/references/consultant.md`.
Each dimension is a *why* plus a *Find in the DB* pointer. If you edit one:

- keep the *why* — it is what lets the model reason about situations outside the
  list; a bare "ask about X" is a rail that snaps on the first unanticipated case;
- keep the *Find in the DB* query runnable — test it against the built DB;
- resist growing past ten. If you want an eleventh, check whether it is a
  sub-question of an existing dimension first.

## After any change

```bash
python3 scripts/build_docs_db.py --src <docs> --out .claude/skills/fastmcp/references/docs_official.db \
  --commit <sha> --mirror plugins/skills-for-fastmcp/skills/fastmcp/references/docs_official.db
python3 scripts/validate_docs_db.py
python3 scripts/validate_evidence.py     # after re-copying any edited prose file to the mirror
```

See [Maintenance and Release](Maintenance-and-Release.md) for the mirror rule and
version bump.

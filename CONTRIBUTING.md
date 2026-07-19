# Contributing to Skills for FastMCP

Thanks for considering a contribution. This is a small, focused project maintained by one
person, so the process here is deliberately light — but two things about this repository are
unusual enough that skipping them will fail CI, and they are covered first.

## Two rules that are easy to miss

**1. The plugin mirror must stay byte-identical.** The skill exists twice: the canonical copy at
`.claude/skills/fastmcp/` and a packaged copy at `plugins/skills-for-fastmcp/skills/fastmcp/`.
Every file must match byte for byte, including the 2.4 MB `.db` blob. Editing the canonical copy
and forgetting to re-copy is the single most common CI failure in this repository:

```bash
cp -R .claude/skills/fastmcp/. plugins/skills-for-fastmcp/skills/fastmcp/
diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp   # must print nothing
```

**2. Every version bump needs a CHANGELOG heading.** If you change `version` in
`plugins/skills-for-fastmcp/.claude-plugin/plugin.json`, `CHANGELOG.md` must gain a matching
`## [x.y.z]` heading in the same change. This coupling is enforced mechanically.

## What contributions are wanted

- **Corrections to the gotchas table.** The twelve stale-reflex entries in `SKILL.md` must each
  be backed by the shipped database. If one is wrong, outdated, or missing, that is the highest
  value fix available.
- **Documentation snapshot refreshes** when FastMCP publishes meaningful changes. This is a
  scripted operation, not a rewrite — the full procedure is in
  [Maintenance-and-Release](docs/wiki/Maintenance-and-Release.md).
- **Build and validation improvements** — sharper checks, clearer failure messages, better
  handling of upstream documentation format changes.
- **Documentation fixes** anywhere in `docs/wiki/` or the root files.

**What is likely to be declined:** new runtime dependencies (all three scripts are deliberately
standard-library only, so CI needs no `pip install`); speculative configuration flags for cases
nobody has yet; and expanding the consultant rubric past ten dimensions — that cap is a design
decision, documented in [Consultant-Rubric](docs/wiki/Consultant-Rubric.md).

## Development setup

There is nothing to install. The repository is Python scripts, Markdown, and one committed
SQLite database.

```bash
git clone https://github.com/tjdwls101010/Skills-for-FastMCP.git
cd Skills-for-FastMCP
python3 --version    # 3.10 or newer; CI uses 3.12
```

Your Python's bundled SQLite must have FTS5 compiled in. The build script checks this and fails
early with an explanatory message if not; you can check it yourself:

```bash
python3 -c "import sqlite3; print('ENABLE_FTS5' in ' '.join(r[0] for r in sqlite3.connect(':memory:').execute('PRAGMA compile_options')))"
```

To rebuild the database you additionally need `git` (to clone the upstream documentation) and
the `sqlite3` CLI for ad-hoc queries.

## Tests & checks

There is no test suite in the conventional sense; correctness here means the shipped artifacts
satisfy their invariants. Run both validators before pushing:

```bash
python3 scripts/validate_evidence.py    # plugin/marketplace naming, SemVer ↔ CHANGELOG, mirror byte-identity
python3 scripts/validate_docs_db.py     # 22 checks over the shipped database
```

Expected output, respectively:

```
Release metadata passed: skills-for-fastmcp v1.0.0
Plugin mirror byte-identical: 3 files
```

```
All checks passed.
```

If you rebuilt the database, also run the build itself — it performs five self-checks and writes
atomically to a temporary file, so a failed build never leaves a partial `.db` behind:

```bash
python3 scripts/build_docs_db.py --src <docs-snapshot> --out <db-path> [--commit <sha>] [--mirror <mirror-db-path>]
```

Failures are mapped to causes and fixes in [Troubleshooting](docs/wiki/Troubleshooting.md).

## What CI checks

`.github/workflows/validate.yml` runs on every push and pull request, on all branches, using
Python 3.12:

1. `python3 scripts/validate_evidence.py`
2. `python3 scripts/validate_docs_db.py`
3. `git show --check HEAD` — a whitespace guard that rejects trailing whitespace and
   space-before-tab in the tip commit

Note that CI **validates** the committed database but never rebuilds it. The `.db` is a
committed artifact; if you regenerate it, you commit the result.

Running the two validators plus checking your diff for trailing whitespace locally will
reproduce CI exactly.

## Making a change

- **Branch** from `main` with a descriptive prefix: `fix/…`, `docs/…`, `build/…`.
- **Keep changes surgical.** Match the surrounding style; no drive-by reformatting. This
  repository's own conventions are in [CLAUDE.md](CLAUDE.md) and they apply to human
  contributors equally.
- **Commit messages** state what changed and why in the imperative mood
  (`Fix the NEAR() form in the SKILL.md query recipes`).
- **A good pull request** describes what changed, why, and what you ran to verify it. If you
  touched the skill payload, say explicitly that you re-copied the mirror. If you touched the
  database, include the new document count and the source commit.
- **Review expectations:** this is a solo-maintained project, so response times vary. A PR that
  passes CI and explains itself will be reviewed considerably faster than one that doesn't.

## Code style

Match what is already there. The Python scripts are standard-library only, use plain
`argparse`, and fail through a shared `die()` helper rather than raising tracebacks at users —
follow those patterns rather than introducing a framework. There is no linter or formatter
configured; the whitespace guard in CI is the only mechanical style rule.

Documentation is written in English, in the voice of the existing pages. The maintainer
communicates in Korean, so issues and pull request discussion in Korean are perfectly welcome —
only the committed artifacts need to be in English.

## Reporting bugs and requesting features

Open an issue at
[github.com/tjdwls101010/Skills-for-FastMCP/issues](https://github.com/tjdwls101010/Skills-for-FastMCP/issues).
There are no issue templates; a useful report includes:

- what you asked Claude to do, and what it produced,
- which install method you used (marketplace, `--plugin-dir`, or manual copy),
- the database stamp, which pins down exactly which snapshot you were running:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT key, value FROM meta;"
```

**Do not open a public issue for a security vulnerability** — follow
[SECURITY.md](SECURITY.md) instead.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are
expected to uphold it.

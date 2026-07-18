# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The
plugin version in `plugins/skills-for-fastmcp/.claude-plugin/plugin.json` is
coupled to the heading here and enforced by CI.

## [1.0.0] - 2026-07-18

### Added

- `fastmcp` skill: a forcing function that routes every FastMCP API question to a
  queryable source of truth instead of stale pretrained (mostly 2.x-era) memory,
  a twelve-item stale-reflex gotchas table distilled from the official 2→3
  migration guide, and a consultant persona that interviews the user and proposes
  an MCP-server architecture over a ten-dimension rubric.
- `references/docs_official.db`: a SQLite/FTS5 snapshot of the current official
  FastMCP docs (v3.4.4 snapshot, ~180 docs across the core folders, python-sdk,
  and integrations) plus a structured `changelog` table.
- Build and validation tooling: `build_docs_db.py`, `validate_docs_db.py`,
  `validate_evidence.py`, and a CI validate workflow.
- Plugin packaging (`skills-for-fastmcp`) and marketplace entry.

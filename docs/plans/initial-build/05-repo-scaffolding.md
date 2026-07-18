# 05 — Repository scaffolding

Full replica of the Skills-for-Langchain repo structure (D1), adapted names. Reference for any layout question: the Skills-for-Langchain repo itself (`https://github.com/tjdwls101010/Skills-for-Langchain`).

## Target tree

```
Skills-for-FastMCP/
├── .claude/
│   ├── harness-spec.md                  # component inventory & rationale (created in planning session, updated at release)
│   └── skills/
│       └── fastmcp/
│           ├── SKILL.md                 # per 03
│           └── references/
│               ├── consultant.md        # per 04
│               └── docs_official.db     # per 02
├── .claude-plugin/
│   └── marketplace.json
├── .github/
│   └── workflows/
│       └── validate.yml
├── .gitignore                           # .tmp/, .DS_Store
├── CHANGELOG.md
├── LICENSE                              # MIT
├── README.md
├── docs/
│   ├── plans/
│   │   └── initial-build/               # these planning docs (committed history)
│   └── wiki/
│       ├── Home.md
│       ├── How-It-Works.md
│       ├── Coverage-and-Limits.md
│       ├── Customization.md
│       └── Maintenance-and-Release.md
├── plugins/
│   └── skills-for-fastmcp/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── fastmcp/                 # byte-identical mirror of .claude/skills/fastmcp/
└── scripts/
    ├── build_docs_db.py
    ├── validate_docs_db.py
    └── validate_evidence.py
```

`.tmp/docs_fastmcp/` (the docs snapshot / re-clone) exists locally but is gitignored.

## plugin.json

Model on the Skills-for-Langchain plugin.json with these values:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "skills-for-fastmcp",
  "displayName": "Skills for FastMCP",
  "version": "1.0.0",
  "description": "Current-API guidance and MCP-server architecture consulting for FastMCP 3.x (Python).",
  "author": { "name": "Seongjin (tjdwls101010)", "email": "chunghun1@naver.com", "url": "https://github.com/tjdwls101010" },
  "homepage": "https://github.com/tjdwls101010/Skills-for-FastMCP",
  "repository": "https://github.com/tjdwls101010/Skills-for-FastMCP",
  "license": "MIT",
  "keywords": ["fastmcp", "mcp", "mcp-server", "python", "model-context-protocol", "claude-code"]
}
```

marketplace.json mirrors the Skills-for-Langchain one: name `skills-for-fastmcp`, single plugin entry with source `./plugins/skills-for-fastmcp`.

## Mirror rule

The plugin skill tree must be byte-identical to the canonical tree at all times — enforce with `diff -rq .claude/skills/fastmcp plugins/skills-for-fastmcp/skills/fastmcp` after every edit, and mechanically by `validate_evidence.py` (sha256 over every file including the .db). The standing gotcha from the LangChain repo: editing the canonical file and forgetting the mirror re-copy is the #1 CI failure mode.

## CI — .github/workflows/validate.yml

Same job shape as Skills-for-Langchain: on push/PR run

1. `python3 scripts/validate_evidence.py`
2. `python3 scripts/validate_docs_db.py`
3. whitespace check via `git show --check` (trailing-whitespace guard; remember it bit the LangChain repo on a planning doc — run it locally on the initial commit too)

## CHANGELOG.md

Keep-a-Changelog style, starting at:

```
## [1.0.0] - <implementation date>
### Added
- fastmcp skill: forcing function, docs_official.db (FastMCP <version> snapshot, ~180 docs + changelog table), consultant persona for MCP server design.
- Build/validation tooling: build_docs_db.py, validate_docs_db.py, validate_evidence.py; CI validate workflow.
- Plugin packaging (skills-for-fastmcp) + marketplace.
```

## README.md outline

Follow the Skills-for-Langchain README structure: what it is (one paragraph, both pillars: DB-grounded current-API answers + consultant), the IMPORTANT stale-knowledge note, install (marketplace / plugin / manual copy), how it works (file tree + the query loop), coverage & limits (FastMCP 3.x snapshot; apps and v2 excluded; snapshot date from meta), maintenance pointer to the wiki, license.

## docs/wiki pages (five, per user decision)

- **Home.md** — index + elevator pitch.
- **How-It-Works.md** — the forcing function, DB schema, query examples, consultant flow; adapted from the LangChain wiki equivalent.
- **Coverage-and-Limits.md** — corpus table from 01, exclusions and why, snapshot/version provenance, the v4 tripwire.
- **Customization.md** — changing the corpus (INCLUDE list), adding sections, rebuilding, editing dimensions.
- **Maintenance-and-Release.md** — refresh workflow, SemVer/CHANGELOG coupling, mirror rule, release steps.

## .claude/harness-spec.md

Created in the planning session (records the interview agreements); the implementation session updates the component statuses from "planned" to "implemented" and appends a Change history entry at release. It is the drift anchor for future harness-creator invocations on this repo.

## Versioning policy

v1.0.0 at first release. DB refresh with no behavior change → minor bump. Skill behavior changes → minor. Breaking restructure → major. Every version bump has a matching CHANGELOG heading (CI-enforced).

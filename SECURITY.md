# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 1.0.x | ✅ Yes |
| < 1.0 | ❌ No — pre-release, never published |

This project ships a single supported line. Fixes land on the latest release; there are no
backports to earlier versions.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Email **chunghun1@naver.com** with the details. This is the same address published in the
plugin and marketplace manifests, so it is already the project's contact of record.

## What to include

The more of this you can provide, the faster it can be confirmed and fixed:

- **What the issue is** and why you believe it is a security problem rather than a bug.
- **Reproduction steps** — the smallest sequence that demonstrates it.
- **Affected versions** — the plugin version from
  `plugins/skills-for-fastmcp/.claude-plugin/plugin.json`, and the database stamp:

  ```bash
  sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT key, value FROM meta;"
  ```

- **Impact** — what an attacker could actually achieve.
- **Your install method** — marketplace, `--plugin-dir`, or a manual copy of the skill folder.

## Response expectations

This is a solo-maintained project, so no formal SLA is promised. In practice:

- **Acknowledgement** within about a week.
- **Assessment** — a decision on whether it is a genuine vulnerability, and a rough remediation
  plan, follows the acknowledgement.
- **Coordinated disclosure** — please give a reasonable window for a fix before publishing
  details. Credit is given in the release notes unless you prefer otherwise.

If you have not heard back in two weeks, feel free to send a follow-up; mail does occasionally
get lost.

## Scope notes

Understanding what this project actually is helps set expectations about what counts as a
vulnerability here.

**In scope:**

- The build and validation scripts under `scripts/` — for example, a crafted documentation
  source that causes `build_docs_db.py` to write outside its intended output path.
- The shipped `docs_official.db` — for example, injected content that could steer an assistant
  reading it toward unsafe instructions.
- The plugin packaging and manifests, including anything that could cause a different payload
  to be installed than the one this repository publishes.

**Out of scope:**

- **Vulnerabilities in FastMCP itself.** This project only redistributes a snapshot of FastMCP's
  documentation. Report those to
  [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp/security).
- **Vulnerabilities in Claude Code**, the plugin system, or any host application. Report those
  to Anthropic.
- **Documentation being out of date.** The snapshot is version-stamped by design and the skill
  declares its own limits; staleness relative to upstream is a maintenance matter, handled
  through the refresh procedure in
  [Maintenance-and-Release](docs/wiki/Maintenance-and-Release.md), not a security issue.
- **Insecure code an assistant produced** while using this skill. The skill improves API
  accuracy; it does not review the security of what you build. Treat generated MCP servers as
  code you own and review.

## A note on what this skill can reach

Worth stating plainly, since it affects how you assess risk: the skill's payload is three files —
Markdown instructions and a read-only SQLite database. It defines no hooks, no commands, and no
executable code, and every documented query invokes `sqlite3` with `-readonly`. The scripts under
`scripts/` are maintainer tooling and are not part of the installed plugin.

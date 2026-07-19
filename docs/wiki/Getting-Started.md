# Getting Started

*Install the skill, see it work, and confirm it actually fired. Follow only this page and you
will reach a working state.*

## Prerequisites

| Requirement | Why | How to check |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | The skill is a Claude Code skill | `claude --version` |
| `sqlite3` with FTS5 | The database uses full-text search | `sqlite3 --version` — the system build on macOS and mainstream Linux includes FTS5 |

Nothing else. There is no Python dependency, no package to install, and no network access
needed at runtime — the documentation snapshot ships inside the skill.

You do **not** need FastMCP itself installed to use the skill. You will need it, of course, to
run the servers you build (`pip install fastmcp`).

## Install

Pick one of three methods.

### Method 1 — Marketplace (recommended)

The normal path. Inside Claude Code:

```
/plugin marketplace add tjdwls101010/Skills-for-FastMCP
/plugin install skills-for-fastmcp
```

This installs the plugin and its skill for your user, available in every project.

### Method 2 — Local plugin directory

Useful for trying a local checkout or a fork without publishing anything:

```bash
git clone https://github.com/tjdwls101010/Skills-for-FastMCP.git
claude --plugin-dir /path/to/Skills-for-FastMCP/plugins/skills-for-fastmcp
```

The skill is supplied by the plugin directory for that session only.

### Method 3 — Manual copy

Copy the skill folder into a project's or your user's skills directory:

```bash
# project-scoped
cp -R /path/to/Skills-for-FastMCP/.claude/skills/fastmcp .claude/skills/

# or user-scoped, available everywhere
cp -R /path/to/Skills-for-FastMCP/.claude/skills/fastmcp ~/.claude/skills/
```

The payload is self-contained — three files, no external references:

```
fastmcp/
├── SKILL.md
└── references/
    ├── consultant.md
    └── docs_official.db
```

Use this method if you want to edit the skill's instructions for yourself; see
[Customization](Customization.md).

## Verify the install

Start Claude Code in any directory and ask a question whose 2.x and 3.x answers differ visibly:

```
Write a minimal FastMCP server with one tool, served over HTTP on port 8080.
```

**What a correct result looks like.** Network settings are passed to `run()`:

```python
from fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8080)
```

**What a stale result looks like.** Network settings on the constructor — this raises
`TypeError` on FastMCP 3.x:

```python
mcp = FastMCP("demo", host="0.0.0.0", port=8080)   # ← the 2.x reflex
mcp.run(transport="http")
```

If you got the second version, the skill did not load. See
[the diagnosis below](#the-skill-did-not-load).

### Confirming the skill actually fired

Two independent signals:

**1. Claude queries the database.** You should see a `sqlite3` command run against
`docs_official.db` in the tool output before the code appears. That is the forcing function
working. No query means the skill is either not loaded or being ignored.

**2. Ask it directly for its provenance:**

```
How current is your FastMCP knowledge? Quote the snapshot stamp.
```

A loaded skill answers with values from the database's `meta` table rather than a vague
reassurance — something like *snapshot_date 2026-07-08, source commit 66c0270, FastMCP v3.4.4,
180 documents*.

You can verify the same facts yourself against a local checkout:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT key, value FROM meta;"
```

```
snapshot_date|2026-07-08
built_at|2026-07-18T11:40:52Z
source_repo|https://github.com/PrefectHQ/fastmcp
source_commit|66c0270bc1b293a8584574f4592f1559433cc016
doc_count|180
schema_version|1
```

## Your first real use

The skill has two behaviors and chooses between them by what you ask. Try each once.

### Ask a specific API question — it answers directly

```
In FastMCP 3.x, how do I mount one server inside another under a namespace?
```

No interview; it queries the database and answers, correcting the 2.x reflex
(`mount(prefix=…)`) to the current form (`mount(namespace=…)`) if that comes up.

### Describe something to expose — it consults

```
I have a folder of Claude Code skills. Can I turn it into an MCP server?
```

Here it switches to the consultant. Expect a short open conversation about who consumes the
server and what should be exposed, then a small number of multiple-choice questions drawn from
the [ten-dimension rubric](Consultant-Rubric.md), then a concrete architecture — and an
explicit request for your go-ahead before any file is written.

That gate is deliberate: design is free and always offered, but nothing is built until you say
so.

## When the skill does not load

The skill loads itself based on what you are asking. It is meant to trigger on FastMCP code,
MCP-server design questions, and "expose X as MCP" phrasings — even when you name no framework.

**It intentionally does not load** for host-side MCP *configuration*: editing `.mcp.json`,
running `claude mcp add`, or wiring a connector. That is Claude Code product knowledge, not
FastMCP framework knowledge, and the boundary is declared in the skill's own description.

### The skill did not load

If a FastMCP question produced no database query, work through these in order:

1. **Confirm it is installed.** Run `/plugin` in Claude Code and check that
   `skills-for-fastmcp` is listed and enabled.
2. **Name it explicitly.** Ask *"Using the fastmcp skill, …"*. If that works, the skill is
   installed and the trigger simply did not match your phrasing.
3. **Make the question unambiguous.** Mention FastMCP or MCP servers directly. "Fix this Python
   file" gives no signal to match on.
4. **Check the files are actually there.** For a manual install, confirm all three files exist
   and `references/docs_official.db` is roughly 2.4 MB — a truncated or Git-LFS-pointer copy of
   the database is a real failure mode.

More symptoms and fixes in [Troubleshooting](Troubleshooting.md).

## Where to go next

- **Understand what you just installed** → [Concepts](Concepts.md), then
  [Architecture](Architecture.md)
- **Get more out of it day to day** → [Usage-Guides](Usage-Guides.md)
- **See the corrections it applies** → [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md)
- **Know where the guidance stops** → [Coverage-and-Limits](Coverage-and-Limits.md)

---

**Next:** [Concepts](Concepts.md)

[← Back to the documentation index](README.md)

# Overview

*What this project is, the problem it solves, and where its boundaries are. Read this first if
you have never seen the repository before.*

## The problem: a framework that moved, and a model that didn't

FastMCP is the most widely used Python framework for building MCP servers. It has been through
three distinct eras:

1. **FastMCP 1.0** — absorbed into the official `mcp` Python SDK and bundled there.
2. **FastMCP 2.x** — an independent project under `jlowin/fastmcp`, and the version that
   dominates the internet's supply of tutorials, blog posts, and Stack Overflow answers.
3. **FastMCP 3.x** — now under `PrefectHQ/fastmcp`, with a rewritten provider system, renamed
   composition APIs, restructured auth, background tasks, and transforms.

A language model's knowledge of FastMCP is assembled from that written record, which means it is
overwhelmingly **2.x**. So when you ask an assistant to build an MCP server, you get 2.x code.
And 2.x code is not subtly stale — it is broken in ways that look entirely reasonable:

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server", port=8080)     # TypeError in 3.x

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}"

print(greet.name)                          # AttributeError in 3.x
```

Every line of that reads like correct FastMCP. It was correct FastMCP, two major versions ago.

The failure mode this creates is worse than a plain wrong answer. The code is fluent and
confident, the API names are real names, and the mistakes surface as `TypeError` at runtime
rather than as anything a reader would catch. You lose the time you thought you were saving, and
you lose it *after* believing you were done.

## What this project does about it

Skills for FastMCP replaces memory with a lookup. It ships two things as a single Claude Code
skill:

**A searchable snapshot of the official documentation.** The full body of ~180 current FastMCP
documentation pages — including the `python-sdk` API reference with exact signatures — is built
into a SQLite database with FTS5 full-text search, stamped with the upstream version, date, and
commit it was built from. It is 2.4 MB and ships inside the skill, so it works offline and
costs nothing to consult.

**A forcing function that makes the lookup non-optional.** The skill's instructions state
plainly that pretrained FastMCP knowledge is stale and require a database query before any API
is relied upon. This is the part that matters: a database Claude *may* consult is a database
Claude will skip whenever it feels confident — and misplaced confidence is precisely the disease.

On top of that same knowledge base sits a second behavior: a **consultant**. When you describe
something you want to expose as MCP rather than asking about existing code, the skill interviews
you across a ten-dimension design rubric, reaches explicit agreement on scope, and only then
proposes an architecture — with every API in it verified against the database first.

## The value, concretely

- **Code that runs.** The primary deliverable is the absence of a debugging session you would
  otherwise have had.
- **Answers with provenance.** Ask how current the guidance is and you get a version, a date,
  and a commit hash out of the database's `meta` table — not a reassurance.
- **Design help before code.** Most people asking to "make X an MCP" know what they want
  exposed, not what FastMCP can do. The rubric surfaces machinery you did not know to ask
  about — transforms, providers, elicitation, visibility — before you have committed to a shape.
- **Declared limits.** Where the corpus does not cover something, the skill says so and points
  upstream instead of improvising an API. Knowing where the guidance stops is part of trusting
  where it holds.

## Who it is for

- **Developers building MCP servers in Python** who want their assistant working from the
  current API rather than the popular one.
- **Anyone with something to expose** — a REST API, a folder of skills, a database, a
  toolchain — who wants a designed server rather than a pile of generated tool functions.
- **Maintainers of similar skills.** The architecture here — forcing function plus a queryable
  docs database plus a consultant persona — is framework-agnostic and documented so it can be
  transplanted. See [Customization](Customization.md).

## Non-goals

Being clear about what this deliberately does **not** do defines it as sharply as its features.

- **It is not a general MCP tutorial.** It is scoped to the FastMCP Python framework.
- **It does not configure MCP servers inside a host.** Editing `.mcp.json`, running
  `claude mcp add`, or wiring a connector in Claude Code or Cursor is host product knowledge, not
  framework knowledge, and the skill explicitly declines to load for those questions. The one
  overlap — installing a server *you built* into a host — is covered, because the corpus
  contains the relevant integration docs.
- **It does not cover the Apps subsystem** (tools that return interactive UI). This is a
  deliberate v1.0.0 scope cut, declared in the skill rather than papered over. See
  [Coverage-and-Limits](Coverage-and-Limits.md).
- **It does not teach FastMCP 2.x.** The corpus carries the official 2→3 migration guide, which
  is the sanctioned way to reason about 2.x code, and nothing else from that era. Including 2.x
  documentation would reproduce inside the database the exact staleness the database exists to
  cure.
- **It is not a client-development consultant.** Client documentation is in the corpus and
  client questions are answered from it, but the interview flow is optimized for designing
  servers.
- **It does not review the security or quality of what you build.** It improves API accuracy.
  Generated servers are code you own.

## How it compares to the alternatives

| Approach | Trade-off |
|---|---|
| **Just ask the model** | Free and instant, but returns 2.x code with high confidence. This is the baseline being fixed. |
| **Paste documentation into context** | Accurate for what you pasted — but you must already know which page to paste, and it costs context on every turn. The database is searched on demand and only matching excerpts enter context. |
| **A documentation MCP server / web fetching** | Always current, but needs a network round trip per query, may be rate-limited or unavailable, and gives you no version stamp to reason about. This snapshot is offline, instant, and pinned. |
| **A hand-written "cheat sheet" skill** | Cheap to write, but silently drops whatever the author did not think to include, and goes stale invisibly. A full-corpus snapshot is refreshed by re-running a script, not by re-curating judgement. |

The trade-off this project accepts is explicit: a snapshot is **pinned**, therefore it goes out
of date. That is answered by making refresh a scripted, validated operation — a few minutes of
mechanical work rather than a rewrite — and by stamping provenance into the artifact so nobody
has to guess how old it is.

## What is in the repository

Three things, each with a distinct audience:

| | For whom |
|---|---|
| **The skill payload** — `SKILL.md`, `consultant.md`, `docs_official.db` | Users; this is what gets installed |
| **The build and validation tooling** — three Python scripts and a CI workflow | Maintainers; how the payload is produced and guarded |
| **The plan and evidence documents** — `docs/plans/initial-build/` | Anyone extending or forking; every design decision with its reasoning |

[Architecture](Architecture.md) covers how they fit together.

## Project status

**Stable — v1.0.0**, released 2026-07-18, MIT-licensed. The shipped database passes 22
automated invariant checks, the packaged plugin copy is verified byte-identical to the canonical
one, and three headless behavioral probes were recorded as release evidence. The snapshot is
FastMCP v3.4.4 as of 2026-07-08.

---

**Next:** [Getting-Started](Getting-Started.md) to install it, or [Concepts](Concepts.md) if you
want the vocabulary first.

[← Back to the documentation index](README.md)

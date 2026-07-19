# Concepts

*The vocabulary needed to follow the rest of this documentation. Terms are defined in dependency
order — each builds on the ones above it. Skip ahead freely if a section is already familiar.*

## MCP (Model Context Protocol)

An open protocol that lets an AI application talk to external systems through a standard
interface, so a capability written once can be used by any compliant application.

Two roles matter:

- A **server** exposes capabilities — a database, an API, a filesystem, your own functions.
- A **host** (or client) consumes them. Claude Code, Claude Desktop, and Cursor are hosts.

Servers expose three kinds of component:

| Component | What it is | Analogy |
|---|---|---|
| **Tool** | Something the model can *call*, with arguments and a return value | A function |
| **Resource** | Something the model can *read*, addressed by URI | A file |
| **Prompt** | A reusable message template the user can invoke | A saved snippet |

Choosing correctly between the three is dimension 3 of the [consultant
rubric](Consultant-Rubric.md): read-only data exposed as a tool wastes a round trip, and an
action exposed as a resource cannot take arguments.

**Transports** carry the protocol. Two matter here: **stdio** (the host launches your server as a
subprocess and talks over standard input/output — local, single-user, no network) and **HTTP**
(the server runs as a network service — shareable, remote, and consequently needs authentication).

## FastMCP

The dominant Python framework for building MCP servers. It handles the protocol so you write
ordinary Python:

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

Its version history is the reason this project exists:

| Era | Repository | Status |
|---|---|---|
| **1.0** | bundled inside the official `mcp` Python SDK | Historical |
| **2.x** | `jlowin/fastmcp` | Superseded — but dominates written material online |
| **3.x** | `PrefectHQ/fastmcp` | **Current** — what this project documents |
| **4** | same | Documented and in progress; built on MCP Python SDK v2 |

3.x is not a polish release. It rewrote how servers source their components (the provider
system), renamed composition, restructured auth, moved network configuration out of the
constructor, and made context state asynchronous. Code written against 2.x does not merely
warn — it raises. The full list is in [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md).

### Providers

The 3.x answer to "where do this server's capabilities come from?" Rather than only registering
hand-written functions, you pass sources to the server:

```python
mcp = FastMCP("my-server", providers=[SkillsDirectoryProvider(path), OpenAPIProvider(spec)])
```

Built-in providers cover local functions, an OpenAPI specification, a filesystem directory, a
skills directory, and proxying another MCP server — and they compose. This is the single largest
architectural fork in designing a server, which is why it is dimension 1 of the rubric.

### Transforms

Machinery for reshaping the surface a host sees without rewriting the underlying components:
namespacing to prevent name collisions, visibility rules, exposing resources as tools (or the
reverse), and tool search. This matters more than newcomers expect — a server exposing fifty raw
tools can be unusable in practice, because every tool description consumes the model's context
whether or not it is called.

## Claude Code skills

A **skill** is a folder containing a `SKILL.md` file — Markdown instructions with YAML
frontmatter — plus any supporting files. Claude reads the frontmatter `description` to decide
when the skill is relevant, and loads the body only when it is. That two-stage design is what
makes skills cheap: an unused skill costs a sentence of context, not its whole contents.

This project's skill:

```
fastmcp/
├── SKILL.md                     # instructions: the forcing function, gotchas, how to query
└── references/
    ├── consultant.md            # the interview protocol and the ten-dimension rubric
    └── docs_official.db         # the documentation snapshot
```

`references/` files are loaded on demand, not up front. `consultant.md` is read only when
entering the consultant path — a code question never pays for it.

### Plugins and marketplaces

A **plugin** packages skills (and optionally commands, agents, and hooks) for distribution, via
a `.claude-plugin/plugin.json` manifest. A **marketplace** is a repository listing installable
plugins through `.claude-plugin/marketplace.json`. This repository is both: it holds the
canonical skill *and* publishes itself as a one-plugin marketplace, which is why
`/plugin marketplace add tjdwls101010/Skills-for-FastMCP` works.

That dual role is also why the same skill exists at two paths in the repository, and why
[keeping them byte-identical](Maintenance-and-Release.md#the-one-rule-that-breaks-ci-most-often)
is enforced by CI.

## The forcing function

The central design idea, and the concept most worth internalizing.

A skill that merely *offers* a documentation database will be consulted when Claude feels
uncertain — and skipped when it feels confident. But confident-and-wrong is exactly the failure
being fixed: a model does not experience 2.x recall as uncertainty. It experiences it as knowing
the answer.

So the skill does not offer. It **asserts that pretrained knowledge is unreliable here** and
requires a query before any API is relied upon:

> You do **not** reliably know the current FastMCP API. Your pretrained knowledge is dominated
> by FastMCP **2.x** and the old `mcp` SDK's bundled FastMCP 1.0 […] Memory is precisely the
> thing that is stale here.

Removing the source of confidence, rather than adding a resource beside it, is what makes the
lookup actually happen.

### Why the gotchas table is not in the database

A companion idea that explains an apparent redundancy. The skill carries twelve stale-reflex
corrections *inline*, even though the database contains the official migration guide covering
the same ground. The reason is a hard limit on what search can do:

**Absence is not searchable.** A query over current documentation returns what still exists. It
cannot return "the `port` argument you are about to pass no longer exists," because nothing in
the current docs mentions it. To find a removed API you would have to already suspect it was
removed — but the whole problem is that it feels present.

So the corrections that only fire on *absence* are internalized, and everything else is looked
up. See [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md).

## SQLite and FTS5

The documentation snapshot is a single **SQLite** file — a complete database in one file, with
no server to run. Queried through the `sqlite3` CLI in read-only mode, it needs no setup and
cannot be modified by accident.

**FTS5** is SQLite's full-text search extension. It builds an inverted index so a search for a
word across 1.3 million characters of documentation is instant. Three features shape how the
database is queried:

- **Ranking** — `ORDER BY rank` returns best matches first, so `LIMIT 5` gives the five most
  relevant documents rather than five arbitrary ones.
- **Snippets** — `snippet()` returns a highlighted excerpt around the match, so a search can
  show context without loading whole documents into the model's context window.
- **Porter stemming** — searching `provider` also matches `providers` and `providing`.

The query syntax has sharp edges worth knowing before writing one; they are collected in
[Usage-Guides](Usage-Guides.md#fts5-syntax-the-sharp-edges).

## The snapshot and its stamp

The database is a **snapshot**: the state of upstream documentation at one moment, not a live
feed. Every build records its own provenance in a `meta` table:

| Key | v1.0.0 value | Meaning |
|---|---|---|
| `snapshot_date` | `2026-07-08` | Date of the newest release in the corpus |
| `source_repo` | `https://github.com/PrefectHQ/fastmcp` | Where the documentation came from |
| `source_commit` | `66c0270…` | The exact upstream commit |
| `doc_count` | `180` | Documents ingested |
| `built_at` | `2026-07-18T11:40:52Z` | When this database was built |
| `schema_version` | `1` | Database schema generation |

The operative rule: **treat anything released after `snapshot_date` as unverified**. The skill
follows it, quoting the stamp rather than claiming timeless currency. See
[Coverage-and-Limits](Coverage-and-Limits.md).

## The consultant rubric

Ten design dimensions the consultant works through when someone wants to expose something as
MCP — tool sourcing, surface efficiency, component fit, interactivity, state, auth, transport,
composition, observability, and operations.

Two properties define how it is used:

- **It is a rubric, not a script.** Not every consultation asks about every dimension. But all
  ten are self-checked before an architecture is proposed, so an omission is a decision rather
  than an oversight.
- **Each dimension carries its *why*.** A bare instruction to "ask about authentication" is a
  rail that snaps on the first unanticipated case. The reasoning lets a situation outside the
  list be reasoned about from first principles.

Full treatment in [Consultant-Rubric](Consultant-Rubric.md).

---

**Next:** [Architecture](Architecture.md) — how these pieces are assembled.

[← Back to the documentation index](README.md)

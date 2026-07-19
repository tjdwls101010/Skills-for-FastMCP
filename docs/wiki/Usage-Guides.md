# Usage Guides

*Task-oriented recipes: getting the most out of both behavior modes, and querying the shipped
database directly when you want to read the documentation yourself.*

## Understanding the two modes

The skill picks one of two behaviors from what you ask. Knowing which one you want gets you a
better answer faster.

| | **Guide mode** | **Consultant mode** |
|---|---|---|
| **Triggered by** | Concrete code, or a specific API question | Describing something you want to expose |
| **Example** | "Why does `mount(prefix=…)` fail?" | "Can my skills folder be an MCP server?" |
| **Behavior** | Queries the database, answers directly | Interviews, agrees scope, then proposes |
| **Interview?** | Never | Yes — but only questions that change the design |
| **Writes files?** | If you asked for code | Only after an explicit go-ahead |

If it is genuinely ambiguous, the skill asks **one** short clarifying question rather than
guessing — not a full interview.

### Getting good results from guide mode

- **Paste the actual code.** The gotchas are pattern-matched against real symbols; a
  paraphrase gives less to work with.
- **Include the error.** `TypeError` on a constructor argument, `AttributeError` on a decorated
  function, and "my mounted tools have the wrong names" each map to a specific known correction.
- **State the version if you know it.** "This is a 2.x codebase I'm migrating" routes straight
  to the migration guide instead of being inferred.

### Getting good results from consultant mode

- **Lead with what you want exposed and who consumes it.** Those two facts determine more of the
  design than anything else.
- **Answer with constraints, not solutions.** "It's just for me, locally" is more useful than
  "use stdio" — it lets several dimensions resolve at once.
- **Push back on the proposal.** The loop is designed for revision. A concrete architecture you
  disagree with is more productive than another round of questions.
- **Say what must never be exposed.** Secrets, internal endpoints, destructive operations. This
  shapes visibility and authorization decisions early, when they are cheap.

See [Consultant-Rubric](Consultant-Rubric.md) for what it is working through.

## Querying the database yourself

The database is an ordinary read-only SQLite file. Nothing stops you from reading the
documentation directly — it is often faster than a web search, and it works offline.

**Path.** In a repository checkout:
`.claude/skills/fastmcp/references/docs_official.db`. In a plugin install, `references/docs_official.db`
next to the installed `SKILL.md`. Always pass `-readonly`.

### Recipe 1 — Find documents about a topic

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT d.path, d.title FROM docs_fts JOIN docs d ON d.rowid=docs_fts.rowid
   WHERE docs_fts MATCH 'openapi' ORDER BY rank LIMIT 5;"
```

`ORDER BY rank` is what makes `LIMIT` meaningful — best matches first, not arbitrary ones.

### Recipe 2 — Search with excerpts

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT d.path, snippet(docs_fts, 2, '[', ']', ' … ', 12)
   FROM docs_fts JOIN docs d ON d.rowid=docs_fts.rowid
   WHERE docs_fts MATCH 'elicitation OR sampling' ORDER BY rank LIMIT 8;"
```

`snippet()`'s second argument is the column index: **0** = title, **1** = description,
**2** = body. Body is almost always what you want.

### Recipe 3 — Read a whole document

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT body FROM docs WHERE path = 'servers/composition';"
```

The standard workflow is search first, then read the promising results in full — the search
tells you the path, this prints it.

### Recipe 4 — Look up an exact signature

The `python-sdk` section is the auto-generated API reference, and the authority on exact
signatures:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT path, title FROM docs WHERE section = 'python-sdk' AND path LIKE '%server%';"
```

### Recipe 5 — Proximity search

For terms that must appear near each other rather than merely in the same document:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT d.path, d.title FROM docs_fts JOIN docs d ON d.rowid=docs_fts.rowid
   WHERE docs_fts MATCH 'NEAR(skills provider, 10)' ORDER BY rank LIMIT 5;"
```

Note the **functional** form. A bare `skills NEAR provider` is not the operator and silently
matches nothing.

### Recipe 6 — Check recency and provenance

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT version, date FROM changelog ORDER BY date DESC LIMIT 5;
   SELECT key, value FROM meta;"
```

Answers both "what changed recently?" and "how current is this snapshot?" — the second question
being the one to ask before trusting the first.

### Recipe 7 — Read a specific release's notes

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT body FROM changelog WHERE version = 'v3.4.0';"
```

### Recipe 8 — Survey the corpus

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT section, COUNT(*) FROM docs GROUP BY section ORDER BY COUNT(*) DESC;"
```

Useful for orienting yourself, and for confirming a refresh ingested what you expected.

## FTS5 syntax: the sharp edges

Four rules cover essentially every query you will write, and two of them fail *silently* if you
get them wrong.

| Pattern | Meaning |
|---|---|
| `'skills provider'` | **Both** terms — whitespace is an implicit AND, not a phrase |
| `'skills OR provider'` | Either term |
| `'"exact phrase"'` | A literal phrase (double quotes inside the single-quoted string) |
| `'NEAR(skills provider, 10)'` | Both terms within 10 tokens of each other |

Plus:

- **Porter stemming is on.** `provider` also matches `providers` and `providing`. You rarely
  need to search for plurals.
- **Quote odd tokens.** A token containing hyphens, parentheses, or heavy underscores can be
  parsed as an operator. Wrap it: `'"on_duplicate"'`, not `'on_duplicate'`.
- **A bare `NEAR` matches nothing.** `'a NEAR b'` is not an error and not the proximity
  operator — it returns zero rows and looks like "no documentation exists." Use the functional
  form.
- **Empty results are ambiguous.** They may mean the concept is absent, or that your terms were
  too narrow. Broaden — drop a word, try a synonym — before concluding the documentation does
  not cover it.

## Working with the results

**Search, then read.** FTS ranking is good at finding the right document and poor at giving you
the whole answer in a snippet. Search to locate, then `SELECT body` to read.

**Prefer paths you have seen.** Documentation paths are stable across refreshes and make good
anchors: `servers/composition`, `servers/providers/skills`,
`getting-started/upgrading/from-fastmcp-2`, `integrations/openapi`.

**Remember what is not there.** Zero results for an Apps question means the corpus excludes
Apps, not that the feature does not exist. Check
[Coverage-and-Limits](Coverage-and-Limits.md) before concluding anything from an absence.

## Common tasks, end to end

### "I'm migrating a 2.x server to 3.x"

Ask the skill directly, pasting the code. It applies the twelve corrections and consults the
official migration guide for anything they do not cover. To read that guide yourself:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT body FROM docs WHERE path = 'getting-started/upgrading/from-fastmcp-2';"
```

Start with [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md) for the shape of what changed.

### "I want to wrap our REST API"

This is consultant territory — say what the API is, who will call the resulting server, and
whether every route should be exposed. Expect questions about route filtering and how
authentication should pass through. Relevant documents: `integrations/openapi`,
`tutorials/rest-api`.

### "My server works locally but breaks over HTTP"

Usually a state or lifecycle assumption that only holds for stdio — dimension 5 of the rubric.
Relevant documents: `servers/context`, `servers/lifespan`, `servers/storage-backends`.

### "The host is drowning in tools"

A real, common problem with a whole subsystem devoted to it that most people do not know exists.
Ask about tool surface shaping; relevant documents: `servers/transforms/*`, `servers/visibility`,
and the tool-search transform.

### "How do I install the server I just built into Claude Code?"

The one place where this skill touches host configuration, and it is in scope because the corpus
carries the integration documents: `integrations/claude-code`,
`integrations/mcp-json-configuration`. General questions about configuring *other people's* MCP
servers are outside the skill's boundary — that is host product knowledge.

---

**Next:** [Consultant-Rubric](Consultant-Rubric.md) — the ten dimensions behind consultant mode.

[← Back to the documentation index](README.md)

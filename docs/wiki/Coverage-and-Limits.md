# Coverage and Limits

*Exactly what the documentation database contains, what is deliberately excluded and why, and
how to tell how current any given copy is. Knowing where guidance stops is part of trusting
where it holds.*

## What is in the corpus

The v1.0.0 snapshot holds the full body of **180 documents** from the official FastMCP
documentation — the `docs/` folder of `PrefectHQ/fastmcp`, which is the gofastmcp.com Mintlify
site — plus **94 release entries** parsed into a separate table. About 1.35 million characters
of Markdown in a 2.4 MB file.

| Section | Docs | What it covers |
|---|---|---|
| `python-sdk` | 50 | Auto-generated API reference, one file per module — **the authority on exact signatures** |
| `servers` | 44 | The heart of the corpus: tools, resources, prompts, context, transforms, providers, composition, elicitation and sampling, middleware, tasks, auth, testing |
| `integrations` | 30 | OAuth providers, frameworks (FastAPI, OpenAPI), SDKs, host setup |
| `clients` | 19 | The FastMCP `Client` — used mainly to test your own server in-process |
| `development` | 9 | Contributing, releases, tests, v3 and v4 notes |
| `cli` | 7 | Overview, running, inspecting, install-mcp, auth, client, generate-cli |
| `getting-started` | 7 | Welcome, installation, quickstart, and **the four upgrading guides** |
| `deployment` | 5 | Running a server, HTTP, server configuration, sandboxed agents, Prefect Horizon |
| `patterns` | 3 | CLI, contrib, testing |
| `tutorials` | 3 | What MCP is, creating a server, wrapping a REST API |
| `more` | 2 | FAQ, settings |
| `community` | 1 | Showcase |
| **Total** | **180** | |

Verify the distribution in any copy:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT section, COUNT(*) FROM docs GROUP BY section ORDER BY COUNT(*) DESC;"
```

The count is guarded by a **150–220 band** in both the build script and the validator — wide
enough that upstream documentation can drift between snapshots without failing the build,
narrow enough that a structural change cannot pass unnoticed. A count outside the band means the
include list or the upstream layout changed materially and must be re-examined.

### The changelog table

`changelog.mdx` is not stored as a document row. Upstream it is a single 352 KB file of 94
`<Update>` blocks — as one document row it would be a useless search hit that buries every real
result. Parsed into `changelog(version, date, body)` it answers two questions directly:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT version, date FROM changelog ORDER BY date DESC LIMIT 5;"
```

```
v3.4.4|2026-07-08
v3.4.3|2026-07-05
v3.4.2|2026-06-06
v3.4.1|2026-06-05
v3.4.0|2026-06-02
```

## What is deliberately excluded, and why

| Excluded | Size | Reason |
|---|---|---|
| **`v2/`** | 81 docs | Previous-major documentation. Putting deprecated APIs into a database whose whole purpose is *current*-API truth would reproduce the exact staleness problem the project exists to fix. A search for `mount` returning both eras is worse than one returning only the current answer. |
| **`apps/`** | 13 docs | The Apps subsystem (tools that return interactive UI) is a deliberate v1.0.0 scope cut. The skill declares the limit rather than improvising. Revisit in a later minor release if consultations start hitting it. |
| **`updates.mdx`** | 1 | A marketing-flavored duplicate of the changelog, which is already ingested properly. |
| **`snippets/`** | 5 | JSX *component definitions*, not content. They are resolved into text during the build instead. |
| Assets, CSS, JS, JSON, images | — | Not documentation. |

The exclusions of `v2/` and `apps/` are asserted mechanically — `validate_docs_db.py` fails if a
single document with either path prefix appears. A leak cannot silently poison the corpus; it
breaks CI.

### The one exception to the 2.x exclusion

The official **2→3 migration guide** (`getting-started/upgrading/from-fastmcp-2`) *is* in the
corpus, along with the **3→4 pre-migration guide**. These are current documents about the past —
the sanctioned way to reason about 2.x code — rather than 2.x documentation presented as
current. They are also the authoritative source for the twelve corrections in
[FastMCP-3-Gotchas](FastMCP-3-Gotchas.md).

## Behavioral limits

Beyond corpus coverage, several limits are built into how the skill behaves.

**Apps questions are declined, not improvised.** If a consultation would genuinely benefit from
an interactive-UI answer, the skill says the corpus does not cover Apps and points at
[gofastmcp.com](https://gofastmcp.com)'s Apps section rather than inventing an API. One nuance:
the `python-sdk` API reference *does* include the apps module's signatures (eight documents).
Treat those as raw signatures, not a consulting playbook — signatures without guides tell you the
shape of a call, not when to make it.

**2.x maintenance is redirected, not answered.** Asked to maintain a 2.x codebase, the skill
offers the migration path rather than 2.x-era answers from memory. If you must stay on 2.x, this
is not the right tool.

**Client development is answerable but not consulted.** Client documentation is fully in the
corpus (19 documents) and client questions are answered from it. But the consultant's interview
is optimized for designing *servers* — a pure client project will not get the rubric treatment,
by design.

**Some things have no MCP equivalent at all.** Claude Code *hooks* are client-side enforcement —
an MCP server exposes capabilities to a host and cannot intercept another agent's tool calls, so
hooks do not map. The consultant is instructed to say so plainly rather than invent a
server-side stand-in. Naming a limit costs a paragraph; faking a capability costs a debugging
session.

## Provenance: how current is this copy?

Every build stamps its own provenance into the database, so the answer never depends on
remembering which version you installed:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db "SELECT key, value FROM meta;"
```

The v1.0.0 snapshot:

| Key | Value | Meaning |
|---|---|---|
| `snapshot_date` | `2026-07-08` | Date of the newest release in the corpus |
| `source_repo` | `https://github.com/PrefectHQ/fastmcp` | Upstream source |
| `source_commit` | `66c0270bc1b293a8584574f4592f1559433cc016` | The exact commit ingested |
| `doc_count` | `180` | Documents |
| `built_at` | `2026-07-18T11:40:52Z` | When this database was built |
| `schema_version` | `1` | Schema generation |

That corresponds to **FastMCP v3.4.4**.

**The operative rule: treat any FastMCP release newer than `snapshot_date` as unverified.** The
skill follows it — asked how current its guidance is, it quotes these values rather than
claiming timeless currency. `source_commit` makes the snapshot exactly reproducible: check out
that commit upstream and you have precisely what was ingested.

If prose anywhere in this documentation disagrees with the `meta` table, **`meta` is right**.
Numbers written into these pages describe the v1.0.0 snapshot; the database describes itself.

## The v4 tripwire

FastMCP 4 — built on MCP Python SDK v2, with snake_case protocol fields, an `mcp_types` package,
and a pydantic ≥ 2.12 floor — is already documented upstream. When it lands, several things must
change together, and the design makes that unmissable rather than relying on anyone noticing.

**The trigger:** the newest `version` in the `changelog` table starts with `v4.`

**What fires:** `validate_docs_db.py` asserts that the newest version begins with `v3.`, so the
first refresh that ingests a v4 release **fails validation**. That is intentional — the failure
*is* the notification.

**What must be revisited in that same refresh:**

1. **The gotchas table** in `SKILL.md`. The 2→3 corrections will be joined, or replaced, by 3→4
   ones. Gotcha 12 already anticipates this: camelCase versus snake_case protocol fields are
   *both correct*, for different versions, so era detection matters more than normalization.
2. **The validator's version assertion** — bump `v3.` to `v4.`, consciously, having handled
   point 1 first. Changing it just to make CI green defeats the entire mechanism.
3. **The corpus include and exclude sets** — which upgrading guides to keep. When v4 becomes
   current, v3 documentation becomes the new `v2/`: the thing whose inclusion would reproduce
   staleness.
4. **This page and [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md)**, which name 3.x as current
   throughout.

Do all of it **in the same refresh**, not as a follow-up. Full procedure in
[Maintenance-and-Release](Maintenance-and-Release.md).

## If you need something the corpus lacks

- **Apps** → [gofastmcp.com](https://gofastmcp.com), Apps section. Adding it is a plausible
  future minor release; see [Customization](Customization.md#change-what-goes-into-the-corpus)
  to do it yourself.
- **Anything newer than `snapshot_date`** → refresh the database
  ([Maintenance-and-Release](Maintenance-and-Release.md)) or check upstream directly.
- **FastMCP 2.x** → the migration guide is in the corpus; the 2.x documentation is not, and
  including it is a deliberate non-goal.
- **Host-side MCP configuration** → out of scope by design. That is host product knowledge, and
  the skill declines it on purpose. See [Overview](Overview.md#non-goals).

---

**Next:** [Customization](Customization.md) to change what the corpus holds, or
[Maintenance-and-Release](Maintenance-and-Release.md) to refresh it.

[← Back to the documentation index](README.md)

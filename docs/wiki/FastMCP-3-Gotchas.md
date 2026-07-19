# FastMCP 3.x Gotchas

*The twelve FastMCP 2.x reflexes that are wrong in 3.x, each with the correct current form.
These are carried inline in the skill rather than looked up — this page explains why, and lists
them all.*

## Why these are not in the database

The skill's whole design says *look it up rather than remember it*. These twelve entries are the
deliberate exception, and the reason is a hard limit on what search can do:

> **Absence is not searchable.**

A query over *current* documentation returns what still exists. It cannot return "the `port`
argument you are about to pass no longer exists," because nothing in the current documentation
mentions `port` on the constructor. To find a removed API by searching, you would have to
already suspect it was removed — but the entire problem is that it feels present. It compiled
last year. It appears in every tutorial. Nothing about recalling it feels like a guess.

So corrections that fire on *absence* are internalized, and everything that fires on *presence*
is looked up. That division is the reason this list is short and stable: it is not a summary of
FastMCP, it is the specific residue that search cannot reach.

Every entry is verified against the shipped database at build time. The authoritative source is
the official migration guide at `getting-started/upgrading/from-fastmcp-2`, which is in the
corpus and should be read directly when touching 2.x code.

## The twelve

### 1. Transport and network settings left the constructor

```python
# ✗ 2.x reflex — raises TypeError in 3.x
mcp = FastMCP("srv", host="0.0.0.0", port=8080)

# ✓ 3.x
mcp = FastMCP("srv")
mcp.run(transport="http", host="0.0.0.0", port=8080)
```

Also moved: `log_level`, `debug`, `sse_path`, `stateless_http`, and others. They belong to
`run()` / `run_http_async()` now, not to server construction.

*This is the most common single failure, and the fastest way to tell whether the skill loaded.*

### 2. Decorators return the original function

```python
@mcp.tool
def greet(name: str) -> str: ...

# ✗ AttributeError in 3.x — greet is just the function
print(greet.name)

# ✓ Get the component from the server
tool = await mcp.get_tool("greet")
```

In 2.x the decorator returned a component object with `.name` and `.description`. In 3.x it
returns your function unchanged, so attribute access fails.

### 3. `get_tools()` → `list_tools()`, and the return type changed

```python
# ✗ gone in 3.x
tools = await mcp.get_tools()          # also get_resources(), get_prompts()

# ✓ 3.x — and these return LISTS, not dicts
tools = await mcp.list_tools()
resources = await mcp.list_resources()
prompts = await mcp.list_prompts()
templates = await mcp.list_resource_templates()
```

The rename is easy to spot; the **list-not-dict** change is the one that slips through, because
code that did `tools["name"]` fails at a different place than the call site.

### 4. Enable/disable moved from the component to the server

```python
# ✗ 2.x
tool.disable()

# ✓ 3.x — the server owns this
server.disable(names={"tool_name"}, components={"tool"})
server.disable(tags={"experimental"})
server.enable(names={"tool_name"}, components={"tool"})
```

Consistent with gotcha 2: you no longer hold a component object to call methods on.

### 5. Context state is async now

```python
# ✗ 2.x
ctx.set_state("key", value)
value = ctx.get_state("key")

# ✓ 3.x — must be awaited
await ctx.set_state("key", value)
value = await ctx.get_state("key")
```

State must also be **JSON-serializable** unless you pass `serializable=False`. Missing the
`await` is especially nasty: you get a coroutine object rather than an error at the call site.

### 6. Prompt returns are typed

```python
# ✗ 2.x
return PromptMessage(role="user", content=TextContent(type="text", text="Hello"))

# ✓ 3.x
from fastmcp.prompts import Message
return Message("Hello")
# — or simply return a plain string
```

Version 3 no longer silently coerces raw dictionaries into prompt messages.

### 7. Composition renamed

```python
# ✗ 2.x
mcp.mount(prefix="sub", server=sub)
mcp.import_server(sub)

# ✓ 3.x
mcp.mount(sub, namespace="sub")
mcp.mount(sub)                      # import_server's replacement
```

`prefix` → `namespace` is a rename with a *silent* failure mode if you pass it positionally —
the concept survived, the keyword did not.

### 8. Proxying moved out of the class

```python
# ✗ 2.x
proxy = FastMCP.as_proxy("http://example.com/mcp")

# ✓ 3.x
from fastmcp.server import create_proxy
proxy = create_proxy("http://example.com/mcp")
```

### 9. The provider system is how 3.x sources components

```python
# ✗ 2.x
from fastmcp.server.openapi import FastMCPOpenAPI
mcp = FastMCPOpenAPI(openapi_spec=spec, client=client)

# ✓ 3.x
from fastmcp.server.providers import OpenAPIProvider
mcp = FastMCP("api", providers=[OpenAPIProvider(spec, client=client)])
```

The most consequential of the twelve, because it is not a rename — it is a different model. In
3.x a server is *populated by providers*: local functions, `OpenAPIProvider`,
`FileSystemProvider`, `SkillsDirectoryProvider`, proxies, and combinations of them. Code written
against the 2.x subclass-per-integration pattern needs restructuring, not a find-and-replace.

Providers are also why "tool source" is dimension 1 of the [consultant
rubric](Consultant-Rubric.md#1-tool-source).

### 10. Auth providers no longer read environment variables implicitly

```python
# ✗ 2.x — credentials picked up from the environment
auth = GitHubProvider()

# ✓ 3.x — pass them explicitly
auth = GitHubProvider(client_id=..., client_secret=...)
```

A silent failure in the worst category: authentication that appears configured and is not.

### 11. Repository and packaging shifts

- The project moved from **`jlowin/fastmcp`** to **`PrefectHQ/fastmcp`**. Links, issue trackers,
  and installation instructions written before the move point at the old home.
- `pip install fastmcp` **will not upgrade** an existing 2.x installation — `--upgrade` is
  required. A machine that "already has fastmcp" may quietly stay on 2.x, which makes the other
  eleven gotchas look like framework bugs.
- Background tasks need the **`fastmcp[tasks]`** extra.

### 12. Era detection for v4

FastMCP 4, built on MCP Python SDK v2, is already documented:

- **camelCase** protocol fields (`inputSchema`, `mimeType`) are pre-v4 style.
- **v4 renames them to snake_case**, with a deprecation bridge during the transition.

Before "fixing" a field in either direction, read
`getting-started/upgrading/from-fastmcp-3` in the database. Both spellings are correct — for
different versions — and mechanically normalizing them is how you break a working codebase.

## Quick reference

| # | 2.x reflex | 3.x form |
|---|---|---|
| 1 | `FastMCP(..., host=, port=)` | `mcp.run(transport=, host=, port=)` |
| 2 | `decorated_fn.name` | `await mcp.get_tool("name")` |
| 3 | `get_tools()` → dict | `list_tools()` → **list** |
| 4 | `tool.disable()` | `server.disable(names={...}, components={...})` |
| 5 | `ctx.set_state(...)` | `await ctx.set_state(...)` |
| 6 | `PromptMessage(role=, content=)` | `fastmcp.prompts.Message("…")` or a string |
| 7 | `mount(prefix="x")` / `import_server(s)` | `mount(namespace="x")` / `mount(s)` |
| 8 | `FastMCP.as_proxy(url)` | `create_proxy(url)` |
| 9 | `FastMCPOpenAPI(...)` | `FastMCP(..., providers=[OpenAPIProvider(...)])` |
| 10 | `GitHubProvider()` from env | `GitHubProvider(client_id=…, client_secret=…)` |
| 11 | `jlowin/fastmcp`, plain `pip install` | `PrefectHQ/fastmcp`, `--upgrade`, `fastmcp[tasks]` |
| 12 | Normalizing `inputSchema` ↔ `input_schema` | Check the era first — both are correct, for different versions |

## Using this list

**Migrating a 2.x server?** Work through the table, then read the official migration guide for
everything the twelve do not cover — it includes a ready-made upgrade prompt:

```bash
sqlite3 -readonly .claude/skills/fastmcp/references/docs_official.db \
  "SELECT body FROM docs WHERE path = 'getting-started/upgrading/from-fastmcp-2';"
```

**Reviewing generated code?** The table doubles as a review checklist. Every entry is something
a model produces confidently and a reader waves through.

**Judging whether the skill is working?** Gotcha 1 is the cheapest test — ask for an HTTP server
on a port and see where the port ends up. See
[Getting-Started](Getting-Started.md#verify-the-install).

## Keeping the list honest

This list is version-coupled, so it is maintained alongside the snapshot rather than left to
drift. Two standing rules:

- **Every refresh re-verifies the twelve** against the refreshed migration guides. Step 4 of the
  refresh procedure exists for exactly this, and it is the step easiest to skip.
- **The v4 tripwire.** When the newest release in the `changelog` table starts with `v4.`, this
  list must be revisited *in the same refresh* — the 2→3 corrections will be joined, or
  replaced, by 3→4 ones. The validator's `v3.` version assertion fires at the same moment, which
  is what makes the tripwire impossible to miss.

See [Maintenance-and-Release](Maintenance-and-Release.md#the-v4-tripwire).

---

**Next:** [Coverage-and-Limits](Coverage-and-Limits.md) — what the database does and does not
contain.

[← Back to the documentation index](README.md)

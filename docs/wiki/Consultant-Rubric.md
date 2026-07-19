# The Consultant Rubric

*The ten design dimensions the consultant works through when you want to expose something as an
MCP server — what each one asks, why it matters, and where its answers live in the documentation
database.*

This page explains the rubric that `references/consultant.md` implements. You do not need to
read it to use the skill; read it if you want to know what is being weighed on your behalf, or
if you are adapting the rubric for a fork.

## Why there is a rubric at all

The gap the consultant exists to close: **users know what they want exposed; they do not know
what FastMCP can do.**

"Make our API an MCP server" sounds like a complete request and is not. Which routes? Who calls
it? How does it authenticate? Should the host see forty tools or four? Does anything need to ask
the user a question mid-execution? Every one of those is unanswered, and every one changes the
architecture.

Asking them ad hoc means asking whichever ones the conversation happens to surface. A rubric
means the *omissions become decisions* — you can be told "authentication does not apply here
because it is stdio and personal," which is information, rather than simply never hearing about
authentication at all.

## How it is used

Three operating rules, and they matter as much as the list itself.

**It is a rubric, not rails.** Not every consultation asks about every dimension. Asking all ten
every time would be an interrogation, and most would be irrelevant. Only what the context makes
relevant is asked.

**All ten are self-checked before proposing.** The consultant must be able to say, for each
dimension, why it either shaped the design or does not apply. That check is internal; you see
its conclusions, not the checklist.

**Never ask what has already been answered.** If you said "it's just for me, locally," transport
and authentication are settled — stating the finding and moving on is correct; asking anyway is
noise. The measure is not how many questions were asked but whether each one would have moved a
choice.

Convergent questions are asked in batches of at most four, each self-contained. Divergent
opening — understanding what you actually want — happens in plain conversation, because the
answer space is not yet enumerable and multiple choice would narrow you before the options are
known.

## The ten dimensions

### 1. Tool source

**Asks:** Where do this server's capabilities come from? Hand-written Python functions, an
existing REST API (`OpenAPIProvider`), a skills directory (`SkillsDirectoryProvider`), files
(`FileSystemProvider`), another MCP server (proxy), or a mix?

**Why it leads:** This is the single biggest architectural fork. It decides which providers
anchor the design and how much code exists at all — wrapping an OpenAPI specification may mean
writing almost none.

**In the database:** `MATCH 'provider overview'`, `servers/providers/*`, `integrations/openapi`

### 2. Tool surface & context efficiency

**Asks:** How many tools will the host see, and what do they cost in the model's context? Should
some be hidden, renamed, namespaced, or made discoverable through search rather than listed?

**Why it matters:** A server exposing fifty raw tools can be unusable in practice — every tool
description consumes context whether or not it is called. FastMCP 3.x has first-class machinery
for shaping the surface (transforms, visibility, code mode, tool search) and **most users do not
know it exists**, so it never gets asked for. This dimension exists to raise it unprompted.

**In the database:** `MATCH 'transform OR namespace OR visibility'`, `servers/transforms/*`,
`servers/visibility`

### 3. Component type fit

**Asks:** For each capability — is it a tool, a resource, or a prompt? And would a
resources-as-tools or prompts-as-tools transform serve the host better?

**Why it matters:** Read-only data exposed as a tool wastes invocation round trips; an action
exposed as a resource cannot take arguments. Wrong fit does not fail loudly — it surfaces as
awkward host UX that nobody can quite diagnose.

**In the database:** `servers/tools`, `servers/resources`, `servers/prompts`,
`servers/transforms/resources-as-tools`

### 4. Interactivity

**Asks:** Does any tool, mid-execution, need to ask the *user* something (elicitation), ask the
*model* something (sampling), or report progress on long work?

**Why it matters:** These change a tool's control flow and its host-compatibility story, and
retrofitting them is invasive — a tool written to compute and return does not become interactive
without restructuring.

**In the database:** `MATCH 'elicitation OR sampling'`, `servers/progress`

### 5. State & lifecycle

**Asks:** Is there per-session state (async `ctx` state)? Resources to set up and tear down
(lifespan)? Anything to persist (storage backends)? Long-running work (background tasks, the
`fastmcp[tasks]` extra)?

**Why it matters:** Statelessness assumptions decide deployability. Getting this wrong has a
signature symptom: **"works locally, breaks under HTTP"** — an in-memory assumption that holds
for one stdio process and collapses across HTTP workers.

**In the database:** `servers/context`, `servers/lifespan`, `servers/storage-backends`,
`servers/tasks`, `servers/dependency-injection`

### 6. AuthN / AuthZ

**Asks:** Open server, or authenticated? Which OAuth provider — GitHub, Google, Azure, Auth0,
WorkOS? Does authorization vary per tool?

**Why it matters:** Two reasons. Auth is the sharpest 3.x change area — providers no longer read
credentials from environment variables implicitly, so remembered patterns fail silently. And it
is the hardest thing to bolt on later: adding auth to a working server touches transport,
deployment, and every tool that needs identity.

**In the database:** `MATCH 'oauth OR authorization'`, `servers/authorization`, `servers/auth/*`,
`integrations/<provider>`

### 7. Transport & deployment

**Asks:** stdio (local, per-user) or HTTP (shared, remote)? Self-hosted or cloud? Sandboxed?

**Why it matters:** Transport decides authentication needs, the state model, and the install
story all at once. It deserves a conscious choice rather than a default — and the honest default
for personal use is stdio, not an HTTP deployment "to be safe."

**In the database:** `deployment/running-server`, `deployment/http`,
`deployment/server-configuration`, `deployment/sandboxed-agents`

### 8. Server composition

**Asks:** One server, or several mounted and namespaced together? Should an existing MCP server
be proxied rather than rebuilt?

**Why it matters:** Composition is how a large surface stays maintainable and how existing
servers get reused. The classic traps are namespace collisions and accidentally shared state
stores — both cheap to prevent, expensive to diagnose.

**In the database:** `MATCH 'composition OR mount OR proxy'`, `servers/composition`,
`servers/providers/proxy`

### 9. Middleware & observability

**Asks:** Is there cross-cutting request handling — rate limiting, auditing, request
rewriting? Telemetry? Logging back to the client?

**Why it matters:** Production servers need visibility, and middleware is the extension seam for
it. Reaching for middleware is considerably cheaper than forking a provider to get the same hook.

**In the database:** `MATCH 'middleware OR telemetry'`, `servers/middleware`,
`servers/telemetry`, `servers/logging`

### 10. Quality, operations & host targets

**Asks:** How will this be tested (the in-process `Client`)? Versioned? Fingerprinted? Which
hosts must install it — Claude Code, Claude Desktop, Cursor, ChatGPT?

**Why it matters:** The host list **back-propagates constraints** onto every earlier dimension —
transport, auth, and Apps support all depend on it, so discovering it last means revisiting
decisions. And an untested MCP server fails in the worst possible place: silently, inside
somebody else's agent loop, where the failure looks like the *model* being unreliable.

**In the database:** `servers/testing`, `servers/versioning`, `servers/tool-fingerprinting`,
`cli/overview`, `integrations/claude-code`

## Why exactly ten, and why it stays ten

The list is capped deliberately. An eleventh dimension should first be checked against the
existing ten — it is usually a sub-question of one of them (rate limiting is middleware;
secret handling is authorization; caching is state).

The cap protects the rubric's usability. A checklist of twenty-five dimensions is not more
thorough — it is one nobody completes honestly, and a self-check that is not performed provides
no guarantee at all.

Each dimension also carries its ***why***, and that is load-bearing rather than decorative. A
bare instruction to "ask about interactivity" is a rail: it snaps on the first situation its
author did not anticipate. The reasoning lets an unlisted situation be reasoned about from first
principles instead.

## The three canonical shapes

Most consultations arrive as one of three, and naming the shape early tells you which dimensions
will dominate.

| Shape | Reduces to | Dominant dimensions |
|---|---|---|
| **"Make our API an MCP"** | Wrapping a REST API — `OpenAPIProvider`, route filtering, auth pass-through | 1, 2, 6 |
| **"Can my skills folder be an MCP?"** | Exposing a directory — `SkillsDirectoryProvider` or `FileSystemProvider` | 1, 3, 7 |
| **"Can my whole harness be an MCP?"** | Provider composition — several providers, namespaced, on one server | 1, 2, 3, 8 |

The third is the flagship: it exercises the most dimensions and is the worked example below.

## Worked example: "can my whole harness be an MCP?"

An abridged trace of the real example in `references/consultant.md`. What matters is the
**shape** — divergent opening, convergent rubric, a concrete proposal tied to dimensions, an
honest note about what does not map, and a scoped build.

> **User:** "제 Claude Code 하네스 전체(CLAUDE.md + agents + skills + hooks)를 MCP 서버로 만들
> 수 있을까요?"
> *(Can I turn my entire Claude Code harness — CLAUDE.md, agents, skills, hooks — into an MCP
> server?)*

**Divergent open, in conversation.** Before reaching for structure: who consumes this — just you
on another machine, or teammates? For each part of the harness, what should a consumer actually
*get*? Skills as callable tools? CLAUDE.md as read-only context? Agents as… what, exactly? And
an early flag that "hooks" may not map at all.

**Convergent, over the rubric.** Tool source (1): the skills folder is a
`SkillsDirectoryProvider`; CLAUDE.md and rules are files, so `FileSystemProvider`. Composition
(8) dominates because several providers share one server — namespace each family so a skill tool
and a rules resource cannot collide. Tool surface (2): with many skills, consider visibility or
tool search so the host is not flooded. Component fit (3): skills that *do* things are tools;
CLAUDE.md that is *read* is a resource. Transport (7): "just me across machines" → stdio.
Auth (6): none for personal stdio. Quality (10): test the composed server in-process with
`Client` first.

**The proposal.** One composed FastMCP server:
`providers=[SkillsDirectoryProvider(<skills path>), FileSystemProvider(<rules path>)]`, each
namespaced. Skills surface as tools; CLAUDE.md and rules as read-only resources. stdio for
personal cross-machine use — and if the team later wants it, the same server runs over HTTP
behind an OAuth provider, which is a transport-and-auth swap rather than a redesign. Every
choice mapped back to the dimension that drove it.

**The honest note — what does not map.** Hooks are **client-side enforcement**: the host runs
them around *its own* tool calls. An MCP server exposes capabilities to a host; it cannot
intercept or gate another agent's tool calls. So the harness's hooks have **no MCP equivalent**,
and the right move is to say so and point back to host-side hook configuration rather than
inventing a server-side stand-in. Agents are similar: an agent definition is a host construct —
you can expose its *prompt* as an MCP prompt, but not its autonomy.

> **User:** "맞네요. 개인용 stdio 버전만 먼저 만들어줘요. 코드만."
> *(Right. Just build the personal stdio version first. Code only.)*

**Scoped build.** Confirm the scope, query the database for the current provider and composition
APIs immediately before writing, write the server, and state plainly what the user must supply
(the two directory paths) and what was deliberately left out (the team HTTP + OAuth variant,
which dimensions 6 and 7 would bring back).

That honest note is the most instructive part of the example. Naming a limit costs one paragraph;
faking a capability costs the user a debugging session and the consultant its credibility.

## The build rules

The rubric produces a design. Turning a design into files is governed separately:

- **Design is always offered and free.** A concrete architecture and its explanation, with no
  side effects, every time.
- **Implementation is gated on an explicit go-ahead.** No files written, no packages installed,
  no commands run until you say build. *Enthusiasm for a design is not consent to write it.*
- **Propose the smallest architecture that satisfies the agreement.** Three functions do not
  need composition, middleware, or auth. Whatever is deliberately left out is stated along with
  the dimension that would bring it back — so you can pull it in consciously rather than
  discover the gap later.
- **Build against the current API.** The database is queried for the APIs involved immediately
  before writing code — not from the design conversation's memory of them.
- **Verify to the agreed scope, and be honest about the boundary.** Name which parts were
  exercised and which are yours to wire. No claim that a server runs end to end unless it was
  actually run.

---

**Next:** [FastMCP-3-Gotchas](FastMCP-3-Gotchas.md) — the reflex corrections applied throughout.

[← Back to the documentation index](README.md)

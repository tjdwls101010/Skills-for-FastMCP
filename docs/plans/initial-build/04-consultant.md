# 04 — Consultant specification (references/consultant.md)

Target: `.claude/skills/fastmcp/references/consultant.md`. Structural template: `docs/plans/initial-build/reference/consultant.md` (Skills-for-Langchain). Keep its architecture — persona, interview protocol, dimensions with "Find in the DB" pointers, worked example, build rules — and rewrite the content for MCP server design.

## Persona

A senior engineer who has designed and operated MCP servers in production, acting as a consultant. Core behaviors carried over from the reference:

- Interviews before designing. Never assumes the user knows FastMCP's feature space — the user typically knows *what they want exposed*, not *what FastMCP can do*. The consultant's job is to bridge that: probe intent, surface options the user didn't know existed, reach explicit agreement, then design.
- Grounds every proposal in the DB. Every API name, class, decorator, and kwarg in a proposed architecture is verified with a query before it appears in the design. No memory-sourced API claims.
- Honest and critical: pushes back on over-engineering ("you described three tools; you do not need middleware, auth, or composition for that"), names tradeoffs, and states assumptions.
- Speaks the user's language (Korean user ↔ Korean conversation); writes code and design artifacts in English.

## Trigger cases (the front door)

The three canonical shapes, worth naming in the doc because they map to distinct DB territories:

1. **"Make xxx API an MCP"** → OpenAPI/REST wrapping: `integrations/openapi`, `tutorials/rest-api`, OpenAPIProvider, route filtering, auth pass-through.
2. **"Can my skills folder be an MCP?"** → `servers/providers/skills` (SkillsDirectoryProvider), `servers/providers/filesystem`.
3. **"Can a whole harness (CLAUDE.md + agents + skills + hooks) be an MCP?"** → provider composition: multiple providers on one server, `servers/composition`, namespacing, visibility. This is the flagship consultation — it exercises the most dimensions and should be the worked example (see below).

## Interview protocol

Carried from the reference, with the session-process rule added:

- Ask with AskUserQuestion, max 4 questions per round, and make each question fully self-contained (context in the question text and option descriptions/previews — surrounding prose may not render in the user's terminal).
- Never ask what the conversation or the code already answers.
- Converge with options; diverge with open conversation.
- End the interview with an explicit agreement summary before designing.

## The ten design dimensions (rubric, not rails)

Operating rule, stated verbatim in the doc: *not every consultation asks about every dimension — ask only what the context makes relevant; but before presenting an architecture, self-check all ten and be able to say why each either shaped the design or doesn't apply. Each dimension's "why" is written so that situations outside this list can be reasoned about from first principles.*

1. **Tool source** — where do the server's capabilities come from: hand-written Python functions, an existing REST API (OpenAPIProvider), a skills directory (SkillsDirectoryProvider), files (FileSystemProvider), another MCP server (proxy), or a mix. *Why: this is the single biggest architectural fork; it decides which provider(s) anchor the design and how much code exists at all.*
2. **Tool surface & context efficiency** — how many tools the host sees and what they cost in the model's context: transforms, namespacing, visibility, code mode, tool search. *Why: a server with 50 raw tools can be unusable in practice; FastMCP 3.x has first-class machinery for shaping the surface, and most users don't know it exists.*
3. **Component type fit** — tools vs. resources vs. prompts (and resources-as-tools / prompts-as-tools transforms). *Why: read-only data exposed as a tool wastes invocation round-trips; actions exposed as resources can't take arguments. Wrong fit shows up as awkward host UX.*
4. **Interactivity** — does a tool mid-execution need to ask the user (elicitation), ask the model (sampling), or report progress. *Why: these change the tool's control flow and the host-compatibility story, and retrofitting them is invasive.*
5. **State & lifecycle** — per-session state (async ctx state), startup/shutdown resources (lifespan), persistence (storage backends), dependency injection, long-running work (background tasks, `fastmcp[tasks]`). *Why: statelessness assumptions decide deployability; getting this wrong surfaces as "works locally, breaks under HTTP".*
6. **AuthN/AuthZ** — is the server open, or does it need OAuth (which provider: GitHub, Google, Azure, Auth0, WorkOS, …) and per-tool authorization. *Why: auth is the sharpest 3.x change area (providers no longer read env vars implicitly) and the hardest thing to bolt on later.*
7. **Transport & deployment** — stdio (local, per-user) vs. HTTP (shared, remote); self-hosted vs. cloud; sandboxing. *Why: transport decides auth needs, state model, and install story; it should be chosen consciously, not defaulted.*
8. **Server composition** — one server or several mounted/namespaced; proxying existing servers. *Why: composition is how big surfaces stay maintainable and how existing servers get reused; namespace collisions and state-store sharing are the classic traps.*
9. **Middleware & observability** — cross-cutting request handling, telemetry, logging back to the client. *Why: production servers need visibility; middleware is also the extension seam for rate-limiting, auditing, and rewriting — cheaper than forking providers.*
10. **Quality, operations & host targets** — testing with the in-process Client, versioning, tool fingerprinting, CLI dev workflow, and which hosts (Claude Code, Claude Desktop, Cursor, ChatGPT, …) must install it. *Why: the host list back-propagates constraints (transport, auth, apps support), and an untested MCP server fails silently in the worst place — inside someone else's agent loop.*

Each dimension in the generated doc gets a `*Find in the DB:*` line with 2–3 concrete FTS queries or paths (e.g. dimension 1 → `MATCH 'provider overview'`, `servers/providers/*`; dimension 6 → `MATCH 'oauth proxy'`, `integrations/<provider>`).

## Worked example (include one, fully played out)

"Harness 통째로 MCP로" — the user asks whether their Claude Code harness (CLAUDE.md + agents + skills + hooks) can be served as MCP. Sketch the consultation: interview establishes what consumers should get (skills as tools? prompts? read-only docs?); design lands on a composed server — SkillsDirectoryProvider for skills, FileSystemProvider (or resources) for CLAUDE.md/rules as read-only context, namespacing per component family, stdio transport for personal use with an HTTP+OAuth variant sketched for team sharing; explicitly notes what does NOT map (hooks are client-side enforcement — an MCP server cannot intercept another agent's tool calls; say so rather than faking it). Every named API verified in the DB during generation.

## Build rules (post-agreement)

Carried from the reference: design doc before code; every API verified via DB query at write time; propose the smallest architecture that satisfies the agreement (CLAUDE.md simplicity rules apply to generated designs too); state what was deliberately left out and which dimension would bring it back.

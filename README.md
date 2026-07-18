# Skills for FastMCP

**Status: planning stage.** This repository will hold a Claude Code skill (`fastmcp`) that (a) forces Claude to query a snapshot of the current official FastMCP 3.x docs (SQLite/FTS5) instead of trusting its stale pretrained API memory, and (b) acts as a consultant that interviews you and proposes a FastMCP server architecture when you want to expose an API, a skills folder, or a whole toolchain as MCP.

It transplants the proven architecture of [Skills-for-Langchain](https://github.com/tjdwls101010/Skills-for-Langchain) v1.2.0.

The complete implementation plan lives in [`docs/plans/initial-build/`](docs/plans/initial-build/) — start at `00-goals-and-decisions.md`. The harness agreement record is [`.claude/harness-spec.md`](.claude/harness-spec.md).

This README will be replaced by the real one at v1.0.0 (see plan doc 05).

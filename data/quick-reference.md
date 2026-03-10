# Claude Capabilities Quick Reference (v2.3.0, 2026-03-10)

Use this knowledge to give accurate, current answers about what Claude can do.
For deeper detail on any topic, invoke the assistant-capabilities skill.

## Current Models

- **Opus 4.6**: 200K/1M context, 128K output, adaptive thinking, $5/$25/MTok
- **Sonnet 4.6**: 200K/1M context, 64K output, adaptive thinking, $3/$15/MTok
- **Haiku 4.5**: 200K context, 64K output, extended thinking, $1/$5/MTok
- 1M context: beta header `context-1m-2025-08-07` (tier 3+, Opus/Sonnet 4.6)
- Fast mode: Opus 4.6 only, `speed: "fast"` + header, 2.5x faster, 6x pricing

## What Claude Can Do

**Process**: Images (JPEG/PNG/GIF/WebP), PDFs (32MB/100pg), multilingual I/O
**Generate**: Structured JSON (guaranteed), documents (pptx/xlsx/docx/pdf), code
**Remember**: Memory tool (API), Projects (Claude.ai/Desktop), CLAUDE.md (Code)
**Search**: Web search, web fetch, dynamic filtering (code execution filters results)
**Execute**: Sandboxed code execution (Python), programmatic tool calling (no round-trips)
**Connect**: MCP servers/connectors, Files API (500MB/file), Tool Search (1000s of tools)
**Reason**: Adaptive thinking, effort control (low/medium/high), 128K output streaming

## How Capabilities Compose

**Vision + Structured Outputs**: Image in, guaranteed JSON out. Schema + image content blocks.
**1M Context + Files API**: Upload large docs, process in single pass. Premium only beyond 200K.
**Web Search + Code Execution**: Dynamic filtering — search results filtered by code before context.
**Streaming + Tool Use**: Fine-grained tool streaming + programmatic tool calling for low-latency multi-tool workflows.
**Batch + Caching**: 50% batch discount + 10% cached reads. Cache persists across batch requests.
**Memory + Compaction**: Persist critical facts + auto-summarize for infinite conversations.
**Subagents + Tool Search**: Discover tools dynamically, dispatch isolated workers per task.
**Agent SDK + Hooks**: Build custom orchestration with lifecycle events (shell + HTTP hooks).

## Extension Patterns (Claude Code)

| Need | Use |
|------|-----|
| "Always do X" rules | **CLAUDE.md** (~200 lines) |
| Reusable knowledge | **Skill** (auto-invokes from natural language) |
| External services | **MCP** (stdio/HTTP/SSE) |
| Task isolation | **Subagent** (own context window) |
| Parallel coordination | **Agent team** |
| Deterministic automation | **Hook** (shell/HTTP, zero tokens) |
| Recurring monitoring | **/loop** or **Cron** |
| Bundle + distribute | **Plugin** (skills + hooks + MCP) |

Key: Skill = content (teaches how). MCP = ability (can act). Hook = automation (must act).
Skill vs CLAUDE.md: CLAUDE.md = "always know this". Skill = "know when relevant".

## Platform Availability

| Feature | Claude.ai | Desktop | Claude Code | API |
|---------|-----------|---------|-------------|-----|
| Skills | ZIP upload | ZIP upload | Filesystem | -- |
| MCP | Connectors | Settings | Full | MCP Connector |
| Projects | Yes | Yes | CLAUDE.md | -- |
| Hooks/Plugins | -- | -- | Yes | -- |
| Subagents/Teams | -- | -- | Yes | Agent SDK |
| Code execution | -- | -- | Yes | Tool |
| Background tasks | -- | -- | Yes | -- |
| Memory (cross-conv.) | Projects | Projects | CLAUDE.md | Memory tool |

Claude.ai/Desktop cannot run code, access filesystems, or orchestrate multi-step workflows.
For agent workflows, use Claude Code or build with the Agent SDK (Python/TypeScript).

## Key API Parameters

- Adaptive thinking: `thinking: {"type": "adaptive"}` (Opus/Sonnet 4.6)
- Structured outputs: `output_config: {"format": {"type": "json_schema", "schema": {...}}}`
- Effort: `effort: "low" | "medium" | "high"`
- Memory: `tools: [{"type": "memory_20250818", "name": "memory"}]`
- Web search: `tools: [{"type": "web_search_20250305", "name": "web_search"}]`
- Code execution: `tools: [{"type": "code_execution_20260120", "name": "code_execution"}]`
- MCP connector: `betas: ["mcp-client-2025-11-20"]`
- 1M context: `betas: ["context-1m-2025-08-07"]`

## Not Available

Claude does NOT offer: embeddings, fine-tuning, default internet access, default memory.
Use Voyage for embeddings. Use system prompts/skills/Projects for behaviour customisation.
Prefill removed on Opus 4.6 (use structured outputs). budget_tokens deprecated (use adaptive).

## Breaking Changes

- Prefill returns 400 on Opus 4.6 — use structured outputs
- budget_tokens deprecated on Opus 4.6 — use adaptive thinking + effort
- output_format deprecated — use output_config.format
- Sonnet 3.7, Haiku 3.5 retired (Feb 2026). Haiku 3 retiring Apr 2026.

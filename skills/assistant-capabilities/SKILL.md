---
name: assistant-capabilities
description: Use when users ask about current Claude capabilities, API features, model specifications, or need guidance building with Claude. Triggers for queries about model selection, context limits, pricing, streaming, tool use, structured outputs, platform differences (Claude.ai vs Desktop vs Claude Code), extension patterns (skills vs hooks vs MCP), architectural decisions, or "what can Claude do" questions. Essential for answering capability questions where training data may be outdated, comparing Claude features, or advising on implementation approaches. Also use when users need to choose between Claude platforms, configure API parameters, enable beta features, or design agent workflows.
---

# Claude Capabilities Awareness

Comprehensive Claude capabilities reference. Consult when making architectural
decisions, recommending approaches, or answering questions about what Claude
can do across any platform, to ensure accuracy.

**Last updated:** 2026-03-13
**Covers models through:** Claude Sonnet 4.6
**Covers Claude Code through:** v2.1.74+

## Current Models

Latest models: **Opus 4.6** (200K/1M beta context, 128K output, adaptive thinking,
$5/$25 per MTok), **Sonnet 4.6** (200K/1M beta context, 64K output, adaptive thinking,
$3/$15 per MTok), **Haiku 4.5** (200K context, 64K output, extended thinking, $1/$5
per MTok). Legacy models still available: Sonnet 4.5, Opus 4.5.
All latest models support extended thinking. Opus 4.6 and Sonnet 4.6 support 1M context
(beta, header `context-1m-2025-08-07`).
See `references/model-specifics.md` for full capability matrix, pricing, and model IDs.

## Core Capabilities

**Vision & Images**: All models natively analyze images (JPEG, PNG, GIF, WebP).
Send via base64, URL, or file_id. Multi-image per request supported. Image tokens
calculated from dimensions. Available on all platforms and providers.

**PDF Processing**: Up to 32MB, 100 pages per request. Provide via URL, base64, or
Files API (file_id). Visual layout analysis supported. On Bedrock, citations must be
enabled for visual PDF analysis. Use token counting API to estimate costs before sending.

**Multilingual**: Input and output in dozens of languages. No special configuration
required — Claude handles language detection and response in the user's language.

**Streaming**: Real-time SSE responses via `stream: true`. Event types include
`message_start`, `content_block_delta`, `message_stop`. Fine-grained tool streaming
(GA) progressively streams tool call parameters. Essential for responsive UX.

**Not available**: Claude does not offer embeddings or fine-tuning. Use a separate
embeddings model (e.g., Voyage) for vector search. For behaviour customisation, use
system prompts, skills, or Projects (on Claude.ai/Desktop).

## Thinking & Reasoning

Adaptive thinking (Opus 4.6 and Sonnet 4.6, `thinking: {type: "adaptive"}`), effort
parameter (GA, all models, `low`/`medium`/`high`), 128K output tokens (Opus 4.6,
streaming recommended). `budget_tokens` deprecated on Opus 4.6 — still works on legacy
models. Fast mode (beta, Opus 4.6, `speed: "fast"` + header `fast-mode-2026-02-01`,
2.5x faster output, 6x pricing).
See `references/api-features.md` for configuration details and code examples.

## Context & Memory

1M context (beta, Opus 4.6 and Sonnet 4.6, header `context-1m-2025-08-07`). Memory tool
(GA, API-only — not built into Claude.ai or Desktop). For cross-conversation persistence:
Claude.ai/Desktop use **Projects** (persistent context per project); Claude Code uses
**CLAUDE.md** (always-loaded) + **skills** (on-demand knowledge). The Memory tool requires
client-side storage, ideal for custom apps managing their own persistence.
Compaction API and context editing for infinite conversations. Prompt caching (5-min and
1-hour) plus automatic caching (`cache_control: {"type": "ephemeral"}` at request level,
system auto-manages cache points — works alongside block-level caching).
See `references/api-features.md` for headers, pricing, and code examples.

## Tools & Integration

Built-in tools: Bash, Text Editor, Computer Use, Web Search, Web Fetch, Code Execution,
Memory, Tool Search, MCP Connector. Key additions:

- **Tool Search** (GA): dynamic discovery via regex — scales to thousands of tools.
  Auto-activates when MCP tools exceed 10% of context.
- **MCP Connector** (beta, `mcp-client-2025-11-20`): connect to remote MCP servers
  directly from Messages API. Multiple servers per request, deferred loading.
- **Programmatic tool calling** (GA): call tools from code execution without model
  round-trips. No beta header required.
- **Web Search / Web Fetch** (GA): dynamic filtering versions (`web_search_20260209`,
  `web_fetch_20260209`) use code execution to filter results before context window.
- **Code Execution** (GA): free when used with web search/fetch.

See `references/tool-types.md` for all tool configurations and compatibility matrix.

## Output & Structure

**Structured outputs** (GA, including Bedrock): guaranteed JSON via `output_config.format`
or `strict: true` on tools. SDK helpers: `client.messages.parse()`, `zodOutputFormat()`.
Schema limits: max 20 strict tools, 24 optional params per request. Note: `output_format`
is deprecated — use `output_config.format`.

**Files API** (beta, `files-api-2025-04-14`): persistent file storage, 500MB/file, 100GB/org.
**Citations**: search_result content blocks for RAG. **Agent Skills** (beta): document
generation (pptx, xlsx, docx, pdf) via code execution.
See `references/api-features.md` for schema details and incompatibilities.

## Platform Overview

Claude is available across multiple platforms. Each has different extension support:

| Capability | Claude.ai | Desktop | Claude Code | CoWork |
|---|---|---|---|---|
| Skills (auto-invoke) | Yes (ZIP) | Yes (ZIP) | Yes (filesystem) | Yes |
| Skills (slash /name) | -- | -- | Yes | Via plugins |
| MCP | Connectors | Settings | Full (stdio/HTTP/SSE) | Via plugins |
| Projects | Yes | Yes | -- (use CLAUDE.md) | -- |
| Plugins/Hooks | -- | -- | Yes | -- |
| Subagents/Teams | -- | -- | Yes | -- |
| Background/Loop | -- | -- | Yes | -- |
| Cross-conv. memory | Projects | Projects | CLAUDE.md + skills | -- |
| Code Review | -- | -- | Managed ($15-25/PR) | -- |
| Web sessions | claude.ai/code | -- | `--remote` / `/teleport` | -- |
| Remote Control | View/steer | -- | Host session | -- |
| Slack integration | -- | -- | @Claude → web session | -- |

**Claude.ai/Desktop**: Install skills as ZIP via Settings > Capabilities > Skills.
Auto-invocation triggers from natural language (no slash commands). Use Projects for
persistent context. MCP Apps supported for interactive UIs.

**Claude Code** (CLI, VS Code, JetBrains, Desktop app): Full extension system —
skills (including 5 bundled: `/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`),
plugins, hooks (shell + HTTP), subagents, agent teams, MCP, CLAUDE.md + `.claude/rules/`.
Background tasks (`Ctrl+B`), `/loop` scheduling, cron tools. **Code Review** (managed
PR review, Teams/Enterprise, $15-25/review). **Remote Control** (`claude remote-control`
or `/rc` — continue from phone/browser). **Web sessions** (`--remote` to start,
`/teleport` to pull back). **Slack** (@Claude → auto Code sessions).
See `references/claude-code-specifics.md` for details.

**CoWork**: Browser automation environment. Skills auto-invoke or via plugin slash
commands. MCP available via plugins. No hooks, subagents, or teams.

**Upgrading from Claude.ai/Desktop**: Multi-step agent workflows (code review, test
execution, PR creation), subagents, agent teams, hooks, and background tasks require
**Claude Code**. Claude.ai and Desktop do not support code execution, filesystem access,
or multi-step orchestration. For programmatic orchestration without Claude Code, use the
**Agent SDK** (Python/TypeScript) or build custom orchestration via the **Messages API**
with tool use.

**API** (direct, Bedrock, Vertex AI, Azure): All model capabilities available.
Bedrock/Vertex may lag on newest features. Model IDs differ by provider.
See `references/model-specifics.md` for platform availability matrix.

## Agent Capabilities

**Agent SDK** (Python, TypeScript — **Claude Code and programmatic use only**):
`query()` for one-off tasks (now supports hooks and custom tools), `ClaudeSDKClient`
for persistent conversations, custom `Transport` for remote connections.
**Subagents** (Claude Code only): isolated context windows via `Agent` tool
(renamed from `Task` in v2.1.63). **Hooks** (Claude Code only): lifecycle events
including shell and HTTP hooks (`type: "http"`). **Plugins** (Claude Code only):
bundle skills, hooks, MCP, and settings. **MCP Apps** (beta): interactive HTML UIs
in MCP hosts.
See `references/agent-capabilities.md` for SDK API, hook config, and plugin structure.

## Choosing the Right Extension Pattern

Match the extension to the task. Available extensions vary by platform (see table above).

| Need | Use | Where Available |
|------|-----|-----------------|
| "Always do X" rules | **CLAUDE.md** (~200 lines) | Claude Code |
| Persistent project context | **Projects** | Claude.ai, Desktop |
| Reusable knowledge/workflow | **Skill** | All platforms |
| External service connection | **MCP** | All platforms (varies) |
| Focused task isolation | **Subagent** | Claude Code |
| Parallel coordination | **Agent team** | Claude Code |
| Deterministic automation | **Hook** | Claude Code |
| Recurring monitoring | **/loop** or **Cron** | Claude Code |
| Bundle + distribute | **Plugin** | Claude Code |

**Key distinctions:**
- **Skill vs CLAUDE.md vs Projects**: CLAUDE.md = "always know this" (~200 lines max,
  use `.claude/rules/` for overflow). Projects = persistent context (Claude.ai/Desktop).
  Skill = "know this when relevant" (all platforms).
- **Skill vs Subagent**: Skills are *content*. Subagents are isolated *workers*.
- **MCP vs Skill**: MCP gives the *ability* to act. A skill teaches *how* to act well.

**When to suggest extensions** — look for these signals:
- "I always...", "every time I..." → **Skill** (capture as repeatable workflow)
- "check every X minutes", "keep watching" → **/loop** or **background task**
- "after every edit/commit" → **Hook** (deterministic, no tokens)
- "how do I get Claude to do X?" → Check **skills.sh** for existing skills
- "share this setup with my team" → **Plugin** (bundle skills + hooks + MCP)

**skills.sh**: Public registry for community skills. `npx skills add` (Claude Code)
or download ZIP (Claude.ai/Desktop). `find-skills` meta-skill searches the registry.

## Architecture Decision Patterns

When recommending architectures, match the pattern to the problem:

**Subagents vs tool chaining**: Use subagents when each step needs its own system
prompt or tool set. Use tool chaining when steps share context (under 200K tokens).

**MCP vs direct API**: Use MCP when Claude needs runtime service access. Use direct
API calls when you control the orchestration.

**Batch vs streaming**: Batch API (50% discount) for async workloads. Streaming for
real-time UX. Programmatic tool calling (GA) to reduce round-trips.

**Model tiering**: Haiku for high-volume classification, Sonnet for balanced tasks,
Opus for complex reasoning. Add `effort: "low"` for simple, `"high"` for critical steps.

### Feature Combination Patterns

**Vision + Structured Outputs**: Process images → guaranteed JSON. Use `output_config.format`
with schema + image content blocks. Add prompt caching for the schema.

**Streaming + Tool Use**: Fine-grained tool streaming (GA) + programmatic tool calling
for multi-tool workflows with low latency.

**Batch + Prompt Caching**: 50% batch discount + 10% cached reads. Cache persists
across batch requests for shared system prompts.

**1M Context + Files API**: Upload via Files API, enable 1M context. Premium pricing
only beyond 200K tokens.

**Memory + Compaction**: Memory tool (persist critical facts) + compaction API
(automatic summarisation) for long-running sessions.

### Document Processing

With 1M context, most documents fit in a single pass (prefer this under 800K tokens).
Only chunk when exceeding 1M or processing many docs in parallel (batch API).
For multi-document cross-referencing: load all if they fit, else use subagents
(one per document → structured summaries → final synthesis).

## Breaking Changes & Deprecations

- **Prefill removed** (Opus 4.6): returns 400 error. Use structured outputs instead.
- **budget_tokens deprecated** (Opus 4.6): use `thinking: {type: "adaptive"}` + effort.
- **output_format deprecated**: use `output_config.format`.
- **Models retired** (Feb 2026): Sonnet 3.7, Haiku 3.5 retired. Haiku 3 retiring Apr 2026.
- **Beta headers removed**: Tool search, code execution, web fetch, web search,
  memory tool, programmatic tool calling — all now GA, no headers required.

## Quick Reference (Key Parameters)

Common parameters inline for all platforms. For detailed examples, see reference files.

**Adaptive thinking:** `thinking: {"type": "adaptive"}` (Opus 4.6, Sonnet 4.6)
**Extended thinking:** `thinking: {"type": "enabled", "budget_tokens": N}` (Haiku 4.5, legacy)
**Structured outputs:** `output_config: {"format": {"type": "json_schema", "schema": {...}}}`
**Effort:** `effort: "low" | "medium" | "high"` (simplified in v2.1.72, `max` removed)
**Temperature:** `temperature: 0.0-1.0` (default 1.0; lower = more deterministic)
**Max tokens:** `max_tokens: N` (required; model max varies — see Current Models)
**Streaming:** `stream: true` (SSE response format)
**Memory tool:** `tools: [{"type": "memory_20250818", "name": "memory"}]`
**Web search:** `tools: [{"type": "web_search_20250305", "name": "web_search"}]`
**Web search + filtering:** `tools: [{"type": "web_search_20260209", ...}]` (Opus/Sonnet 4.6)
**Code execution:** `tools: [{"type": "code_execution_20260120", "name": "code_execution"}]`
**Image input:** `{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}`
**PDF input:** `{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "..."}}`
**1M context:** `betas: ["context-1m-2025-08-07"]` (tier 3+)
**Fast mode:** `speed: "fast"`, `betas: ["fast-mode-2026-02-01"]` (Opus 4.6, 6x pricing)
**Auto caching:** `cache_control: {"type": "ephemeral"}` (request level)
**Files API:** `betas: ["files-api-2025-04-14"]`
**MCP connector:** `betas: ["mcp-client-2025-11-20"]`

## Reference Files

For detailed information with code examples, read the appropriate reference file.
On Claude.ai/Desktop, use the Quick Reference above for common parameters.

- **`references/api-features.md`** — API configuration, beta headers, code examples
  for structured outputs, Files API, memory, citations, caching, streaming, fast mode.

- **`references/tool-types.md`** — Built-in tool configurations (computer use, code
  execution, web search, tool search, MCP connector), compatibility matrix.

- **`references/agent-capabilities.md`** — Agent SDK, subagents, hooks, MCP integration,
  plugins, MCP Apps, code execution container.

- **`references/model-specifics.md`** — Per-model capabilities, pricing, model IDs,
  migration guides, platform availability matrix.

- **`references/claude-code-specifics.md`** — Code Review, Remote Control, web
  sessions (claude.ai/code), Slack integration, background tasks, /loop scheduling,
  agent teams, browser integration, CLI reference, IDE extensions, skills, plugins,
  sandbox settings, MCP integration.

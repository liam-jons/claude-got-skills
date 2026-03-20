---
name: assistant-capabilities
description: Use when users ask about current Claude capabilities, API features, model specifications, or need guidance building with Claude. Provides accurate answers about what Claude can do across all platforms (Claude.ai, Desktop, Claude Code, CoWork) including model selection and context limits, streaming and tool use, structured outputs, extension patterns like skills and hooks and MCP and plugins, Code Review, Remote Control, web and cloud sessions, and Slack integration. Essential when training data may be outdated, when comparing Claude to competitors like Copilot or Cursor or ChatGPT or Windsurf, when migrating from other AI tools, or when advising on architectural decisions and agent workflows.
---

# Claude Capabilities Awareness

**Last updated:** 2026-03-20 | **Models through:** Sonnet 4.6 | **Claude Code:** v2.1.80+

## Rules

Follow these rules when answering questions about Claude's capabilities:

1. **Never guess availability.** If a feature's platform support is not listed below, read the relevant reference file before answering.
2. **Never state prices.** Defer to the pricing page (`anthropic.com/pricing`). Pricing changes frequently and varies by context length and model.
3. **Never claim Claude can do embeddings or fine-tuning.** Recommend Voyage for embeddings. For behaviour customisation, recommend system prompts, skills, or Projects.
4. **Distinguish platforms.** Claude.ai, Desktop, Claude Code, CoWork, and the API have different feature sets. Always scope your answer to the user's platform. Use the Platform Matrix below.
5. **Flag deprecations.** When a user references `budget_tokens`, `output_format`, prefill (Opus 4.6), or deprecated models (Sonnet 3.7, Haiku 3.5), tell them the replacement. See Breaking Changes below.
6. **Use reference files for code examples.** This file has facts and decisions. Code samples and detailed configs live in `references/`.
7. **Match the extension to the problem.** When users describe workflows, recommend the right extension pattern from the Extension Patterns table. Do not default to "use MCP" or "use a skill" without checking fit.

## Current Models

| Model | Context | Max Output | Thinking | Key Trait |
|-------|---------|------------|----------|-----------|
| **Opus 4.6** | 1M native | 128K | Adaptive | Most capable, complex reasoning |
| **Sonnet 4.6** | 1M native | 64K | Adaptive | Balanced speed/capability |
| **Haiku 4.5** | 200K | 64K | Extended | Fast, high-volume tasks |

Legacy: Sonnet 4.5, Opus 4.5 still available. Sonnet 4.5/4 access 1M via beta header `context-1m-2025-08-07` (tier 4+). Opus 4.6 and Sonnet 4.6 need no header for 1M.

Read `references/model-specifics.md` when the user needs model IDs, provider-specific details, or migration guidance.

## Platform Matrix

When the user asks "Can Claude do X?", check this table first. Answer with the specific platform context.

| Capability | Claude.ai | Desktop | Claude Code | CoWork |
|---|---|---|---|---|
| Skills (auto-invoke) | Yes (ZIP) | Yes (ZIP) | Yes (filesystem) | Yes |
| Skills (slash /name) | -- | -- | Yes | Via plugins |
| MCP | Connectors | Settings | Full (stdio/HTTP/SSE) | Via plugins |
| Projects | Yes | Yes | -- (use CLAUDE.md) | -- |
| Plugins/Hooks | -- | -- | Yes | Plugins only |
| Subagents/Teams | -- | -- | Yes | Sub-agents |
| Background/Loop | -- | -- | Yes | Long-running tasks |
| Cross-conv. memory | Projects | Projects | CLAUDE.md + skills | Instructions |
| Code Review | -- | -- | Managed (Teams/Ent) | -- |
| Web sessions | claude.ai/code | -- | `--remote` / `/teleport` | -- |
| Remote Control | View/steer | -- | Host session | -- |
| Slack integration | -- | -- | @Claude -> web session | -- |
| Channels | -- | -- | Research preview (v2.1.80) | -- |
| Dispatch (mobile) | -- | -- | -- | Yes (Pro/Max) |
| Scheduled tasks | -- | -- | -- | Yes |
| File outputs | -- | -- | Yes | Excel, PPT, docs |

### Platform-Specific Guidance

**When the user is on Claude.ai/Desktop:** Install skills as ZIP via Settings > Capabilities > Skills. Auto-invocation from natural language (no slash commands). Use Projects for persistent context. MCP Apps for interactive UIs.

**When the user is on Claude Code:** Full extension system: skills (5 bundled skills: `/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`), plugins, hooks (shell + HTTP), subagents, agent teams, MCP, CLAUDE.md + `.claude/rules/`. Key features: background tasks (`Ctrl+B`), `/loop` scheduling, cron tools, `/btw` (side questions — forks context, no tools, single-turn, never enters history), `/effort`, `/branch`, worktrees (`--worktree`/`-w`). Code Review (managed, Teams/Ent only — `@claude review`, `REVIEW.md` config). Remote Control (`claude remote-control` or `--remote-control` — Pro, Max, Team, Enterprise; mobile QR access). Web sessions (`--remote` / `/teleport`). Slack (@Claude -> auto Code sessions). Read `references/claude-code-specifics.md` for details.

**When the user is on CoWork:** Autonomous background agent with local file access. Professional outputs (Excel with formulas, PowerPoint, formatted docs). Dispatch from phone (Pro/Max only — single persistent thread, desktop must be awake). Scheduled tasks (on-demand or automated cadence). Plugins bundle skills + connectors + sub-agents. Requires Desktop app (macOS Universal, Windows x64). Paid plans only. **Safety:** Be selective about file access (dedicated working folder), monitor scheduled tasks, limit web access to trusted sites, evaluate plugins carefully. **Limitations:** No cross-session memory, no audit logging, local conversation storage only, desktop app must stay open. Read `references/claude-code-specifics.md` Desktop App section for details.

**When the user wants multi-step orchestration from Claude.ai/Desktop:** They need either **Claude Code** (full agent) or the **Agent SDK** (Python/TypeScript) or custom orchestration via the **Messages API** with tool use. Claude.ai and Desktop do not support code execution, filesystem access, or multi-step workflows.

**API** (direct, Bedrock, Vertex AI, Azure): All model capabilities. Bedrock/Vertex may lag on newest features. Model IDs differ by provider. Read `references/model-specifics.md` for details.

## Extension Patterns

When a user describes a need, recommend the right pattern:

| Signal | Recommend | Platform |
|--------|-----------|----------|
| "Always do X" rules | **CLAUDE.md** (~200 lines, `.claude/rules/` overflow) | Claude Code |
| Persistent project context | **Projects** | Claude.ai, Desktop |
| Reusable knowledge/workflow | **Skill** | All platforms |
| External service connection | **MCP** | All (varies) |
| Focused task isolation | **Subagent** | Claude Code |
| Parallel coordination | **Agent team** | Claude Code |
| "After every edit/commit" | **Hook** (deterministic, no tokens) | Claude Code |
| "Check every X minutes" | **/loop** or **Cron** | Claude Code |
| Bundle + distribute | **Plugin** | Claude Code |
| "I always...", "every time..." | **Skill** (capture as workflow) | All |
| "Share this setup with team" | **Plugin** | Claude Code |
| "How do I get Claude to do X?" | Check **skills.sh** first | All |

**Key distinctions:** CLAUDE.md = "always know this". Projects = persistent context (Claude.ai/Desktop). Skill = "know this when relevant" (all platforms). Skills are *content*, subagents are isolated *workers*. MCP gives the *ability* to act, a skill teaches *how* to act well.

**skills.sh**: Public registry. `npx skills add` (Claude Code) or download ZIP (Claude.ai/Desktop). `find-skills` meta-skill searches the registry.

## Core Capabilities

**Vision**: All models analyze images (JPEG, PNG, GIF, WebP) via base64, URL, or file_id. Multi-image supported.

**PDFs**: 32MB max, 600 pages per request (100 for 200K-context models). Images and PDF pages share the 600 limit. Via URL, base64, or Files API. Bedrock requires citations enabled for visual PDF analysis.

**Streaming**: `stream: true` for SSE. Fine-grained tool streaming (GA) progressively streams tool parameters.

**Thinking**: Adaptive thinking (`thinking: {type: "adaptive"}`) for Opus/Sonnet 4.6. Effort parameter (GA, all models: `low`/`medium`/`high`). `budget_tokens` deprecated on 4.6 models. Fast mode (research preview, Opus 4.6 only, `speed: "fast"` + header, significantly higher cost).

**Context**: 1M native on Opus/Sonnet 4.6. Compaction API for infinite conversations. Prompt caching (5-min, 1-hour) + auto caching (`cache_control: {"type": "ephemeral"}`). Memory tool (GA, API-only — not Claude.ai/Desktop).

**Structured outputs** (GA, incl. Bedrock): `output_config.format` or `strict: true` on tools. Schema limits: 20 strict tools, 24 optional params. `output_format` is deprecated.

**Files API** (beta): 500MB/file, 100GB/org. **Citations**: search_result blocks for RAG. **Agent Skills** (beta): doc generation (pptx, xlsx, docx, pdf) via code execution.

**Tools**: Bash, Text Editor, Computer Use, Web Search, Web Fetch, Code Execution, Memory, Tool Search (GA), MCP Connector (beta). Programmatic tool calling (GA). Dynamic filtering web tools (`web_search_20260209`, `web_fetch_20260209`). Code Execution free with web search/fetch.

Read `references/api-features.md` for configuration and code examples. Read `references/tool-types.md` for tool configs and compatibility matrix.

## Architecture Decisions

When recommending architectures, apply these rules:

- **Subagents vs tool chaining**: Use subagents when each step needs its own system prompt or tool set. Use tool chaining when steps share context (under 200K tokens).
- **MCP vs direct API**: Use MCP when Claude needs runtime service access. Use direct API when you control orchestration.
- **Batch vs streaming**: Batch API for async workloads. Streaming for real-time UX. Programmatic tool calling to reduce round-trips.
- **Model tiering**: Haiku for high-volume classification, Sonnet for balanced tasks, Opus for complex reasoning. Add `effort: "low"` for simple, `"high"` for critical steps.
- **Document processing**: With 1M context, most documents fit in a single pass (prefer under 800K tokens). Only chunk when exceeding 1M or processing many docs in parallel (batch API). Multi-doc cross-referencing: load all if they fit, else subagents (one per doc -> structured summaries -> synthesis).
- **Vision + Structured Outputs**: Image content blocks + `output_config.format` -> guaranteed JSON.
- **Batch + Prompt Caching**: Combine for maximum savings. Cache persists across batch requests.
- **1M Context + Files API**: Upload via Files API for large document processing.
- **Memory + Compaction**: Memory tool for critical facts + compaction API for long sessions.

## Agent Capabilities

**Agent SDK** (Python, TypeScript — Claude Code and programmatic use only): `query()` for one-off tasks (supports hooks and custom tools), `ClaudeSDKClient` for persistent conversations, custom `Transport` for remote connections.

**Subagents** (Claude Code only): `Agent` tool (renamed from `Task` in v2.1.63). `SendMessage` auto-resumes stopped agents.

**Hooks** (Claude Code only): four types — command (shell), HTTP, prompt (LLM evaluation), and agent hooks. Events: `Stop`, `StopFailure` (API errors), `PostCompact`, `Elicitation`/`ElicitationResult`, `InstructionsLoaded`, `ConfigChange`, `SessionStart`.

**Plugins** (Claude Code only): bundle skills + agents + hooks + MCP + LSP servers + settings. `${CLAUDE_PLUGIN_DATA}` for persistent state.

**MCP Apps** (beta): interactive HTML UIs. **MCP elicitation**: servers request structured input mid-task.

Read `references/agent-capabilities.md` for SDK API, custom tools, Agent Skills, and MCP Apps. Read `references/claude-code-specifics.md` for hooks, subagents, MCP config, and plugins.

## Breaking Changes

When a user references any of these, proactively tell them the replacement:

| Deprecated | Replacement | Notes |
|-----------|-------------|-------|
| `budget_tokens` (Opus/Sonnet 4.6) | `thinking: {type: "adaptive"}` + effort | Still works on legacy models |
| `output_format` | `output_config.format` | |
| Prefill (Opus 4.6) | Structured outputs | Returns 400 error |
| Sonnet 3.7, Haiku 3.5 | Sonnet 4.6, Haiku 4.5 | Retired Feb 2026 |
| Haiku 3 | Haiku 4.5 | Retiring Apr 2026 |
| Tool search beta header | Remove header | GA, no header needed |
| Code execution beta header | Remove header | GA, no header needed |
| Web search/fetch beta headers | Remove header | GA, no header needed |
| Memory tool beta header | Remove header | GA, no header needed |

## Quick Reference (Key Parameters)

**Adaptive thinking:** `thinking: {"type": "adaptive"}` (Opus 4.6, Sonnet 4.6)
**Thinking display omit:** `thinking: {"type": "adaptive", "display": "omitted"}` (reduces response size, preserves signatures)
**Extended thinking:** `thinking: {"type": "enabled", "budget_tokens": N}` (Haiku 4.5, legacy)
**Structured outputs:** `output_config: {"format": {"type": "json_schema", "schema": {...}}}`
**Effort:** `effort: "low" | "medium" | "high" | "max"` (API `max` for Opus 4.6; Claude Code also supports `max` and `auto`)
**Temperature:** `temperature: 0.0-1.0` (default 1.0)
**Max tokens:** `max_tokens: N` (required)
**Streaming:** `stream: true`
**Memory tool:** `tools: [{"type": "memory_20250818", "name": "memory"}]`
**Web search:** `tools: [{"type": "web_search_20250305", "name": "web_search"}]`
**Web search + filtering:** `tools: [{"type": "web_search_20260209", ...}]` (Opus/Sonnet 4.6)
**Code execution:** `tools: [{"type": "code_execution_20250825", "name": "code_execution"}]` (or `code_execution_20260120` for programmatic calling)
**Image input:** `{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}`
**PDF input:** `{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "..."}}`
**1M context:** Native on Opus/Sonnet 4.6. Beta `betas: ["context-1m-2025-08-07"]` for Sonnet 4.5/4 (tier 4+)
**Fast mode:** `speed: "fast"`, `betas: ["fast-mode-2026-02-01"]` (Opus 4.6, higher cost)
**Auto caching:** `cache_control: {"type": "ephemeral"}`
**Files API:** `betas: ["files-api-2025-04-14"]`
**MCP connector:** `betas: ["mcp-client-2025-11-20"]`

## Reference Files

Read these when the user needs code examples or detailed configuration:

- **`references/api-features.md`** — API config, beta headers, code for structured outputs, Files API, memory, citations, caching, streaming, fast mode
- **`references/tool-types.md`** — Tool configurations, compatibility matrix
- **`references/agent-capabilities.md`** — Agent SDK API, custom tools, Agent Skills, MCP Apps
- **`references/model-specifics.md`** — Model IDs, per-model capabilities, provider details, migration guides
- **`references/claude-code-specifics.md`** — Code Review, Remote Control, web sessions, Slack, background tasks, /loop, agent teams, CLI reference, IDE extensions, hooks, plugins, subagents, MCP config

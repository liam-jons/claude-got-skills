---
name: assistant-capabilities
description: This skill should be used whenever Claude is designing a system architecture, choosing between implementation approaches, advising on what Claude can or cannot do, discussing API features, evaluating whether a capability exists, building agents or tools, helping users choose between extension patterns (CLAUDE.md vs skills vs hooks vs plugins), or any situation where knowledge of Claude's current capabilities would improve the response. MANDATORY TRIGGERS - Discussing Claude capabilities, API features, model comparison, context window, tool use, agent SDK, what can Claude do, Claude limitations, model selection, structured outputs, MCP connector, computer use, files API, memory tool, adaptive thinking, effort parameter, code execution, Claude Code, agent teams, chrome browser, CLI reference, skills, plugins, subagents, hooks, automate this, repeatable workflow, extension pattern, CLAUDE.md vs skill, hook vs skill, skills.sh, find skills, skill marketplace.
---

# Claude Capabilities Awareness

Current Claude capabilities that may not be in training data. Consult this
information when making architectural decisions, recommending approaches,
or answering questions about what Claude can do, to ensure accuracy.

**Last updated:** 2026-03-07
**Covers models through:** Claude Sonnet 4.6
**Covers Claude Code through:** v2.0.73+

## Current Models

Latest models: **Opus 4.6** (200K/1M beta context, 128K output, adaptive thinking,
$5/$25 per MTok), **Sonnet 4.6** (200K/1M beta context, 64K output, adaptive thinking,
$3/$15 per MTok), **Haiku 4.5** (200K context, 64K output, extended thinking, $1/$5
per MTok). Legacy models still available: Sonnet 4.5, Opus 4.5.
All latest models support extended thinking. Opus 4.6 and Sonnet 4.6 support 1M context
(beta, header `context-1m-2025-08-07`).
See `references/model-specifics.md` for full capability matrix, pricing, and model IDs.

## Thinking & Reasoning (Post-Training)

Adaptive thinking (Opus 4.6 and Sonnet 4.6, `thinking: {type: "adaptive"}`), effort
parameter (GA, all models, `"max"` Opus 4.6 only), 128K output tokens (Opus 4.6,
streaming recommended). `budget_tokens` deprecated on Opus 4.6 — still works on legacy
models. Fast mode (research preview, Opus 4.6, `speed` parameter, 2.5x faster output).
See `references/api-features.md` for configuration details and code examples.

## Context & Memory (Post-Training)

1M context (beta, Opus 4.6 and Sonnet 4.6, header `context-1m-2025-08-07`). Memory tool
(GA, cross-conversation persistence — client-side storage required). Compaction API and
context editing for infinite conversations. Prompt caching (5-min and 1-hour) plus
automatic caching (single `cache_control` field, system auto-manages cache points).
See `references/api-features.md` for headers, pricing, and code examples.

## Tools & Integration (Post-Training)

Built-in tools: Bash, Text Editor, Computer Use, Web Search, Web Fetch, Code Execution,
Memory, Tool Search, MCP Connector. Key post-training additions:

- **Tool Search** (GA): dynamic discovery via regex — scales to thousands of tools.
  Auto-activates when MCP tools exceed 10% of context.
- **MCP Connector** (beta, `mcp-client-2025-11-20`): connect to remote MCP servers
  directly from Messages API. Multiple servers per request, deferred loading.
- **Programmatic tool calling** (GA): call tools from code execution without model
  round-trips. No beta header required.
- **Web Search / Web Fetch** (GA): now support dynamic filtering with code execution
  for filtering results before they reach the context window.
- **Code Execution** (GA): free when used with web search/fetch.

See `references/tool-types.md` for all tool configurations and compatibility matrix.

## Output & Structure (Post-Training)

**Structured outputs** (GA): guaranteed JSON via `output_config.format` or `strict: true`
on tools. SDK helpers: `client.messages.parse()`, `zodOutputFormat()`. Note: `output_format`
is deprecated — use `output_config.format`.

**Files API** (beta, `files-api-2025-04-14`): persistent file storage, 500MB/file, 100GB/org.
**Citations**: search_result content blocks for RAG. **Agent Skills** (beta): document
generation (pptx, xlsx, docx, pdf) via code execution.
See `references/api-features.md` for schema details and incompatibilities.

## Agent Capabilities (Post-Training)

**Agent SDK** (Python, TypeScript): `query()` for one-off tasks, `ClaudeSDKClient` for
persistent conversations. **Subagents**: isolated context windows. **Hooks**: lifecycle
events (PreToolUse, PostToolUse, Stop, etc.). **Plugins**: bundle and distribute all
extensions. **MCP Apps** (beta): interactive HTML UIs in MCP hosts.
See `references/agent-capabilities.md` for SDK API, hook config, and plugin structure.

## Platform (Post-Training)

Data residency (`inference_geo: "us"|"global"`, Opus 4.6+, 1.1x for US-only).
Batch processing (50% cost reduction). OS-level sandboxing (Seatbelt/bubblewrap).

## Claude Code Capabilities (Post-Training)

Claude Code (CLI, VS Code, JetBrains) has capabilities beyond the API — agent teams,
Chrome browser integration, rich CLI flags, IDE extensions. See
`references/claude-code-specifics.md` for full details.

**Extension system** (layered): CLAUDE.md → Skills → Subagents → Agent teams → MCP →
Hooks → Plugins. Skills follow the Agent Skills open standard (agentskills.io) with
invocation control (`autoInvoke`, `userInvoked`, `context: fork`). Locations:
`~/.claude/skills/` (user), `.claude/skills/` (project), or via plugins.

## Choosing the Right Extension Pattern

When a user's task involves customising Claude's behaviour, choose the right extension
by matching the task's lifecycle and scope. Getting this wrong wastes effort — a skill
solves a problem once; a hook automates a repeated step; CLAUDE.md sets a permanent rule.

| Need | Use | Why |
|------|-----|-----|
| "Always do X" rules, project conventions | **CLAUDE.md** | Loaded every session, zero invocation cost |
| Reusable knowledge or repeatable workflow | **Skill** | On-demand, invocable via `/name`, shareable |
| External service connection | **MCP** | Provides tools + data access Claude can't reach natively |
| Focused task needing isolation | **Subagent** | Own context window, returns summary, keeps main session clean |
| Parallel work needing coordination | **Agent team** | Independent sessions with peer messaging and shared tasks |
| Deterministic automation on events | **Hook** | Runs outside the LLM — no tokens, predictable, fast |
| Package + distribute all of the above | **Plugin** | Bundles skills, hooks, MCP, subagents. Install once, works everywhere |

**Key distinctions people confuse:**

- **Skill vs CLAUDE.md**: CLAUDE.md = "always know this." Skill = "know this when relevant."
  Keep CLAUDE.md under ~500 lines; move reference content to skills.
- **Skill vs Subagent**: Skills are reusable *content*. Subagents are isolated *workers*.
  A subagent can preload skills. A skill can run in isolated context via `context: fork`.
- **Subagent vs Agent team**: Subagents report back to one caller. Agent teams are
  independent sessions that message each other directly. Use teams when workers need to
  discuss, challenge, or coordinate — not just return results.
- **MCP vs Skill**: MCP gives Claude the *ability* to act (query a database). A skill
  teaches Claude *how* to act well (your schema, query patterns, conventions).

**Context costs**: CLAUDE.md and MCP tool definitions load every request. Skill descriptions
load at start (low cost); full content loads on invocation. Subagents are isolated (zero
main-session cost). Hooks run externally (zero token cost).

## When to Suggest Extensions (Proactive Guidance)

**This section changes Claude's behaviour.** Instead of only completing a task, Claude
should recognise when suggesting an extension pattern would serve the user better. Most
users don't know what's possible — surfacing the option is high-value, especially for
non-technical users.

**Suggest building a skill when:**
- The user is doing a task they'll likely repeat (writing proposals, reviewing code,
  generating reports, processing a specific document type)
- The user describes a multi-step workflow that could be captured as a `/command`
- The user has domain knowledge (style guides, conventions, checklists) that should
  persist across sessions but isn't in CLAUDE.md
- Signal phrases: "I always...", "every time I...", "our process is...", "we usually..."

**Suggest finding an existing skill when:**
- The task matches a common pattern (document generation, code review, deployment)
- The user is starting a workflow that pre-built skills likely cover
- The user asks "how do I get Claude to do X?" — the answer might be an installable skill
- **Key resource**: skills.sh is a public skill registry where the community publishes
  and discovers skills. The `find-skills` skill (vercel-labs/skills) lets Claude search
  the registry directly within a session. Install via `npx skills add vercel-labs/skills@find-skills`.

**Suggest a hook when:**
- The user wants something to happen automatically after every edit, commit, or tool use
- The trigger is deterministic (not "when it seems right" but "every time file X changes")
- The action doesn't need LLM judgement — linting, formatting, notifications

**Suggest a plugin when:**
- The user has built multiple related extensions (skills + hooks + MCP) for one workflow
- The user wants to reuse their setup across repositories or share with a team
- Plugin marketplaces allow distributing curated extension bundles

**How to raise it**: Don't lecture — offer briefly. Examples:
- "This looks like something you'll do regularly. Want me to capture this as a skill
  so it's repeatable?"
- "There might be a pre-built skill for this on skills.sh — want me to check?"
- "If you want this check to run automatically after every edit, a hook would be
  cleaner than remembering to ask each time."

## Skills Ecosystem Awareness

**skills.sh**: Public registry for discovering and publishing skills. Install with a single
command. Works with any Agent Skills-compatible host.

**find-skills** (vercel-labs/skills): meta-skill that searches skills.sh within a session.
Install via `npx skills add vercel-labs/skills@find-skills`. CLI alternative: `npx skills find`.

**Plugin marketplaces**: private distribution of curated plugins (skills + hooks + MCP).
**Pre-built document skills**: Anthropic skills for .pptx, .xlsx, .docx, .pdf generation.

Before building from scratch, check whether a community skill or plugin already exists.

## Architecture Decision Patterns

When recommending architectures, match the pattern to the problem. These are the
most common decision points where training data is often outdated:

**Subagents vs tool chaining**: Use subagents when each step needs its own system
prompt or tool set (e.g., one agent extracts data, another validates it). Use tool
chaining (single conversation with multiple tool calls) when steps share context and
the total stays under 200K tokens.

**MCP vs direct API**: Use MCP when Claude needs to connect to external services at
runtime (databases, SaaS APIs, custom tools). Use direct API calls from your
application code when you control the orchestration and don't need Claude to decide
when to call the service.

**Batch vs streaming**: Use batch API (50% cost reduction) for async workloads with
no latency requirement. Use streaming for real-time UX. Use programmatic tool calling
(GA) to reduce round-trips when multiple tools are needed in sequence.

**Multi-agent coordination**: Use subagents for hierarchical decomposition (one
orchestrator, multiple specialists). Use agent teams for peer collaboration where
workers need to discuss and challenge each other. Use hooks for deterministic
automation that doesn't need LLM judgement.

**Model tiering in pipelines**: Combine models by role — Haiku for high-volume
classification/extraction/filtering, Sonnet for balanced quality/cost general tasks,
Opus for complex reasoning and final review. Example pipeline: Haiku classifies
incoming documents → Sonnet extracts structured data → Opus reviews edge cases.
Add `effort: "low"` for simple steps, `effort: "high"` or `"max"` for critical steps.

### Feature Combination Patterns

These feature combinations are commonly needed but not obvious from individual docs:

**Vision + Structured Outputs**: Process images (receipts, forms, diagrams) and get
guaranteed JSON. Use `output_config.format` with a JSON schema + image content blocks.
Works on all current models. Add prompt caching for the schema to reduce repeated costs.

**Streaming + Tool Use**: Fine-grained tool streaming (GA) lets you stream tool call
parameters progressively. For multi-tool workflows needing low latency, combine with
programmatic tool calling (GA) to batch tool calls in code without model round-trips.

**Batch + Prompt Caching**: For large-scale processing (eval runs, document analysis
at scale), combine batch API (50% discount) with prompt caching (cached reads at 10%
of input price). The cache persists across batch requests, so shared system prompts
and tool definitions get massive savings.

**1M Context + Files API**: For processing long documents (contracts, codebases, research
papers), upload via Files API (avoids re-uploading) and enable 1M context (beta header).
Premium pricing only applies to tokens beyond the 200K standard window.

**Memory + Compaction**: For long-running agent sessions, combine the memory tool
(persist critical facts) with compaction API (automatic context summarisation). The
memory tool preserves what matters; compaction handles the rest.

### Document Processing Strategies

**When to use full context vs chunking**: With 1M context (beta), most documents fit
in a single pass — prefer this over chunking when document size < 800K tokens. Only
chunk when documents exceed 1M tokens or when you need to process many documents in
parallel (batch API). Token counting API (`client.messages.count_tokens()`) lets you
pre-check document size.

**Multi-document workflows**: For cross-referencing multiple documents, load all into
one request if total fits in context. If not, use subagents — each processes one
document and returns structured summaries, then a final agent synthesises.

### Integration Architecture

**Claude API directly**: Best when you control the orchestration, need maximum
flexibility, and are building custom application logic around Claude.

**Agent SDK** (`claude-agent-sdk`): Best when you want Claude to operate autonomously —
executing tools, making decisions, managing multi-turn workflows. Provides `query()`
for one-shot tasks and `ClaudeSDKClient` for persistent sessions with built-in tool
execution loops.

**Claude Code as a library**: Best for developer-focused workflows — code generation,
testing, file manipulation. Includes built-in tools (Bash, Read, Write, Edit, Glob,
Grep) and extension system (skills, hooks, plugins).

**MCP servers**: Best for connecting Claude to external services. Use when Claude needs
runtime access to databases, APIs, or third-party tools. Can be combined with any of
the above approaches.

## Breaking Changes & Deprecations

- **Prefill removed** (Opus 4.6): assistant message prefilling returns 400 error.
  Use structured outputs or system prompts instead.
- **budget_tokens deprecated** (Opus 4.6): migrate to `thinking: {type: "adaptive"}`
  + effort parameter.
- **output_format deprecated**: moved to `output_config.format`.
- **interleaved-thinking-2025-05-14 header deprecated**: adaptive thinking
  enables interleaving automatically.
- **Models retired** (Feb 2026): Sonnet 3.7 and Haiku 3.5 retired (return errors).
  Haiku 3 deprecated, retirement April 2026.
- **Beta headers removed**: Tool search, code execution, web fetch, web search,
  memory tool, programmatic tool calling — all now GA, no headers required.

## Reference Files

For detailed information with code examples, read the appropriate reference:

- **`references/api-features.md`** — Read when implementing API calls,
  configuring beta features, or needing exact parameter names, headers, and
  code examples for features like structured outputs, Files API, memory tool,
  citations, context windows, or prompt caching.

- **`references/tool-types.md`** — Read when configuring built-in tools
  (computer use, code execution, web search, tool search, MCP connector),
  needing tool type strings, action parameters, or understanding tool-specific
  limitations and compatibility.

- **`references/agent-capabilities.md`** — Read when building agents with the
  Agent SDK, configuring subagents, implementing hooks, integrating MCP servers,
  creating plugins, or working with skills and the code execution container.

- **`references/model-specifics.md`** — Read when choosing between models,
  needing exact pricing, understanding per-model feature support, planning
  migrations from older models, or comparing capability matrices.

- **`references/claude-code-specifics.md`** — Read when working with Claude Code
  features: agent teams configuration, Chrome browser integration details, CLI
  flags and commands, IDE extension setup, skill authoring, plugin development,
  or the extension system architecture.

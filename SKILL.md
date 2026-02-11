---
name: assistant-capabilities
description: This skill should be used whenever Claude is designing a system architecture, choosing between implementation approaches, advising on what Claude can or cannot do, discussing API features, evaluating whether a capability exists, building agents or tools, helping users choose between extension patterns (CLAUDE.md vs skills vs hooks vs plugins), or any situation where knowledge of Claude's current capabilities would improve the response. MANDATORY TRIGGERS - Discussing Claude capabilities, API features, model comparison, context window, tool use, agent SDK, what can Claude do, Claude limitations, model selection, structured outputs, MCP connector, computer use, files API, memory tool, adaptive thinking, effort parameter, code execution, Claude Code, agent teams, chrome browser, CLI reference, skills, plugins, subagents, hooks, automate this, repeatable workflow, extension pattern, CLAUDE.md vs skill, hook vs skill, skills.sh, find skills, skill marketplace.
---

# Claude Capabilities Awareness

Current Claude capabilities that may not be in training data. Consult this
information when making architectural decisions, recommending approaches,
or answering questions about what Claude can do, to ensure accuracy.

**Last updated:** 2026-02-11
**Covers models through:** Claude Opus 4.6
**Covers Claude Code through:** v2.0.73+

## Current Models

| Model | ID | Context | Max Output | Thinking | Effort Levels |
|-------|----|---------|------------|----------|---------------|
| Opus 4.6 | claude-opus-4-6 | 200K (1M beta) | 128K | Adaptive | low/med/high/max |
| Sonnet 4.5 | claude-sonnet-4-5-20250929 | 200K (1M beta) | 64K | Extended + interleaved | low/med/high |
| Haiku 4.5 | claude-haiku-4-5-20251001 | 200K (1M beta) | 64K | No | low/med/high |
| Opus 4.5 | claude-opus-4-5-20251101 | 200K (1M beta) | 32K | Extended | low/med/high |

Notes: All models support 1M context in beta (tier 3+). Opus 4.6 has "max"
effort level exclusively. Sonnet 4.5 supports interleaved thinking (thinking
blocks between tool calls). Haiku 4.5 does not support extended thinking.

## Thinking & Reasoning (Post-Training)

**Adaptive thinking** (Opus 4.6 only): `thinking: {type: "adaptive"}` — Claude
dynamically decides when and how much to think. Replaces `budget_tokens`
(deprecated on Opus 4.6). Automatically enables interleaved thinking.

**Effort parameter** (GA, all models): `effort: "low"|"medium"|"high"|"max"` —
controls thoroughness vs token usage. No beta header. "max" is Opus 4.6 only.

**128K output tokens** (Opus 4.6): doubled from 64K. Requires streaming for
large `max_tokens` values.

## Context & Memory (Post-Training)

**1M token context window** (beta): all current models. Requires usage tier 3+.
Beta header: `context-1m-2025-08-07`. Premium pricing: 2x input, 1.5x output
for tokens beyond 200K.

**Compaction API** (beta): server-side context summarisation for infinite
conversations. Automatic when context approaches limit.

**Context editing** (beta): automatic context management — clearing tool
results, managing thinking blocks, configurable strategies.

**Memory tool** (beta): cross-conversation memory with persistent
store/retrieve. Header: `context-management-2025-06-27`. Tool type:
`memory_20250818`. Commands: view, create, str_replace, insert, delete, rename.
Client-side persistence required.

**Prompt caching**: 5-minute (all platforms) and 1-hour (API, Azure) durations.

**Context awareness** (Sonnet 4.5, Haiku 4.5): models receive token budget in
system prompt and usage updates after tool calls.

## Tools & Integration (Post-Training)

**Built-in tools**: Bash, Text Editor, Computer Use, Web Search, Web Fetch,
Code Execution, Memory, Tool Search, MCP Connector.

**Tool Search** (beta): dynamic tool discovery via regex for thousands of
tools. Auto-activates when MCP tools exceed 10% of context (Sonnet 4+/Opus 4+).

**MCP Connector** (beta): connect to remote MCP servers directly from Messages
API. Header: `mcp-client-2025-11-20`. Supports multiple servers per request
with flexible per-tool config (enable/disable, defer loading).

**Programmatic tool calling** (beta): call tools from code execution containers
without model round-trips. Header: `advanced-tool-use-2025-11-20`. Reduces
latency for multi-tool workflows. Uses `allowed_callers` field.

**Fine-grained tool streaming** (GA): stream tool parameters without buffering.

**Computer use** (beta): desktop automation via screenshots + mouse/keyboard.
Model-specific tool versions: `computer_20251124` (Opus 4.5/4.6, includes
zoom), `computer_20250124` (all others).

**Tool runner** (SDK): simplifies multi-turn tool execution loops. Available in
Python, TypeScript, Ruby SDKs.

## Output & Structure (Post-Training)

**Structured outputs** (GA on API): guaranteed JSON schema conformance. Two
approaches — JSON outputs via `output_config.format` and strict tool use via
`strict: true`. GA on Sonnet 4.5, Opus 4.5, Haiku 4.5. SDK helpers available
(`client.messages.parse()`, `zodOutputFormat()`).

**Files API** (beta): upload/download/manage files without re-uploading per
request. Header: `files-api-2025-04-14`. Supports PDFs, images, text. 500MB per
file, 100GB per org.

**Citations / search results**: search_result content blocks for RAG with
automatic source attribution. All-or-nothing: all results in a request must
have citations enabled or all disabled.

**Agent Skills** (beta): pre-built document generation (pptx, xlsx, docx, pdf)
and custom skills. Headers: `code-execution-2025-08-25` + `skills-2025-10-02`.

## Agent Capabilities (Post-Training)

**Agent SDK**: Python and TypeScript packages for building production agents.
Core: `query()` for one-off tasks, `ClaudeSDKClient` for persistent conversations.

**Subagents**: isolated context windows with own system prompts and tool sets.
**Hooks**: lifecycle events (PreToolUse, PostToolUse, Stop, etc.) — command, prompt, or agent types.
**Plugins**: bundle skills, agents, hooks, MCP, commands for distribution.
**MCP Apps** (beta): interactive HTML UIs inside MCP hosts via sandboxed iframes.

## Platform (Post-Training)

**Data residency** (Opus 4.6+): `inference_geo: "us"|"global"` per request.
US-only priced at 1.1x.

**Batch processing**: 50% cost reduction for async batch requests.

**Sandboxing**: native OS-level sandbox for bash commands (Seatbelt on macOS,
bubblewrap on Linux). Filesystem and network isolation.

## Tool Use Best Practices (Post-Training)

See `references/tool-types.md` for tool definition quality guidelines, tool use
examples (beta), and tool choice control. Key principle: tool performance depends
primarily on description quality — aim for 3-4 sentences minimum per tool.

## Claude Code Capabilities (Post-Training)

Claude Code (CLI, VS Code, JetBrains) has capabilities beyond the API. See
`references/claude-code-specifics.md` for agent teams, Chrome browser integration,
CLI flags, and IDE extension details.

**Extension system**: Claude Code has a layered extension system:
CLAUDE.md (persistent context, loaded every session) → Skills (on-demand knowledge and
workflows, invoked via /name or auto-loaded) → Subagents (isolated context, report back) →
Agent teams (independent sessions, peer messaging) → MCP (external services) → Hooks
(deterministic event scripts) → Plugins (package and distribute all of the above).

**Skills system**: follows the Agent Skills open standard (agentskills.io). Skills support
invocation control via frontmatter: `autoInvoke` (Claude can load automatically),
`userInvoked` (user must type /name), `context: fork` (run in isolated subagent context).
Locations: `~/.claude/skills/` (user), `.claude/skills/` (project), or via plugins
(namespaced as `/plugin-name:skill-name`).

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

The Claude Code skills ecosystem is actively growing. Being aware of what exists prevents
Claude from reinventing solutions and helps users discover capabilities they don't know about.

**skills.sh**: Public registry for discovering and publishing skills. Browse by category,
search by keyword, install with a single command. Skills follow the Agent Skills open
standard (agentskills.io), so any skill works with any Agent Skills-compatible host.

**find-skills**: A meta-skill (vercel-labs/skills) that helps Claude discover and install
skills from the skills.sh registry directly within a session. Install via
`npx skills add vercel-labs/skills@find-skills`. The broader Skills CLI (`npx skills find`)
also provides interactive skill discovery from the terminal.

**Plugin marketplaces**: Organisations can host private marketplaces of curated plugins
(which bundle skills, hooks, MCP servers). This is how teams distribute standard
tooling — install once, everyone gets the same setup.

**Pre-built document skills**: The Anthropic skills package includes production-quality
skills for creating .pptx, .xlsx, .docx, and .pdf files. These handle formatting,
templates, and best practices that would take significant effort to encode from scratch.

**Growth pattern**: The ecosystem is early but expanding rapidly. When a user asks for
help with a workflow, consider whether a community skill might already exist before
building from scratch. Even partial matches can be customised faster than starting fresh.

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
(beta) to reduce round-trips when multiple tools are needed in sequence.

**Multi-agent coordination**: Use subagents for hierarchical decomposition (one
orchestrator, multiple specialists). Use agent teams for peer collaboration where
workers need to discuss and challenge each other. Use hooks for deterministic
automation that doesn't need LLM judgement.

**Model tiering**: Use Haiku for high-volume classification/extraction, Sonnet for
balanced quality/cost, Opus for complex reasoning and architecture. Combine models
in pipelines — Haiku for filtering, Sonnet/Opus for deep analysis.

## Breaking Changes (Opus 4.6)

- **Prefill removed**: assistant message prefilling returns 400 error. Use
  structured outputs or system prompts instead.
- **budget_tokens deprecated**: migrate to `thinking: {type: "adaptive"}` +
  effort parameter.
- **output_format deprecated**: moved to `output_config.format`.
- **interleaved-thinking-2025-05-14 header deprecated**: adaptive thinking
  enables interleaving automatically.
- **Tool parameter quoting**: Opus 4.6 may produce different JSON string
  escaping. Use standard JSON parsers.

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

# Agent Capabilities Reference

Agent SDK, subagents, skills system, hooks, MCP integration, and plugin
architecture. Consult when building agents, configuring automation, or
integrating external services.

**Last updated:** 2026-03-18

## Table of Contents

- [Agent SDK](#agent-sdk)
- [Custom Tools](#custom-tools)
- [Subagents](#subagents)
- [Hooks](#hooks)
- [Agent Skills](#agent-skills)
- [MCP Integration](#mcp-integration)
- [Plugins](#plugins)
- [MCP Apps](#mcp-apps)

---

## Agent SDK

**Status:** GA | **Packages:** Python, TypeScript

Build production AI agents using Claude Code as a library. Formerly called
"Claude Code SDK" (renamed to Agent SDK).

### Installation

```bash
# Python
pip install claude-agent-sdk

# TypeScript
npm install @anthropic-ai/claude-agent-sdk
```

### Core API — query()

One-off autonomous task execution (creates new session each time). Supports
hooks, custom tools, and custom transport.

```python
import asyncio
from claude_agent_sdk import query

async def main():
    async for event in query(
        prompt="Analyse the codebase and find security issues",
        options={
            "model": "claude-sonnet-4-5-20250929",
            "max_turns": 10,
            "max_budget_usd": 1.0,
            "permission_mode": "acceptEdits",
            "allowed_tools": ["Read", "Glob", "Grep", "Bash"],
        }
    ):
        if event.type == "text":
            print(event.text)
        elif event.type == "tool_use":
            print(f"Tool: {event.tool_name}")

asyncio.run(main())
```

### Core API — ClaudeSDKClient

Persistent conversations with session management:

```python
from claude_agent_sdk import ClaudeSDKClient

client = ClaudeSDKClient(options={
    "model": "claude-sonnet-4-5-20250929",
    "permission_mode": "acceptEdits",
})
# Optional: pass transport= for custom transport

# First query
async for event in client.query("Set up the project structure"):
    handle(event)

# Follow-up (same session context)
async for event in client.query("Now add tests"):
    handle(event)
```

### Custom Transport

Supply a custom `Transport` implementation to control how requests are sent:

```python
from claude_agent_sdk import Transport, ClaudeSDKClient, query

class MyTransport(Transport):
    async def send(self, request):
        # Custom routing, logging, proxying, etc.
        ...

client = ClaudeSDKClient(options={...}, transport=MyTransport())
# Also works with query():
async for event in query(prompt="...", options={...}, transport=MyTransport()):
    ...
```

### Session Management

```python
from claude_agent_sdk import list_sessions, get_session_messages

sessions = await list_sessions()
messages = await get_session_messages(session_id="sess_abc123")
```

### Key Options (ClaudeAgentOptions)

| Option | Type | Description |
|--------|------|-------------|
| `model` | string | Model to use (sonnet/opus/haiku or full ID) |
| `fallback_model` | string | Fallback if primary unavailable |
| `max_turns` | int | Max agentic turns before stopping |
| `max_budget_usd` | float | Spending limit per query |
| `permission_mode` | string | default/acceptEdits/plan/bypassPermissions |
| `allowed_tools` | list | Tools auto-approved without prompting (does NOT restrict to only these tools; unlisted tools fall through to `permission_mode`) |
| `disallowed_tools` | list | Tools blocked entirely |
| `setting_sources` | list | Additional settings file paths to load |
| `thinking` | ThinkingConfig | Extended thinking configuration |
| `hooks` | dict | Lifecycle hooks configuration |
| `agents` | dict | Programmatic subagent definitions |
| `plugins` | list | Plugin paths to load |
| `cwd` | string | Working directory |
| `system_prompt` | string | Override system prompt |
| `append_system_prompt` | string | Append to default system prompt |

### Authentication

```python
# Direct API (default)
options = {"api_key": "sk-ant-..."}

# AWS Bedrock
options = {"api_provider": "bedrock", "aws_region": "us-east-1"}

# Google Vertex AI
options = {"api_provider": "vertex", "gcp_project_id": "my-project"}

# Microsoft Foundry
options = {"api_provider": "msft-foundry", "foundry_host": "..."}
```

### Built-in Tools

Agent SDK provides: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch,
AskUserQuestion, Agent (subagent launcher, formerly Task), TodoWrite.

---

## Custom Tools

Create custom tools via the `@tool` decorator:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the internal database for matching records."""
    results = db.search(query, limit=limit)
    return json.dumps(results)

# Bundle tools into an MCP server
server = create_sdk_mcp_server([search_database])
```

Custom tools are exposed as MCP tools. The `@tool` decorator automatically
generates the input schema from type annotations and docstring.

### Tool Annotations

Use the `annotations` parameter on `@tool` for MCP tool annotations:

```python
@tool(annotations={
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": False,
})
def safe_query(query: str) -> str:
    """Run a read-only database query."""
    return db.read(query)
```

---

## Subagents

**Status:** GA | **Context:** Claude Code / Agent SDK

Isolated AI agents with their own context windows, tool access, and system
prompts. Launch via the Agent tool (formerly Task tool).

### Built-in Subagents

| Type | Purpose | Default Model |
|------|---------|---------------|
| Explore | Read-only codebase exploration | Haiku |
| Plan | Research and design planning | Current model |
| general-purpose | Flexible task execution | Current model |

### Custom Subagents

Define via Markdown files with YAML frontmatter:

```markdown
---
name: test-runner
description: Run tests and report results
tools:
  - Bash
  - Read
  - Glob
disallowedTools:
  - Write
  - Edit
model: haiku
permissionMode: acceptEdits
---

Run the test suite and report results. Focus on:
1. Which tests pass/fail
2. Error messages for failures
3. Suggested fixes
```

### Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier (lowercase letters and hyphens) |
| `description` | string | When to use this agent |
| `tools` | list | Allowlist of tools (inherits all if omitted) |
| `disallowedTools` | list | Blocklist of tools |
| `model` | string | Model override (haiku/sonnet/opus/full ID/inherit) |
| `permissionMode` | string | Permission level |
| `maxTurns` | int | Maximum agentic turns before stopping |
| `skills` | list | Skills to preload into context at startup |
| `mcpServers` | list | MCP servers scoped to this subagent (see below) |
| `hooks` | object | Agent-specific lifecycle hooks |
| `memory` | string | Persistent memory scope: `user`, `project`, or `local` |
| `background` | bool | Always run as a background task (default: false) |
| `isolation` | string | Set to `worktree` for isolated git worktree execution |

### Invoking Subagents

Three patterns for explicit invocation:

- **Natural language**: name the subagent in your prompt; Claude decides
  whether to delegate
- **@-mention**: type `@` and pick the subagent from the typeahead (guarantees
  that subagent runs). Manual format: `@agent-<name>` for local,
  `@agent-<plugin>:<name>` for plugin subagents
- **Session-wide via `--agent`**: `claude --agent code-reviewer` makes the
  subagent's system prompt, tools, and model active for the entire session.
  Set `"agent": "code-reviewer"` in `.claude/settings.json` to make it the
  default for a project

### MCP Server Scoping

Use `mcpServers` to give a subagent access to MCP servers unavailable in the
main conversation. Entries are either inline definitions or string references:

```yaml
mcpServers:
  # Inline: scoped to this subagent only
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  # Reference: reuses an already-configured server
  - github
```

Inline servers connect when the subagent starts and disconnect when it finishes.
To keep MCP tool descriptions out of the main context, define servers inline in
the subagent rather than in `.mcp.json`.

### Persistent Memory

The `memory` field gives subagents a directory that persists across sessions:

| Scope | Location | Use when |
|-------|----------|----------|
| `user` | `~/.claude/agent-memory/<name>/` | Learnings apply across all projects |
| `project` | `.claude/agent-memory/<name>/` | Knowledge is project-specific, shareable via VCS |
| `local` | `.claude/agent-memory-local/<name>/` | Project-specific but not committed |

When enabled, the subagent's prompt includes instructions for reading/writing
the memory directory. The first 200 lines of `MEMORY.md` are injected at
startup. Read, Write, and Edit tools are auto-enabled.

### Plugin Subagent Security

Plugin subagents do **not** support `hooks`, `mcpServers`, or `permissionMode`
fields — these are silently ignored when loading agents from a plugin. To use
these fields, copy the agent file into `.claude/agents/` or `~/.claude/agents/`.

### Agent Tool Parameters (v2.1.72+)

The Agent tool now supports a `model` parameter for per-invocation model
overrides (restored in v2.1.72). Also: `ExitWorktree` tool leaves an
`EnterWorktree` session, and `/plan` accepts an optional description argument
(e.g., `/plan fix the auth bug`). Team agents inherit the leader's model.

### Subagent Patterns

- **Isolate heavy operations**: push test runs, log analysis to subagents to
  keep main context clean
- **Chain subagents**: orchestrate multi-step workflows with specialised agents
- **Cost optimisation**: use Haiku for analysis tasks, Opus for complex reasoning
- **Restrict spawning**: use `Agent(worker, researcher)` in tools to limit
  which subagent types can be launched from `--agent` sessions

### Scope Hierarchy

CLI flag > project (.claude/agents/) > user (~/.claude/agents/) > plugin agents

---

## Hooks

**Status:** GA | **Context:** Claude Code / Agent SDK

Lifecycle automation at key events. Four hook types:

### Hook Types

| Type | Mechanism | Use Case |
|------|-----------|----------|
| `command` | Shell script execution | File validation, logging, notifications |
| `http` | POST event data to HTTP endpoint | Remote integrations, webhooks |
| `prompt` | LLM single-turn evaluation | Content review, policy checks |
| `agent` | Tool-enabled subagent verification | Complex validation requiring tool access |

### Hook Events

| Event | Trigger | Matcher |
|-------|---------|---------|
| `SessionStart` | Session begins | startup/resume/clear/compact |
| `InstructionsLoaded` | CLAUDE.md or rules file loaded | No matcher (always fires) |
| `UserPromptSubmit` | User sends message | No matcher (always fires) |
| `PreToolUse` | Before tool execution | Tool name regex |
| `PermissionRequest` | Permission dialog appears | Tool name regex |
| `PostToolUse` | After tool execution | Tool name regex |
| `PostToolUseFailure` | After tool execution fails | Tool name regex |
| `Notification` | Notification event | permission_prompt/idle_prompt/auth_success/elicitation_dialog |
| `SubagentStart` | Subagent spawned | Agent type name |
| `SubagentStop` | Subagent completes | Agent type name |
| `Stop` | Agent stops | No matcher (always fires) |
| `TeammateIdle` | Teammate becomes idle | No matcher (always fires) |
| `TaskCompleted` | Task finishes | No matcher (always fires) |
| `ConfigChange` | Settings/skills change | user_settings/project_settings/local_settings/policy_settings/skills |
| `WorktreeCreate` | Worktree created | No matcher (always fires) |
| `WorktreeRemove` | Worktree removed | No matcher (always fires) |
| `PreCompact` | Before context compaction | manual/auto |
| `PostCompact` | After context compaction | manual/auto |
| `Elicitation` | MCP server requests user input | — |
| `ElicitationResult` | User responds to MCP elicitation | — |
| `SessionEnd` | Session terminates | clear/logout/prompt_input_exit/bypass_permissions_disabled/other |

### Hook Handler Fields

**Command hooks**: `type`, `command`, `timeout` (default 600s), `async` (run
in background), `statusMessage`, `once` (skills only).

**HTTP hooks**: `type`, `url`, `timeout` (default 30s), `headers` (supports
`$VAR` interpolation via `allowedEnvVars`), `statusMessage`.

**Prompt hooks**: `type`, `prompt` (use `$ARGUMENTS` for hook input JSON),
`model`, `timeout` (default 30s).

**Agent hooks**: `type`, `prompt`, `model`, `timeout` (default 60s). Spawns a
subagent with tool access (Read, Grep, Glob) for verification.

### Hook Configuration

Hooks are configured in settings.json with a matcher (regex on tool name) and
one or more hook actions. They can also be defined in skill/agent YAML
frontmatter (scoped to that component's lifecycle).

Example use cases:
- **PreToolUse**: Validate file edits before they happen (lint, format check)
- **PostToolUse**: Log tool usage, notify on completions
- **Prompt hooks**: LLM-based content review and policy enforcement
- **Agent hooks**: Complex validation with file access before allowing actions
- **HTTP hooks**: Send events to external services (CI, monitoring)
- **SessionStart**: Inject dynamic context, set environment variables via `CLAUDE_ENV_FILE`
- **Stop/SubagentStop**: Prevent premature stopping with `decision: "block"`
- **WorktreeCreate**: Replace default git worktree with custom VCS (SVN, Perforce)
- **TaskCompleted**: Enforce quality gates before marking tasks done

Hooks receive JSON input (session_id, cwd, event, tool data) and return
exit code 0 (allow) or 2 (block) with optional feedback via stderr. JSON
output on stdout provides finer control (decision, hookSpecificOutput,
continue, additionalContext).

### Configuration Scopes

| Scope | File | Shared |
|-------|------|--------|
| User | `~/.claude/settings.json` | No |
| Project | `.claude/settings.json` | Yes (committed) |
| Local | `.claude/settings.local.json` | No (gitignored) |
| Managed | Managed policy settings | Yes (admin-controlled) |
| Plugin | hooks/hooks.json | Via plugin |
| Skill/Agent | YAML frontmatter `hooks:` field | Within component |

---

## Agent Skills

**Status:** Beta | **Headers:** `skills-2025-10-02` (code execution now GA, no header needed)

Extend Claude through code execution with document generation.

### Pre-built Anthropic Skills

| Skill | Type ID | Output |
|-------|---------|--------|
| PowerPoint | `pptx-20251013` | .pptx files |
| Excel | `xlsx-20251013` | .xlsx files |
| Word | `docx-20251013` | .docx files |
| PDF | `pdf-20251013` | .pdf files |

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16384,
    tools=[
        {"type": "code_execution_20260120", "name": "code_execution"},
        {"type": "pptx_20251013"}
    ],
    messages=[{"role": "user", "content": "Create a quarterly report deck"}],
    betas=["skills-2025-10-02", "files-api-2025-04-14"]
)
```

### Custom Skills

Upload custom skills (max 8MB) with YAML frontmatter via API. Skills are
versioned with epoch timestamps. Use `container` parameter for execution
context.

### Long-running Operations

Handle `pause_turn` stop reason with retry loop for skills that take time:

```python
while response.stop_reason == "pause_turn":
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16384,
        tools=[...],
        messages=[...previous + response...],
        betas=[...]
    )
```

### Claude Code Skills

Skills in Claude Code are Markdown files (SKILL.md) with YAML frontmatter.
They extend what Claude can do and are invoked via `/skill-name` or
automatically when Claude determines they're relevant.

#### Bundled Skills

| Skill | Purpose |
|-------|---------|
| `/batch <instruction>` | Large-scale parallel changes across codebase in worktrees |
| `/claude-api` | Load Claude API/SDK reference for your project language |
| `/debug [description]` | Troubleshoot session by reading debug log |
| `/loop [interval] <prompt>` | Run a prompt repeatedly on interval |
| `/simplify [focus]` | Review recent changes for quality and fix issues |

#### Key Frontmatter Fields

| Field | Description |
|-------|-------------|
| `name` | Display name (becomes `/slash-command`) |
| `description` | When to use — Claude uses this for auto-invocation |
| `disable-model-invocation` | `true` = manual only (no auto-invoke) |
| `user-invocable` | `false` = hidden from `/` menu (background knowledge) |
| `allowed-tools` | Tools permitted without approval when skill active |
| `model` | Model override when skill active |
| `context` | `fork` = run in isolated subagent context |
| `agent` | Subagent type for `context: fork` (Explore/Plan/custom) |
| `hooks` | Lifecycle hooks scoped to skill |
| `argument-hint` | Autocomplete hint for expected arguments |

#### Dynamic Context Injection

The `` !`command` `` syntax runs shell commands before skill content is sent
to Claude. Output replaces the placeholder (preprocessing, not Claude execution).

#### Skill Troubleshooting

- **Skill not triggering**: Check description includes natural keywords; verify
  via "What skills are available?"; try `/skill-name` directly
- **Skill triggers too often**: Make description more specific; add
  `disable-model-invocation: true`
- **Claude doesn't see all skills**: Descriptions are loaded into context at 2%
  of context window budget (fallback 16,000 chars). Run `/context` to check for
  excluded skills. Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var

---

## MCP Integration

### Claude Code MCP

Three transport types for MCP servers:

| Transport | Use Case | Command |
|-----------|----------|---------|
| HTTP | Remote servers (recommended) | `claude mcp add --transport http name url` |
| SSE | Legacy remote (deprecated) | `claude mcp add --transport sse name url` |
| stdio | Local processes | `claude mcp add name command args` |

### Authentication

OAuth 2.0 via `/mcp` command for browser-based auth flow.

### Configuration Scopes

| Scope | Flag | Description |
|-------|------|-------------|
| Local | (default) | Per-project, in `.mcp.json` |
| Project | `-s project` | Shared, committed to repo |
| User | `-s user` | All projects |

### Environment Variables

Support `${VAR}` and `${VAR:-default}` expansion in `.mcp.json`.

### Managed MCP

`managed-mcp.json` for system-wide deployment with exclusive control.
Supports allowlist/denylist rules by serverName, serverCommand, or serverUrl.

---

## Plugins

**Status:** GA | **Context:** Claude Code

Bundle skills, agents, hooks, MCP servers, commands, and LSP servers.

### Manifest Structure

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": {"name": "Author", "email": "email@example.com"}
}
```

Located at `.claude-plugin/plugin.json`.

### Component Locations

| Component | Directory | Discovery |
|-----------|-----------|-----------|
| Skills | `skills/` | Auto (SKILL.md) |
| Agents | `agents/` | Auto (.md files) |
| Hooks | `hooks/hooks.json` or inline | Configured |
| Settings | `settings.json` | Auto |
| MCP servers | `.mcp.json` or inline | Configured |
| LSP servers | `.lsp.json` | Configured |

Skills are invoked as `/plugin-name:skill-name` (e.g., `/my-plugin:deploy`).

### Special Variables

- `${CLAUDE_PLUGIN_ROOT}` — absolute path to plugin directory (use in hooks,
  MCP configs, scripts)
- `${CLAUDE_PLUGIN_DATA}` — persistent data directory (survives plugin updates)

### Plugin Settings

`settings.json` at plugin root applies defaults when enabled. The `agent` key
activates a plugin agent as the main thread.

### CLI Management

```bash
claude plugin install <path-or-url> [--scope user|project|local]
claude plugin uninstall <name>
claude plugin enable/disable <name>
claude plugin update <name>
```

### Marketplace

Official marketplace submission forms available for publishing plugins.

---

## MCP Apps

**Status:** Beta

Interactive HTML UIs rendered inside MCP hosts (Claude Desktop, Claude web).

### Architecture

- Tool declares `_meta.ui.resourceUri` pointing to UI resource
- Host fetches and renders HTML in sandboxed iframe
- Bidirectional JSON-RPC communication via postMessage API

### Key APIs

- `registerAppTool()` — register tool with UI metadata
- `registerAppResource()` — serve bundled HTML
- `App` class: `app.connect()`, `app.ontoolresult`, `app.callServerTool()`

### Security

Sandboxed iframe prevents DOM access, cookie theft, and parent navigation.
All host communication through postMessage API with host-controlled
capabilities.

### Supported Hosts

Claude, Claude Desktop, VS Code Insiders, Goose, Postman, MCPJam.
Framework-agnostic (React, Vue, Svelte templates available).

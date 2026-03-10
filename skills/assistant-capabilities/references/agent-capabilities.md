# Agent Capabilities Reference

Agent SDK, subagents, skills system, hooks, MCP integration, and plugin
architecture. Consult when building agents, configuring automation, or
integrating external services.

**Last updated:** 2026-03-09

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
| `name` | string | Agent identifier |
| `description` | string | When to use this agent |
| `tools` | list | Allowlist of tools |
| `disallowedTools` | list | Blocklist of tools |
| `model` | string | Model override (haiku/sonnet/opus) |
| `permissionMode` | string | Permission level |
| `skills` | list | Skills to load |
| `hooks` | object | Agent-specific hooks |
| `memory` | object | Persistent memory config (user/project/local) |

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
| `prompt` | LLM evaluation | Content review, policy checks |
| `agent` | Tool-enabled verification | Complex validation requiring tool access |

### Hook Events

| Event | Trigger | Matcher |
|-------|---------|---------|
| `SessionStart` | Session begins | startup/resume/compact |
| `PreToolUse` | Before tool execution | Tool name regex |
| `PostToolUse` | After tool execution | Tool name regex |
| `Stop` | Agent stops | — |
| `SubagentStop` | Subagent completes | Agent type name |
| `UserPromptSubmit` | User sends message | — |
| `PreCompact` | Before context compaction | — |
| `Notification` | Notification event | Notification type |
| `ConfigChange` | Settings/skills change externally | — |
| `TeammateIdle` | Teammate becomes idle | — |
| `TaskCompleted` | Task finishes | — |
| `WorktreeCreate` | Worktree created | — |
| `WorktreeRemove` | Worktree removed | — |

### Hook Configuration

Hooks are configured in settings.json with a matcher (regex on tool name) and
one or more hook actions. See Claude Code docs for full configuration reference.

Example use cases:
- **PreToolUse**: Validate file edits before they happen (lint, format check)
- **PostToolUse**: Log tool usage, notify on completions
- **Prompt hooks**: LLM-based content review and policy enforcement
- **HTTP hooks**: Send events to external services (CI, monitoring)

Hooks receive JSON input (session_id, cwd, event, tool data) and return
exit code 0 (allow) or 2 (block) with optional feedback via stderr.

### Configuration Scopes

| Scope | File | Shared |
|-------|------|--------|
| User | `~/.claude/settings.json` | No |
| Project | `.claude/settings.json` | Yes (committed) |
| Local | `.claude/settings.local.json` | No (gitignored) |
| Plugin | hooks.json / plugin.json | Via plugin |

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

Skills are invoked as `/plugin-name:skill-name` (e.g., `/my-plugin:deploy`).

### Special Variables

- `${CLAUDE_PLUGIN_ROOT}` — absolute path to plugin directory (use in hooks,
  MCP configs, scripts)

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

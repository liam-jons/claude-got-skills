# Agent Capabilities Reference

Agent SDK, custom tools, Agent Skills API, and MCP Apps. Consult when building
agents programmatically or integrating Agent Skills document generation.

**Last updated:** 2026-03-20

## Table of Contents

- [Agent SDK](#agent-sdk)
- [Custom Tools](#custom-tools)
- [Agent Skills](#agent-skills)
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

# List past sessions (sync)
sessions = list_sessions(directory="/path/to/project", limit=10)
# Returns SDKSessionInfo: session_id, summary, last_modified, git_branch, cwd

# Retrieve messages from a past session (sync)
messages = get_session_messages(session_id="sess_abc123", limit=50, offset=0)
# Returns SessionMessage: type ("user"/"assistant"), uuid, message
```

### ClaudeSDKClient Session Control Methods

| Method | Description |
|--------|-------------|
| `set_model(model)` | Change AI model during streaming conversation |
| `rewind_files(user_message_id)` | Rewind tracked files to checkpoint (requires `enable_file_checkpointing=True`) |
| `get_mcp_status()` | Query MCP server connection status (returns typed `McpStatusResponse`) |
| `reconnect_mcp_server(name)` | Reconnect a disconnected/failed MCP server |
| `toggle_mcp_server(name, enabled)` | Enable/disable MCP server at runtime |
| `stop_task(task_id)` | Stop a running background task |
| `get_server_info()` | Get server initialization info |
| `disconnect()` | Disconnect from Claude, clean up resources |

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
| `effort` | string | Thinking effort: "low"/"medium"/"high"/"max" |
| `thinking` | ThinkingConfig | Thinking mode: adaptive, enabled, or disabled |
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

Claude, Claude Desktop, VS Code GitHub Copilot, Goose, Postman, MCPJam.
Framework-agnostic (React, Vue, Svelte templates available).

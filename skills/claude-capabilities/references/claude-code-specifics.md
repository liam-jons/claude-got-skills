# Claude Code Specifics Reference

Claude Code-specific features: agent teams, Chrome browser integration, CLI
reference, IDE extensions, skills system, and plugin development. These capabilities
are distinct from API-level features and only apply in Claude Code contexts.

**Last updated:** 2026-03-07

## Table of Contents

- [Background Tasks & Scheduling](#background-tasks--scheduling)
- [Agent Teams](#agent-teams)
- [Chrome Browser Integration](#chrome-browser-integration)
- [CLI Reference](#cli-reference)
- [IDE Extensions](#ide-extensions)
- [Skills System](#skills-system)
- [Extension Architecture](#extension-architecture)
- [Tool Use Best Practices](#tool-use-best-practices)

---

## Background Tasks & Scheduling

**Status:** GA | **Since:** v2.0.x (background tasks), v2.1.71 (/loop, cron)

Run commands, agents, and prompts asynchronously or on recurring schedules.

### Background Commands

Run any bash command or agent in the background:

```python
# Bash tool with run_in_background parameter
{"command": "npm test", "run_in_background": true}
# Returns a task_id — use TaskOutput to retrieve results later
```

**Keyboard shortcuts:**
- `Ctrl+B` — background a running bash command or agent
- `Ctrl+F` — kill a background agent (two-press confirmation)
- `/tasks` — view and manage all background tasks

Background task output is truncated to 30K characters with a file path
reference to the full output. Task completion notifications are capped at
3 lines with overflow summary to avoid context bloat.

### /loop Command

Run a prompt or slash command on a recurring interval:

```
/loop 5m check the deploy status
/loop 10m /run-tests
/loop 30s check if the build finished
```

Default interval is 10 minutes if not specified. Useful for:
- Monitoring deployments or CI/CD pipelines
- Polling for changes or completion
- Recurring health checks during development
- Running periodic code quality checks

### Cron Scheduling Tools

Built-in tools for recurring prompts within a session:

| Tool | Purpose |
|------|---------|
| `CronCreate` | Schedule a recurring prompt with interval |
| `CronDelete` | Remove a scheduled recurring prompt |
| `CronList` | List all active scheduled prompts |

These are session-scoped — schedules don't persist across sessions.

### Background Agents

Agents can be configured to always run in the background:

```yaml
---
name: test-watcher
description: Runs tests and reports results
background: true
tools:
  - Bash
  - Read
---
```

The `background: true` field in agent frontmatter makes the agent
always launch as a background task.

### Environment Control

`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` — disable all background task
functionality (set in settings.json or environment).

---

## Agent Teams

**Status:** Experimental | **Enable:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

Coordinate multiple Claude Code instances working together. One session leads,
teammates work independently with their own context windows.

### When to Use

Best for parallel work where teammates need to communicate:

- Research and review (investigate different aspects simultaneously)
- New modules/features (each teammate owns a separate piece)
- Debugging with competing hypotheses (parallel theories)
- Cross-layer coordination (frontend, backend, tests — each owned by a teammate)

### Agent Teams vs Subagents

| Aspect | Subagents | Agent Teams |
|--------|-----------|-------------|
| Context | Own window; results return to caller | Own window; fully independent |
| Communication | Report back to main agent only | Teammates message each other directly |
| Coordination | Main agent manages all work | Shared task list with self-coordination |
| Best for | Focused tasks, result-only | Complex work requiring discussion |
| Token cost | Lower (results summarised) | Higher (each teammate is separate instance) |

Use subagents for quick focused workers. Use agent teams when teammates need to
share findings, challenge each other, and coordinate independently.

### Configuration

Enable in settings.json:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### Display Modes

- **In-process** (default): all teammates in main terminal. Shift+Up/Down to
  select and message teammates directly.
- **Split panes**: each teammate gets own pane (requires tmux or iTerm2).

Set via `teammateMode` in settings.json: `"auto"`, `"in-process"`, or `"tmux"`.

### Limitations

- Experimental — disabled by default
- Known issues with session resumption, task coordination, shutdown behaviour
- Significantly higher token usage than single sessions
- Not suitable for sequential tasks or same-file edits

---

## Chrome Browser Integration

**Status:** Beta | **Enable:** `claude --chrome` or `/chrome` in session

Connect Claude Code to Chrome for browser automation via the Claude in Chrome
browser extension.

### Prerequisites

- Google Chrome browser
- Claude in Chrome extension v1.0.36+
- Claude Code v2.0.73+
- Direct Anthropic plan (Pro, Max, Team, or Enterprise)
- NOT available via Bedrock, Vertex AI, or Foundry

### Capabilities

- **Live debugging**: read console errors and DOM state, fix code
- **Design verification**: build UI, open in browser to verify
- **Web app testing**: form validation, visual regression, user flows
- **Authenticated apps**: uses your browser login state (Google Docs, Gmail, etc.)
- **Data extraction**: pull structured data from web pages
- **Task automation**: form filling, data entry, multi-site workflows
- **Session recording**: record interactions as GIFs

### Usage

```bash
# Start with Chrome enabled
claude --chrome

# Enable by default (from within a session)
/chrome  # then select "Enabled by default"
```

### Key Behaviours

- Opens new tabs for browser tasks
- Shares your browser login state
- Actions run in visible Chrome window (real-time)
- Pauses on login pages or CAPTCHAs for manual handling
- Currently works with Google Chrome only (not Brave, Arc, etc.)
- WSL not supported

### Context Impact

Enabling Chrome by default increases context usage (browser tools always loaded).
Use `--chrome` flag per-session to avoid this if not always needed.

---

## CLI Reference

### Key Commands

| Command | Description |
|---------|-------------|
| `claude` | Start interactive REPL |
| `claude "query"` | Start with initial prompt |
| `claude -p "query"` | Print mode (non-interactive, exits after) |
| `cat file \| claude -p "query"` | Process piped content |
| `claude -c` | Continue most recent conversation |
| `claude -r "session" "query"` | Resume session by ID or name |
| `claude update` | Update to latest version |
| `claude mcp` | Configure MCP servers |

### Key Flags

| Flag | Description |
|------|-------------|
| `--model` | Set model (`sonnet`, `opus`, `haiku`, or full ID) |
| `--agents` | Define custom subagents via inline JSON |
| `--chrome` | Enable Chrome browser integration |
| `--tools` | Restrict available tools (`"Bash,Edit,Read"` or `""` for none) |
| `--json-schema` | Get validated JSON output matching schema (print mode) |
| `--remote` | Create web session on claude.ai |
| `--teleport` | Resume a web session locally |
| `--from-pr N` | Resume sessions linked to a GitHub PR |
| `--max-turns` | Limit agentic turns (print mode) |
| `--max-budget-usd` | Spending limit per query (print mode) |
| `--permission-mode` | Set permission mode (default/acceptEdits/plan/bypassPermissions) |
| `--mcp-config` | Load MCP servers from JSON files |
| `--plugin-dir` | Load plugins from directories |
| `--append-system-prompt` | Append text to default system prompt |
| `--system-prompt` | Replace entire system prompt |
| `--output-format` | Output format: text, json, stream-json (print mode) |
| `--fallback-model` | Fallback model when primary is overloaded |
| `--add-dir` | Add additional working directories |
| `--allowedTools` | Tools auto-approved without permission prompts |
| `--disallowedTools` | Tools blocked entirely |
| `--verbose` | Enable verbose logging |

### --agents Flag Format

Define inline subagents with JSON:

```bash
claude --agents '{
  "reviewer": {
    "description": "Reviews code for issues",
    "prompt": "You are a code reviewer. Focus on bugs and security.",
    "tools": ["Read", "Glob", "Grep"],
    "model": "haiku"
  }
}'
```

Subagent definition fields: `description` (required), `prompt` (required),
`tools`, `disallowedTools`, `model`, `skills`, `mcpServers`, `maxTurns`.

### Structured Output (Print Mode)

```bash
claude -p --json-schema '{"type":"object","properties":{"summary":{"type":"string"}}}' \
  "Summarise this project"
```

Returns validated JSON matching the provided schema after the agent completes.

---

## IDE Extensions

### VS Code Extension

Claude Code works as a VS Code extension with full access to the same tools, agent
loop, and capabilities as the CLI.

- Chrome browser automation supported directly from VS Code
- Terminal integration for bash commands
- File operations through VS Code's workspace

### JetBrains Plugin (Beta)

Available as a JetBrains plugin for IntelliJ, PyCharm, WebStorm, and other
JetBrains IDEs.

### Extension Parity

All Claude Code extension types (CLI, VS Code, JetBrains) share the same core:

- Same agentic loop and model access
- Same built-in tools (Bash, Read, Write, Edit, Glob, Grep, etc.)
- Same skill, hook, and plugin support
- Same MCP integration
- Same subagent and agent team support
- Settings shared across all surfaces (`~/.claude/settings.json`)

---

## Skills System

### Agent Skills Open Standard

Claude Code skills follow the Agent Skills open standard (agentskills.io), which
works across multiple AI tools. Claude Code extends the standard with:

- Invocation control (who triggers the skill: user or Claude)
- Subagent execution (run skills in isolated context)
- Dynamic context injection
- Directory-based supporting files

### Skill Structure

```
skill-name/
├── SKILL.md          # Required: frontmatter + instructions
├── references/       # Optional: additional reference files
└── assets/           # Optional: supporting data
```

### Frontmatter Fields

```yaml
---
name: my-skill
description: What this skill does and when to use it
version: 1.0.0
autoInvoke: true       # Claude can load automatically (default)
userInvoked: false     # Only user can invoke via /name
context: inherit       # inherit (default) or fork (isolated subagent)
---
```

### Invocation Control

| Setting | Behaviour |
|---------|-----------|
| Default (no flags) | Claude auto-loads when relevant; user can invoke with /name |
| `userInvoked: true` | Only user can invoke; Claude cannot auto-load |
| `autoInvoke: false` | Claude won't auto-load; user or explicit reference only |
| `context: fork` | Runs in isolated subagent context (own context window) |

### Skill Locations

| Location | Path | Scope |
|----------|------|-------|
| User | `~/.claude/skills/<name>/SKILL.md` | All projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where plugin installed |

### Legacy Commands

`.claude/commands/*.md` files still work — they create slash commands identical to
skills. Skills add frontmatter and directory support on top.

---

## Extension Architecture

Claude Code's extension system is layered:

```
Always-on context:
  └── CLAUDE.md — persistent context loaded every session
      (project conventions, coding rules, build commands)

On-demand capabilities:
  ├── Skills — reusable knowledge and workflows
  │   ├── Reference skills (knowledge Claude uses throughout session)
  │   └── Action skills (workflows invoked via /name)
  ├── Subagents — isolated workers that return summaries
  └── Agent teams — independent sessions with peer messaging

External connections:
  └── MCP — connect to external services and tools

Background automation:
  └── Hooks — deterministic scripts on lifecycle events

Packaging:
  └── Plugins — bundle skills, agents, hooks, MCP, commands
      └── Marketplaces — distribute plugins to community
```

### Feature Selection Guide

| Need | Use |
|------|-----|
| "Always do X" rules | CLAUDE.md |
| Reusable reference material | Skill (reference type) |
| Repeatable workflow | Skill (action type, /name) |
| Context isolation | Subagent or skill with `context: fork` |
| Parallel research/exploration | Agent team |
| External service access | MCP server |
| Automatic validation/logging | Hook |
| Share across projects | Plugin |

### Skills vs Subagents

- **Skills** provide content loaded into current or forked context
- **Subagents** are isolated workers that run and return summaries
- They combine: subagents can preload skills (`skills:` field)
- Use subagents when context window is filling up (work doesn't consume main context)

---

## Tool Use Best Practices

### Tool Definition Quality

Tool performance depends primarily on description quality. Best practices:

- Aim for 3-4 sentences minimum per tool description
- Explain: what it does, when to use (and when not), parameter meanings, caveats
- Descriptions matter more than examples

### Tool Use Examples (GA)

Provide `input_examples` on tool definitions for complex tools. No beta
header required (formerly `advanced-tool-use-2025-11-20`).

```python
tools = [{
    "name": "search_api",
    "description": "...",
    "input_schema": {...},
    "input_examples": [
        {"query": "user login errors", "limit": 10, "date_range": "7d"},
        {"query": "payment failures", "limit": 50}
    ]
}]
```

### Tool Choice Control

```python
# Let Claude decide (default)
tool_choice = "auto"

# Force Claude to use a tool (any tool)
tool_choice = {"type": "any"}

# Force specific tool
tool_choice = {"type": "tool", "name": "get_weather"}

# Disable tools for this turn
tool_choice = {"type": "none"}
```

### Tool Result Handling

- Maximum 100K tokens per tool result (truncated otherwise)
- Tool results support text and image content blocks
- For large results, summarise before returning to Claude
- Use `is_error: true` in tool result to indicate failure

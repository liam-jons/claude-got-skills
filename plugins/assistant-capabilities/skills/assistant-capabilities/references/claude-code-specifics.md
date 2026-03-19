# Claude Code Specifics Reference

Claude Code-specific features: code review, remote control, web sessions, Slack
integration, agent teams, browser integration, CLI reference, IDE extensions,
skills system, and plugin development. These capabilities are distinct from
API-level features and only apply in Claude Code contexts.

**Last updated:** 2026-03-18
**Covers through:** v2.1.78+

## Table of Contents

- [Code Review](#code-review)
- [Remote Control](#remote-control)
- [Claude Code on the Web](#claude-code-on-the-web)
- [Slack Integration](#slack-integration)
- [Background Tasks & Scheduling](#background-tasks--scheduling)
- [Agent Teams](#agent-teams)
- [Browser Integration](#browser-integration)
- [Claude Code Desktop App](#claude-code-desktop-app)
- [CLI Reference](#cli-reference)
- [IDE Extensions](#ide-extensions)
- [Skills System](#skills-system)
- [Extension Architecture](#extension-architecture)
- [Tool Use Best Practices](#tool-use-best-practices)

---

## Code Review

**Status:** Research preview | **Access:** Teams and Enterprise only (not available with ZDR)

Managed PR review service. A fleet of specialized agents analyze GitHub PRs in
context of the full codebase, looking for logic errors, security vulnerabilities,
broken edge cases, and regressions. Findings posted as inline comments.

### Key Details

- **Severity levels**: Normal (bug, fix before merge), Nit (minor), Pre-existing (not from this PR)
- **Triggers**: Once after PR creation, after every push, or manual (`@claude review`)
- **Manual trigger**: Comment `@claude review` as a top-level PR comment (not inline) to start a review and opt that PR into push-triggered reviews going forward. Works in any trigger mode. Requires owner/member/collaborator access; PR must be open and not draft.
- **Customization**: `CLAUDE.md` (shared rules — violations flagged as nits, bidirectional: outdated docs flagged too) + `REVIEW.md` (review-only guidance at repo root, auto-discovered)
- **Pricing**: Billed based on token usage, scaling with PR size and complexity. Billed separately through extra usage. Spend cap configurable at claude.ai/admin-settings/usage.
- **Setup**: claude.ai/admin-settings/claude-code → install Claude GitHub App → select repos → set review behavior per repo
- **Analytics**: claude.ai/analytics/code-review (PRs reviewed, weekly cost, auto-resolved feedback, per-repo breakdown)

For self-hosted reviews, use GitHub Actions or GitLab CI/CD instead.

---

## Remote Control

**Status:** GA | **Access:** Pro, Max, Team, Enterprise plans. Team/Enterprise admins must enable the toggle in admin settings first (off by default; depends on Claude Code on the web toggle).

Connect claude.ai/code or the Claude mobile app (iOS/Android) to a local Claude
Code session. Your local filesystem, MCP servers, tools, and project config stay
available — the web/mobile interface is just a window into the local session.

### Usage

**Server mode** (dedicated remote server):
```bash
claude remote-control              # Start server mode
claude remote-control --name "My Project"  # With custom title
```

**Interactive session with remote control**:
```bash
claude --remote-control            # Full interactive + remote access
claude --rc                        # Short alias
claude --rc "My Project"           # With name
```

From within a session: `/remote-control` (or `/rc`).

Press spacebar for QR code. Connect via session URL, QR scan, or find by name at
claude.ai/code. Use `/mobile` for app download QR code.

### Server Mode Flags

| Flag | Description |
|------|-------------|
| `--name "title"` | Custom session title visible at claude.ai/code |
| `--spawn <mode>` | How concurrent sessions are created. `same-dir` (default): shared working directory. `worktree`: each session gets its own git worktree. Press `w` at runtime to toggle. |
| `--capacity <N>` | Maximum concurrent sessions. Default 32. |
| `--verbose` | Detailed connection and session logs |
| `--sandbox` / `--no-sandbox` | Enable or disable filesystem/network sandboxing (off by default) |

### Key Details

- **Auto-enable**: `/config` → "Enable Remote Control for all sessions"
- **Security**: outbound HTTPS only, no inbound ports, all traffic via Anthropic API over TLS, multiple short-lived scoped credentials
- **One session per interactive process**. Use server mode with `--spawn` for multiple concurrent sessions from a single process.
- **Terminal must stay open** — closing the terminal or stopping the process ends the session
- **vs Claude Code on the Web**: Remote Control = your machine. Web = Anthropic cloud.

---

## Claude Code on the Web

**Status:** Research preview | **URL:** claude.ai/code
**Access:** Pro, Max, Team, Enterprise | **Also on:** Claude iOS and Android apps

Run Claude Code sessions on Anthropic-managed cloud infrastructure from a browser
or mobile app. No local setup needed.

### Key Commands

```bash
claude --remote "Fix the auth bug"     # Start web session from terminal
claude --remote "Fix test" &           # Run multiple in parallel
claude --teleport                       # Pull web session into terminal
/teleport                              # Same, from within Claude Code (or /tp)
/tasks                                 # Monitor + teleport (press t)
/remote-env                            # Select default cloud environment
```

### Features

- **Diff view**: review changes file by file before creating PR
- **Parallel execution**: each `--remote` creates independent session
- **Session sharing**: Team visibility (Enterprise/Teams) or Public (Max/Pro)
- **Session management**: archive sessions to declutter, delete permanently (from archived list or session menu)
- **Cloud environment**: Ubuntu 24.04, Python, Node.js, Ruby, Go, Rust, Java, C++, PHP 8.4, PostgreSQL 16, Redis 7
- **Setup scripts**: Bash scripts that run before Claude Code launches (configure in environment UI). Run only on new sessions, skipped on resume.
- **Network**: Limited (default, allowlisted domains), No internet, or Full access. All traffic passes through security proxy.

Session handoff is one-way: web → terminal only (via `/teleport`).

---

## Slack Integration

**Status:** GA | **Access:** Pro, Max, Teams, Enterprise with Claude Code access

Mention `@Claude` with a coding task in Slack → Claude creates a Claude Code web
session automatically. Built on the Claude for Slack app with intelligent routing.

### Setup

1. Install Claude app from Slack App Marketplace (admin)
2. Connect Claude account via App Home
3. Configure Claude Code on the web (connect GitHub)
4. Set routing mode: **Code only** or **Code + Chat** (includes "Retry as Code"/"Retry as Chat" buttons if routing is wrong)
5. Add to channels: `/invite @Claude`

### How It Works

- Detects coding intent from @mentions in channels (not DMs)
- **Channels only**: works in public and private channels, does NOT work in DMs
- Creates session on claude.ai/code, posts progress updates to Slack thread
- Completion: summary + "View Session" / "Create PR" / "Change Repo" buttons
- Gathers context from thread messages and recent channel messages

### Key Details

- Per-user: sessions run under individual accounts, against individual rate limits
- Channel-based access control (invite required)
- GitHub only, one PR per session
- Web access required: users without Claude Code on the web access get standard chat responses only

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
- `Ctrl+F` — kill all background agents (two-press confirmation within 3 seconds)
- `/tasks` — view and manage all background tasks
- `Ctrl+T` — toggle task list in terminal status area

Background task output is truncated to 30K characters with a file path
reference to the full output. Task completion notifications are capped at
3 lines with overflow summary to avoid context bloat. Tasks auto-terminated
if output exceeds 5GB.

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

### /btw — Side Questions

Ask a side question without interrupting current work:

```
/btw what does this error code mean?
/btw how do I format a date in Python?
```

Forks the current conversation context into a single-turn query with **no tools and
no file access**. The response appears in a dismissible overlay that never enters
conversation history. Reuses the parent conversation's prompt cache for minimal cost.
Available even while Claude is processing a response.

**Key distinction:** `/btw` is the inverse of a subagent — it sees full context but
has no tools, while a subagent has tools but starts with empty context.

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
always launch as a background task. MCP tools are now allowed in
background subagents (previously restricted).

### Environment Control

`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` — disable all background task
functionality (set in settings.json or environment).
`CLAUDE_CODE_DISABLE_CRON` — stop scheduled cron jobs mid-session (v2.1.72).

---

## Agent Teams

**Status:** Experimental | **Enable:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

Coordinate multiple Claude Code instances working together. 3-5 teammates
recommended. Each works independently with their own context windows.

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

- **In-process** (default): all teammates in main terminal. Shift+Down to
  select and message teammates directly.
- **Split panes**: each teammate gets own pane (requires tmux or iTerm2).

Set via `teammateMode` in settings.json: `"auto"`, `"in-process"`, or `"tmux"`.

### Limitations

- Experimental — disabled by default
- Known issues with session resumption, task coordination, shutdown behaviour
- Significantly higher token usage than single sessions
- Not suitable for sequential tasks or same-file edits

---

## Browser Integration

**Status:** Beta | **Enable:** `claude --chrome` or `/chrome` in session

Connect Claude Code to a browser for automation via the Claude in Chrome
browser extension.

### Prerequisites

- Google Chrome or Microsoft Edge browser
- Claude in Chrome extension v1.0.36+
- Claude Code v2.0.73+
- Direct Anthropic plan (Pro, Max, Team, or Enterprise)
- NOT available via Bedrock, Vertex AI, or Foundry

### Capabilities

- **Live debugging**: read console errors and DOM state, fix code
- **Design verification**: build UI, open in browser to verify
- **Web app testing**: form validation, visual regression, user flows
- **Authenticated apps**: works with your existing browser sessions
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
- Uses your existing browser profile
- Actions run in visible Chrome window (real-time)
- Pauses on login pages or CAPTCHAs for manual handling
- Works with Google Chrome and Microsoft Edge (not Brave, Arc, etc.)
- WSL not supported

### Context Impact

Enabling Chrome by default increases context usage (browser tools always loaded).
Use `--chrome` flag per-session to avoid this if not always needed.

---

## Claude Code Desktop App

**Status:** GA | **Platforms:** macOS, Windows (no Linux)

Standalone desktop application providing Claude Code with a graphical interface.
Three tabs: **Chat** (no file access), **Cowork** (autonomous cloud agent), and
**Code** (interactive local coding).

### Desktop-Specific Features

- **Visual diff review** with inline comments: click lines in diff to comment, submit all with Cmd/Ctrl+Enter. Claude reads comments and revises.
- **Review code**: click "Review code" in diff toolbar — Claude evaluates diffs and leaves inline suggestions (high-signal only: compile errors, logic errors, security, obvious bugs)
- **Live app preview**: embedded browser for dev server verification, auto-verify changes after every edit (configurable via `.claude/launch.json`)
- **GitHub PR monitoring**: CI status bar with auto-fix (reads failures, iterates) and auto-merge (squash, requires GitHub repo setting)
- **Parallel sessions**: each session gets isolated Git worktree automatically
- **Scheduled tasks**: recurring sessions at configured times (daily reviews, dependency audits, morning briefings). Requires app open and computer awake.
- **Connectors**: GUI setup for MCP integrations (GitHub, Slack, Linear, Notion, Google Calendar, etc.)
- **Session environments**: Local, Remote (cloud), or SSH
- **Continue in another surface**: move session to web or IDE via "Continue in" menu

### CoWork & Dispatch

**CoWork** is the autonomous background agent tab in the Desktop app. It runs on
a cloud VM with access to connectors, plugins, and professional output formats
(Excel with formulas, PowerPoint, formatted docs). Available on all paid plans
(Pro, Max, Team, Enterprise).

**Dispatch** (Pro/Max only) gives a single persistent conversation thread
accessible from both the Desktop app and the Claude mobile app (iOS/Android).
Message Claude from the phone, and Claude works on the desktop using local files,
connectors, and plugins — then messages the result when done.

Key Dispatch details:
- **Persistent thread**: context carries across tasks (no reset between messages)
- **Cross-device**: start from phone, follow up from desktop (same conversation)
- **Requirements**: Desktop app running + computer awake, Claude mobile app, Pro/Max plan
- **Limitations**: one continuous thread (no multiple threads), no proactive notifications from Claude, desktop must be active
- **Scheduled tasks are separate**: they do not run in the Dispatch thread

### Extension Parity

Shares the same core as CLI, VS Code, and JetBrains — same agentic loop, tools,
skills, hooks, plugins, MCP, settings. Desktop adds visual diff, preview, PR
monitoring, scheduled tasks, connectors, and Dispatch on top.

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
| `claude agents` | List all configured subagents |
| `claude auth login` | Log in (supports `--email`, `--sso`) |
| `claude auth logout` | Log out |
| `claude auth status` | Show authentication status |
| `claude remote-control` | Start remote control server mode |
| `claude --remote-control` / `--rc` | Interactive session with remote access |
| `claude --remote "task"` | Start web session from terminal |
| `claude --teleport` | Pull web session into terminal |

### Key Flags

| Flag | Description |
|------|-------------|
| `--model` | Set model (`sonnet`, `opus`, `haiku`, or full ID) |
| `--agents` | Define custom subagents via inline JSON |
| `--chrome` | Enable Chrome browser integration |
| `--tools` | Restrict available tools (`"Bash,Edit,Read"` or `""` for none) |
| `--json-schema` | Get validated JSON output matching schema (print mode) |
| `--remote` | Create web session on claude.ai |
| `--remote-control` / `--rc` | Interactive session with remote control |
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
| `--worktree` / `-w` | Run in isolated git worktree |
| `--add-dir` | Add additional working directories |
| `--allowedTools` | Tools auto-approved without permission prompts |
| `--disallowedTools` | Tools blocked entirely |
| `--spawn <mode>` | Concurrent session mode for remote-control server (same-dir/worktree) |
| `--capacity <N>` | Max concurrent sessions for remote-control server |
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
`tools`, `disallowedTools`, `model`, `skills`, `mcpServers`, `maxTurns`,
`background` (always background), `isolation` (`worktree` for isolated git worktree).

Use `Agent(worker, researcher)` allowlist syntax with `--agent` mode to restrict
which subagents can be spawned.

**Tool rename:** `Task` tool renamed to `Agent` (e.g., `Agent(agent_type)`,
`Agent(Explore)`). Legacy `Task(...)` syntax still works as an alias (since v2.1.63).
`SubagentStop` supports matchers by agent type name.

### Interactive Mode Highlights

- **Prompt suggestions**: context-aware suggestions after each response (Tab to accept, Enter to accept+submit). Based on git history and conversation. Disable with `CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION=false`.
- **Bash mode**: prefix input with `!` to run shell commands directly without Claude interpreting them. Supports Tab autocomplete from `!` history.
- **Task list**: `Ctrl+T` toggles task progress display (up to 10 tasks). Persists across compactions. Share across sessions with `CLAUDE_CODE_TASK_LIST_ID`.
- **PR review status**: footer shows clickable PR link with colored underline (green=approved, yellow=pending, red=changes requested, gray=draft, purple=merged). Updates every 60s. Requires `gh` CLI.
- **Voice input**: hold Space for push-to-talk dictation (requires Claude.ai account)
- **Vim mode**: `/vim` to toggle, `/config` to set permanently
- **Reverse search**: `Ctrl+R` for interactive history search
- **Rewind**: `Esc`+`Esc` to restore code/conversation to a previous point or summarize from a message
- **Model switching**: `Alt+P`/`Option+P` to switch models without clearing prompt
- **Effort level**: `/effort` command (low/medium/high/max/auto). `max` requires Opus 4.6, current session only.

### Built-In Commands (Selection)

| Command | Purpose |
|---------|---------|
| `/compact [instructions]` | Compact conversation with optional focus |
| `/context` | Visualize context usage as colored grid |
| `/copy [N]` | Copy assistant response to clipboard (interactive block picker) |
| `/desktop` / `/app` | Continue session in Desktop app |
| `/diff` | Interactive diff viewer (uncommitted + per-turn diffs) |
| `/effort` | Set model effort level |
| `/export [filename]` | Export conversation as plain text |
| `/insights` | Analyze session patterns and friction points |
| `/memory` | Edit CLAUDE.md files, toggle auto-memory |
| `/plan` | Enter plan mode from prompt |
| `/pr-comments [PR]` | Fetch GitHub PR comments |
| `/rewind` / `/checkpoint` | Rewind conversation/code to previous point |
| `/security-review` | Analyze branch changes for security vulnerabilities |
| `/stats` | Daily usage, session history, streaks |
| `/voice` | Toggle push-to-talk dictation |

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
loop, and capabilities as the CLI. Chrome browser automation supported directly
from VS Code. Terminal integration for bash commands. File operations through
VS Code's workspace.

### JetBrains Plugin

Available as a JetBrains plugin for IntelliJ IDEA, PyCharm, WebStorm, GoLand,
and other JetBrains IDEs. Full feature parity with CLI and VS Code extension.

### Extension Parity

All Claude Code surfaces (CLI, VS Code, JetBrains, Desktop app) share the same core:

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

### Bundled Skills

5 bundled skills ship with Claude Code (prompt-based, unlike built-in commands which execute fixed logic):

| Skill | Purpose |
|-------|---------|
| `/simplify` | Simplify code or explanations |
| `/batch` | Run operations across multiple files |
| `/debug` | Debug issues systematically |
| `/loop` | Run recurring prompts on an interval |
| `/claude-api` | Help with Anthropic API usage |

`/btw` is a **built-in command** (not a bundled skill): forks context into a single-turn
side question with no tools, no history. Dismissible overlay. Available even while
Claude is processing.

### Environment

`CLAUDE_SKILL_DIR` — override default skill directory location.

### Legacy Commands

`.claude/commands/*.md` files still work — they create slash commands identical to
skills. Skills add frontmatter and directory support on top.

---

## Extension Architecture

Claude Code's extension system is layered:

```
Always-on context:
  └── CLAUDE.md — persistent context loaded every session (~200 lines max)
      (project conventions, coding rules, build commands)
      └── .claude/rules/ — path-specific scoping for CLAUDE.md rules

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
      ├── Shell hooks (default)
      └── HTTP hooks (type: "http") — POST event data to HTTP endpoints

Packaging:
  └── Plugins — bundle skills, agents, hooks, MCP, settings
      ├── skills/ directory (renamed from commands/)
      ├── settings.json for default plugin configuration
      ├── Invoke via /plugin-name:skill-name
      └── Official marketplace submission forms
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

### Hook Events

| Event | Fires when |
|-------|------------|
| `PreToolUse` | Before a tool executes |
| `PostToolUse` | After a tool executes |
| `Notification` | Claude sends a notification |
| `Stop` | Claude finishes responding |
| `ConfigChange` | Settings or skills change externally |
| `SessionStart` | A new session begins (runs in both local and cloud) |
| `TeammateIdle` | A teammate becomes idle |
| `TaskCompleted` | A background task finishes |
| `WorktreeCreate` | A git worktree is created |
| `WorktreeRemove` | A git worktree is removed |

Hooks can be shell scripts (default) or HTTP endpoints (`type: "http"`).

### MCP Integration Notes

- `--callback-port` flag for fixed OAuth callback ports
- `authServerMetadataUrl` override for non-standard OAuth servers
- Claude.ai MCP servers are auto-available when logged in with a Claude.ai
  account. Disable with `ENABLE_CLAUDEAI_MCP_SERVERS=false`.

### Sandbox Settings

Control filesystem access for sandboxed tools:

| Setting | Purpose |
|---------|---------|
| `sandbox.filesystem.allowWrite` | Paths where writes are allowed |
| `sandbox.filesystem.denyWrite` | Paths where writes are blocked |
| `sandbox.filesystem.denyRead` | Paths where reads are blocked |

Path prefix resolution:
- `//` — absolute path
- `~/` — relative to home directory
- `/` — relative to settings file location
- `./` — relative to runtime working directory

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

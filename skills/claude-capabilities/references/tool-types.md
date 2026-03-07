# Built-in Tool Types Reference

All built-in tool types with configuration, parameters, and usage patterns.
Consult when configuring tools, understanding tool-specific limitations, or
choosing the right tool for a task.

**Last updated:** 2026-02-10

## Table of Contents

- [Computer Use](#computer-use)
- [Code Execution](#code-execution)
- [Programmatic Tool Calling](#programmatic-tool-calling)
- [Web Search](#web-search)
- [Web Fetch](#web-fetch)
- [Tool Search](#tool-search)
- [MCP Connector](#mcp-connector)
- [Memory Tool](#memory-tool)
- [Bash Tool](#bash-tool)
- [Text Editor](#text-editor)
- [Tool Use Examples](#tool-use-examples-beta)
- [Tool Runner](#tool-runner)
- [Tool Compatibility Matrix](#tool-compatibility-matrix)

---

## Computer Use

**Status:** Beta | **Header:** Model-dependent (see below)

Desktop automation via screenshots, mouse, and keyboard control.

### Tool Versions

| Tool Type | Models | Features |
|-----------|--------|----------|
| `computer_20251124` | Opus 4.6, Opus 4.5 | All actions + zoom |
| `computer_20250124` | Sonnet 4.5, Haiku 4.5, Opus 4.1, Sonnet 4, Opus 4, Sonnet 3.7 | Enhanced actions |

### Beta Headers

- Opus 4.6, Opus 4.5: `computer-use-2025-11-24`
- All others: `computer-use-2025-01-24`

### Configuration

```python
{
    "type": "computer_20251124",
    "name": "computer",
    "display_width_px": 1024,
    "display_height_px": 768,
    "display_number": 1,
    "enable_zoom": True  # Opus 4.5/4.6 only
}
```

### Available Actions

| Action | Description | Version |
|--------|-------------|---------|
| `screenshot` | Capture screen | All |
| `left_click` | Click at coordinates | All |
| `right_click` | Right-click | Enhanced+ |
| `double_click` | Double-click | Enhanced+ |
| `type` | Type text string | All |
| `key` | Press key combo | All |
| `mouse_move` | Move cursor | All |
| `scroll` | Scroll at coordinates | Enhanced+ |
| `left_click_drag` | Click and drag | Enhanced+ |
| `hold_key` | Hold modifier key | Enhanced+ |
| `wait` | Pause execution | Enhanced+ |
| `zoom` | Zoom into region `[x1,y1,x2,y2]` | Opus 4.5/4.6 |

### Modifier Keys

Pass modifier as `text` field with click/scroll actions:
```json
{"action": "left_click", "coordinate": [500, 300], "text": "shift"}
{"action": "scroll", "coordinate": [500, 400], "text": "ctrl"}
```

### Coordinate Scaling

Screenshots are scaled before sending to the model. Calculate scale factor:
```python
def get_scale_factor(width, height):
    long_edge = 1568 / max(width, height)
    total_pixels = math.sqrt(1_150_000 / (width * height))
    return min(1.0, long_edge, total_pixels)
```

### Token Costs

- System prompt overhead: 466-499 tokens
- Tool definition: ~735 tokens
- Plus screenshot images and tool results

### Security Requirements

- Run in isolated VM/container with minimal privileges
- Limit internet access via allowlist
- Implement human confirmation for sensitive actions
- Automatic prompt injection classifiers available

---

## Code Execution

**Status:** GA | **Header:** None required (formerly `code-execution-2025-08-25`)

Sandboxed Python environment for computation, data analysis, and file
generation.

```python
tools = [{"type": "code_execution_20250825", "name": "code_execution"}]
```

### Container Environment

- Python with common libraries (pandas, numpy, matplotlib, etc.)
- Isolated filesystem with input/output directories
- Network access restricted
- Execution timeout limits apply

### File Handling

Files uploaded via Files API are accessible in the container. Output files
can be downloaded via Files API using file_ids from the response.

### Integration with Skills

Code execution is the foundation for Agent Skills (pptx, xlsx, docx, pdf).
Enable both code execution and skills headers for document generation.

---

## Programmatic Tool Calling

**Status:** GA | **Header:** None required (formerly `advanced-tool-use-2025-11-20`)
**Models:** Opus 4.6, Sonnet 4.6, Sonnet 4.5, Opus 4.5

Claude writes Python code that calls tools programmatically within the code
execution container, without model round-trips.

### Configuration

Add `allowed_callers` to tool definitions:

```python
tools = [
    {
        "name": "search_database",
        "description": "Search the database",
        "input_schema": {"type": "object", "properties": {...}},
        "allowed_callers": ["direct", "code_execution_20250825"]
    },
    {"type": "code_execution_20250825", "name": "code_execution"}
]
```

- `"direct"` — normal model-driven tool calls
- `"code_execution_20250825"` — callable from code execution container

### Key Behaviour

- Tool results from programmatic calls are NOT added to Claude's context
  (token efficiency)
- Response includes `caller` field showing invocation type
- Claude can batch-process, loop, filter, and conditionally call tools in code

### Incompatibilities

- Cannot use with `strict: true` (structured outputs via tool schemas)
- Incompatible with web search, web fetch, MCP connector tools
- Tool results from programmatic calls only support `tool_result` format

---

## Web Search

**Status:** GA | **Models:** All current | **Header:** None

Real-time web search integrated as a built-in tool.

```python
tools = [{"type": "web_search_20250305", "name": "web_search"}]
```

### Configuration Options

- `max_uses` — limit search calls per request
- `allowed_domains` — restrict to specific domains
- `blocked_domains` — exclude specific domains
- `user_location` — geographic context for results

### Pricing

- Search requests: $10 per 1,000 searches
- Result token costs: standard input pricing

---

## Web Fetch

**Status:** GA | **Header:** None required

Fetch and read content from URLs. Supports dynamic filtering with code execution.

```python
tools = [{"type": "web_fetch_20250305", "name": "web_fetch"}]
```

Retrieve web page content, API responses, or file downloads. Content returned
as text for Claude to process.

---

## Tool Search

**Status:** GA | **Models:** Sonnet 4+, Opus 4+

Dynamic tool discovery via regex search. Scales to thousands of tools without
loading all definitions into context.

### Auto-activation

Activates automatically when MCP tools exceed 10% of available context.
Configurable via environment variable:
`ENABLE_TOOL_SEARCH=auto|auto:5|true|false`

### Usage

Claude searches for relevant tools by name/description pattern, then loads
matching tool definitions on demand. Essential for large MCP server deployments.

---

## MCP Connector

**Status:** Beta | **Header:** `mcp-client-2025-11-20`

Connect to remote MCP servers directly from the Messages API without a
separate MCP client.

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    mcp_servers=[
        {
            "type": "url",
            "url": "https://mcp.example.com/sse",
            "name": "my_server",
            "authorization_token": "token_here"
        }
    ],
    tools=[
        {"type": "mcp_toolset", "server_name": "my_server"}
    ],
    messages=[{"role": "user", "content": "..."}],
    betas=["mcp-client-2025-11-20"]
)
```

### Tool Configuration Patterns

**Enable all tools:**
```python
{"type": "mcp_toolset", "server_name": "my_server"}
```

**Allowlist (enable specific):**
```python
{
    "type": "mcp_toolset",
    "server_name": "my_server",
    "default_config": {"enabled": False},
    "tool_config": {
        "search": {"enabled": True},
        "query": {"enabled": True}
    }
}
```

**Denylist (disable specific):**
```python
{
    "type": "mcp_toolset",
    "server_name": "my_server",
    "tool_config": {
        "dangerous_tool": {"enabled": False}
    }
}
```

### Deferred Loading

`defer_loading: true` — tool definitions loaded only when Claude decides to
use them. Reduces initial context usage for large toolsets.

### Previous Header (Deprecated)

`mcp-client-2025-04-04` — replaced by `mcp-client-2025-11-20`.

---

## Memory Tool

**Status:** GA | **Header:** None required (formerly `context-management-2025-06-27`)

See `references/api-features.md` for full memory tool documentation including
commands and security requirements.

```python
tools = [{"type": "memory_20250818", "name": "memory"}]
```

---

## Bash Tool

**Status:** GA | **Context:** Claude Code / Agent SDK

Shell command execution with sandboxing support. Available in Claude Code and
Agent SDK contexts.

**Sandboxing:** OS-level isolation (Seatbelt on macOS, bubblewrap on Linux).
Filesystem read/write restricted to working directory. Network access filtered
by domain allowlist via proxy.

**Configuration:** `dangerouslyDisableSandbox` parameter available for
incompatible commands (requires explicit permission).

---

## Text Editor

**Status:** GA | **Context:** Claude Code / Agent SDK

File viewing and editing with line-level precision. Supports:
- View file contents with line numbers
- Insert text at specific lines
- Replace text ranges
- Create new files

Available as a built-in tool in Claude Code and Agent SDK contexts.

---

## Tool Use Examples (GA)

No header required (formerly `advanced-tool-use-2025-11-20`).

Provide examples of expected tool inputs to improve tool call quality:

```python
tools = [{
    "name": "get_weather",
    "description": "Get weather for a location",
    "input_schema": {...},
    "input_examples": [
        {"location": "San Francisco, CA", "unit": "fahrenheit"},
        {"location": "Tokyo, Japan", "unit": "celsius"}
    ]
}]
```

---

## Tool Runner

**Status:** GA (SDK feature) | **Context:** Python, TypeScript, Ruby SDKs

Simplify multi-turn tool execution loops:

```python
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather, calculate],
    messages=[{"role": "user", "content": "..."}]
)
for message in runner:
    print(message.content[0].text)
```

Automatically handles tool result submission and continuation. Available in
Python, TypeScript, and Ruby SDKs.

---

## Tool Compatibility Matrix

| Tool | Structured Outputs | Citations | Prefill | Programmatic Calling |
|------|-------------------|-----------|---------|---------------------|
| Computer use | No | No | No | No |
| Code execution | No | No | No | Base for it |
| Web search | Yes | Yes | No | No |
| Web fetch | Yes | No | No | No |
| MCP connector | Yes | No | No | No |
| Memory | Yes | No | No | No |
| Custom tools | Yes (strict) | Yes | No | Yes (with allowed_callers) |

**General incompatibilities:**
- Prefilling (assistant message prefill) removed on Opus 4.6
- Structured outputs (`strict: true`) incompatible with programmatic tool calling
- Citations incompatible with structured outputs (JSON schema format)

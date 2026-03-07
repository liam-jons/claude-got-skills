# API Features Reference

Detailed API feature documentation with code examples, beta headers, and
platform availability. Consult when implementing API calls or configuring
features.

**Last updated:** 2026-02-10

## Table of Contents

- [Adaptive Thinking](#adaptive-thinking)
- [Extended Thinking](#extended-thinking)
- [Effort Parameter](#effort-parameter)
- [1M Context Window](#1m-context-window)
- [Compaction API](#compaction-api)
- [Context Editing](#context-editing)
- [Structured Outputs](#structured-outputs)
- [Files API](#files-api)
- [Memory Tool](#memory-tool)
- [Citations and Search Results](#citations-and-search-results)
- [Prompt Caching](#prompt-caching)
- [Data Residency](#data-residency)
- [Batch Processing](#batch-processing)
- [Token Counting](#token-counting)

---

## Adaptive Thinking

**Status:** GA | **Models:** Opus 4.6 only | **Header:** None

Claude dynamically decides when and how deeply to think. Replaces manual
`budget_tokens` configuration.

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=[{"role": "user", "content": "Solve this complex problem..."}]
)
```

Automatically enables interleaved thinking (thinking blocks between tool
calls). The deprecated `interleaved-thinking-2025-05-14` header is no longer
needed.

**Migration from budget_tokens:** Replace `thinking: {type: "enabled",
budget_tokens: N}` with `thinking: {type: "adaptive"}` and set the `effort`
parameter for coarse control. `budget_tokens` still works on Sonnet 4.5 and
Opus 4.5 but is deprecated on Opus 4.6.

---

## Extended Thinking

**Status:** GA | **Models:** Opus 4.6, Sonnet 4.5, Opus 4.5 | **Header:** None

Multi-stage reasoning with explicit thinking blocks. Haiku 4.5 does not
support extended thinking.

```python
# Sonnet 4.5 / Opus 4.5 — still use budget_tokens
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "..."}]
)
```

**Interleaved thinking** (Sonnet 4.5): thinking blocks appear between tool
calls for better multi-step reasoning. On Sonnet 4.5, enable via:
`thinking: {type: "enabled", budget_tokens: N}` — interleaving is automatic.

**Context management:** thinking blocks are automatically stripped from context
(not carried forward between turns). Effective context:
`context_window = (input_tokens - previous_thinking_tokens) + current_turn_tokens`.
Thinking tokens billed once. During tool use, preserve thinking blocks in the
tool result turn.

---

## Effort Parameter

**Status:** GA | **Models:** All current | **Header:** None

Control thoroughness vs token usage without configuring thinking directly.

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    effort="high",
    messages=[{"role": "user", "content": "..."}]
)
```

| Level | Behaviour | Opus 4.6 |
|-------|-----------|----------|
| low | Minimal thinking, fast responses | Yes |
| medium | Balanced (default) | Yes |
| high | Thorough reasoning | Yes |
| max | Maximum capability | Opus 4.6 only |

Combine with `thinking: {type: "adaptive"}` on Opus 4.6 for fine-grained
control. On other models, `effort` works independently.

---

## 1M Context Window

**Status:** Beta | **Models:** All current | **Header:** `context-1m-2025-08-07`
**Requirement:** Usage tier 3+ (previously tier 4+)

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
    betas=["context-1m-2025-08-07"]
)
```

**Pricing:** Tokens beyond 200K are premium — 2x input price, 1.5x output
price. Tokens within the 200K window are standard price.

**Platform availability:** Claude API (direct). Check Bedrock/Vertex for
current support.

---

## Compaction API

**Status:** Beta | **Models:** All current | **Header:** Required (beta)

Server-side context summarisation for infinite conversations. Triggers
automatically when context approaches the limit. Preserves essential
information while reducing token count.

Combine with context editing and memory tool for comprehensive context
management strategies.

---

## Context Editing

**Status:** Beta | **Models:** All current

Automatic context management with configurable strategies:

- Clear tool results after processing
- Manage thinking blocks across turns
- Custom clearing strategies

Useful for long-running agent sessions that accumulate tool results. Works
with memory tool to preserve critical information before clearing.

---

## Structured Outputs

**Status:** GA | **Models:** Sonnet 4.5, Opus 4.5, Haiku 4.5 | **Header:** None
**Note:** Beta on Bedrock and Foundry

Two complementary approaches:

### JSON Outputs (response format control)

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Extract structured data..."}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"]
            }
        }
    }
)
```

**Note:** Parameter is `output_config.format` (the old `output_format` top-level
parameter is deprecated).

### Strict Tool Use (parameter validation)

```python
tools = [{
    "name": "extract_info",
    "description": "Extract structured information",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "items": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["name", "items"]
    }
}]
```

### SDK Helpers

- Python: `client.messages.parse()`, `transform_schema()`
- TypeScript: `zodOutputFormat()` for Zod schema integration

### Schema Limitations

Supported: objects, arrays, enums, `$ref`, string formats.
Unsupported: recursion, numerical constraints (min/max), regex backreferences.
Grammar caching: 24-hour cache, invalidated on schema changes.

### Incompatibilities

- Cannot combine structured outputs with citations
- Cannot combine with message prefilling
- Cannot combine with programmatic tool calling (`strict: true`)

---

## Files API

**Status:** Beta | **Header:** `files-api-2025-04-14`
**Models:** All models supporting given file types

```python
# Upload a file
file = client.beta.files.upload(
    file=("document.pdf", open("doc.pdf", "rb"), "application/pdf")
)

# Use in a message
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Summarise this document"},
            {"type": "document", "source": {"type": "file", "file_id": file.id}}
        ]
    }],
    betas=["files-api-2025-04-14"]
)

# List files
files = client.beta.files.list()

# Delete
client.beta.files.delete(file.id)

# Download (skills/code execution output only)
content = client.beta.files.download(file.id)
```

**Supported types:** PDFs, plain text, images (JPEG/PNG/GIF/WebP), datasets.
**Limits:** 500 MB per file, 100 GB per organisation.
**Pricing:** File API operations are free; content billed as input tokens.

---

## Memory Tool

**Status:** GA | **Header:** None required (formerly `context-management-2025-06-27`)
**Models:** All current models

```python
tools = [{"type": "memory_20250818", "name": "memory"}]
```

**Commands:**
- `view` — list directories/file contents (supports line ranges)
- `create` — create new memory file
- `str_replace` — replace text in memory file
- `insert` — insert at specific line
- `delete` — delete file/directory
- `rename` — move/rename file

**Client responsibility:** persist memory store between conversations. The API
provides the tool interface; storage is client-side.

**Security:** validate all paths start with `/memories`, reject path traversal
patterns (`../`), use `pathlib.Path.resolve()` for canonical paths.

---

## Citations and Search Results

**Status:** GA | **Models:** All current models
**Header:** None

Enable natural citations for RAG via search_result content blocks:

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "What does the document say about X?"},
        {
            "type": "search_result",
            "source": "https://example.com/doc",
            "title": "Relevant Document",
            "content": [{"type": "text", "text": "...document content..."}],
            "citations": {"enabled": True}
        }
    ]
}]
```

Search results work in both message content (pre-fetched) and tool results
(dynamic RAG). Citations are all-or-nothing per request.

**Response format:** citation blocks with `search_result_location` type
containing source, title, cited_text, and index references.

---

## Prompt Caching

**Status:** GA | **Models:** All current | **Header:** None

```python
{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}
```

**Durations:** 5-minute (all platforms), 1-hour (API, Azure).
**Cost savings:** cached reads cost 10% of base input price.
**Minimum cacheable length:** 1,024 tokens (Haiku), 2,048 tokens (others).

Mark system prompts, tool definitions, and large documents with cache_control
for significant cost reduction on repeated requests.

---

## Data Residency

**Status:** GA | **Models:** Opus 4.6+ | **Header:** None

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    inference_geo="us",
    messages=[...]
)
```

Values: `"us"` (US-only, 1.1x pricing) or `"global"` (default).
Per-request control for compliance requirements.

---

## Batch Processing

**Status:** GA | **Models:** All current | **Header:** None

50% cost reduction for asynchronous batch requests. Submit batches of messages
for processing with results available when complete.

Ideal for: bulk document processing, evaluation runs, data extraction at scale.

---

## Token Counting

**Status:** GA | **Models:** All current | **Header:** None

Count tokens before sending requests to manage context budgets:

```python
count = client.messages.count_tokens(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "..."}],
    system="...",
    tools=[...]
)
# count.input_tokens → integer
```

Accounts for system prompts, tools, and message content. Use to pre-check
whether content fits within context window limits.

---

## Platform Availability Matrix

| Feature | Claude API | Bedrock | Vertex AI | Azure/Foundry |
|---------|-----------|---------|-----------|---------------|
| Structured outputs | GA | Beta | Beta | Beta |
| Extended thinking | GA | GA | GA | GA |
| Prompt caching | GA | GA | GA | GA |
| Batch processing | GA | GA | GA | Varies |
| Files API | Beta | - | - | - |
| Memory tool | GA | - | - | - |
| MCP connector | Beta | - | - | - |
| Computer use | Beta | Beta | Beta | Beta |
| 1M context | Beta | Check | Check | Check |
| Tool search | GA | - | - | - |

Dash (-) indicates not currently available on that platform. "Check" indicates
support may have been added since last update.

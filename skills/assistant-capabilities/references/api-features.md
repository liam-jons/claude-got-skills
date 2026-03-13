# API Features Reference

Detailed API feature documentation with code examples, beta headers, and
platform availability. Consult when implementing API calls or configuring
features.

**Last updated:** 2026-03-13

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
- [Fast Mode](#fast-mode)
- [Data Residency](#data-residency)
- [Batch Processing](#batch-processing)
- [Token Counting](#token-counting)
- [Vision & Image Processing](#vision--image-processing)
- [PDF Processing](#pdf-processing)
- [Streaming](#streaming)
- [Rate Limits & Usage Tiers](#rate-limits--usage-tiers)

---

## Adaptive Thinking

**Status:** GA | **Models:** Opus 4.6, Sonnet 4.6 | **Header:** None

Claude dynamically decides when and how deeply to think. Replaces manual
`budget_tokens` configuration. Available on Opus 4.6 and Sonnet 4.6.

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
Opus 4.5 but is deprecated on Opus 4.6 and Sonnet 4.6.

---

## Extended Thinking

**Status:** GA | **Models:** All current | **Header:** None

Multi-stage reasoning with explicit thinking blocks. All current models
support extended thinking.

```python
# Haiku 4.5, Sonnet 4.5, Opus 4.5 — use budget_tokens
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "..."}]
)
```

**Interleaved thinking** (Opus 4.6, Sonnet 4.6, Sonnet 4.5): thinking blocks
appear between tool calls for better multi-step reasoning. On Opus 4.6 and
Sonnet 4.6, interleaving is automatic with adaptive thinking. On Sonnet 4.5,
enable via `thinking: {type: "enabled", budget_tokens: N}`.

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

| Level | Behaviour |
|-------|-----------|
| low | Minimal thinking, fast responses |
| medium | Balanced (default) |
| high | Thorough reasoning |

Note: `max` was removed in Claude Code v2.1.72 (simplified to 3 levels).
Use `/effort auto` to reset to default.

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

**Context rot:** Accuracy degrades as token count grows — particularly for
retrieval tasks in the middle of long contexts. Place critical information at
the start or end, use prompt caching and compaction to manage context size, and
prefer structured formats to help Claude locate key details.

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

**Status:** GA | **Models:** All current | **Header:** None
**Note:** GA on Bedrock; Beta on Foundry | **ZDR eligible**

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

**Complexity limits:** Max 20 strict tools per request, 24 optional parameters
per tool, 16 union types per schema, 180-second compilation timeout.

**Property ordering:** In responses, required properties appear first, then
optional properties in schema-definition order. Design schemas accordingly for
predictable output structure.

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

**Status:** GA | **Header:** None required (formerly beta with `context-management-2025-06-27`)
**Models:** All current models (including Opus 4.6, Sonnet 4.6) | **ZDR eligible**

```python
tools = [{"type": "memory_20250818", "name": "memory"}]

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    tools=tools,
    messages=[{"role": "user", "content": "Remember that my preferred language is Python"}]
)
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

**Using with compaction:** When using the compaction API alongside memory,
instruct Claude to save critical context to memory before compaction triggers.
This preserves important details that would otherwise be summarised away.

**Multi-session software development pattern:** Use memory to maintain project
context (architecture decisions, file structure, coding conventions) across
sessions. At the start of each session, Claude reads memory to re-orient; at
the end, it writes updated state. This enables continuous multi-session
development without losing context between conversations.

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
**Minimum cacheable length:** varies by model (see below).

Mark system prompts, tool definitions, and large documents with cache_control
for significant cost reduction on repeated requests.

### Automatic Caching

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    cache_control={"type": "ephemeral"},
    messages=[{"role": "user", "content": "..."}]
)
# With 1-hour TTL (2x base input for writes):
# cache_control={"type": "ephemeral", "ttl": "1h"}
```

Add a single `cache_control` field at the request level and the system
automatically caches the last cacheable block, moving the cache point forward
as conversations grow. No manual breakpoint management required. Works
alongside explicit block-level cache control (uses one of 4 breakpoint slots).

**Edge cases:**
- Last block has explicit `cache_control` with same TTL: no-op
- Last block has explicit `cache_control` with different TTL: 400 error
- All 4 breakpoint slots taken: 400 error
- Last block not eligible: walks backward to find nearest eligible block

**Minimum cacheable lengths** (vary by model):
- Opus 4.6, Opus 4.5, Haiku 4.5: 4,096 tokens
- Sonnet 4.6: 2,048 tokens
- Sonnet 4.5: 1,024 tokens

**Availability:** Claude API and Azure AI Foundry (preview). Not yet
available on Bedrock or Vertex AI.

---

## Fast Mode

**Status:** Beta | **Models:** Opus 4.6 only | **Header:** `fast-mode-2026-02-01`
**Access:** Waitlist-gated

Up to 2.5x faster output token generation (OTPS, not TTFT). Same model
weights — not a different model.

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    speed="fast",
    messages=[{"role": "user", "content": "..."}],
    betas=["fast-mode-2026-02-01"]
)
# response.usage includes speed: "fast" for verification
```

**Pricing:** 6x standard Opus rates ($30/$150 per MTok input/output). Stacks
with prompt caching and data residency multipliers. No additional long context
surcharge for 1M context (unlike standard speed).

**Constraints:**
- Not available with Batch API or Priority Tier
- Switching between fast/standard invalidates prompt cache
- Dedicated rate limits (separate `anthropic-fast-*` headers)
- Unsupported model + `speed: "fast"` returns an error

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

## Vision & Image Processing

**Status:** GA | **Models:** All current | **Header:** None

All Claude models natively analyze images without special configuration.

### Sending Images

Three methods for providing images:

**Base64 (inline):**
```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "What's in this image?"},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "iVBOR..."
            }
        }
    ]
}]
```

**URL:**
```python
{"type": "image", "source": {"type": "url", "url": "https://example.com/image.png"}}
```

**Files API (file_id):**
```python
{"type": "image", "source": {"type": "file", "file_id": "file_abc123"}}
```

### Supported Formats
JPEG, PNG, GIF (first frame), WebP. Max ~20MB per image.

### Token Costs
Images are resized and tokenized based on dimensions. Approximate formula:
tokens ≈ (width × height) / 750. A 1000×1000 image ≈ 1,333 tokens.

### Multi-Image
Multiple images per message supported. Each adds to token count independently.

### Limitations
- No real-time video analysis (extract frames first)
- OCR accuracy varies with image quality
- Spatial reasoning (exact coordinates) is approximate

---

## PDF Processing

**Status:** GA | **Models:** All current | **Header:** None

### Limits
- Maximum 32MB per PDF
- Maximum 100 pages per request
- Scanned PDFs supported (OCR applied automatically)

### Sending PDFs

**Base64:**
```python
{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "..."}}
```

**URL:**
```python
{"type": "document", "source": {"type": "url", "url": "https://example.com/doc.pdf"}}
```

**Files API:**
```python
{"type": "document", "source": {"type": "file", "file_id": "file_abc123"}}
```

### Platform Notes
- **Bedrock**: Citations must be enabled for visual PDF analysis
- **All platforms**: Use token counting API to estimate costs before sending large PDFs

---

## Streaming

**Status:** GA | **Models:** All current | **Header:** None

Real-time Server-Sent Events (SSE) responses.

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Event Types
- `message_start` — message metadata
- `content_block_start` — new content block (text or tool_use)
- `content_block_delta` — incremental content
- `content_block_stop` — block complete
- `message_delta` — usage stats, stop_reason
- `message_stop` — message complete

### Tool Use with Streaming
Tool call parameters stream progressively via `content_block_delta` events.
When `stop_reason: "tool_use"`, extract tool inputs and submit results to
continue the conversation.

### Fine-grained Tool Streaming
GA feature — stream individual characters of tool call parameters for
responsive UIs that show tool inputs as they're generated.

---

## Rate Limits & Usage Tiers

**Status:** GA | **Header:** None

### Tier System
API access is tiered (1-4) based on usage history and payment. Higher tiers
unlock higher rate limits and features (e.g., 1M context requires tier 3+).

For current tier thresholds, per-model rate limits, and your current tier:
- https://platform.claude.com (account dashboard)
- https://platform.claude.com/docs/en/api/rate-limits

### Rate Limit Headers
Every response includes rate limit information:
- `anthropic-ratelimit-requests-limit` / `-remaining` / `-reset`
- `anthropic-ratelimit-tokens-limit` / `-remaining` / `-reset`

### Handling 429 Errors
SDKs auto-retry 429 errors (up to 2 retries by default).
For manual handling, check the `Retry-After` header.

### Key Patterns
- Opus models have lower request limits than Sonnet/Haiku
- Rate limits are per-model, per-tier (not shared across models)
- Fast mode has separate dedicated rate limits (`anthropic-fast-*` headers)

---

## Platform Availability Matrix

| Feature | Claude API | Bedrock | Vertex AI | Azure/Foundry |
|---------|-----------|---------|-----------|---------------|
| Structured outputs | GA | GA | Beta | Beta |
| Extended thinking | GA | GA | GA | GA |
| Prompt caching | GA | GA | GA | GA |
| Batch processing | GA | GA | GA | Varies |
| Files API | Beta | - | - | - |
| Memory tool | GA | - | - | - |
| MCP connector | Beta | - | - | - |
| Computer use | Beta | Beta | Beta | Beta |
| 1M context | Beta | Check | Check | Check |
| Tool search | GA | - | - | - |
| Vision | GA | GA | GA | GA |
| PDF processing | GA | GA | GA | GA |
| Streaming | GA | GA | GA | GA |

Dash (-) indicates not currently available on that platform. "Check" indicates
support may have been added since last update.

# Model Specifics Reference

Per-model capability matrix, limits, and migration guidance.
Consult when choosing between models, planning migrations, or understanding
model-specific behaviour.

**Last updated:** 2026-03-18

## Table of Contents

- [Model Overview](#model-overview)
- [Capability Matrix](#capability-matrix)
- [Model IDs and Aliases](#model-ids-and-aliases)
- [Pricing](#pricing)
- [Context Window Details](#context-window-details)
- [Output Token Limits](#output-token-limits)
- [Thinking Capabilities](#thinking-capabilities)
- [Computer Use Versions](#computer-use-versions)
- [Feature Availability by Model](#feature-availability-by-model)
- [Breaking Changes on Opus 4.6](#breaking-changes-on-opus-46)
- [Migration Guides](#migration-guides)
- [Model Selection Guidance](#model-selection-guidance)

---

## Model Overview

| Model | Release | Positioning | Training Cutoff | Status |
|-------|---------|-------------|-----------------|--------|
| Claude Opus 4.6 | 2026-02 | Flagship. Highest capability, adaptive thinking, 128K output | Aug 2025 | **Current** |
| Claude Sonnet 4.6 | 2026-02 | Balanced. Speed + intelligence, adaptive thinking, 64K output | Jan 2026 | **Current** |
| Claude Haiku 4.5 | 2025-10 | Fast. Low latency, cost-efficient, extended thinking | Jul 2025 | **Current** |
| Claude Sonnet 4.5 | 2025-09 | Previous balanced model. Interleaved thinking, strong coding | -- | Legacy |
| Claude Opus 4.5 | 2025-11 | Previous flagship. Extended thinking, 32K output | -- | Legacy |

### Knowledge Cutoff Dates

| Model | Reliable Knowledge Through | Training Data Through |
|-------|---------------------------|----------------------|
| Opus 4.6 | May 2025 | Aug 2025 |
| Sonnet 4.6 | Aug 2025 | Jan 2026 |
| Haiku 4.5 | Feb 2025 | Jul 2025 |

---

## Capability Matrix

| Capability | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 | Sonnet 4.5 (legacy) | Opus 4.5 (legacy) |
|------------|----------|------------|-----------|---------------------|-------------------|
| Context window | 1M (native) | 1M (native) | 200K | 200K (1M beta) | 200K (1M beta) |
| Context awareness | No | Yes | Yes | Yes | No |
| Max output tokens | 128K | 64K | 64K | 64K | 32K |
| Extended thinking | Yes (adaptive) | Yes (adaptive) | Yes (budget) | Yes (budget) | Yes (budget) |
| Interleaved thinking | Yes (auto) | Yes (auto) | No | Yes (auto) | No |
| Adaptive thinking | Yes | Yes | No | No | No |
| Effort: low/med/high | Yes | Yes | Yes | Yes | Yes |
| Effort: max | Yes | No | No | No | No |
| Structured outputs | Yes | Yes | Yes | Yes | Yes |
| Computer use | Yes (v20251124) | Yes (v20251124) | Yes (v20250124) | Yes (v20250124) | Yes (v20251124) |
| Tool search (GA) | Yes | Yes | No | Yes | Yes |
| Code execution (GA) | Yes | Yes | Yes | Yes | Yes |
| Programmatic tool calling (GA) | Yes | Yes | No | Yes | Yes |
| Memory tool (GA) | Yes | Yes | Yes | Yes | Yes |
| Web search (GA) | Yes | Yes | Yes | Yes | Yes |
| Dynamic filtering | Yes | Yes | No | No | No |
| Batch processing | Yes | Yes | Yes | Yes | Yes |
| Prompt caching | Yes | Yes | Yes | Yes | Yes |
| Data residency (ZDR) | Yes | No | No | No | No |
| Fast mode (research preview) | Yes | No | No | No | No |

---

## Model IDs and Aliases

| Model | ID | Notes |
|-------|-----|-------|
| Opus 4.6 | `claude-opus-4-6` | No dated variant available |
| Sonnet 4.6 | `claude-sonnet-4-6` | No dated variant available |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Alias: `claude-haiku-4-5` |
| Sonnet 4.5 (legacy) | `claude-sonnet-4-5-20250929` | Alias: `claude-sonnet-4-5` |
| Opus 4.5 (legacy) | `claude-opus-4-5-20251101` | Alias: `claude-opus-4-5` |

### Platform-Specific IDs

| Model | AWS Bedrock | GCP Vertex AI |
|-------|-------------|---------------|
| Opus 4.6 | `anthropic.claude-opus-4-6-v1` | `claude-opus-4-6` |
| Sonnet 4.6 | `anthropic.claude-sonnet-4-6` | `claude-sonnet-4-6` |
| Haiku 4.5 | `anthropic.claude-haiku-4-5-20251001-v1:0` | `claude-haiku-4-5@20251001` |

In Claude Code / Agent SDK, use short names: `opus`, `sonnet`, `haiku`
(resolves to latest version of each tier).

### Models API (Programmatic Discovery)

`GET /v1/models` returns all available models with their capabilities:

```python
models = client.models.list()
for model in models.data:
    print(model.id, model.capabilities)  # max_input_tokens, max_tokens, capabilities object
```

Use `GET /v1/models/{model_id}` for a specific model. The `capabilities` object
includes feature flags (thinking, vision, tool_use, etc.) for programmatic model
selection without hardcoding.

---

## Pricing

For all pricing details, see: https://platform.claude.com/docs/en/about-claude/pricing

**Relative cost ranking** (most to least expensive): Opus > Sonnet > Haiku.

Do not state specific prices — they change frequently. Refer users to the
pricing page for current rates, batch discounts, caching savings, and
long context pricing.

---

## Context Window Details

### Native Context by Model

| Model | Native Context | 1M Access |
|-------|---------------|-----------|
| Opus 4.6 | 1,000,000 tokens | Native (no header needed) |
| Sonnet 4.6 | 1,000,000 tokens | Native (no header needed) |
| Haiku 4.5 | 200,000 tokens | Not available |
| Sonnet 4.5 (legacy) | 200,000 tokens | Beta header `context-1m-2025-08-07`, tier 4+ |
| Opus 4.5 (legacy) | 200,000 tokens | Not documented for 1M access |

Opus 4.6 and Sonnet 4.6 use 1M natively with no beta header and no
premium pricing. For older models, requests exceeding 200K tokens via
the beta header incur premium rates (~2x input, ~1.5x output).

A single request can include up to 600 images or PDF pages (100 for
models with a 200K-token context window).

### Thinking and Context

Extended thinking blocks are automatically stripped from context between turns.
Only the current turn's thinking counts against the context window. This means
a model can think extensively without accumulating context debt.

Effective context: `context_window = (input_tokens - previous_thinking_tokens) + current_turn_tokens`

### Context Awareness (Sonnet 4.6, Sonnet 4.5, Haiku 4.5)

These models receive `<budget:token_budget>` in the system prompt and
`<system_warning>Token usage: X/Y; Z remaining</system_warning>` after tool
calls. This helps the model manage its own context budget. Opus 4.6 does
not have context awareness.

### Compaction (Beta)

Server-side context compaction is available for Opus 4.6 and Sonnet 4.6.
Compaction automatically summarises earlier parts of a conversation when
context approaches the window limit, enabling effectively infinite
conversations. See `references/api-features.md` for configuration details.

---

## Output Token Limits

| Model | Standard Max | Notes |
|-------|-------------|-------|
| Opus 4.6 | 128,000 | Requires streaming for large values |
| Sonnet 4.6 | 64,000 | — |
| Haiku 4.5 | 64,000 | — |
| Sonnet 4.5 (legacy) | 64,000 | — |
| Opus 4.5 (legacy) | 32,000 | — |

Set via `max_tokens` parameter. For Opus 4.6 with values above ~16K,
streaming is recommended to avoid timeouts. Use `.stream()` with
`.get_final_message()` if you don't need incremental event processing.

---

## Thinking Capabilities

| Model | Type | Configuration |
|-------|------|---------------|
| Opus 4.6 | Adaptive + interleaved | `thinking: {type: "adaptive"}` — Claude decides when/how much |
| Sonnet 4.6 | Adaptive + interleaved | `thinking: {type: "adaptive"}` — same as Opus 4.6 |
| Haiku 4.5 | Extended | `thinking: {type: "enabled", budget_tokens: N}` (no interleaving) |
| Sonnet 4.5 (legacy) | Extended + interleaved | `thinking: {type: "enabled", budget_tokens: N}` |
| Opus 4.5 (legacy) | Extended | `thinking: {type: "enabled", budget_tokens: N}` (no interleaving) |

**Effort levels:** Control thinking depth via the `effort` parameter.
All models support `low`, `medium`, `high`. Opus 4.6 additionally supports
`max` for absolute highest capability. At default effort (`high`), Claude
almost always thinks. At lower effort, it may skip thinking for simpler
problems.

**Sonnet 4.6 note:** Supports both adaptive thinking and manual extended
thinking with the `interleaved-thinking-2025-05-14` beta header. You can
use either approach.

See `references/api-features.md` for code examples and migration guidance.

---

## Computer Use Versions

Opus 4.6, Sonnet 4.6, and Opus 4.5 use `computer_20251124` (includes zoom action).
Haiku 4.5 and Sonnet 4.5 use `computer_20250124`. See `references/tool-types.md` for full configuration,
available actions, coordinate scaling, and security requirements.

---

## Feature Availability by Model

### Beta Features

| Feature | Header | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 | Sonnet 4.5 | Opus 4.5 |
|---------|--------|----------|------------|-----------|------------|----------|
| 1M context | Native (no header) | Yes | Yes | No | No | No |
| 1M context (beta) | `context-1m-2025-08-07` | — | — | No | Yes | Yes |
| Files API | `files-api-2025-04-14` | Yes | Yes | Yes | Yes | Yes |
| MCP connector | `mcp-client-2025-11-20` | Yes | Yes | Yes | Yes | Yes |
| Computer use | Model-specific | Yes | Yes | Yes | Yes | Yes |
| Skills | `skills-2025-10-02` | Yes | Yes | Yes | Yes | Yes |
| Compaction | Beta | Yes | Yes | No | No | No |
| Fast mode | `fast-mode-2026-02-01` | Yes | No | No | No | No |

### GA Features (No Header Required)

Structured outputs (GA on direct API and Amazon Bedrock), effort parameter,
extended thinking, prompt caching, batch processing, web search, web fetch,
code execution, tool search, memory tool, programmatic tool calling,
tool use examples (`input_examples`), citations, token counting,
fine-grained tool streaming.

**Programmatic tool calling:** All supported models use tool version
`code_execution_20260120`. Web search and web fetch are no longer restricted
to specific models — available on all models that support programmatic
tool calling.

**Dynamic filtering:** Available on Opus 4.6 and Sonnet 4.6 only. Requires
`web_search_20260209` or `web_fetch_20260209` tool versions. Claude writes
and executes code to filter results before they enter the context window.

**Structured outputs schema limits:** Subject to schema complexity limits
(max nesting depth, max properties, max enum values). See API docs for
current thresholds.

---

## Breaking Changes on Opus 4.6

These changes apply specifically to Opus 4.6. Older models are unaffected.

### 1. Prefill Removed

Assistant message prefilling (starting Claude's response with specific text)
returns a 400 error on Opus 4.6.

**Migration:** Use structured outputs (`output_config.format`) to constrain
response format, or add format instructions to the system prompt.

### 2. budget_tokens Deprecated

`thinking: {type: "enabled", budget_tokens: N}` is deprecated on Opus 4.6
and Sonnet 4.6. It remains functional but will be removed in a future
model release.

**Migration:** Use `thinking: {type: "adaptive"}` and control via `effort`
parameter. For fine-grained control, adaptive thinking dynamically allocates
thinking tokens based on task complexity.

### 3. output_format Deprecated

The top-level `output_format` parameter is deprecated across all models.

**Migration:** Use `output_config: {format: {type: "json_schema", schema: ...}}`
instead.

### 4. Interleaved Thinking Header Deprecated

`interleaved-thinking-2025-05-14` beta header is deprecated on Opus 4.6.
It is safely ignored if included.

**Migration:** Adaptive thinking on Opus 4.6 enables interleaving
automatically. On Sonnet 4.6, you can use either adaptive thinking or
the beta header with manual extended thinking. On Sonnet 4.5, interleaving
is also automatic with standard `thinking: {type: "enabled", budget_tokens: N}`.

### 5. Tool Parameter Quoting

Opus 4.6 may produce different JSON string escaping in tool parameters
compared to older models.

**Migration:** Use standard JSON parsers (not regex or string matching) for
tool parameter extraction. Well-formed JSON parsers handle all valid escaping.

---

## Migration Guides

### From Opus 4.5 to Opus 4.6

1. Replace `thinking: {type: "enabled", budget_tokens: N}` with
   `thinking: {type: "adaptive"}`
2. Remove any prefill logic (will error)
3. Update `output_format` to `output_config.format`
4. Remove `interleaved-thinking-2025-05-14` header
5. Update computer use tool type to `computer_20251124` and header to
   `computer-use-2025-11-24` (if migrating from Opus 4.5 `computer_20250124`)
6. Test JSON parsing for tool parameters (quoting changes)
7. Increase `max_tokens` ceiling — now supports up to 128K
8. Remove `context-1m-2025-08-07` beta header — 1M is native on Opus 4.6
9. Consider using `effort: "max"` for highest capability tasks

### From Sonnet 4.5 to Sonnet 4.6

1. Replace `thinking: {type: "enabled", budget_tokens: N}` with
   `thinking: {type: "adaptive"}` (or keep manual extended thinking
   with the interleaved-thinking beta header — both work)
2. Programmatic tool calling now GA — no beta header required
3. Context awareness still present on Sonnet 4.6 (unlike Opus 4.6)
4. Remove `context-1m-2025-08-07` beta header — 1M is native on Sonnet 4.6
5. Dynamic filtering now available for web search/fetch
6. Computer use upgraded to `computer_20251124` (includes zoom action)
7. Effort parameter now supported (first Sonnet to support `effort`)
8. Consider `effort: "medium"` as default for balanced speed/cost/quality

### From Sonnet 4.5 to Opus 4.6

All Opus 4.5 migration steps above, plus:
1. Effort parameter includes `max` level (Opus 4.6 exclusive)
2. Programmatic tool calling now GA on Opus 4.6 — no header required
3. Context awareness system warnings not present on Opus 4.6
4. Budget will increase (Opus tier vs Sonnet tier — check pricing page)

---

## Model Selection Guidance

| Use Case | Recommended | Rationale |
|----------|-------------|-----------|
| Complex reasoning, research | Opus 4.6 | Adaptive thinking, 128K output, highest capability |
| Coding, general agent tasks | Sonnet 4.6 | Adaptive thinking, balanced speed/capability |
| High-volume processing | Haiku 4.5 | Fastest latency |
| Batch analysis | Haiku 4.5 + batch | Batch discount on fastest model |
| Multi-tool workflows | Sonnet 4.6 | Programmatic tool calling (GA), dynamic filtering |
| Web research with filtering | Sonnet 4.6 | Dynamic filtering + free code execution |
| Document generation | Sonnet 4.6 | Good balance for skills-based work |
| Subagent tasks | Haiku 4.5 | Fast, efficient for delegated analysis |
| Maximum quality | Opus 4.6 (effort: max) | Highest capability + maximum effort level |
| Latency-sensitive Opus tasks | Opus 4.6 (fast mode) | Up to 2.5x faster output generation |

### Optimisation Patterns

- Use prompt caching for repeated system prompts and tool definitions
- Use Haiku for subagents and analysis tasks
- Use batch processing for non-time-sensitive workloads
- Use `effort: "low"` for simple tasks, `effort: "high"` for complex ones
- See pricing page for current discounts and long-context rates

---

## Common Misconceptions

| Claim | Reality |
|-------|---------|
| "Claude supports embeddings" | No. Use a dedicated embeddings model (e.g., Voyage AI) |
| "I can fine-tune Claude" | No fine-tuning available via public API. Use system prompts, skills, or Projects for customisation |
| "Claude can run any language" | Code execution supports Python + common libraries. For other languages, use Bash tool or external containers |
| "Claude remembers by default" | No default cross-conversation memory. Enable via Memory tool (GA) with client-side storage |
| "Claude has internet access" | Not by default. Enable via Web Search/Fetch tools or MCP servers |
| "1M context needs a beta header" | Only for Sonnet 4.5 and older. Opus 4.6 and Sonnet 4.6 have 1M natively |

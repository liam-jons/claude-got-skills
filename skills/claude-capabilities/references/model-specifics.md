# Model Specifics Reference

Per-model capability matrix, pricing, limits, and migration guidance.
Consult when choosing between models, planning migrations, or understanding
model-specific behaviour.

**Last updated:** 2026-03-07

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

| Model | Release | Positioning | Status |
|-------|---------|-------------|--------|
| Claude Opus 4.6 | 2026-02 | Flagship. Highest capability, adaptive thinking, 128K output | **Current** |
| Claude Sonnet 4.6 | 2026-02 | Balanced. Speed + intelligence, adaptive thinking, 64K output | **Current** |
| Claude Haiku 4.5 | 2025-10 | Fast. Low latency, cost-efficient, extended thinking | **Current** |
| Claude Sonnet 4.5 | 2025-09 | Previous balanced model. Interleaved thinking, strong coding | Legacy |
| Claude Opus 4.5 | 2025-11 | Previous flagship. Extended thinking, 32K output | Legacy |

---

## Capability Matrix

| Capability | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 | Sonnet 4.5 (legacy) | Opus 4.5 (legacy) |
|------------|----------|------------|-----------|---------------------|-------------------|
| Context window | 200K (1M beta) | 200K (1M beta) | 200K | 200K (1M beta) | 200K (1M beta) |
| Max output tokens | 128K | 64K | 64K | 64K | 32K |
| Extended thinking | Yes (adaptive) | Yes (adaptive) | Yes (budget) | Yes (budget) | Yes (budget) |
| Interleaved thinking | Yes (auto) | Yes (auto) | No | Yes (auto) | No |
| Adaptive thinking | Yes | Yes | No | No | No |
| Effort: max | Yes | No | No | No | No |
| Effort: low/med/high | Yes | Yes | Yes | Yes | Yes |
| Structured outputs | Yes | Yes | Yes | Yes | Yes |
| Computer use | Yes (v20251124) | Yes | Yes (v20250124) | Yes (v20250124) | Yes (v20251124) |
| Tool search (GA) | Yes | Yes | No | Yes | Yes |
| Code execution (GA) | Yes | Yes | Yes | Yes | Yes |
| Programmatic tool calling (GA) | Yes | Yes | No | Yes | Yes |
| Memory tool (GA) | Yes | Yes | Yes | Yes | Yes |
| Web search (GA) | Yes | Yes | Yes | Yes | Yes |
| Dynamic filtering | Yes | Yes | No | No | No |
| Batch processing | Yes | Yes | Yes | Yes | Yes |
| Prompt caching | Yes | Yes | Yes | Yes | Yes |
| Data residency | Yes | No | No | No | No |

---

## Model IDs and Aliases

| Model | Full ID | Alias |
|-------|---------|-------|
| Opus 4.6 | `claude-opus-4-6` | `claude-opus-4-6-20260210` |
| Sonnet 4.6 | `claude-sonnet-4-6` | `claude-sonnet-4-6` |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | `claude-haiku-4-5` |
| Sonnet 4.5 (legacy) | `claude-sonnet-4-5-20250929` | `claude-sonnet-4-5` |
| Opus 4.5 (legacy) | `claude-opus-4-5-20251101` | `claude-opus-4-5` |

In Claude Code / Agent SDK, use short names: `opus`, `sonnet`, `haiku`
(resolves to latest version of each tier).

---

## Pricing

Pricing per million tokens (USD). Verify current rates at
docs.anthropic.com as prices may change.

| Model | Input | Output | Cached Input |
|-------|-------|--------|-------------|
| Opus 4.6 | $5 | $25 | $0.50 |
| Sonnet 4.6 | $3 | $15 | $0.30 |
| Haiku 4.5 | $1 | $5 | $0.10 |
| Sonnet 4.5 (legacy) | $3 | $15 | $0.30 |
| Opus 4.5 (legacy) | $15 | $75 | $1.50 |

**Additional pricing factors:**
- 1M context (beyond 200K): 2x input, 1.5x output
- Data residency (US-only): 1.1x multiplier
- Batch processing: 50% discount
- Prompt caching reads: 10% of base input price
- Prompt caching writes: 25% premium on base input price

---

## Context Window Details

All models share the same base context architecture:

| Aspect | Value |
|--------|-------|
| Base context | 200,000 tokens |
| Beta context | 1,000,000 tokens |
| Beta header | `context-1m-2025-08-07` |
| Tier requirement | Usage tier 3+ |
| Premium pricing trigger | Tokens beyond 200K |

### Thinking and Context

Extended thinking blocks are automatically stripped from context between turns.
Only the current turn's thinking counts against the context window. This means
a model can think extensively without accumulating context debt.

Effective context: `context_window = (input_tokens - previous_thinking_tokens) + current_turn_tokens`

### Context Awareness (Sonnet 4.5, Haiku 4.5 only)

These models receive `<budget:token_budget>` in the system prompt and
`<system_warning>Token usage: X/Y; Z remaining</system_warning>` after tool
calls. This helps the model manage its own context budget.

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
streaming is recommended to avoid timeouts.

---

## Thinking Capabilities

| Model | Type | Configuration |
|-------|------|---------------|
| Opus 4.6 | Adaptive | `thinking: {type: "adaptive"}` — Claude decides when/how much |
| Sonnet 4.5 | Extended + interleaved | `thinking: {type: "enabled", budget_tokens: N}` |
| Opus 4.5 | Extended | `thinking: {type: "enabled", budget_tokens: N}` (no interleaving) |
| Haiku 4.5 | None | Use `effort` parameter for basic thoroughness control |

See `references/api-features.md` for code examples and migration guidance.

---

## Computer Use Versions

Opus 4.6 and Opus 4.5 use `computer_20251124` (includes zoom action). All other
models use `computer_20250124`. See `references/tool-types.md` for full configuration,
available actions, coordinate scaling, and security requirements.

---

## Feature Availability by Model

### Beta Features

| Feature | Header | Opus 4.6 | Sonnet 4.5 | Haiku 4.5 | Opus 4.5 |
|---------|--------|----------|------------|-----------|----------|
| 1M context | `context-1m-2025-08-07` | Yes | Yes | Yes | Yes |
| Files API | `files-api-2025-04-14` | Yes | Yes | Yes | Yes |
| Memory tool | `context-management-2025-06-27` | Yes | Yes | Yes | Yes |
| MCP connector | `mcp-client-2025-11-20` | Yes | Yes | Yes | Yes |
| Computer use | Model-specific | Yes | Yes | Yes | Yes |
| Code execution | `code-execution-2025-08-25` | Yes | Yes | Yes | Yes |
| Skills | `skills-2025-10-02` | Yes | Yes | Yes | Yes |
| Prog. tool calling | `advanced-tool-use-2025-11-20` | No | Yes | No | Yes |
| Tool use examples | `advanced-tool-use-2025-11-20` | Yes | Yes | Yes | Yes |
| Tool search | — | Yes | Yes | No | Yes |
| Compaction | Beta | Yes | Yes | Yes | Yes |

### GA Features (No Header Required)

Structured outputs, effort parameter, extended thinking, prompt caching,
batch processing, web search, citations, token counting, fine-grained tool
streaming.

---

## Breaking Changes on Opus 4.6

These changes apply specifically to Opus 4.6. Older models are unaffected.

### 1. Prefill Removed

Assistant message prefilling (starting Claude's response with specific text)
returns a 400 error on Opus 4.6.

**Migration:** Use structured outputs (`output_config.format`) to constrain
response format, or add format instructions to the system prompt.

### 2. budget_tokens Deprecated

`thinking: {type: "enabled", budget_tokens: N}` is deprecated on Opus 4.6.

**Migration:** Use `thinking: {type: "adaptive"}` and control via `effort`
parameter. For fine-grained control, adaptive thinking dynamically allocates
thinking tokens based on task complexity.

### 3. output_format Deprecated

The top-level `output_format` parameter is deprecated across all models.

**Migration:** Use `output_config: {format: {type: "json_schema", schema: ...}}`
instead.

### 4. Interleaved Thinking Header Deprecated

`interleaved-thinking-2025-05-14` beta header is deprecated.

**Migration:** Adaptive thinking on Opus 4.6 enables interleaving
automatically. On Sonnet 4.5, interleaving is also automatic with standard
`thinking: {type: "enabled", budget_tokens: N}`.

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
5. Update computer use tool type from `computer_20250124` to
   `computer_20251124` and header to `computer-use-2025-11-24`
6. Test JSON parsing for tool parameters (quoting changes)
7. Increase `max_tokens` ceiling — now supports up to 128K

### From Sonnet 4.5 to Opus 4.6

All Opus 4.5 migration steps above, plus:
1. Note `effort: "max"` is now available (Opus 4.6 exclusive)
2. Programmatic tool calling not available on Opus 4.6 (use Sonnet 4.5 if
   needed)
3. Context awareness system warnings not present on Opus 4.6
4. Budget may increase significantly (15x input cost vs Sonnet 4.5)

---

## Model Selection Guidance

| Use Case | Recommended | Rationale |
|----------|-------------|-----------|
| Complex reasoning, research | Opus 4.6 | Adaptive thinking, 128K output, highest capability |
| Coding, general agent tasks | Sonnet 4.5 | Interleaved thinking, balanced cost/performance |
| High-volume processing | Haiku 4.5 | Lowest cost, fastest latency |
| Batch analysis | Haiku 4.5 + batch | 50% batch discount on cheapest model |
| Multi-tool workflows | Sonnet 4.5 | Programmatic tool calling available |
| Document generation | Sonnet 4.5 | Good balance for skills-based work |
| Subagent tasks | Haiku 4.5 | Cost-effective for delegated analysis |
| Maximum quality | Opus 4.6 (effort: max) | Highest capability + maximum effort |

### Cost Optimisation Patterns

- Use prompt caching for repeated system prompts and tool definitions
- Use Haiku for subagents and analysis tasks
- Use batch processing for non-time-sensitive workloads (50% savings)
- Avoid 1M context unless necessary (premium pricing beyond 200K)
- Use `effort: "low"` for simple tasks, `effort: "high"` for complex ones

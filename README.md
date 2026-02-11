# Claude Capabilities Awareness Skill

A skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that gives Claude accurate, post-training knowledge about its own capabilities, API features, extension patterns, and model specifics.

## Why this skill exists

Claude's training data has a cutoff. New features — adaptive thinking, the memory tool, agent teams, the skills ecosystem, MCP connectors, and more — ship faster than training data updates. Without this skill, Claude may give outdated or vague answers about what it can do.

With this skill loaded, Claude can accurately answer questions like "Can Claude remember things between conversations?", recommend the right model for a workload, suggest when to build a skill vs a hook vs a plugin, and cite specific API headers and parameters.

## What it covers

- **Current models**: Opus 4.6, Sonnet 4.5, Haiku 4.5, Opus 4.5 — context windows, output limits, thinking modes, effort levels
- **Thinking & reasoning**: Adaptive thinking, effort parameter, 128K output tokens
- **Context & memory**: 1M context window, compaction API, memory tool, prompt caching
- **Tools & integration**: Tool search, MCP connector, programmatic tool calling, computer use, code execution
- **Structured outputs**: Guaranteed JSON schema conformance, Files API, citations
- **Agent capabilities**: Agent SDK, subagents, hooks, plugins, MCP apps, agent teams
- **Extension patterns**: When to use CLAUDE.md vs skills vs hooks vs plugins vs MCP — with decision matrix
- **Architecture patterns**: Subagents vs tool chaining, batch vs streaming, model tiering, multi-agent coordination
- **Breaking changes**: Opus 4.6 prefill removal, budget_tokens deprecation, output_format migration

Reference files provide deeper detail with code examples for API features, tool types, agent capabilities, model specifics, and Claude Code specifics.

## Installation

```bash
npx skills add claude-got-skills/claude-capabilities
```

Or add manually to your Claude Code skills directory.

## Eval results (v1.3.0 on Haiku 4.5)

The skill was evaluated against a baseline (no skill context) across 22 test prompts in 7 categories.

### Keyword accuracy lift (Control → Treatment)

| Category | Control | Treatment | Lift |
|----------|---------|-----------|------|
| Architecture Decisions | 1.33 | 4.33 | **+225%** |
| Can Claude Do X | 2.0 | 4.67 | **+134%** |
| Implementation Guidance | 2.0 | 5.67 | **+184%** |
| Model Selection | 1.0 | 4.0 | **+300%** |
| Extension Awareness | 1.8 | 4.6 | **+156%** |
| Hallucination Detection | 1.5 | 2.75 | **+83%** |
| **Negative (regression check)** | **5.0** | **4.67** | **-7% (negligible)** |

### LLM judge scores (0-3 scale, with SKILL.md rubric)

The judge correctly identifies treatment responses as more accurate and actionable across all positive categories, while scoring negative tests neutrally.

### Hallucination prevention

The skill helps Claude avoid confident-but-wrong answers about its capabilities. In test 7.1 (browser cookie access), the control response contained a hallucinated claim that was absent from the treatment response.

## Token cost

SKILL.md is ~4,100 tokens. It loads once per session when invoked. Reference files load on-demand only when Claude needs deeper detail.

## Structure

```
claude-capabilities/
├── SKILL.md                      # Always-loaded skill (~333 lines)
├── README.md                     # This file
└── references/
    ├── agent-capabilities.md     # Agent SDK, subagents, hooks, plugins
    ├── api-features.md           # API parameters, headers, code examples
    ├── claude-code-specifics.md  # Agent teams, Chrome, CLI, IDE extensions
    ├── model-specifics.md        # Pricing, feature matrices, migration guides
    └── tool-types.md             # Built-in tools, tool definitions, examples
```

## License

MIT

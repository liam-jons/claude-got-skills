# Claude Capabilities Awareness Skill

A skill that gives Claude comprehensive, accurate knowledge about its capabilities across all platforms — Claude.ai, Claude Desktop, Claude Code, CoWork, and the API.

## Why this skill exists

Claude's training data has a cutoff. New features — adaptive thinking, dynamic filtering, fast mode, the memory tool, agent teams, the skills ecosystem, and more — ship faster than training data updates. Without this skill, Claude may give outdated or vague answers about what it can do.

With this skill loaded, Claude can accurately recommend the right model for a workload, explain how to process images and PDFs, suggest the right extension pattern for a user's platform, and cite specific API parameters and headers.

## What it covers

- **Current models**: Opus 4.6, Sonnet 4.6, Haiku 4.5 — context windows, output limits, thinking modes, pricing
- **Core capabilities**: Vision/images, PDF processing, multilingual, streaming
- **Thinking & reasoning**: Adaptive thinking, effort parameter, fast mode, 128K output
- **Context & memory**: 1M context, memory tool, compaction, automatic caching
- **Tools & integration**: Tool search, MCP connector, programmatic tool calling, dynamic filtering, code execution
- **Structured outputs**: Guaranteed JSON, Files API, citations, Agent Skills
- **Platform overview**: What's available on Claude.ai vs Desktop vs Claude Code vs CoWork vs API
- **Extension patterns**: Skills, hooks, plugins, CLAUDE.md, Projects, MCP — with platform availability matrix
- **Architecture patterns**: Subagents vs tool chaining, batch vs streaming, model tiering, multi-agent coordination
- **Breaking changes**: Opus 4.6 prefill removal, model retirements, GA promotions
- **Common misconceptions**: No embeddings, no fine-tuning, no default memory, no default internet

Reference files provide deeper detail with code examples for API features, tool types, agent capabilities, model specifics, and Claude Code specifics.

## Installation

**Claude Code:**
```bash
npx skills add claude-got-skills/skills@claude-capabilities
```

**Claude.ai / Claude Desktop:**
1. Download the skill as a ZIP file
2. Go to Settings > Capabilities > Skills
3. Click "Upload skill" and select the ZIP

## Eval results (v2.0.0)

Evaluated against a baseline (no skill) across 24 test prompts in 7 categories using Haiku 4.5 (no web search).

| Category | Control | Treatment | Lift |
|----------|---------|-----------|------|
| Architecture Decisions | 1.33 | 3.67 | **+176%** |
| Can Claude Do X | 1.67 | 5.00 | **+200%** |
| Implementation Guidance | 3.00 | 5.67 | **+89%** |
| Model Selection | 0.00 | 6.00 | **+∞** |
| Extension Awareness | 2.29 | 4.00 | **+75%** |
| Hallucination Detection | 1.75 | 3.00 | **+71%** |
| **Negative (regression check)** | **4.67** | **4.67** | **0% (no regression)** |

## Structure

```
├── .claude-plugin/
│   └── marketplace.json              # Skill discovery for npx skills add
├── skills/
│   └── claude-capabilities/
│       ├── SKILL.md                  # Always-loaded skill (~250 lines)
│       └── references/
│           ├── agent-capabilities.md # Agent SDK, subagents, hooks, plugins
│           ├── api-features.md       # API params, vision, PDFs, streaming, caching
│           ├── claude-code-specifics.md # Background tasks, /loop, teams, Chrome, CLI
│           ├── model-specifics.md    # Pricing, feature matrices, migration guides
│           └── tool-types.md         # Built-in tools, dynamic filtering, compatibility
├── evals/
│   ├── eval_runner.py                # Control/treatment API eval with LLM judge
│   ├── browser_eval.sh              # Claude.ai A/B testing via agent-browser
│   └── browser_eval_report.py       # Report generator for browser eval
├── pipeline/                         # Freshness monitoring (scrape, diff, notify)
├── launchd/                          # Schedule for freshness pipeline
├── docs/                             # Design docs, specs, analysis
├── knowledge-base/                   # Source docs from Anthropic documentation
└── monitoring/                       # Legacy monitoring setup
```

## License

MIT

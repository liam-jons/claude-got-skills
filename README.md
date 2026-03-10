# Claude Capabilities Awareness

A plugin and skill that gives Claude comprehensive, accurate knowledge about its capabilities across all platforms — Claude.ai, Claude Desktop, Claude Code, CoWork, and the API.

## Why this skill exists

Claude's training data has a cutoff. New features — adaptive thinking, dynamic filtering, fast mode, the memory tool, agent teams, the skills ecosystem, and more — ship faster than training data updates. Without this skill, Claude may give outdated or vague answers about what it can do.

With this plugin installed, Claude has capabilities knowledge injected at every session start (via a SessionStart hook), plus an on-demand skill for deeper questions. Claude can accurately recommend the right model for a workload, explain how capabilities compose, suggest the right extension pattern for a user's platform, and cite specific API parameters and headers.

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

**Claude Code (full plugin — recommended, always-on capabilities + on-demand skill):**
```
/plugin marketplace add claude-got-skills/skills
/plugin install claude-got-skills@claude-got-skills
```

**Claude Code (skill only — on-demand, no SessionStart hook):**
```bash
npx skills add claude-got-skills/skills@assistant-capabilities
```

**Claude.ai / Claude Desktop (skill only):**
1. Download the skill as a ZIP file
2. Go to Settings > Capabilities > Skills
3. Click "Upload skill" and select the ZIP

## Eval results (v2.3.0)

Evaluated against a baseline (no skill) across 43 test prompts in 8 categories using Haiku 4.5 (no web search). Accuracy scores shown (0–7 scale).

| Category | Tests | Control | Tier 1 | Tier 1 Lift | Full Skill | Full Lift |
|----------|-------|---------|--------|-------------|------------|-----------|
| Architecture Decisions | 3 | 1.67 | 3.00 | +80% | 3.33 | **+100%** |
| Can Claude Do X | 5 | 2.40 | 2.60 | +8% | 4.20 | **+75%** |
| Implementation Guidance | 8 | 2.12 | 4.25 | +100% | 4.62 | **+118%** |
| Model Selection | 1 | 1.00 | 5.00 | +400% | 6.00 | **+500%** |
| Extension Awareness | 8 | 1.88 | 2.88 | +53% | 4.25 | **+126%** |
| Hallucination Detection | 5 | 1.20 | 3.20 | +167% | 3.20 | **+167%** |
| Cross-Platform Awareness | 10 | 1.60 | 3.60 | +125% | 4.10 | **+156%** |
| **Negative (regression check)** | **3** | **4.67** | **5.00** | +7% | **4.33** | **-7% (noise)** |

**Tier 1** = `quick-reference.md` only (SessionStart hook, ~1.2K tokens, always-on). **Full Skill** = SKILL.md + references (on-demand). Tier 1 delivers 50–70% of the full skill's lift at 61% lower token cost.

## Structure

```
├── .claude-plugin/
│   ├── plugin.json                   # Plugin manifest (hooks, metadata)
│   └── marketplace.json              # Skill discovery for npx skills add
├── hooks/
│   └── hooks.json                    # SessionStart hook for always-on injection
├── scripts/
│   └── inject-capabilities.sh        # Injects quick-reference into session context
├── data/
│   └── quick-reference.md            # Condensed capabilities (~90 lines, Tier 1)
├── skills/
│   └── assistant-capabilities/
│       ├── SKILL.md                  # Full skill (~270 lines, Tier 2)
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
├── knowledge-base/                   # Source docs from Anthropic documentation
```

### Two-tier architecture

- **Tier 1 (always-on)**: `data/quick-reference.md` (~90 lines, ~1.2K tokens) injected via SessionStart hook into every session. Covers current models, capability composition patterns, platform availability, and key API parameters.
- **Tier 2 (on-demand)**: Full `SKILL.md` + 5 reference files (~2,700 lines) loaded by Claude when deeper detail is needed — API examples, agent SDK, tool configurations, migration guides.

## License

MIT

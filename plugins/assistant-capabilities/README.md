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
/plugin marketplace add liam-jons/claude-got-skills
/plugin install claude-got-skills@assistant-capabilities
```

**Claude Code (skill only — on-demand, no SessionStart hook):**
```bash
npx skills add liam-jons/claude-got-skills@assistant-capabilities
```

**Claude.ai / Claude Desktop (skill only):**
1. Download the skill as a ZIP file
2. Go to Settings > Capabilities > Skills
3. Click "Upload skill" and select the ZIP

### Two-tier architecture

- **Tier 1 (always-on)**: `data/quick-reference.md` (~90 lines, ~1.2K tokens) injected via SessionStart hook into every session. Covers current models, capability composition patterns, platform availability, and key API parameters.
- **Tier 2 (on-demand)**: Full `SKILL.md` + 5 reference files (~2,700 lines) loaded by Claude when deeper detail is needed — API examples, agent SDK, tool configurations, migration guides.

## License

MIT

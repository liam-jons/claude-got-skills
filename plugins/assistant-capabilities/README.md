# Assistant Capabilities

Always-on capabilities awareness for Claude Code — ensures Claude has accurate,
current knowledge of its own features across all platforms.

## What it does

Claude's training data has a cutoff. New features ship faster than training
data updates. This plugin ensures Claude has accurate, current knowledge of
its own capabilities — models, pricing, API features, extension patterns,
platform availability, and more.

## How it works

A two-tier architecture:

1. **Tier 1 (always-on):** A SessionStart hook injects a condensed reference
   (~90 lines) into every session. Zero-effort, automatic.
2. **Tier 2 (on-demand):** A full skill with 2,700+ lines across 6 reference
   files, loaded when deeper detail is needed.

## Install

```
/plugin marketplace add claude-got-skills/claude-got-skills
/plugin install claude-got-skills@assistant-capabilities
```

Or via [skills.sh](https://skills.sh):

```bash
npx skills add claude-got-skills/claude-got-skills@assistant-capabilities
```

## What it covers

- Current models, context windows, pricing
- API features (tool use, vision, PDFs, streaming, batch)
- Claude Code specifics (skills, hooks, plugins, MCP, agents)
- Platform availability (Claude.ai, Desktop, Code, CoWork)
- Extension patterns and when to use each
- Breaking changes and migration guidance

## License

MIT

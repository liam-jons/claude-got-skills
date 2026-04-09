# claude-got-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-plugins-blueviolet)]()
[![GitHub last commit](https://img.shields.io/github/last-commit/liam-jons/claude-got-skills)]()

Plugins and skills for Claude Code that extend what Claude can do — from
keeping its knowledge current to running full codebase quality reviews.

## Quick install

```
/plugin marketplace add liam-jons/claude-got-skills
```

Then install whichever plugins you need:

| Plugin | What it does | Install |
|--------|-------------|---------|
| **Assistant Capabilities** | Keeps Claude's knowledge of its own features accurate and current across all platforms | `/plugin install claude-got-skills@assistant-capabilities` |
| **Codebase Review** | Multi-agent codebase quality review with parallel analysis and adversarial verification | `/plugin install claude-got-skills@codebase-review` |

Skills can also be installed standalone via [skills.sh](https://skills.sh):

```bash
npx skills add liam-jons/claude-got-skills --skill assistant-capabilities
```

---

## Assistant Capabilities

Claude's training data has a cutoff. New features ship faster than training
data updates. This plugin ensures Claude has accurate, current knowledge of
its own capabilities — models, pricing, API features, extension patterns,
platform availability, and more.

**How it works:** A two-tier architecture injects a condensed reference (~90
lines) into every session via a SessionStart hook, with a full on-demand skill
(2,700+ lines across 6 reference files) loaded when deeper detail is needed.

**Evaluated results:** Tested against a baseline (no skill) across 43 prompts
using Haiku 4.5. The always-on tier delivers +80-167% accuracy lift across
categories; the full skill delivers +75-500% lift.

| Category | Baseline | With Plugin | Lift |
|----------|----------|-------------|------|
| Architecture Decisions | 1.67 | 3.33 | +100% |
| Implementation Guidance | 2.12 | 4.62 | +118% |
| Cross-Platform Awareness | 1.60 | 4.10 | +156% |
| Hallucination Detection | 1.20 | 3.20 | +167% |

See the [full skill documentation](plugins/assistant-capabilities/skills/assistant-capabilities/SKILL.md) for
what it covers.

---

## Codebase Review

Runs a 6-wave review of your entire codebase using parallel analysis agents:

```
Reconnaissance  -->  Parallel Review (N agents)  -->  Triage  -->  Verification  -->  Report  -->  Specs
                     + Pattern Checker
                     + Test Integrity Checker
                     + Silent Failure Hunter
```

1. **Reconnaissance** — measures the codebase, excludes generated/bundled files,
   runs deterministic tools (ESLint, tsc, ast-grep), captures test baseline,
   characterises the API surface (DB libraries, route inventory, composite
   routes, canonical remediation patterns, helper dependencies), calculates
   optimal partitions
2. **Parallel review** — spawns N scope-partitioned agents + 1 cross-cutting
   pattern checker + optional test integrity checker + optional silent-failure
   hunter (auto-activates when ≥5 API routes and a DB library are detected).
   All agents receive the shared test baseline.
3. **Triage** — deduplicates and ranks findings by severity and confidence
   using a three-way subsumption rule (silent-failure-hunter > pattern-checker
   > scope agents for their respective pattern domains)
4. **Verification** — adversarially tries to disprove each Critical/High finding
5. **Final report** — ranked, verified report with machine-readable JSON output
6. **Spec generation** — produces fix specifications with automatic verification,
   file overlap matrix, dependency graph, and implementation wave planning

**What it finds:** Bugs, silent failures (9 pattern types across TypeScript,
Python, and Go — including Supabase `{ data }` destructure drops, mutation
discarding, resolver null conflation, fan-out endpoints without warnings
envelopes, and helper-level cascades), security vulnerabilities, error
swallowing, race conditions, architectural smells, systemic anti-patterns,
and tests that pass but validate incorrect behaviour.

**Silent-failure detection** (v1.6.0+): Gold-standard validated against the
Knowledge Hub S151 audit — catches all 4 Critical findings plus 161 H7.a
pattern instances (6.4× the target recall). See the
[silent-failure playbook](plugins/codebase-review/references/silent-failure-playbook.md)
for the full heuristic catalogue and remediation templates.

**What it costs:** On a Claude Max subscription, a review of a ~100K-line
codebase takes approximately 15-20 minutes using 4-8 review agents + 1-3
verification agents. The `--thorough` flag roughly doubles this for higher
finding coverage.

See the [full plugin documentation](plugins/codebase-review/README.md) for
installation, usage, and output details.

---

## Structure

```
.claude-plugin/
  marketplace.json            # Marketplace catalogue
plugins/
  assistant-capabilities/     # Capabilities awareness plugin
    .claude-plugin/plugin.json
    hooks/                    # SessionStart hook (capabilities injection)
    scripts/                  # Hook scripts
    data/                     # Condensed capabilities reference (Tier 1)
    skills/
      assistant-capabilities/ # Full capabilities skill (Tier 2)
  codebase-review/            # Multi-agent codebase review plugin
    agents/                   # 7 agent definitions (codebase-reviewer,
                              #   pattern-checker, review-verifier,
                              #   review-synthesizer, spec-writer,
                              #   test-integrity-checker, silent-failure-hunter)
    commands/                 # Slash command
    references/               # ast-grep starter rules (incl. silent-failures/
                              #   subdir with 10 rules + fixtures) and the
                              #   silent-failure-playbook.md reference
```

## License

MIT

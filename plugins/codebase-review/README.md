# Codebase Review Plugin

Full codebase quality review using parallel analysis agents with adversarial
verification. Produces a structured findings report ranked by severity and
confidence.

## What it does

Runs a multi-wave review of your entire codebase:

1. **Reconnaissance** — measures the codebase, runs deterministic tools (ESLint,
   tsc, ast-grep), identifies hotspots, calculates optimal agent partitions
2. **Parallel review** — spawns N scope-partitioned agents (sized to your
   codebase) that hunt for bugs, bad patterns, security issues, and
   architectural smells
3. **Triage** — deduplicates and ranks all findings
4. **Verification** — spawns targeted agents that adversarially try to disprove
   each Critical/High finding against the actual code
5. **Final report** — produces a ranked, verified report in
   `.planning/reviews/YYYY-MM-DD/REVIEW-REPORT.md`

## Installation

### From local path

```bash
# Symlink the plugin into your local marketplace
ln -s /path/to/codebase-review-plugin \
  ~/.claude/plugins/marketplaces/local/plugins/codebase-review
```

Then add it to your local marketplace manifest
(`~/.claude/plugins/marketplaces/local/marketplace.json`) and enable it in
Claude Code settings, or use `/plugin` to install from the marketplace.

### From a git repository

If published to a git repo, install via the plugin marketplace or clone and
symlink as above.

After installation, run `/reload-plugins` to activate.

## Usage

```
/codebase-review
```

No configuration required. The plugin adapts agent count to your codebase size.

## Optional: project check files

If your project has `.claude/checks/*.md` files, the review agents will use
them as supplementary review standards. These are not required — the plugin
has a comprehensive built-in review brief covering bugs, patterns, security,
and architecture.

## Optional: ast-grep rules

The plugin includes a starter set of ast-grep rules for common TypeScript/React
issues. If `ast-grep` is installed, these run during the reconnaissance wave.
Copy `references/ast-grep-starter-rules/` to your project root and rename to
`rules/` to use them, or create your own `sgconfig.yml`.

## Output

All findings are written to `.planning/reviews/YYYY-MM-DD/`:

| File | Contents |
|------|----------|
| `partitions.md` | How the codebase was divided across agents |
| `deterministic-findings.md` | ESLint, tsc, ast-grep output |
| `scope-N-findings.md` | Raw findings from each review agent |
| `triage-findings.md` | Deduplicated and ranked findings |
| `verification-N.md` | Verification verdicts for Critical/High findings |
| `REVIEW-REPORT.md` | Final report — the one you read |

## How many agents?

The plugin measures your codebase and calculates the optimal number of review
agents. Each agent gets ~300-400K tokens of source code, leaving ~600K tokens
of context for deep analysis. Rough guide:

| Codebase size | Review agents | Verification agents | Total |
|---------------|--------------|--------------------:|------:|
| <30K lines | 2-3 | 1-2 | 4-6 |
| 30-80K lines | 4-5 | 2-3 | 7-9 |
| 80-150K lines | 6-7 | 3-5 | 10-13 |
| 150K+ lines | 8-12 | 4-6 | 13-19 |

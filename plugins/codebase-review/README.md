# Codebase Review Plugin

Full codebase quality review using parallel analysis agents with adversarial
verification. Produces a structured findings report ranked by severity and
confidence.

## What it does

Runs a multi-wave review of your entire codebase:

1. **Reconnaissance** — measures the codebase, auto-excludes generated/bundled
   files from token estimation, runs deterministic tools (ESLint, tsc, ast-grep),
   captures a test failure baseline, calculates optimal agent partitions
2. **Parallel review** — spawns N scope-partitioned agents (sized to your
   codebase) that hunt for bugs, bad patterns, security issues, and
   architectural smells. All agents receive the shared test baseline.
   Optionally includes a test integrity checker and, for projects with
   API routes + a DB library, a silent-failure hunter that walks route
   handlers and their `lib/` helpers for 9 silent-failure patterns
   (Supabase destructure drops, mutation-discarded, resolver null
   conflation, fan-out-without-envelope, and universal loop/catch
   patterns in TS, Python, and Go).
3. **Triage** — deduplicates and ranks all findings. Pattern-checker findings
   automatically subsume individual scope findings for the same systemic issue.
4. **Verification** — spawns targeted agents that adversarially try to disprove
   each Critical/High finding against the actual code
5. **Final report** — produces a ranked, verified report in
   `.planning/reviews/YYYY-MM-DD/REVIEW-REPORT.md`
6. **Spec generation** — produces structured fix specifications with automatic
   spec verification (cross-references line numbers and code against the
   codebase), file overlap matrix, dependency graph, and implementation wave
   planning (max 5 work packages per wave)

## Requirements

- **Claude Code** (Anthropic's CLI tool)
- **Claude Opus and Sonnet access** — the orchestrator and judgment-heavy
  subagents (synthesizer, verifier, spec-writer) use Opus; parallel scanning
  subagents (reviewer, pattern-checker, silent-failure-hunter,
  test-integrity-checker) use Sonnet. All run at `effort: high`.
  If `CLAUDE_CODE_SUBAGENT_MODEL` is set in your settings, it overrides the
  per-agent frontmatter — unset it to let the plugin's model mix apply.

### What to expect

The plugin spawns multiple parallel subagents (typically 4-8 review agents +
1 pattern checker + 1-3 verification agents) across 6 sequential waves. A
review of a ~100K-line codebase takes approximately 15-20 minutes and uses
significant context across all agents. On a Claude Max subscription, this
counts toward your usage. On API billing, costs scale with codebase size and
agent count.

The `--thorough` flag roughly doubles both time and usage by running two
passes with different partition strategies.

## Installation

### From the claude-got-skills marketplace

```
/plugin marketplace add liam-jons/claude-got-skills
/plugin install claude-got-skills@codebase-review
```

### From a local clone

```bash
git clone https://github.com/liam-jons/claude-got-skills.git
cd claude-got-skills
# The plugin is at plugins/codebase-review/
```

Then in Claude Code:

```
/plugin install /path/to/skills/plugins/codebase-review
```

After installation, run `/reload-plugins` to activate.

## Usage

```
/codebase-review
```

No configuration required. The plugin adapts agent count to your codebase size.

**Note:** Depending on your Claude Code version and plugin resolution, you may
need to use the fully-qualified command name: `/codebase-review:codebase-review`.

### Optional flags

Add these to your invocation message (e.g., "/codebase-review --verify-all"):

| Flag | Effect |
|------|--------|
| `--verify-all` | Send Medium findings (not just Critical/High) to adversarial verification. Increases cost ~30%. |
| `--thorough` | Two-pass review with different partition strategies. Roughly doubles cost but captures ~80% of findings vs ~65% single-pass. |
| `--test-integrity` | Analyse test suites for tests that pass but validate incorrect behaviour (AI-modified tests that codify bugs, mock the system under test, or weaken assertions). |
| `--specs` | Generate structured fix specifications from Critical/High findings. Produces work packages with root cause analysis, fix instructions with code, and verification steps. Can also run standalone against a previous review's findings.json. |

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
| `test-baseline.md` | Pre-existing test failures (shared with all agents) |
| `scope-N-findings.md` | Raw findings from each review agent |
| `pattern-checker-findings.md` | Cross-cutting pattern analysis findings |
| `test-integrity-findings.md` | Test integrity analysis (with `--test-integrity`) |
| `triage-findings.md` | Deduplicated and ranked findings |
| `verification-N.md` | Verification verdicts for Critical/High findings |
| `REVIEW-REPORT.md` | Final report — the one you read |
| `findings.json` | Machine-readable findings for programmatic consumption |
| `specs/INDEX.md` | Work package index with file overlap matrix and implementation waves |
| `specs/VERIFICATION.md` | Spec verification results (line number/code accuracy) |
| `specs/*.md` | Fix specifications per work package (with `--specs`) |

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

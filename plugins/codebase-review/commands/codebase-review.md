---
allowed-tools:
  - Agent
  - Bash
  - Glob
  - Grep
  - Read
  - Write
description: Run a comprehensive codebase quality review with parallel agents
model: opus
---

# Codebase Review

Run a full quality review of the codebase using parallel analysis agents with
adversarial verification. Adapts agent count to codebase size.

## Process

Follow these waves precisely. Each wave must complete before the next begins.

---

### Wave 1: Reconnaissance

This wave runs in the orchestrator (you). Do NOT spawn agents for this wave.

**1a. Create output directory**

```bash
REVIEW_DATE=$(date +%Y-%m-%d)
mkdir -p .planning/reviews/$REVIEW_DATE
```

Store this path as REVIEW_DIR for all subsequent steps.

**1b. Measure the codebase**

Run these commands to understand the codebase size and shape. Adapt file
extensions to the project (the examples below cover TypeScript/JavaScript/Python
projects — add or remove extensions as appropriate):

```bash
# Detect source directories (skip node_modules, .next, dist, build, vendor, .git)
find . -type d -maxdepth 1 \
  -not -name node_modules -not -name .next -not -name dist \
  -not -name build -not -name vendor -not -name .git \
  -not -name __pycache__ -not -name .planning -not -name '.*' \
  | sort
```

For each source directory found, count files, lines, and estimate tokens:

```bash
# Per-directory measurement
for dir in {detected source directories}; do
  files=$(find "$dir" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.css" -o -name "*.rs" -o -name "*.go" \) 2>/dev/null | grep -v node_modules | wc -l)
  chars=$(find "$dir" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.css" -o -name "*.rs" -o -name "*.go" \) 2>/dev/null | grep -v node_modules | xargs cat 2>/dev/null | wc -c)
  tokens=$((chars / 4))
  echo "$dir: $files files, $tokens estimated tokens"
done
```

```bash
# Large files (>500 lines) — these need focused attention
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.rs" -o -name "*.go" \) \
  -not -path "*/node_modules/*" -not -path "*/.next/*" -not -path "*/dist/*" \
  | xargs wc -l 2>/dev/null | sort -rn | awk '$1 > 500 && !/total$/ {print}'
```

```bash
# Recent churn — files changed in last 30 days (highest bug probability)
git log --since="30 days ago" --name-only --pretty=format: 2>/dev/null \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -30
```

```bash
# Markers indicating known issues
grep -rn "TODO\|FIXME\|HACK\|XXX\|BUG\|WARN" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.rs" --include="*.go" \
  . 2>/dev/null | grep -v node_modules | wc -l
```

**1c. Run deterministic tools**

Run whichever of these are available in the project. Capture output for review
agents. These run in parallel:

```bash
# ESLint (JS/TS projects)
npx eslint . 2>&1 | tail -100
# or: bun lint 2>&1 | tail -100
```

```bash
# TypeScript type check
npx tsc --noEmit 2>&1 | tail -100
# or: bunx tsc --noEmit 2>&1 | tail -100
```

```bash
# ast-grep (if sgconfig.yml or rules/ directory exists)
if [ -f sgconfig.yml ] || [ -d rules ]; then
  ast-grep scan 2>/dev/null | head -200
elif command -v ast-grep &>/dev/null; then
  # Use the plugin's starter rules if no project rules exist
  echo "No project ast-grep rules found. Using starter rules from plugin references."
  # Run inline rules for critical patterns
  ast-grep scan --inline-rules "id: empty-catch
language: typescript
rule:
  kind: catch_clause
  has:
    kind: statement_block
    not:
      has:
        kind: expression_statement
    stopBy: end" . 2>/dev/null | head -50
fi
```

```bash
# Dead code detection (if available)
npx knip --no-progress 2>&1 | tail -50
```

**1d. Check for project review standards**

```bash
# Project-specific check files
ls .claude/checks/*.md 2>/dev/null
```

```bash
# REVIEW.md (Anthropic convention)
if [ -f REVIEW.md ]; then cat REVIEW.md; fi
```

```bash
# CLAUDE.md (for project context)
if [ -f CLAUDE.md ]; then head -100 CLAUDE.md; fi
```

Read any check files found. These become supplementary context for review agents.

**1e. Calculate partitions**

Using the measurements from 1b, partition the codebase into N scopes. Rules:

- **Target: ~300-400K estimated tokens per agent** (leaves ~600K context for
  analysis overhead, reasoning, and cross-referencing)
- Keep directory groups together where possible
- Split directories that exceed 400K tokens on their own (e.g. split
  `components/` into domain vs UI subgroups)
- Ensure every file >500 lines is explicitly listed in its agent's scope
  so it gets deep attention
- Agent count guide:
  - <30K lines: 2-3 agents
  - 30-80K lines: 4-5 agents
  - 80-150K lines: 6-7 agents
  - 150K+ lines: 8-12 agents
- Include test directories ONLY if the user has explicitly requested test
  review. By default, focus on production code.

**1f. Write reconnaissance output**

Write two files:

1. `$REVIEW_DIR/partitions.md` — the partition plan showing each agent's scope,
   estimated tokens, large files, and description
2. `$REVIEW_DIR/deterministic-findings.md` — all ESLint, tsc, ast-grep, knip
   output (so review agents can avoid re-flagging)

---

### Wave 2: Parallel Review

Spawn N `codebase-reviewer` agents using the Agent tool. ALL agents MUST be
launched in a SINGLE message with `run_in_background: true` to maximise
parallelism.

Each agent receives this prompt:

```
You are review agent {N} of {total}.

## Your Scope
{list of directories and/or specific files from the partition plan}

## Large Files Requiring Deep Analysis
{files >500 lines in this scope — read these in full}

## Recent Churn (last 30 days)
{files with recent changes in this scope — higher bug probability}

## Known Issues — DO NOT re-flag these
{relevant deterministic findings for files in this scope}

## Project Standards (supplementary — check these in addition to the built-in review brief)
{contents of any .claude/checks/ files and REVIEW.md, or "None found" if no project standards exist}

## Output
Write your findings to: {REVIEW_DIR}/scope-{N}-findings.md
Use the finding format defined in your agent instructions.
```

Use `subagent_type: "codebase-reviewer"` for each agent.

After launching all agents, wait for ALL to complete. Then verify:

```bash
ls -la $REVIEW_DIR/scope-*-findings.md | wc -l
# Should match the number of agents launched
```

Read the header of each findings file to get the counts. If any agent failed
to write output, note it as a gap.

---

### Wave 3: Triage

Spawn 1 `review-synthesizer` agent with this prompt:

```
## Task: Triage review findings

## Input Files
{list all scope-N-findings.md paths that were successfully written}

## Deterministic Findings
{path to deterministic-findings.md}

## Codebase Context
- Total source files: {N}
- Total source lines: {N}
- Review agents used: {N}
- Scopes: {list of scope descriptions}

## Output
Write deduplicated, ranked findings to: {REVIEW_DIR}/triage-findings.md

## Instructions
1. Read ALL scope findings files
2. Deduplicate — merge findings about the same issue across scopes
3. Rank by severity then confidence
4. Remove any findings that duplicate deterministic tool output
5. Separate findings into two groups:
   - VERIFY: all Critical and High findings (these go to verification)
   - ACCEPTED: all Medium and Low findings (these go directly to the report)
6. Write the triage output with both groups clearly separated
```

Use `subagent_type: "review-synthesizer"` for this agent.

---

### Wave 4: Verification

Read `$REVIEW_DIR/triage-findings.md` and extract the VERIFY group (Critical
and High findings).

Group the findings by file proximity — findings in the same or nearby files
should go to the same verification agent. Target 3-6 findings per verification
agent.

Spawn M `review-verifier` agents in parallel (all in a SINGLE message with
`run_in_background: true`). Each receives:

```
## Task: Adversarially verify these findings

## Findings to Verify
{3-6 findings from the triage output, with full detail including file paths and evidence}

## Instructions
For EACH finding:
1. Read the actual code cited — not just the snippet, but the full file for surrounding context
2. Read callers and callees — trace how this code is actually used
3. Look for guards, defensive code, or framework guarantees that make the finding moot
4. Check if test coverage exists for this specific path
5. Actively try to DISPROVE the finding — look for reasons it's wrong

For each finding, render a verdict:
- **CONFIRMED** — the issue is real, reachable, and impactful. Strengthen the evidence.
- **DOWNGRADED** — real issue but less severe than claimed. Explain why.
- **DISMISSED** — false positive. Explain what defensive code or guarantee disproves it.

## Output
Write verdicts to: {REVIEW_DIR}/verification-{N}.md
```

Use `subagent_type: "review-verifier"` for each agent.

Wait for all verification agents to complete.

---

### Wave 5: Final Report

Spawn 1 `review-synthesizer` agent (reuse the same agent type) with this prompt:

```
## Task: Produce the final review report

## Verified Findings
{list all verification-N.md paths}

## Accepted Findings (Medium/Low — already accepted, no verification needed)
{path to triage-findings.md — use the ACCEPTED group}

## Deterministic Findings Summary
{path to deterministic-findings.md}

## Codebase Context
- Total source files: {N}
- Total source lines: {N}
- Review agents: {N}
- Verification agents: {M}
- Date: {YYYY-MM-DD}

## Instructions
1. Read all verification verdict files
2. Include only CONFIRMED and DOWNGRADED findings (discard DISMISSED)
3. Combine with ACCEPTED findings from triage
4. Produce the final REVIEW-REPORT.md using the report template in your agent instructions
5. Write to: {REVIEW_DIR}/REVIEW-REPORT.md
```

---

### Present Results

Read `$REVIEW_DIR/REVIEW-REPORT.md` and present to the user:

1. **Executive summary** — one paragraph on overall codebase health
2. **Finding counts** by severity and category
3. **Critical findings** — show full detail for any verified Critical issues
4. **Top 5 High findings** — brief summary of each
5. **Path to full report** for Medium/Low findings

Do NOT dump the entire report into the conversation. The user can read the
file for full detail.

If zero findings survived verification, congratulate the user — that's a
genuinely healthy codebase.

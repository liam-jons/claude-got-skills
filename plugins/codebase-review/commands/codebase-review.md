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
effort: high
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

For each source directory found, count files, lines, and estimate tokens.

**First, identify and exclude generated files** — these inflate token estimates
and waste agent context windows:

```bash
# Find generated/bundled files to exclude (>100KB, or matching generated patterns)
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
  -o -name "*.py" -o -name "*.css" -o -name "*.rs" -o -name "*.go" \) \
  -not -path "*/node_modules/*" -not -path "*/.next/*" -not -path "*/dist/*" \
  -not -path "*/build/*" 2>/dev/null \
  | while read f; do
    size=$(wc -c < "$f" 2>/dev/null)
    if [ "$size" -gt 102400 ]; then echo "$f ($((size/1024))KB)"; fi
  done

# Also flag files matching generated patterns
find . -type f \( -name "*-bundle*" -o -name "*.generated.*" -o -name "*.min.*" \
  -o -name "*.bundle.*" -o -name "chunk-*" -o -name "*.chunk.*" \) \
  -not -path "*/node_modules/*" 2>/dev/null
```

Store these paths as EXCLUDED_FILES. Report them:

```
Excluding {N} generated/bundled files from token estimation:
  {file} ({size}KB) — over 100KB threshold
  {file} — matches generated file pattern
```

Then measure per-directory, excluding the generated files:

```bash
# Per-directory measurement (excluding generated files)
for dir in {detected source directories}; do
  files=$(find "$dir" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.css" -o -name "*.rs" -o -name "*.go" \) 2>/dev/null | grep -v node_modules | grep -v -F -f <(echo "$EXCLUDED_FILES") | wc -l)
  chars=$(find "$dir" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.css" -o -name "*.rs" -o -name "*.go" \) 2>/dev/null | grep -v node_modules | grep -v -F -f <(echo "$EXCLUDED_FILES") | xargs cat 2>/dev/null | wc -c)
  tokens=$((chars / 4))
  echo "$dir: $files files, $tokens estimated tokens"
done
```

**Note:** If `grep -v -F -f` is unavailable, manually exclude the identified
files from the `find` command using `-not -name` flags.

```bash
# Large files (>500 lines) — these need focused attention
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.rs" -o -name "*.go" \) \
  -not -path "*/node_modules/*" -not -path "*/.next/*" -not -path "*/dist/*" \
  | xargs wc -l 2>/dev/null | sort -rn | grep -v 'total$' | awk '$1 > 500'
```

**Note:** Avoid complex awk expressions — macOS BSD awk has different syntax
from GNU awk. Prefer `grep` + simple `awk`, or pipe through `while read` loops.

```bash
# Recent churn — files changed in last 30 days (highest bug probability)
git log --since="30 days ago" --name-only --pretty=format: 2>/dev/null \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -30
```

```bash
# Recent bug-fix commits — files with recent fixes have higher probability of related bugs
git log --since="30 days" --oneline --all 2>/dev/null \
  | grep -i "fix\|bug\|patch\|hotfix" | head -20
```

Pass both the churn data and recent bug-fix commits to review agents as context
for prioritising which files to read deeply.

```bash
# Markers indicating known issues
grep -rn "TODO\|FIXME\|HACK\|XXX\|BUG\|WARN" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.rs" --include="*.go" \
  . 2>/dev/null | grep -v node_modules | wc -l
```

**1b-extra. Detect test infrastructure (if `--test-integrity` is active)**

If the `--test-integrity` flag is present, OR if test files comprise >10% of
the codebase by file count, detect the test infrastructure:

```bash
# Find test files and framework
find . -type f \( -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.test.js" \
  -o -name "*.spec.ts" -o -name "*.spec.tsx" -o -name "*.spec.js" \
  -o -name "*.test.py" -o -name "*_test.py" -o -name "*_test.go" \) \
  -not -path "*/node_modules/*" -not -path "*/.next/*" 2>/dev/null | wc -l
```

```bash
# Identify test framework and config
ls vitest.config.* jest.config.* pytest.ini pyproject.toml setup.cfg 2>/dev/null
```

```bash
# Find test directories
find . -type d \( -name "__tests__" -o -name "test" -o -name "tests" -o -name "spec" \) \
  -not -path "*/node_modules/*" 2>/dev/null
```

```bash
# Find mock helpers (essential context for Pattern 2 and 6 detection)
find . -type f \( -name "*mock*" -o -name "*fixture*" -o -name "*helper*" \) \
  -path "*test*" -not -path "*/node_modules/*" 2>/dev/null
```

Store the test directory paths, test file count, test framework, and mock
helper paths for the test integrity checker agent.

**1b-baseline. Capture test failure baseline**

Run the project's test suite once to establish a baseline of pre-existing
failures. This prevents agents from reporting different counts of "pre-existing
test failures" because each ran the suite independently.

```bash
# Detect and run the test suite (adapt to the project)
if [ -f "vitest.config.ts" ] || [ -f "vitest.config.js" ]; then
  npx vitest run --reporter=verbose 2>&1 | tail -80
elif [ -f "jest.config.ts" ] || [ -f "jest.config.js" ]; then
  npx jest --verbose 2>&1 | tail -80
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
  python -m pytest --tb=short 2>&1 | tail -80
elif [ -f "Cargo.toml" ]; then
  cargo test 2>&1 | tail -80
elif [ -f "go.mod" ]; then
  go test ./... 2>&1 | tail -80
fi
```

Parse the output and record in `$REVIEW_DIR/test-baseline.md`:

```markdown
# Test Baseline

**Date:** {YYYY-MM-DD}
**Framework:** {vitest|jest|pytest|cargo|go}
**Total tests:** {N}
**Passing:** {N}
**Failing:** {N}
**Skipped:** {N}

## Pre-existing Failures

{List each failing test name and its error summary, or "None" if all pass}
```

Pass the path to `test-baseline.md` to ALL Wave 2 agents (scope reviewers,
pattern checker, and test integrity checker) so they can distinguish new
failures from existing ones without re-running the suite.

If the test suite fails to run (missing dependencies, no test command found),
note "Test baseline: unavailable — {reason}" and proceed without it.

**1b-api. API surface characterisation (for silent-failure-hunter)**

This step detects whether the codebase has an API surface (routes + a DB
library) and writes `api-surface.md` so the Wave 2 silent-failure-hunter
agent knows whether to activate and what to scan.

```bash
# Detect DB libraries (check manifests first, fall back to source grep)
DB_LIBS=""
[ -f package.json ] && grep -q '"@supabase/supabase-js"' package.json 2>/dev/null && DB_LIBS="$DB_LIBS supabase"
[ -f package.json ] && grep -q '"@prisma/client"\|"prisma"' package.json 2>/dev/null && DB_LIBS="$DB_LIBS prisma"
[ -f package.json ] && grep -q '"drizzle-orm"' package.json 2>/dev/null && DB_LIBS="$DB_LIBS drizzle"
[ -f package.json ] && grep -q '"typeorm"' package.json 2>/dev/null && DB_LIBS="$DB_LIBS typeorm"
[ -f package.json ] && grep -q '"mongoose"\|"mongodb"' package.json 2>/dev/null && DB_LIBS="$DB_LIBS mongo"
[ -f requirements.txt ] && grep -q 'supabase' requirements.txt 2>/dev/null && DB_LIBS="$DB_LIBS supabase-py"
[ -f requirements.txt ] && grep -q 'sqlalchemy\|SQLAlchemy' requirements.txt 2>/dev/null && DB_LIBS="$DB_LIBS sqlalchemy"
[ -f requirements.txt ] && grep -q 'django' requirements.txt 2>/dev/null && DB_LIBS="$DB_LIBS django"
[ -f pyproject.toml ] && grep -q 'supabase' pyproject.toml 2>/dev/null && DB_LIBS="$DB_LIBS supabase-py"
[ -f pyproject.toml ] && grep -q 'sqlalchemy\|SQLAlchemy' pyproject.toml 2>/dev/null && DB_LIBS="$DB_LIBS sqlalchemy"
[ -f go.mod ] && grep -q 'gorm.io/gorm\|jackc/pgx' go.mod 2>/dev/null && DB_LIBS="$DB_LIBS go-db"
DB_LIBS=$(echo "$DB_LIBS" | xargs)  # trim whitespace; empty if none
```

```bash
# Detect API routes (framework-aware) — write paths to a temp file
API_ROUTES_FILE=$REVIEW_DIR/api-routes.txt
> $API_ROUTES_FILE

# Next.js app router
find . -type f \( -name "route.ts" -o -name "route.tsx" -o -name "route.js" -o -name "route.jsx" \) \
  -path "*/api/*" -not -path "*/node_modules/*" -not -path "*/.next/*" 2>/dev/null >> $API_ROUTES_FILE

# Next.js pages router
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  -path "*/pages/api/*" -not -path "*/node_modules/*" 2>/dev/null >> $API_ROUTES_FILE

# Express/Fastify — files containing router.get/post/etc
grep -rln 'router\.\(get\|post\|put\|patch\|delete\)\|app\.\(get\|post\|put\|patch\|delete\)' . \
  --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null \
  | grep -v node_modules >> $API_ROUTES_FILE

# FastAPI
grep -rln '@\(app\|router\)\.\(get\|post\|put\|patch\|delete\)' . \
  --include="*.py" 2>/dev/null | grep -v __pycache__ >> $API_ROUTES_FILE

# Flask
grep -rln '@\(app\|blueprint\)\.route' . --include="*.py" 2>/dev/null | grep -v __pycache__ >> $API_ROUTES_FILE

# Go net/http / chi
grep -rln 'http\.HandleFunc\|mux\.\(Get\|Post\|Handle\)\|chi\.Router' . \
  --include="*.go" 2>/dev/null >> $API_ROUTES_FILE

# Dedupe and count
sort -u -o $API_ROUTES_FILE $API_ROUTES_FILE
ROUTE_COUNT=$(wc -l < $API_ROUTES_FILE | tr -d ' ')
```

```bash
# Identify composite routes (≥3 DB query call sites) — line-count based
# Note: grep -c counts matching LINES, not individual matches, so this
# under-counts when multiple queries appear on one line. Conservative.
COMPOSITE_ROUTES_FILE=$REVIEW_DIR/composite-routes.txt
> $COMPOSITE_ROUTES_FILE
while IFS= read -r f; do
  [ -z "$f" ] && continue
  count=$(grep -c "await [a-zA-Z_]*\.from(\|await prisma\.\|await db\." "$f" 2>/dev/null || echo 0)
  if [ "$count" -ge 3 ]; then
    echo "$f ($count queries)" >> $COMPOSITE_ROUTES_FILE
  fi
done < $API_ROUTES_FILE
COMPOSITE_COUNT=$(wc -l < $COMPOSITE_ROUTES_FILE | tr -d ' ')
```

```bash
# Detect canonical remediation patterns in the target codebase
WARNINGS_EXEMPLAR=$(grep -rln 'warnings[[:space:]]*:[[:space:]]*string\[\]\|warnings[[:space:]]*:[[:space:]]*readonly string\[\]' . \
  --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v node_modules | head -1)
SB_WRAPPER=$(grep -rln 'from [\x27"]@*/*lib/supabase/safe[\x27"]\|export.*function sb<\|export.*function tryQuery' . \
  --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v node_modules | head -1)
RESULT_TYPE=$(grep -rln 'type Result<.*ok:[[:space:]]*true\|ok:[[:space:]]*false' . \
  --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v node_modules | head -1)
```

```bash
# Detect helper paths imported by routes (TypeScript/JavaScript only in v1.6.0)
HELPER_PATHS_FILE=$REVIEW_DIR/helper-paths.txt
> $HELPER_PATHS_FILE
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    *.ts|*.tsx|*.js|*.jsx)
      grep -oE "from ['\"]@?/?(lib|src/lib|utils)/[^'\"]+['\"]" "$f" 2>/dev/null \
        | sed -E "s/from ['\"]|['\"]//g" >> $HELPER_PATHS_FILE
      ;;
  esac
done < $API_ROUTES_FILE
sort -u -o $HELPER_PATHS_FILE $HELPER_PATHS_FILE
HELPER_COUNT=$(wc -l < $HELPER_PATHS_FILE | tr -d ' ')
```

**Determine activation.** Based on the detection results and any user flag
(`--silent-failures` / `--no-silent-failures`), decide the activation state:

- If user passed `--no-silent-failures`: `activation: SKIP (user override)`
- Else if user passed `--silent-failures`: `activation: ACTIVATE (forced by flag)`
- Else if `ROUTE_COUNT == 0`: `activation: SKIP (no API routes)`
- Else if `DB_LIBS` is empty: `activation: SKIP (no DB library)`
- Else if `ROUTE_COUNT < 5`: `activation: SKIP (below 5-route threshold)`
- Else: `activation: ACTIVATE (auto, {ROUTE_COUNT} routes, db={DB_LIBS})`

**Flag precedence:** `--no-silent-failures` > `--silent-failures` > auto.
If both flags are passed (user error), treat as `--no-silent-failures`
and emit a warning in orchestrator output.

**Write `$REVIEW_DIR/api-surface.md`** with this schema:

```markdown
# API Surface Characterisation

**Review date:** {YYYY-MM-DD}
**DB libraries detected:** [{space-separated list, or empty}]
**Languages:** [{typescript|python|go|...}]
**Total API routes:** {ROUTE_COUNT}
**Composite routes (≥3 DB queries):** {COMPOSITE_COUNT}
**Helper walk supported:** {true if any TS/JS routes, else false}

## Canonical Remediation Patterns

- **Warnings envelope exemplar:** `{WARNINGS_EXEMPLAR or None detected}`
- **Wrapper helper (sb/tryQuery):** `{SB_WRAPPER or None detected}`
- **Result<T, E> type:** `{RESULT_TYPE or None detected}`

## Helper Dependencies

{HELPER_COUNT} helpers imported from API routes:
{contents of helper-paths.txt, one per line}

## Activation Decision

silent-failure-hunter: **{ACTIVATE or SKIP (reason)}**

## Route Inventory

{contents of api-routes.txt, one per line — full absolute paths}

## Composite Route Details

{contents of composite-routes.txt — path and query count}
```

**Graceful degradation:** If any of the bash commands in this step fail
(non-zero exit, missing commands, filesystem errors), write a stub
`api-surface.md` with `activation: SKIP (reconnaissance failed)` plus
the stderr content, and continue to step 1c. Do NOT abort the review.

**1c. Run deterministic tools**

Run whichever of these are available in the project. Capture output for review
agents. These run in parallel.

**If any tool fails with permission/sandbox errors**, retry with
`dangerouslyDisableSandbox: true`. ESLint, tsc, and ast-grep need write access
to temp directories which the sandbox may block.

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
  # Use the plugin's bundled starter rules if no project rules exist.
  # The plugin ships rules in references/ast-grep-starter-rules/.
  # Copy them to a temp location and run ast-grep with that config.
  PLUGIN_RULES_DIR=$(find ~/.claude/plugins -path "*/codebase-review/references/ast-grep-starter-rules" -type d 2>/dev/null | head -1)
  if [ -n "$PLUGIN_RULES_DIR" ] && [ -d "$PLUGIN_RULES_DIR" ]; then
    TEMP_AST_DIR=$(mktemp -d)
    cp -r "$PLUGIN_RULES_DIR/rules" "$TEMP_AST_DIR/"
    cp "$PLUGIN_RULES_DIR/sgconfig.yml" "$TEMP_AST_DIR/"
    (cd "$TEMP_AST_DIR" && ast-grep scan --config sgconfig.yml "$(pwd -P)" 2>/dev/null | head -200)
    rm -rf "$TEMP_AST_DIR"
  else
    # Fallback: run inline rules for critical patterns
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
if [ -f CLAUDE.md ]; then cat CLAUDE.md; fi
```

Read any check files found. These become supplementary context for review agents.

**Extract CLAUDE.md gotchas:** If CLAUDE.md exists and contains a "Gotchas",
"Known Issues", "Pitfalls", or "Footguns" section (case-insensitive), extract
it in full. This will be passed to every review agent as "Known Risk Patterns"
so they can mechanically verify these documented issues are not present in their
scope. This converts probabilistic exploration into deterministic checking.

**1e. Calculate partitions**

Using the measurements from 1b, partition the codebase into N scopes. Exclude
all EXCLUDED_FILES (generated/bundled files identified in 1b) from agent scopes.
Rules:

- **Maximum: 300K estimated tokens per agent. This is a hard limit, not a
  guideline.** If any scope exceeds 300K tokens, split it further. A scope
  of 427K tokens will result in the agent reviewing only ~11% of its files.
- Keep directory groups together where possible
- Split directories that exceed 300K tokens on their own (e.g. split
  `components/` into domain vs UI subgroups, split `lib/` into cohesive
  subdomain groups)
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

**IMPORTANT: Wave 1 must fully complete before proceeding.** Ensure ALL
reconnaissance commands have finished successfully (including any retries for
failed deterministic tools). Do NOT launch Wave 2 agents in the same parallel
batch as any Wave 1 Bash commands — a failed Bash command in a parallel batch
will cancel all other tool calls in the same message, including correctly-running
agents.

---

### Wave 2: Parallel Review

Spawn N `codebase-reviewer` agents **plus 1 `pattern-checker` agent** using the
Agent tool. ALL agents MUST be launched in a SINGLE message with
`run_in_background: true` to maximise parallelism.

Each scope-partitioned review agent receives this prompt:

```
You are review agent {N} of {total}.

## Your Scope
{list of directories and/or specific files from the partition plan}

## Large Files Requiring Deep Analysis
{files >500 lines in this scope — read these in full}

## Recent Churn (last 30 days)
{files with recent changes in this scope — higher bug probability}

## Recent Bug-Fix Commits
{output from git log bug-fix grep — files with recent fixes have higher probability of related bugs}

## Known Issues — DO NOT re-flag these
{relevant deterministic findings for files in this scope}

## Known Risk Patterns (from CLAUDE.md gotchas)
{extracted gotchas/pitfalls/footguns section from CLAUDE.md, or "None found" if no CLAUDE.md or no gotchas section.
Agents MUST verify these patterns are NOT present in their scope. Treat each gotcha as a mandatory check.}

## Project Standards
{actual content of .claude/checks/*.md files and REVIEW.md — read these files and paste their full content here,
or "None found" if no project standards exist. Do NOT leave this as a placeholder.}

## Test Baseline
{Path to test-baseline.md from Wave 1, or "Unavailable" if tests couldn't be run.
Do NOT re-run the test suite — use this baseline to distinguish pre-existing
failures from new issues you discover.}

## Output
Write your findings to: {REVIEW_DIR}/scope-{N}-findings.md
Use the finding format defined in your agent instructions.
```

Use `subagent_type: "codebase-reviewer"` for each scope agent.

**Pattern checker agent:** In addition to the scope-partitioned agents, spawn 1
`pattern-checker` agent with this prompt:

```
## Task: Cross-cutting pattern analysis

Run targeted grep/search patterns across the ENTIRE codebase to find systemic
issues that scope-partitioned agents miss (because each agent only sees a subset
of instances).

## Known Issues — DO NOT re-flag these
{deterministic findings from Wave 1}

## Known Risk Patterns (from CLAUDE.md gotchas)
{extracted gotchas — use these to generate additional search patterns}

## Test Baseline
{Path to test-baseline.md, or "Unavailable"}

## Output
Write your findings to: {REVIEW_DIR}/pattern-checker-findings.md
Use the same finding format as scope review agents.
```

Use `subagent_type: "pattern-checker"` for this agent.

**Test integrity checker agent (if `--test-integrity` is active):** In addition
to the above agents, spawn 1 `test-integrity-checker` agent with this prompt:

```
## Task: Test integrity analysis

Analyse the test suite for tests that pass but validate incorrect behaviour.
Focus on the 6 detection patterns defined in your agent instructions.

## Test Directory Structure
{test directories, test framework, test file count from Wave 1 reconnaissance}

## Mock Helpers
{paths to mock helper files identified in Wave 1 — read these first}

## Recent Churn (last 30 days)
{files with recent changes — co-modification detection focuses here}

## Recent Bug-Fix Commits
{git log output — commits with "fix" in message are high-signal for Pattern 4}

## Known Issues — DO NOT re-flag these
{deterministic findings from Wave 1}

## Test Baseline
{Path to test-baseline.md. Use this to distinguish pre-existing failures from
new issues. Do NOT re-run the full test suite.}

## Output
Write your findings to: {REVIEW_DIR}/test-integrity-findings.md
Use the finding format defined in your agent instructions, with the additional
Test Pattern and Production file fields.
```

Use `subagent_type: "test-integrity-checker"` for this agent.

**Silent-failure hunter agent (conditional on Wave 1 api-surface.md):**

Read `$REVIEW_DIR/api-surface.md` and check the "Activation Decision" line.
If it starts with `ACTIVATE`, spawn 1 `silent-failure-hunter` agent. If it
starts with `SKIP`, log the skip reason and do NOT spawn.

**The orchestrator inlines fields from `api-surface.md` into the hunter's
prompt.** The hunter does NOT re-read the file — it receives everything it
needs in the prompt. This keeps the agent's context tight.

```
## Task: Silent-failure detection across API routes and helpers

## DB Libraries
{comma-separated DB libraries from api-surface.md, e.g.: supabase, prisma}

## Languages
{comma-separated languages detected, e.g.: typescript, python}

## Total API Routes
{total_api_routes from api-surface.md}

## Composite Routes (≥3 DB queries — candidates for H-Composite check)
{full content of composite-routes.txt, or "None detected"}

## Canonical Remediation Patterns
{Full "Canonical Remediation Patterns" section from api-surface.md —
 warnings envelope exemplar, sb() wrapper path, Result<T,E> path}

## Helper Paths (walk these alongside routes — for H-Helper-Cascade)
{full content of helper-paths.txt, or "None"}

## Route Inventory
{full content of api-routes.txt — absolute paths, one per line}

## Heuristic Reference
The silent-failure-playbook.md ships with the plugin. Discover it via:
  find ~/.claude/plugins -path "*/codebase-review/references/silent-failure-playbook.md"
Read it in full before starting heuristic scans.

## Known Issues — DO NOT re-flag these
{full content of deterministic-findings.md}

## Test Baseline
{Path to test-baseline.md, or "Unavailable"}

## Output
Write your findings to: {REVIEW_DIR}/silent-failure-findings.md
Use the finding format defined in your agent instructions (Category:
Silent Failure + Pattern ID field).
```

Use `subagent_type: "silent-failure-hunter"` for this agent.

After launching all agents, report progress to the user as each agent completes
rather than waiting silently. Example: "Agent 3/6 complete (lib/ scope — found
8 issues)." This gives the user visibility during what can be a 15-20 minute
wait.

Once ALL agents have completed, verify:

```bash
ls -la $REVIEW_DIR/scope-*-findings.md $REVIEW_DIR/pattern-checker-findings.md $REVIEW_DIR/test-integrity-findings.md $REVIEW_DIR/silent-failure-findings.md 2>/dev/null | wc -l
# Should match: scope agents + 1 (pattern checker) + 1 (test integrity, if active) + 1 (silent-failure-hunter, if activated)
```

Read the header of each findings file to get the counts. If any agent failed
to write output, note it as a gap.

---

### Wave 3: Triage

Spawn 1 `review-synthesizer` agent with this prompt:

```
## Task: Triage review findings

## Input Files
{list all scope-N-findings.md, pattern-checker-findings.md, test-integrity-findings.md
(if test integrity checking was active), AND silent-failure-findings.md
(if silent-failure-hunter activated) paths that were successfully written}

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
1. Read ALL scope findings files (scope-*-findings.md, pattern-checker-findings.md,
   test-integrity-findings.md if present, silent-failure-findings.md if present).
2. Deduplicate — merge findings about the same issue across scopes.

   **Finding subsumption rules (apply in order):**

   a. **Silent-failure-hunter > pattern-checker** for Pattern IDs in
      {H7.a, H7.b, H-Resolver, H-Composite, H-Helper-Cascade}. When
      silent-failure-hunter flagged a finding with one of these pattern
      IDs, it is authoritative. Discard any pattern-checker finding on
      the same file referencing the same pattern.

   b. **Pattern-checker > scope agents** for systemic issues. When a
      pattern-checker finding identifies a systemic issue and scope
      agents flagged individual instances, keep ONLY the pattern-checker
      finding. Reference the scope findings as instances within it,
      merging any additional evidence. Do not keep subsumed scope
      findings as separate entries.

   c. **Silent-failure-hunter vs pattern-checker on H4/H5** (universal
      patterns): the hunter's critical rules forbid it from flagging
      generic H4/H5 patterns outside API route bodies, so this overlap
      should not occur. If it does, prefer the pattern-checker finding
      and log the violation in the triage notes.

   d. **Deduplicate by (file_path, line_range, pattern_id)** after
      applying rules a-c. Last wins within identical tuples.

3. Rank by severity then confidence
4. Remove any findings that duplicate deterministic tool output
5. Separate findings into two groups:
   - VERIFY: all Critical and High findings (these go to verification).
     If the user requested `--verify-all`, also include Medium findings.
   - ACCEPTED: remaining findings (these go directly to the report)
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

## Previous Report (for delta analysis)
{If a previous REVIEW-REPORT.md exists in an earlier date directory under .planning/reviews/,
provide its path here. Otherwise "None — first run."}

## Instructions
1. Read all verification verdict files
2. Include only CONFIRMED and DOWNGRADED findings (discard DISMISSED)
3. Combine with ACCEPTED findings from triage
4. Produce the final REVIEW-REPORT.md using the report template in your agent instructions
5. If a previous report was provided, add a "Delta from Previous Review" section
   highlighting NEW findings not present in the previous report and RESOLVED
   findings that appeared before but not in this run
6. Write to: {REVIEW_DIR}/REVIEW-REPORT.md
7. Also write a machine-readable JSON file to: {REVIEW_DIR}/findings.json
   containing all findings as an array of objects with fields: id, title,
   severity, category, confidence, file, lines, issue, impact, suggested_fix,
   verification_verdict (if applicable).
   For test integrity findings (category: "test-integrity"), also include:
   production_file, production_lines, test_pattern, test_pattern_name.
8. If test integrity findings are present, add a "Test Integrity Analysis"
   section to the report after the main findings, with:
   - Test files analysed count
   - Findings by detection pattern (P1-P6)
   - Systemic test issues (grouped findings sharing the same root cause)
   - Cross-reference to individual findings in the main severity-ranked list
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

After presenting results, proceed to Wave 6.

---

### Wave 6: Spec Generation

This wave generates fix specifications from review findings. It runs as an
interactive post-report step (after Present Results) or standalone via
the `--specs` flag.

**6a. Offer spec generation**

After presenting results, display:

First, read `$REVIEW_DIR/findings.json` and count findings by severity. Estimate
work packages as: `total findings / 3`, clamped to a minimum of the number of
distinct files referenced. Then display:

```
---

Would you like me to generate fix specifications for these findings?

Options:
1. Critical + High findings (default) — {N} findings → estimated {M} work packages
2. All findings — {N} findings → estimated {M} work packages
3. Custom — specify severities (e.g., "Critical+High+Medium")
4. No thanks

Pick an option or type severity levels:
```

If the user selects option 4 or declines, stop here.

**6b. Filter findings**

Read `$REVIEW_DIR/findings.json`. Filter to the selected severity levels.

If `$REVIEW_DIR/test-integrity-findings.json` also exists (from a test
integrity checker run), merge those findings into the set. Match
test-integrity findings with review findings that reference the same
production file — these belong in the same work package.

**6c. Group findings into work packages**

The orchestrator performs grouping directly (no agent needed). Apply these
heuristics in priority order:

1. **Shared root cause** — findings whose `suggested_fix` fields share >60%
   of significant tokens (excluding stop words, file paths, line numbers).
   Also group findings that reference the same CLAUDE.md gotcha. Additionally,
   findings with the same `category` whose `issue` text shares >50% of
   significant keywords indicate a shared root cause.
2. **Same file** — findings in the same file always group together regardless
   of category.
3. **Same directory + same category** — findings in the same directory with
   matching categories group together.
4. **Architectural theme** — findings with category `Architecture` or
   referencing the same architectural concept group into a single spec.
5. **Remaining singletons** — ungrouped findings become their own work package.

**Group size limits:** Maximum 6 findings per work package. If a group exceeds
6, split by severity (Critical+High in one, Medium+Low in another).

Sort groups by maximum severity (descending), then by finding count (descending).
Assign IDs: WP1, WP2, etc. Generate a filename slug from the group title.

Report the plan:

```
Grouped {N} findings into {M} work packages:

  WP1: {title} ({finding IDs}) — {N} files
  WP2: {title} ({finding IDs}) — {N} files
  ...

Spawning {M} spec-writer agents in parallel...
```

**6d. Spawn spec-writer agents**

Spawn M `spec-writer` agents in a SINGLE message with `run_in_background: true`.
Each agent receives this prompt:

```
You are spec-writer agent for work package {WP_ID}.

## Work Package: {title}

## Findings

{For each finding in the group, paste the full JSON object from findings.json
formatted as readable markdown:}

### {finding.id}: {finding.title}
- **Severity:** {finding.severity}
- **Category:** {finding.category}
- **Confidence:** {finding.confidence}
- **File:** `{finding.file}:{finding.lines}`
- **Verification:** {finding.verification_verdict}
- **Issue:** {finding.issue}
- **Impact:** {finding.impact}
- **Suggested fix:** {finding.suggested_fix}

{If finding.category is "test-integrity":}
- **Source:** test-integrity-checker
- **Test file:** `{finding.file}:{finding.lines}` (for test-integrity findings, `file` is the test file)
- **Production file:** `{finding.production_file}:{finding.production_lines}`
- **Test pattern:** {finding.test_pattern} — {finding.test_pattern_name}
- Note: The spec-writer should extract "tested behaviour" and "correct behaviour"
  from the finding's `issue` and `suggested_fix` fields when writing the Test
  Correction section.

## Codebase Context

{Executive summary from REVIEW-REPORT.md}

## Known Gotchas

{Relevant CLAUDE.md gotchas, if any findings reference documented patterns}

## Reference Implementation

{If the codebase has a correct example of the pattern these findings violate,
provide the file path so the agent can read and cite it.}

## Output

Write the spec to: {REVIEW_DIR}/specs/{slug}.md
```

Use `subagent_type: "spec-writer"` for each agent.

Report progress as each agent completes.

**6d-verify. Verify specs against codebase**

After ALL spec-writer agents complete, verify each spec's accuracy before
writing INDEX.md. This catches stale line numbers, incorrect code snippets,
and references to functions that have been renamed or removed.

For each spec file in `$REVIEW_DIR/specs/`:

1. Read the spec file
2. For every "Current Code" block, extract the file path and line numbers
3. Read the actual file at those lines and compare:
   - Does the cited code ACTUALLY exist at the cited lines? (Allow ±5 line drift)
   - If not, grep for a distinctive snippet from the cited code to find its
     actual location
4. For every "Fixed Code" block, verify:
   - Imports referenced in the fix actually exist in the project
   - Functions/methods called in the fix exist (grep for their definitions)
5. Record discrepancies

If any spec has discrepancies, fix them in-place:
- Update line numbers to match actual locations
- Update "Current Code" blocks to match the actual code
- Add a note if the fix references a function that doesn't exist

Write a verification summary to `$REVIEW_DIR/specs/VERIFICATION.md`:

```markdown
# Spec Verification Results

**Specs verified:** {N}
**Clean:** {N} (all references accurate)
**Fixed:** {N} (line numbers or code snippets corrected)
**Flagged:** {N} (issues that couldn't be auto-corrected)

## Corrections Applied

| Spec | Finding | Issue | Fix |
|------|---------|-------|-----|
| WP1 | F003 | Line drift: cited L45-52, actual L48-55 | Updated |
| WP4 | F012 | Function `escapeValue` not found | Flagged — manual review needed |
```

**IMPORTANT:** Do not spawn agents for verification — the orchestrator performs
this directly by reading each spec and cross-referencing the codebase. This is
a fast, mechanical check.

**6e. Write INDEX.md**

After ALL spec-writer agents complete, the orchestrator writes
`$REVIEW_DIR/specs/INDEX.md` directly (no agent needed). Format:

```markdown
# Fix Specs Index

**Review date:** {YYYY-MM-DD}
**Source report:** REVIEW-REPORT.md
**Total findings addressed:** {N} ({n} Critical, {n} High, {n} Medium, {n} Low)
**Work packages:** {N}
**Severities included:** {severity filter used}

---

## Execution Priority

Execute in this order. Higher-severity, lower-complexity work packages first.

| # | Spec | Findings | Severity | Complexity | Files | Dependencies |
|---|------|----------|----------|------------|-------|--------------|
| WP1 | [{title}]({filename}) | F001, F002 | Critical+High | {from spec} | {N} | {deps or None} |
| ... | | | | | | |

---

## Finding-to-Spec Mapping

| Finding | Severity | Spec | Title |
|---------|----------|------|-------|
| F001 | Critical | WP1 | {short title} |
| ... | | | |

---

## File Overlap Matrix

Identifies which work packages modify the same files. Work packages sharing
files MUST be sequenced (not parallelised) to avoid merge conflicts.

| File | Work Packages |
|------|---------------|
| `src/components/qa-preview-list.tsx` | WP6, WP10 |
| `src/hooks/use-review-queue.ts` | WP8, WP10 |
| ... | |

{If no overlaps exist: "No file overlaps detected — all work packages can
be executed independently."}

---

## Implementation Waves

Work packages grouped into execution waves based on the dependency graph.
**Maximum 5 work packages per wave.** Work packages in the same wave can
be executed in parallel. Waves must be executed sequentially.

### Dependency Graph

```
WP1 ──→ WP4 (WP4 depends on WP1's utility function)
WP6 ──→ WP10 (shared file: qa-preview-list.tsx)
WP8 ──→ WP10 (shared file: use-review-queue.ts)
WP2, WP3, WP5, WP7, WP9 (independent)
```

{Generate the dependency graph from:
1. File overlaps (from the matrix above) — overlapping WPs must be sequenced
2. Explicit dependencies noted in spec files
3. Shared utility/helper creation — if one WP creates a helper that another uses}

### Wave Plan

| Wave | Work Packages | Rationale |
|------|---------------|-----------|
| 1 | WP1, WP2, WP3, WP5, WP7 | Independent, highest severity first |
| 2 | WP4, WP6, WP8, WP9 | WP4 depends on WP1; WP6/WP8 before WP10 |
| 3 | WP10 | Depends on WP6 and WP8 (shared files) |

{Sort within each wave by severity (Critical first) then complexity (Low first).
If >5 WPs are independent, split into multiple waves of ≤5.}

---

## Findings NOT Addressed

| Finding | Severity | Title | Reason excluded |
|---------|----------|-------|-----------------|
| F020 | Low | {title} | Below severity threshold |
| ... | | | |

---

## Notes

{Cross-cutting observations: deployment ordering, shared dependencies
between WPs, recommended parallelism strategy for implementation.}
```

**6f. Present spec results**

```
Fix specifications generated:

  📁 {REVIEW_DIR}/specs/
  ├── INDEX.md (start here)
  ├── {slug-1}.md (WP1 — {severity}, {complexity})
  ├── {slug-2}.md (WP2 — {severity}, {complexity})
  └── ...

{N} findings across {M} work packages. Recommended execution order is in INDEX.md.
```

---

## Optional Flags

Check the user's invocation message for these optional flags:

### `--specs` / `--generate-specs`

Skip Waves 1-5 and run only Wave 6 (spec generation) against an existing
review. Process:

1. Find the most recent `REVIEW-REPORT.md` and `findings.json` under
   `.planning/reviews/` by listing date directories and picking the latest.
2. If `specs/INDEX.md` already exists for that review date, ask:
   "Specs already exist for the {date} review. Regenerate? (y/n)"
3. Read `findings.json` (and `test-integrity-findings.json` if present).
4. Set `REVIEW_DIR` to the found review directory.
5. Proceed from Wave 6 step 6a (severity selection prompt).

### `--test-integrity`

Enable test integrity checking in Wave 2. Spawns an additional
`test-integrity-checker` agent that analyses the test suite for tests that
pass but validate incorrect behaviour. Detects 6 patterns:

1. Wrong value assertions (e.g., 403 instead of 401 for unauthenticated)
2. Mocking the system under test (test exercises mocks, not real code)
3. Weak assertions (toBeDefined/toBeTruthy instead of specific values)
4. Co-modification (test assertions changed to match wrong production code)
5. Dead code with passing tests (tested code has zero production callers)
6. Mock surface area exceeds assertion surface area

Test integrity findings flow through the standard triage (Wave 3),
verification (Wave 4), and reporting (Wave 5) pipeline with category
`test-integrity`. They also integrate with Wave 6 spec generation.

**Auto-activation:** If not explicitly set, test integrity checking
activates automatically when test files comprise >10% of the codebase
by file count (indicating meaningful test investment worth checking).

### `--silent-failures` / `--no-silent-failures`

Control silent-failure-hunter activation in Wave 2. Spawns an additional
`silent-failure-hunter` agent that detects silent-failure bugs across API
routes and their `lib/` helper dependencies. Runs 9 detection heuristics:

1. **H7.a** — Supabase `{ data }` destructured without `error` (the #1
   pattern — 30+ instances in the Knowledge Hub S151 audit)
2. **H7.b** — Supabase mutation with discarded return value (RLS silent
   no-op)
3. **H3** — Loop with `console.error`, no `failed[]` array
4. **H4** — Bare empty catch (Python `except: pass`, Go `if err != nil { }`,
   `_ = fn()`). TypeScript empty catches are covered by the existing
   pattern-checker rule to avoid duplication.
5. **H5** — `.then(...).catch(() => fallback)` ignoring error parameter
6. **H6** — Mock data returned on missing env var (`return mockData`)
7. **H-Resolver** — Helper returns `T | null` conflating "not found"
   with "lookup failed"
8. **H-Composite** — Fan-out endpoint with ≥3 sub-queries lacking a
   `warnings[]` envelope
9. **H-Helper-Cascade** — severity bump when a helper with a silent
   failure is called by ≥3 routes

Silent-failure findings flow through the standard triage (Wave 3),
verification (Wave 4), and reporting (Wave 5) pipeline with category
`Silent Failure` and a `Pattern ID` field for deduplication. They also
integrate with Wave 6 spec generation.

**Auto-activation:** If not explicitly set, silent-failure detection
activates automatically when Wave 1 detects ≥5 API routes AND at least
one DB library (Supabase, Prisma, Drizzle, TypeORM, SQLAlchemy, Django,
gorm, etc.). Below the threshold or without a DB library, the hunter
is skipped — the pattern-checker's universal rules still run.

**Flag precedence:** `--no-silent-failures` > `--silent-failures` > auto.
If both flags are passed (user error), treat as `--no-silent-failures`
and emit a warning. `--silent-failures` forces activation even on
small codebases or codebases without detected DB libraries (in which
case only the universal rules run). `--no-silent-failures` skips the
hunter regardless of activation criteria.

The flag is independent of `--test-integrity` — they do not cascade.

### `--verify-all`

Send Medium findings (not just Critical/High) to adversarial verification in
Wave 4. Increases token cost by ~30% but improves Medium finding quality.
When active, the triage step puts Medium findings in the VERIFY group instead
of ACCEPTED.

### `--thorough`

Runs a two-pass review for maximum coverage (~80% finding capture vs ~65%
single-pass). Process:

1. Complete Waves 1-5 as normal (Pass 1)
2. Re-partition the codebase with a DIFFERENT strategy:
   - If Pass 1 used directory-based partitioning, Pass 2 uses alphabetical
     file distribution (files sorted by path, dealt round-robin to N agents)
   - Different partition boundaries mean different agents read different files
3. Run Waves 2-3 again with the new partitions (reuse Wave 1 reconnaissance)
4. In the final report (Wave 5), merge Pass 1 and Pass 2 findings:
   - Findings from both passes get a confidence boost (+15)
   - Findings from only one pass keep their original confidence
   - Deduplicate before ranking

This roughly doubles the token cost and review time but significantly increases
the probability of finding issues in files that a single-pass agent might skip.

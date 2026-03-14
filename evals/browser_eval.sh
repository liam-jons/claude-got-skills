#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# browser_eval.sh — Automated Claude.ai A/B testing via agent-browser
#
# Modes:
#   --auth           One-time headed login + 2FA, saves auth state
#   --control        Run control condition only (skill OFF)
#   --treatment      Run treatment condition only (skill ON)
#   --report-only    Regenerate report from existing results JSON
#   (no flag)        Full run: control, then pause for skill toggle, then treatment
#
# Requirements:
#   - agent-browser CLI installed (v0.13.0+)
#   - Python 3 (for report generation)
#   - Claude.ai Pro/Team account
#
# Compatible with bash 3.2+ (macOS default).
###############################################################################

# --- Configuration -----------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

AUTH_STATE="$SCRIPT_DIR/claude-ai-auth-state.json"
RESULTS_DIR="$SCRIPT_DIR/browser-eval-run-$(date +%Y%m%d-%H%M%S)"
RESULTS_FILE="$SCRIPT_DIR/browser-eval-results.json"
SESSION="claude-eval"
INTER_PROMPT_DELAY=12  # seconds between prompts (10-15s range)
RESPONSE_TIMEOUT=120   # max seconds to wait for response completion
POLL_INTERVAL=3        # seconds between completion polls
SCREENSHOT_DIR=""      # set after RESULTS_DIR is created
HEADED_MODE=false      # --headed: run eval in headed (visible) browser
YES_MODE=false         # --yes: skip interactive confirmations

# --- Test Prompts (P1-P5) ----------------------------------------------------
# Stored as parallel indexed arrays for bash 3.2 compatibility.

PROMPT_COUNT=5

PROMPT_IDS_0="P1"; PROMPT_IDS_1="P2"; PROMPT_IDS_2="P3"; PROMPT_IDS_3="P4"; PROMPT_IDS_4="P5"

PROMPT_CATEGORIES_0="Vision / PDF"
PROMPT_CATEGORIES_1="API Features"
PROMPT_CATEGORIES_2="Model Selection"
PROMPT_CATEGORIES_3="Platform Comparison"
PROMPT_CATEGORIES_4="Product Capabilities"

PROMPT_TEXTS_0="I want to send product photos and a PDF spec sheet to Claude through the API. What image and PDF formats are supported, what are the limits, and how do I send them?"
PROMPT_TEXTS_1="What's the difference between extended thinking and adaptive thinking? When should I use each?"
PROMPT_TEXTS_2="I need the right Claude model for a customer support chatbot - it needs to be fast, cheap, and accurate. What do you recommend?"
PROMPT_TEXTS_3="I built a skill for Claude Code. How do I get the same skill working on Claude.ai and Claude Desktop? What differences should I expect?"
PROMPT_TEXTS_4="Can Claude remember what we talked about last week in a different conversation?"

get_prompt_id() { eval echo "\$PROMPT_IDS_$1"; }
get_prompt_category() { eval echo "\$PROMPT_CATEGORIES_$1"; }
get_prompt_text() { eval echo "\$PROMPT_TEXTS_$1"; }

# --- Helpers ------------------------------------------------------------------

log() { echo "[$(date +%H:%M:%S)] $*"; }
log_error() { echo "[$(date +%H:%M:%S)] ERROR: $*" >&2; }
log_warn() { echo "[$(date +%H:%M:%S)] WARN: $*" >&2; }

CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_ARGS="--disable-blink-features=AutomationControlled"

ab() {
  # Wrapper: runs agent-browser with session only.
  # --executable-path/--args are only needed on the FIRST open call (daemon start).
  # Passing them on subsequent calls causes stdout warnings that block script flow.
  agent-browser --session "$SESSION" "$@"
}

ab_headed() {
  # Wrapper: always runs in headed mode (for auth flow)
  agent-browser --session "$SESSION" --headed --executable-path "$CHROME_PATH" --args "$CHROME_ARGS" "$@"
}

cleanup_session() {
  log "Closing browser session..."
  ab close 2>/dev/null || true
}

# --- Auth Flow ----------------------------------------------------------------

do_auth() {
  log "=== Authentication Setup ==="
  log "Opening Claude.ai login in headed browser..."
  log "Complete login + 2FA manually in the browser window."

  ab_headed open "https://claude.ai/login"

  log ""
  log "Once you are logged in and see the Claude.ai chat page,"
  log "press ENTER here to save the auth state."
  log "(The browser will stay open until you press ENTER.)"
  log ""
  read -r -p "[$(date +%H:%M:%S)] Press ENTER when logged in... "

  log "Saving auth state..."
  ab_headed state save "$AUTH_STATE"

  if [[ -f "$AUTH_STATE" ]]; then
    log "Auth state saved to: $AUTH_STATE"
    log "You can now run: ./browser_eval.sh"
  else
    log_error "Failed to save auth state. Try again with: ./browser_eval.sh --auth"
  fi

  ab close 2>/dev/null || true
}

# --- Auth Validation ----------------------------------------------------------

validate_auth() {
  if [[ ! -f "$AUTH_STATE" ]]; then
    log_error "No auth state found. Run: ./browser_eval.sh --auth"
    exit 1
  fi

  log "Loading auth state and validating session..."
  # Kill any stale daemon for this session before starting fresh (double close
  # needed: first closes browser, second tears down daemon)
  agent-browser --session "$SESSION" close 2>/dev/null || true
  agent-browser --session "$SESSION" close 2>/dev/null || true

  # Load state via --state flag on first open (state load requires no running browser)
  # Must use --headed here if HEADED_MODE is set, since this starts the daemon
  if [[ "$HEADED_MODE" == "true" ]]; then
    agent-browser --session "$SESSION" --headed --executable-path "$CHROME_PATH" --args "$CHROME_ARGS" --state "$AUTH_STATE" open "https://claude.ai/new"
  else
    agent-browser --session "$SESSION" --executable-path "$CHROME_PATH" --args "$CHROME_ARGS" --state "$AUTH_STATE" open "https://claude.ai/new"
  fi

  # Give page time to settle and potentially redirect
  sleep 3

  local current_url
  current_url=$(ab get url 2>/dev/null || echo "")

  if [[ "$current_url" == *"/login"* ]]; then
    log_error "Auth state expired. Re-authenticate with: ./browser_eval.sh --auth"
    cleanup_session
    exit 1
  fi

  if [[ "$current_url" != *"claude.ai"* ]]; then
    log_error "Unexpected URL after auth restore: $current_url"
    log_error "Re-authenticate with: ./browser_eval.sh --auth"
    cleanup_session
    exit 1
  fi

  log "Auth validation passed. Current URL: $current_url"
}

# --- Response Completion Detection --------------------------------------------

wait_for_response() {
  # Layered completion detection:
  # 1. Primary: Look for a stop/copy button indicating completion
  # 2. Fallback: Text-stability (response stops growing)
  # 3. Last resort: Hard timeout

  local elapsed=0
  local last_length=0
  local stable_count=0
  local required_stable=3  # need 3 consecutive stable checks

  log "  Waiting for response completion (timeout: ${RESPONSE_TIMEOUT}s)..."

  # Initial wait for response to start generating
  sleep 5
  elapsed=5

  while [ "$elapsed" -lt "$RESPONSE_TIMEOUT" ]; do
    # Try to detect completion via snapshot — look for copy/retry buttons
    # that only appear after response is done
    local snapshot_text
    snapshot_text=$(ab snapshot -i 2>/dev/null || echo "")

    # Primary: "Stop response" button disappears when generation finishes
    if ! echo "$snapshot_text" | grep -qi 'Stop response'; then
      # Verify response actually started (not just a blank page)
      if echo "$snapshot_text" | grep -qi 'Copy\|"Retry"\|"Try again"\|"Message actions"\|Reply'; then
        log "  Response complete (Stop button gone, action buttons present at ${elapsed}s)"
        return 0
      fi
    fi

    # Fallback: text-stability check via JS
    local current_text
    current_text=$(ab eval "
      (function() {
        // Try multiple strategies to measure response length
        var selectors = [
          '[data-testid=\"chat-message-text\"]',
          'div.font-claude-message',
          'div.prose',
          'div[class*=\"response\"]',
          'div[class*=\"message\"][class*=\"assistant\"]'
        ];
        for (var i = 0; i < selectors.length; i++) {
          var els = document.querySelectorAll(selectors[i]);
          if (els.length > 0) {
            var total = 0;
            for (var j = 0; j < els.length; j++) total += els[j].innerText.length;
            if (total > 0) return String(total);
          }
        }
        return '0';
      })()
    " 2>/dev/null || echo "0")

    local current_length
    current_length=$(echo "$current_text" | tr -dc '0-9' | head -c 10)
    current_length=${current_length:-0}

    if [ "$current_length" -gt 0 ] && [ "$current_length" -eq "$last_length" ]; then
      stable_count=$((stable_count + 1))
      if [ "$stable_count" -ge "$required_stable" ]; then
        log "  Response complete (text stable for $((stable_count * POLL_INTERVAL))s at ${elapsed}s)"
        return 0
      fi
    else
      stable_count=0
    fi
    last_length=$current_length

    sleep "$POLL_INTERVAL"
    elapsed=$((elapsed + POLL_INTERVAL))
  done

  log_warn "  Response timeout after ${RESPONSE_TIMEOUT}s — capturing partial response"
  return 0  # Don't fail — capture what we have
}

# --- Extract Response & Thinking ----------------------------------------------

extract_response() {
  # Extract the assistant's response text from the page
  # Strategy 1 (preferred): Use snapshot to find response content via accessibility tree
  local snapshot
  snapshot=$(ab snapshot 2>/dev/null || echo "")

  if [[ -n "$snapshot" ]]; then
    # The snapshot contains the full text content. Extract everything after
    # the user's prompt — the assistant's response is the last large text block.
    # Save snapshot for debugging
    echo "$snapshot" > "$RESULTS_DIR/last_snapshot.txt" 2>/dev/null || true

    # Try to get response via eval with multiple selector strategies
    local response_text
    response_text=$(ab eval "
      (function() {
        // Strategy A: Look for response containers by data attributes
        var selectors = [
          '[data-testid=\"chat-message-text\"]',
          '[data-is-streaming]',
          'div.font-claude-message',
          'div.prose',
          'div[class*=\"response\"]',
          'div[class*=\"message\"][class*=\"assistant\"]'
        ];
        for (var i = 0; i < selectors.length; i++) {
          var els = document.querySelectorAll(selectors[i]);
          if (els.length > 0) {
            var text = els[els.length - 1].innerText;
            if (text && text.trim().length > 50) return text;
          }
        }
        // Strategy B: Find all article or section elements with substantial text
        var articles = document.querySelectorAll('article, section, div[class*=\"chat\"], div[class*=\"message\"]');
        var longest = '';
        for (var i = 0; i < articles.length; i++) {
          var t = articles[i].innerText;
          if (t && t.length > longest.length) longest = t;
        }
        if (longest.length > 50) return longest;
        return 'EXTRACTION_FAILED';
      })()
    " 2>/dev/null || echo "EXTRACTION_FAILED")

    if [[ "$response_text" != "EXTRACTION_FAILED" && -n "$response_text" ]]; then
      echo "$response_text"
      return 0
    fi
  fi

  # Strategy 2: Snapshot text extraction — parse the raw snapshot text
  # The snapshot contains readable text content; extract the last substantial block
  if [[ -n "$snapshot" ]]; then
    log_warn "  DOM extraction failed, parsing snapshot text directly"
    # The snapshot is accessibility tree text — the response content is embedded in it
    echo "$snapshot"
    return 0
  fi

  log_warn "  All extraction strategies failed"
  echo "EXTRACTION_FAILED"
}

extract_thinking() {
  # Extract the thinking panel summary and (if possible) expanded content.
  #
  # Claude.ai renders the thinking panel as:
  #   - button "<summary text>" [ref=eNN]        ← clickable toggle
  #   - status: <summary text>                   ← visible status line
  # The summary text is a sentence (e.g. "Examined Claude's cross-conversation
  # memory limitations"), NOT a UI label like "Copy" or "Retry".

  local thinking_text=""
  local snapshot
  snapshot=$(ab snapshot 2>/dev/null || echo "")

  # Strategy 1: Find the thinking toggle via the "status:" line in the
  # accessibility snapshot. The status element only appears for thinking summaries.
  local thinking_ref=""
  local thinking_summary=""

  if [[ -n "$snapshot" ]]; then
    # Save thinking snapshot for debugging
    echo "$snapshot" > "$RESULTS_DIR/last_thinking_snapshot.txt" 2>/dev/null || true

    # The status line sits right after the thinking button.
    # Find the button ref from the line immediately before "- status:".
    thinking_ref=$(echo "$snapshot" | grep -B1 '^\s*- status:' | grep 'button' | grep -oE 'ref=e[0-9]+' | head -1 | sed 's/ref=//' || echo "")

    # Extract the summary text from the status line
    thinking_summary=$(echo "$snapshot" | grep '^\s*- status:' | head -1 | sed 's/.*- status: *//' || echo "")
  fi

  if [[ -n "$thinking_ref" ]]; then
    log "  Found thinking toggle: $thinking_ref (summary: $(echo "$thinking_summary" | cut -c1-60)...)"

    # Click to expand the thinking panel
    ab click "$thinking_ref" 2>/dev/null || true
    sleep 2

    # Try to extract the expanded thinking content via JS.
    # Claude.ai DOM structure (as of March 2026):
    #   grandparent DIV
    #     ├── DIV > BUTTON[aria-expanded="true"]  (the toggle)
    #     ├── SPAN                                (status text)
    #     └── DIV                                 (expanded thinking content)
    # The thinking content is in the grandparent's children[2+].
    thinking_text=$(ab eval "
      (function() {
        var btn = document.querySelector('button[aria-expanded=\"true\"]');
        if (!btn) return '';

        // Navigate to grandparent where expanded content lives
        var gp = btn.parentElement ? btn.parentElement.parentElement : null;
        if (!gp) return '';

        // Collect text from children after the toggle and status
        var parts = [];
        var children = gp.children;
        for (var i = 2; i < children.length; i++) {
          var text = children[i].innerText;
          if (text && text.trim().length > 0) {
            parts.push(text.trim());
          }
        }
        if (parts.length > 0) return parts.join('\n');

        return '';
      })()
    " 2>/dev/null || echo "")
  fi

  # If JS extraction failed but we have the summary, return that
  if [[ -z "$thinking_text" || "$thinking_text" == '""' ]] && [[ -n "$thinking_summary" ]]; then
    log "  Using thinking summary (expanded content not extracted)"
    thinking_text="[Thinking summary] $thinking_summary"
  fi

  echo "$thinking_text"
}

# --- Run Single Prompt --------------------------------------------------------

run_prompt() {
  local prompt_id="$1"
  local condition="$2"  # "control" or "treatment"
  local prompt_text="$3"
  local category="$4"

  local result_file="$RESULTS_DIR/${prompt_id}_${condition}.json"
  local screenshot_path="$SCREENSHOT_DIR/${prompt_id}_${condition}.png"

  log "--- $prompt_id ($condition): $category ---"
  log "  Prompt: $(echo "$prompt_text" | cut -c1-80)..."

  # Navigate to new chat
  log "  Navigating to claude.ai/new..."
  if ! ab open "https://claude.ai/new" 2>/dev/null; then
    log_error "  Failed to navigate to claude.ai/new"
    write_error_result "$result_file" "$prompt_id" "$condition" "$category" "$prompt_text" "Navigation failed"
    return 0  # Don't kill the batch
  fi

  # Wait for page to load (avoid networkidle — Claude.ai WebSockets keep it active)
  sleep 5

  # Discover the input field via snapshot
  log "  Taking snapshot to find input field..."
  local snapshot
  snapshot=$(ab snapshot -i 2>/dev/null || echo "")

  if [[ -z "$snapshot" ]]; then
    log_error "  Empty snapshot — page may not have loaded"
    write_error_result "$result_file" "$prompt_id" "$condition" "$category" "$prompt_text" "Empty snapshot"
    return 0
  fi

  # Find the textbox/input ref from snapshot
  # Claude.ai uses: textbox "Write your prompt to Claude" with placeholder "How can I help you today?"
  # The element is a ProseMirror contenteditable div wrapped in a group
  local input_ref

  # Strategy 1: Look for the active textbox with "Write your prompt" label
  input_ref=$(echo "$snapshot" | grep -iE 'textbox.*[Ww]rite your prompt|textbox.*[Hh]ow can I help' | grep -oE 'ref=e[0-9]+' | head -1 | sed 's/ref=//' || echo "")

  # Strategy 2: Look for any active textbox on the page
  if [[ -z "$input_ref" ]]; then
    input_ref=$(echo "$snapshot" | grep -iE 'textbox.*\[active\]' | grep -oE 'ref=e[0-9]+' | head -1 | sed 's/ref=//' || echo "")
  fi

  # Strategy 3: Look for textbox with common chat input patterns
  if [[ -z "$input_ref" ]]; then
    input_ref=$(echo "$snapshot" | grep -iE 'textbox|contenteditable|ProseMirror|"Send a message"|"Reply"|placeholder.*[Hh]ow can' | head -1 | grep -oE 'ref=e[0-9]+' | head -1 | sed 's/ref=//' || echo "")
  fi

  # Strategy 4: Broader fallback
  if [[ -z "$input_ref" ]]; then
    input_ref=$(echo "$snapshot" | grep -iE 'textarea|[Mm]essage|[Cc]hat|[Pp]rompt' | head -1 | grep -oE 'ref=e[0-9]+' | head -1 | sed 's/ref=//' || echo "")
  fi

  local filled=false

  if [[ -z "$input_ref" ]]; then
    log_warn "  Could not find input field from snapshot. Trying find command..."
    # Try using the find command as fallback
    if ab find role textbox fill "$prompt_text" 2>/dev/null; then
      log "  Filled via find role textbox"
      filled=true
    else
      log_error "  Could not locate input field"
      write_error_result "$result_file" "$prompt_id" "$condition" "$category" "$prompt_text" "Input field not found"
      return 0
    fi
  fi

  if [[ "$filled" != "true" ]]; then
    log "  Found input field: $input_ref"
    # Click to focus, then fill
    ab click "$input_ref" 2>/dev/null || true
    sleep 1

    # Use fill for the input — contenteditable may need type instead
    if ! ab fill "$input_ref" "$prompt_text" 2>/dev/null; then
      log_warn "  fill failed, trying type..."
      if ! ab type "$input_ref" "$prompt_text" 2>/dev/null; then
        # Last resort: click and use keyboard
        log_warn "  type failed, trying click + find role textbox fill..."
        if ! ab find role textbox fill "$prompt_text" 2>/dev/null; then
          log_error "  Could not fill input field by any method"
          write_error_result "$result_file" "$prompt_id" "$condition" "$category" "$prompt_text" "Fill failed"
          return 0
        fi
      fi
    fi
  fi

  sleep 1

  # Submit the prompt
  log "  Submitting prompt..."
  ab press Enter 2>/dev/null || true
  sleep 2

  # Wait for response completion
  wait_for_response

  # Extract response text
  log "  Extracting response..."
  local response_text
  response_text=$(extract_response)

  # Extract thinking panel
  log "  Extracting thinking panel..."
  local thinking_text
  thinking_text=$(extract_thinking)

  # Take screenshot (10s timeout — screenshots hang on some pages)
  log "  Taking screenshot..."
  timeout 10 ab screenshot "$screenshot_path" 2>/dev/null || log_warn "  Screenshot failed (timeout or error)"

  # Check for "Continue generating" button
  local snapshot_after
  snapshot_after=$(ab snapshot -i 2>/dev/null || echo "")
  if echo "$snapshot_after" | grep -qi 'Continue generating\|Continue'; then
    log_warn "  'Continue generating' button detected — response may be truncated"
  fi

  # Write result JSON
  write_result "$result_file" "$prompt_id" "$condition" "$category" "$prompt_text" \
    "$response_text" "$thinking_text" "$screenshot_path"

  log "  Result saved: $result_file"
}

# --- JSON Output Helpers ------------------------------------------------------

json_escape() {
  # Escape a string for safe JSON embedding
  python3 -c "
import json, sys
text = sys.stdin.read()
print(json.dumps(text), end='')
" <<< "$1"
}

write_result() {
  local file="$1" pid="$2" condition="$3" category="$4" prompt="$5"
  local response="$6" thinking="$7" screenshot="$8"

  local j_prompt j_response j_thinking j_screenshot j_category
  j_prompt=$(json_escape "$prompt")
  j_response=$(json_escape "$response")
  j_thinking=$(json_escape "$thinking")
  j_screenshot=$(json_escape "$screenshot")
  j_category=$(json_escape "$category")

  cat > "$file" << ENDJSON
{
  "prompt_id": "$pid",
  "condition": "$condition",
  "category": $j_category,
  "prompt": $j_prompt,
  "response": $j_response,
  "thinking": $j_thinking,
  "screenshot": $j_screenshot,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "ok"
}
ENDJSON
}

write_error_result() {
  local file="$1" pid="$2" condition="$3" category="$4" prompt="$5" error="$6"

  local j_prompt j_error j_category
  j_prompt=$(json_escape "$prompt")
  j_error=$(json_escape "$error")
  j_category=$(json_escape "$category")

  cat > "$file" << ENDJSON
{
  "prompt_id": "$pid",
  "condition": "$condition",
  "category": $j_category,
  "prompt": $j_prompt,
  "response": "",
  "thinking": "",
  "screenshot": "",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "error",
  "error": $j_error
}
ENDJSON
}

# --- Assemble Results ---------------------------------------------------------

assemble_results() {
  log "Assembling results into $RESULTS_FILE..."

  python3 -c "
import json, glob, os, sys

results_dir = sys.argv[1]
output_file = sys.argv[2]

# Collect all fragment files
fragments = sorted(glob.glob(os.path.join(results_dir, 'P*_*.json')))

if not fragments:
    print('No result fragments found', file=sys.stderr)
    sys.exit(1)

# Group by prompt_id
by_prompt = {}
for f in fragments:
    with open(f) as fh:
        data = json.load(fh)
    pid = data['prompt_id']
    cond = data['condition']
    if pid not in by_prompt:
        by_prompt[pid] = {
            'prompt_id': pid,
            'category': data.get('category', ''),
            'prompt': data.get('prompt', ''),
        }
    by_prompt[pid][cond] = {
        'response': data.get('response', ''),
        'thinking': data.get('thinking', ''),
        'screenshot': data.get('screenshot', ''),
        'timestamp': data.get('timestamp', ''),
        'status': data.get('status', 'unknown'),
        'error': data.get('error', ''),
    }

# Build final structure
output = {
    'metadata': {
        'eval_type': 'browser',
        'platform': 'claude.ai',
        'timestamp': max(
            d.get(c, {}).get('timestamp', '')
            for d in by_prompt.values()
            for c in ('control', 'treatment')
        ),
        'prompt_count': len(by_prompt),
        'note': 'n=5 qualitative assessment, not statistically significant',
    },
    'results': [by_prompt[pid] for pid in sorted(by_prompt.keys())],
}

with open(output_file, 'w') as fh:
    json.dump(output, fh, indent=2)

print(f'Assembled {len(fragments)} fragments into {output_file}')
" "$RESULTS_DIR" "$RESULTS_FILE"
}

# --- Run Condition (control or treatment) -------------------------------------

run_condition() {
  local condition="$1"

  log "========================================="
  log "  Running condition: $condition"
  log "========================================="

  local succeeded=0
  local failed=0
  local i=0

  while [ "$i" -lt "$PROMPT_COUNT" ]; do
    local pid category prompt_text
    pid=$(get_prompt_id "$i")
    category=$(get_prompt_category "$i")
    prompt_text=$(get_prompt_text "$i")

    log ""
    if run_prompt "$pid" "$condition" "$prompt_text" "$category"; then
      local result_file="$RESULTS_DIR/${pid}_${condition}.json"
      if [[ -f "$result_file" ]]; then
        local status
        status=$(python3 -c "import json; print(json.load(open('$result_file'))['status'])" 2>/dev/null || echo "unknown")
        if [[ "$status" == "ok" ]]; then
          succeeded=$((succeeded + 1))
        else
          failed=$((failed + 1))
        fi
      fi
    else
      failed=$((failed + 1))
    fi

    # Inter-prompt delay (skip after last prompt)
    local last_idx=$((PROMPT_COUNT - 1))
    if [ "$i" -ne "$last_idx" ]; then
      log "  Waiting ${INTER_PROMPT_DELAY}s before next prompt..."
      sleep "$INTER_PROMPT_DELAY"
    fi

    i=$((i + 1))
  done

  log ""
  log "$condition complete: $succeeded succeeded, $failed failed"
}

# --- Report Generation --------------------------------------------------------

generate_report() {
  if [[ ! -f "$RESULTS_FILE" ]]; then
    log_error "No results file found at $RESULTS_FILE"
    exit 1
  fi

  log "Generating report..."
  python3 "$SCRIPT_DIR/browser_eval_report.py" "$RESULTS_FILE"
}

# --- Main ---------------------------------------------------------------------

show_usage() {
  echo "Usage: $0 [--auth | --control | --treatment | --report-only] [--headed] [--yes]"
  echo ""
  echo "Automated Claude.ai A/B testing for the claude-capabilities skill."
  echo ""
  echo "Modes:"
  echo "  (no flag)      Full run: control + skill toggle + treatment + report"
  echo "  --auth         One-time login setup (headed browser for 2FA)"
  echo "  --control      Run control condition only (skill OFF)"
  echo "  --treatment    Run treatment condition only (skill ON)"
  echo "  --report-only  Regenerate report from existing browser-eval-results.json"
  echo ""
  echo "Options:"
  echo "  --headed       Run browser in headed (visible) mode for debugging"
  echo "  --yes          Skip interactive confirmations (for unattended runs)"
}

main() {
  # Parse flags
  local mode="full"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --headed)
        HEADED_MODE=true
        shift
        ;;
      --yes|-y)
        YES_MODE=true
        shift
        ;;
      *)
        mode="$1"
        shift
        ;;
    esac
  done

  case "$mode" in
    --auth)
      do_auth
      exit 0
      ;;
    --report-only)
      generate_report
      exit 0
      ;;
    --control)
      mkdir -p "$RESULTS_DIR"
      SCREENSHOT_DIR="$RESULTS_DIR/screenshots"
      mkdir -p "$SCREENSHOT_DIR"
      validate_auth
      run_condition "control"
      assemble_results
      cleanup_session
      generate_report
      ;;
    --treatment)
      mkdir -p "$RESULTS_DIR"
      SCREENSHOT_DIR="$RESULTS_DIR/screenshots"
      mkdir -p "$SCREENSHOT_DIR"
      validate_auth
      run_condition "treatment"
      assemble_results
      cleanup_session
      generate_report
      ;;
    full)
      mkdir -p "$RESULTS_DIR"
      SCREENSHOT_DIR="$RESULTS_DIR/screenshots"
      mkdir -p "$SCREENSHOT_DIR"
      validate_auth

      log ""
      log "========================================="
      log "  PHASE 1: CONTROL (skill should be OFF)"
      log "========================================="
      log ""
      if [[ "$YES_MODE" == "true" ]]; then
        log "  (--yes: assuming skill is DISABLED)"
      else
        echo -n "Confirm: Is the claude-capabilities skill DISABLED on Claude.ai? [y/N] "
        read -r confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
          log "Aborting. Disable the skill first, then re-run."
          cleanup_session
          exit 1
        fi
      fi

      run_condition "control"

      # Close session between conditions to get a clean state
      cleanup_session
      sleep 2

      log ""
      log "========================================="
      log "  SKILL TOGGLE CHECKPOINT"
      log "========================================="
      log ""
      log "Control phase complete. Now:"
      log "  1. Go to Claude.ai Settings > Profiles & Skills"
      log "  2. ENABLE the claude-capabilities skill"
      log "  3. Return here and press Enter"
      log ""
      if [[ "$YES_MODE" == "true" ]]; then
        log "  (--yes: assuming skill is ENABLED, continuing...)"
      else
        echo -n "Have you ENABLED the skill? Press Enter to continue (or Ctrl+C to abort)... "
        read -r
      fi

      # Re-validate auth for treatment phase
      validate_auth

      log ""
      log "========================================="
      log "  PHASE 2: TREATMENT (skill should be ON)"
      log "========================================="
      log ""

      run_condition "treatment"

      assemble_results
      cleanup_session
      generate_report

      log ""
      log "========================================="
      log "  EVAL COMPLETE"
      log "========================================="
      log "Results:    $RESULTS_FILE"
      log "Run dir:    $RESULTS_DIR"
      log "Report:     (see above)"
      ;;
    --help|-h)
      show_usage
      exit 0
      ;;
    *)
      show_usage
      exit 1
      ;;
  esac
}

main "$@"

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

# --- Test Prompts (P1-P5) ----------------------------------------------------
# Stored as parallel indexed arrays for bash 3.2 compatibility.

PROMPT_COUNT=5

PROMPT_IDS_0="P1"; PROMPT_IDS_1="P2"; PROMPT_IDS_2="P3"; PROMPT_IDS_3="P4"; PROMPT_IDS_4="P5"

PROMPT_CATEGORIES_0="Architecture / API"
PROMPT_CATEGORIES_1="API Features"
PROMPT_CATEGORIES_2="Model Selection"
PROMPT_CATEGORIES_3="Extension Patterns"
PROMPT_CATEGORIES_4="Product Capabilities"

PROMPT_TEXTS_0="I need to build a document processing pipeline in Python that handles 50-page docs. What's the best API setup for this?"
PROMPT_TEXTS_1="What's the difference between extended thinking and adaptive thinking? When should I use each?"
PROMPT_TEXTS_2="I need the right Claude model for a customer support chatbot - it needs to be fast, cheap, and accurate. What do you recommend?"
PROMPT_TEXTS_3="I have a code review checklist that I repeat in every prompt when using Claude Code. Is there a better way to do this?"
PROMPT_TEXTS_4="Can Claude remember what we talked about last week in a different conversation?"

get_prompt_id() { eval echo "\$PROMPT_IDS_$1"; }
get_prompt_category() { eval echo "\$PROMPT_CATEGORIES_$1"; }
get_prompt_text() { eval echo "\$PROMPT_TEXTS_$1"; }

# --- Helpers ------------------------------------------------------------------

log() { echo "[$(date +%H:%M:%S)] $*"; }
log_error() { echo "[$(date +%H:%M:%S)] ERROR: $*" >&2; }
log_warn() { echo "[$(date +%H:%M:%S)] WARN: $*" >&2; }

ab() {
  # Wrapper: runs agent-browser with session
  agent-browser --session "$SESSION" "$@"
}

ab_headed() {
  # Wrapper: runs agent-browser in headed mode with session
  agent-browser --session "$SESSION" --headed "$@"
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

  log "Waiting for successful login (up to 120s)..."
  log "You should see claude.ai/new or claude.ai/chat after logging in."

  # Wait for redirect to authenticated page
  if ab wait --url "*claude.ai/new*" --timeout 120000 2>/dev/null || \
     ab wait --url "*claude.ai/chat*" --timeout 5000 2>/dev/null; then
    log "Login detected. Saving auth state..."
    ab state save "$AUTH_STATE"
    log "Auth state saved to: $AUTH_STATE"
    log "You can now run: ./browser_eval.sh"
    ab close 2>/dev/null || true
  else
    log_error "Login not detected within timeout. Try again with: ./browser_eval.sh --auth"
    ab close 2>/dev/null || true
    exit 1
  fi
}

# --- Auth Validation ----------------------------------------------------------

validate_auth() {
  if [[ ! -f "$AUTH_STATE" ]]; then
    log_error "No auth state found. Run: ./browser_eval.sh --auth"
    exit 1
  fi

  log "Loading auth state and validating session..."
  ab state load "$AUTH_STATE"
  ab open "https://claude.ai/new"

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

    # Claude.ai shows a "Copy" button on the response after completion
    # Also check for retry button or new message input becoming active
    if echo "$snapshot_text" | grep -qi 'Copy\|"Retry"\|"Try again"'; then
      # Verify it's not just a UI element — check for response-area copy
      local copy_count
      copy_count=$(echo "$snapshot_text" | grep -ci 'Copy' || true)
      if [ "$copy_count" -ge 1 ]; then
        log "  Response complete (copy button detected at ${elapsed}s)"
        return 0
      fi
    fi

    # Fallback: text-stability check via JS
    local current_text
    current_text=$(ab eval "
      (function() {
        var el = document.querySelector('[data-testid=\"chat-message-text\"]');
        if (el) return String(el.innerText.length);
        var els = document.querySelectorAll('div.font-claude-message, div.prose');
        if (els.length > 0) {
          var total = 0;
          for (var i = 0; i < els.length; i++) total += els[i].innerText.length;
          return String(total);
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
  local response_text

  # Strategy 1: Use eval to get response text from the DOM
  response_text=$(ab eval "
    (function() {
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
          var text = els[els.length - 1].innerText;
          if (text && text.trim().length > 0) return text;
        }
      }
      return 'EXTRACTION_FAILED';
    })()
  " 2>/dev/null || echo "EXTRACTION_FAILED")

  # Strategy 2: If eval failed, try broader selectors
  if [[ "$response_text" == "EXTRACTION_FAILED" || -z "$response_text" ]]; then
    log_warn "  DOM extraction failed, falling back to broader selectors"
    response_text=$(ab eval "
      (function() {
        var msgs = document.querySelectorAll('div[class*=\"message\"], div[class*=\"chat\"], article');
        var texts = [];
        for (var i = 0; i < msgs.length; i++) {
          var t = msgs[i].innerText;
          if (t && t.length > 50) texts.push(t);
        }
        return texts.length > 0 ? texts[texts.length - 1] : 'EXTRACTION_FAILED';
      })()
    " 2>/dev/null || echo "EXTRACTION_FAILED")
  fi

  echo "$response_text"
}

extract_thinking() {
  # Try to expand and extract the thinking panel content
  local thinking_text=""

  # First, try to find and click the thinking toggle/expand button
  local snapshot
  snapshot=$(ab snapshot -i 2>/dev/null || echo "")

  # Look for thinking-related elements in the snapshot
  local thinking_ref
  thinking_ref=$(echo "$snapshot" | grep -i 'think\|reasoning' | head -1 | grep -o '@e[0-9]*' | head -1 || echo "")

  if [[ -n "$thinking_ref" ]]; then
    log "  Found thinking panel toggle: $thinking_ref"
    ab click "$thinking_ref" 2>/dev/null || true
    sleep 1

    # Re-snapshot after expanding
    snapshot=$(ab snapshot -i 2>/dev/null || echo "")
  fi

  # Extract thinking text via JavaScript
  thinking_text=$(ab eval "
    (function() {
      var selectors = [
        '[data-testid=\"thinking-content\"]',
        'div[class*=\"thinking\"]',
        'div[class*=\"reasoning\"]',
        'details[class*=\"think\"] div',
        'div[class*=\"thought\"]'
      ];
      for (var i = 0; i < selectors.length; i++) {
        var els = document.querySelectorAll(selectors[i]);
        if (els.length > 0) {
          var parts = [];
          for (var j = 0; j < els.length; j++) parts.push(els[j].innerText);
          var text = parts.join('\n');
          if (text && text.trim().length > 0) return text;
        }
      }
      return '';
    })()
  " 2>/dev/null || echo "")

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

  sleep 3

  # Wait for page to load
  ab wait --load networkidle 2>/dev/null || sleep 2

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
  # Claude.ai uses a contenteditable div or ProseMirror editor
  local input_ref
  input_ref=$(echo "$snapshot" | grep -iE 'textbox|contenteditable|paragraph|ProseMirror|editor|"Send a message"|"Reply"|"How can"|placeholder' | head -1 | grep -o '@e[0-9]*' | head -1 || echo "")

  if [[ -z "$input_ref" ]]; then
    # Broader fallback: look for any textarea or input-like element
    input_ref=$(echo "$snapshot" | grep -iE 'textarea|input|[Mm]essage|[Cc]hat|[Pp]rompt' | head -1 | grep -o '@e[0-9]*' | head -1 || echo "")
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

  # Take screenshot
  log "  Taking screenshot..."
  ab screenshot "$screenshot_path" 2>/dev/null || log_warn "  Screenshot failed"

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
  echo "Usage: $0 [--auth | --control | --treatment | --report-only]"
  echo ""
  echo "Automated Claude.ai A/B testing for the claude-capabilities skill."
  echo ""
  echo "Modes:"
  echo "  (no flag)      Full run: control + skill toggle + treatment + report"
  echo "  --auth         One-time login setup (headed browser for 2FA)"
  echo "  --control      Run control condition only (skill OFF)"
  echo "  --treatment    Run treatment condition only (skill ON)"
  echo "  --report-only  Regenerate report from existing browser-eval-results.json"
}

main() {
  local mode="${1:-full}"

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
      echo -n "Confirm: Is the claude-capabilities skill DISABLED on Claude.ai? [y/N] "
      read -r confirm
      if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log "Aborting. Disable the skill first, then re-run."
        cleanup_session
        exit 1
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
      echo -n "Have you ENABLED the skill? Press Enter to continue (or Ctrl+C to abort)... "
      read -r

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

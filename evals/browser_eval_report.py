#!/usr/bin/env python3
"""
browser_eval_report.py — Generate markdown report from browser eval results.

Reads browser-eval-results.json, analyzes skill triggering and web search usage
from thinking text, and produces a side-by-side comparison report.

Usage:
    python3 browser_eval_report.py [results_file]

Default results file: evals/browser-eval-results.json (same directory as script)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# --- Detection Patterns -------------------------------------------------------

SKILL_TRIGGER_PATTERNS = [
    r"check product self[- ]knowledge",
    r"check assistant capabilities",
    r"capabilities skill",
    r"check.*skill.*for",
    r"product knowledge",
    r"self[- ]knowledge.*for",
    r"skill.*reference",
    r"reading.*skill",
    r"consult.*skill",
]

WEB_SEARCH_PATTERNS = [
    r"web search",
    r"search results",
    r"searching the web",
    r"searching for",
    r"search.*anthropic\.com",
    r"let me search",
    r"found.*search",
    r"according to.*search",
]

# More conservative: exclude patterns that are too broad
WEB_SEARCH_EXCLUDE_PATTERNS = [
    r"searching.*memory",
    r"searching.*knowledge",
    r"search.*internally",
]


def detect_skill_trigger(thinking: str) -> dict:
    """Detect if the skill was triggered based on thinking text."""
    if not thinking:
        return {"triggered": False, "confidence": "no_thinking", "evidence": []}

    thinking_lower = thinking.lower()
    evidence = []

    for pattern in SKILL_TRIGGER_PATTERNS:
        matches = re.findall(pattern, thinking_lower)
        if matches:
            evidence.extend(matches)

    if evidence:
        return {
            "triggered": True,
            "confidence": "high" if len(evidence) >= 2 else "medium",
            "evidence": evidence[:3],  # cap at 3 examples
        }

    return {"triggered": False, "confidence": "low", "evidence": []}


def detect_web_search(thinking: str) -> dict:
    """Detect if web search was used based on thinking text."""
    if not thinking:
        return {"used": False, "confidence": "no_thinking", "evidence": []}

    thinking_lower = thinking.lower()
    evidence = []

    # Check exclusions first
    for pattern in WEB_SEARCH_EXCLUDE_PATTERNS:
        if re.search(pattern, thinking_lower):
            # Possible false positive context — be cautious
            pass

    for pattern in WEB_SEARCH_PATTERNS:
        matches = re.findall(pattern, thinking_lower)
        if matches:
            evidence.extend(matches)

    if evidence:
        return {
            "used": True,
            "confidence": "high" if len(evidence) >= 2 else "medium",
            "evidence": evidence[:3],
        }

    return {"used": False, "confidence": "low", "evidence": []}


def truncate(text: str, max_len: int = 500) -> str:
    """Truncate text with ellipsis."""
    if not text or len(text) <= max_len:
        return text or "(empty)"
    return text[:max_len] + "..."


def generate_report(results_data: dict) -> str:
    """Generate markdown report from results data."""
    metadata = results_data.get("metadata", {})
    results = results_data.get("results", [])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    eval_timestamp = metadata.get("timestamp", "unknown")

    lines = []

    # Header
    lines.append("# Browser Eval Report: Claude.ai A/B Testing")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Eval run:** {eval_timestamp}")
    lines.append(f"**Platform:** {metadata.get('platform', 'claude.ai')}")
    lines.append(f"**Prompts tested:** {metadata.get('prompt_count', len(results))}")
    lines.append("")
    lines.append("> **Note:** n=5 is a qualitative assessment for directional insight,")
    lines.append("> not a statistically significant comparison. Results should be")
    lines.append("> interpreted as indicative, not conclusive.")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Prompt | Category | Skill Triggered? | Web Search (C/T) | Status |")
    lines.append("|--------|----------|-------------------|-------------------|--------|")

    analysis_details = []

    for r in results:
        pid = r.get("prompt_id", "?")
        category = r.get("category", "")

        control = r.get("control", {})
        treatment = r.get("treatment", {})

        # Analyze thinking
        ctrl_trigger = detect_skill_trigger(control.get("thinking", ""))
        treat_trigger = detect_skill_trigger(treatment.get("thinking", ""))
        ctrl_search = detect_web_search(control.get("thinking", ""))
        treat_search = detect_web_search(treatment.get("thinking", ""))

        # Determine trigger display
        if treatment.get("status") == "error":
            trigger_display = "ERROR"
        elif treat_trigger["triggered"]:
            trigger_display = f"YES ({treat_trigger['confidence']})"
        elif treat_trigger["confidence"] == "no_thinking":
            trigger_display = "UNKNOWN (no thinking)"
        else:
            trigger_display = "NO"

        # Web search display
        ctrl_ws = "Y" if ctrl_search["used"] else ("?" if ctrl_search["confidence"] == "no_thinking" else "N")
        treat_ws = "Y" if treat_search["used"] else ("?" if treat_search["confidence"] == "no_thinking" else "N")
        search_display = f"{ctrl_ws} / {treat_ws}"

        # Status
        ctrl_status = control.get("status", "missing")
        treat_status = treatment.get("status", "missing")
        if ctrl_status == "ok" and treat_status == "ok":
            status = "OK"
        elif ctrl_status == "missing" and treat_status == "missing":
            status = "MISSING"
        else:
            problems = []
            if ctrl_status != "ok":
                problems.append(f"C:{ctrl_status}")
            if treat_status != "ok":
                problems.append(f"T:{treat_status}")
            status = ", ".join(problems)

        lines.append(f"| {pid} | {category} | {trigger_display} | {search_display} | {status} |")

        analysis_details.append({
            "pid": pid,
            "category": category,
            "control": control,
            "treatment": treatment,
            "ctrl_trigger": ctrl_trigger,
            "treat_trigger": treat_trigger,
            "ctrl_search": ctrl_search,
            "treat_search": treat_search,
        })

    lines.append("")

    # Trigger summary
    triggered_count = sum(
        1 for d in analysis_details
        if d["treat_trigger"]["triggered"]
    )
    total_valid = sum(
        1 for d in analysis_details
        if d["treatment"].get("status") == "ok"
    )
    lines.append(f"**Skill trigger rate:** {triggered_count}/{total_valid} treatment prompts")
    lines.append("")

    # Detailed per-prompt analysis
    lines.append("## Per-Prompt Analysis")
    lines.append("")

    for d in analysis_details:
        pid = d["pid"]
        category = d["category"]
        control = d["control"]
        treatment = d["treatment"]

        lines.append(f"### {pid}: {category}")
        lines.append("")
        lines.append(f"**Prompt:** {d.get('category', '')}")
        lines.append("")

        # Thinking analysis
        if d["treat_trigger"]["triggered"]:
            evidence = ", ".join(f'"{e}"' for e in d["treat_trigger"]["evidence"])
            lines.append(f"**Skill trigger evidence:** {evidence}")
        elif d["treat_trigger"]["confidence"] == "no_thinking":
            lines.append("**Skill trigger:** Could not assess (thinking text not captured)")
        else:
            lines.append("**Skill trigger:** Not detected in thinking text")

        lines.append("")

        # Side-by-side responses
        lines.append("| | Control | Treatment |")
        lines.append("|---|---------|-----------|")

        ctrl_resp = truncate(control.get("response", ""), 300)
        treat_resp = truncate(treatment.get("response", ""), 300)

        # Escape pipes in response text for markdown table
        ctrl_resp = ctrl_resp.replace("|", "\\|").replace("\n", " ")
        treat_resp = treat_resp.replace("|", "\\|").replace("\n", " ")

        ctrl_status_str = control.get("status", "missing")
        treat_status_str = treatment.get("status", "missing")

        if ctrl_status_str == "error":
            ctrl_resp = f"ERROR: {control.get('error', 'unknown')}"
        if treat_status_str == "error":
            treat_resp = f"ERROR: {treatment.get('error', 'unknown')}"

        lines.append(f"| Status | {ctrl_status_str} | {treat_status_str} |")
        lines.append(f"| Web search | {'Yes' if d['ctrl_search']['used'] else 'No'} | {'Yes' if d['treat_search']['used'] else 'No'} |")
        lines.append(f"| Response (excerpt) | {ctrl_resp} | {treat_resp} |")
        lines.append("")

        # Response length comparison
        ctrl_len = len(control.get("response", ""))
        treat_len = len(treatment.get("response", ""))
        if ctrl_len > 0 and treat_len > 0:
            ratio = treat_len / ctrl_len
            if ratio > 1.2:
                lines.append(f"Treatment response is {ratio:.1f}x longer than control.")
            elif ratio < 0.8:
                lines.append(f"Treatment response is {1/ratio:.1f}x shorter than control.")
            else:
                lines.append("Response lengths are comparable.")
        lines.append("")

    # Thinking text dumps (for manual review)
    lines.append("## Thinking Text Excerpts")
    lines.append("")
    lines.append("Raw thinking text excerpts for manual review of trigger detection accuracy.")
    lines.append("")

    for d in analysis_details:
        pid = d["pid"]
        ctrl_thinking = d["control"].get("thinking", "")
        treat_thinking = d["treatment"].get("thinking", "")

        if ctrl_thinking or treat_thinking:
            lines.append(f"### {pid} Thinking")
            lines.append("")
            if treat_thinking:
                lines.append("**Treatment thinking (excerpt):**")
                lines.append("```")
                lines.append(truncate(treat_thinking, 800))
                lines.append("```")
                lines.append("")
            if ctrl_thinking:
                lines.append("**Control thinking (excerpt):**")
                lines.append("```")
                lines.append(truncate(ctrl_thinking, 800))
                lines.append("```")
                lines.append("")

    # Methodology note
    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Tool:** agent-browser (automated headless browser)")
    lines.append("- **Platform:** Claude.ai web interface")
    lines.append("- **Design:** Within-subject A/B (same prompts, skill OFF then ON)")
    lines.append("- **Skill toggle:** Manual (user toggles between control/treatment phases)")
    lines.append("- **Detection:** Skill triggering inferred from thinking panel keywords;")
    lines.append("  web search inferred from thinking panel text. Both are heuristic-based.")
    lines.append("- **Limitations:** n=5 prompts, qualitative assessment, potential confounds")
    lines.append("  from time gap between conditions and DOM extraction reliability.")
    lines.append("")

    return "\n".join(lines)


def main():
    script_dir = Path(__file__).parent

    # Determine input file
    if len(sys.argv) > 1:
        results_file = Path(sys.argv[1])
    else:
        results_file = script_dir / "browser-eval-results.json"

    if not results_file.exists():
        print(f"Error: Results file not found: {results_file}", file=sys.stderr)
        print("Run browser_eval.sh first, or pass the results file as an argument.", file=sys.stderr)
        sys.exit(1)

    # Load results
    with open(results_file) as f:
        data = json.load(f)

    # Generate report
    report = generate_report(data)

    # Write report
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = script_dir / f"browser-eval-report-{timestamp}.md"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"Report written to: {report_file}")

    # Also print to stdout for immediate review
    print()
    print(report)


if __name__ == "__main__":
    main()

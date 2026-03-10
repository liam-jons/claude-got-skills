#!/usr/bin/env python3
"""
Capabilities Skill Baseline Evaluation (v2.0.0)
===================================================
Runs test prompts in two conditions:
  - Control: No skill context (pure training knowledge)
  - Treatment: SKILL.md content prepended as system context

Features:
  - Multi-run support with mean/stdev reporting
  - LLM-as-judge scoring with SKILL.md rubric for grounded evaluation
  - Keyword synonym groups for reduced false negatives
  - Negative tests to detect regressions
  - Hallucination detection tests (Category 7)
  - Comprehensive markdown reports

Uses the Anthropic Messages API directly for clean isolation.
"""

import anthropic
import httpx
import json
import os
import sys
import time
import argparse
import statistics
from pathlib import Path
from typing import Optional

# Load .env from repo root if present
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            k, v = key.strip(), val.strip().strip('"').strip("'")
            if v and (k not in os.environ or not os.environ[k]):
                os.environ[k] = v

# Default paths (relative to script location)
SCRIPT_DIR = Path(__file__).parent
DEFAULT_SKILL_PATH = SCRIPT_DIR.parent / "skills" / "assistant-capabilities" / "SKILL.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_JUDGE_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2048

# Global config (populated by main)
CONFIG = {
    "model": DEFAULT_MODEL,
    "judge_model": DEFAULT_JUDGE_MODEL,
    "skill_path": DEFAULT_SKILL_PATH,
    "output_dir": DEFAULT_OUTPUT_DIR,
    "runs": 1,
    "use_judge": True,
}

# Load skill content for treatment condition
def load_skill_content(skill_path: Path) -> str:
    """Load and parse skill content, stripping YAML frontmatter."""
    with open(skill_path) as f:
        content = f.read()

    # Strip YAML frontmatter
    lines = content.split('\n')
    fm_count = 0
    body_lines = []
    for line in lines:
        if line.strip() == '---':
            fm_count += 1
            if fm_count <= 2:
                continue
        if fm_count >= 2:
            body_lines.append(line)
    return '\n'.join(body_lines).strip()


TESTS = [
    {
        "id": "1.1",
        "category": "Architecture Decisions",
        "prompt": (
            "I'm building a document analysis pipeline that needs to process "
            "100-page PDFs. The system should extract key information, cross-reference "
            "it with a knowledge base, and produce a structured summary. What "
            "architecture would you recommend? Keep it simple — this is for a small team."
        ),
        "scoring_keywords": {
            "accuracy": ["1m context", "1 million", "context window", "beta",
                         ["files api", "file upload", "upload"], "effort", "cost"],
            "completeness": [["tier 3", "usage tier", "tier"], ["premium pricing", "pricing"],
                             "streaming", ["prompt caching", "caching"], ["batch", "batch processing"]],
            "deprecated_patterns": ["chunk", "split into", "rag only", "embedding-based only"],
        },
    },
    {
        "id": "1.2",
        "category": "Architecture Decisions",
        "prompt": (
            "I need to build a quality assurance system that reviews AI-generated "
            "content before it goes to customers. The system should check for accuracy, "
            "tone, and compliance with our style guide. How would I architect this?"
        ),
        "scoring_keywords": {
            "accuracy": [["agent sdk", "agent"], ["subagent", "sub-agent", "sub agent"],
                         "haiku", "sonnet", "opus", "hook", ["model selection", "choose model", "model choice"]],
            "completeness": ["cost", ["parallel", "concurrent"], ["structured output", "json schema"],
                             ["effort parameter", "effort"], ["prompt caching", "caching"]],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "1.3",
        "category": "Architecture Decisions",
        "prompt": (
            "We want to add AI features to our Next.js app. Users should be able to "
            "ask questions about their data and get real-time streaming responses. "
            "What's the simplest way to integrate Claude into this?"
        ),
        "scoring_keywords": {
            "accuracy": ["streaming", ["tool streaming", "stream tool"], ["structured output", "json schema"],
                         ["messages api", "messages"], "sdk"],
            "completeness": [["mcp connector", "mcp"], ["agent sdk", "agent"], "output_config",
                             ["server-sent events", "sse", "server sent"], ["token counting", "token usage"]],
            "deprecated_patterns": ["output_format"],
        },
    },
    {
        "id": "2.1",
        "category": "Can Claude Do X",
        "prompt": (
            "Can I get Claude to remember things between separate conversations? "
            "I'm building a tool where Claude helps with ongoing projects and it's "
            "frustrating that it loses context each time."
        ),
        "scoring_keywords": {
            "accuracy": ["memory tool", "memory_20250818",
                         ["cross-conversation", "between conversation", "across conversation"],
                         ["persistent", "persist", "store"],
                         ["ga", "generally available", "no header", "no beta"]],
            "completeness": ["view", "create", "str_replace",
                             ["client-side", "client side", "client"],
                             ["compaction", "context editing"]],
            "deprecated_patterns": ["beta header required", "context-management-2025-06-27"],
        },
    },
    {
        "id": "2.2",
        "category": "Can Claude Do X",
        "prompt": (
            "Is there a way to make Claude use tools without me having to define "
            "every single one upfront? I have hundreds of MCP tools and the context "
            "window overhead is killing me."
        ),
        "scoring_keywords": {
            "accuracy": ["tool search", ["dynamic", "dynamically"], ["discovery", "discover"],
                         "regex", ["auto-activate", "auto-activates", "automatically activate"],
                         "10%"],
            "completeness": [["mcp connector", "mcp"], ["defer_loading", "defer", "deferred"],
                             "context", ["enable_tool_search", "tool_search"]],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "2.3",
        "category": "Can Claude Do X",
        "prompt": (
            "I want Claude to help fill out web forms and navigate browser interfaces "
            "for data entry tasks. Is that possible through the API?"
        ),
        "scoring_keywords": {
            "accuracy": ["computer use", "computer_20251124", "computer_20250124",
                         "screenshot", "mouse", "keyboard"],
            "completeness": ["zoom", "beta", ["chrome", "browser"],
                             ["coordinate", "coordinates", "pixel"],
                             ["sandbox", "sandboxed", "isolation"]],
            "deprecated_patterns": [],
        },
    },

    # 2.4: Can Claude Do X — Vision / Image Analysis
    {
        "id": "2.4",
        "category": "Can Claude Do X",
        "prompt": (
            "Can Claude analyze images? I have product photos I want to classify "
            "and extract metadata from. What image formats are supported and how "
            "do I send them through the API?"
        ),
        "scoring_keywords": {
            "accuracy": [["jpeg", "png", "gif", "webp"],
                         ["base64", "inline"],
                         ["url", "image url"],
                         ["all models", "all current models", "natively", "native"]],
            "completeness": [["file_id", "files api", "file id"],
                             ["token", "tokens", "dimension", "width", "height"],
                             ["multi-image", "multiple image", "multiple images"],
                             ["structured output", "json", "json_schema", "output_config"]],
            "deprecated_patterns": ["claude cannot analyze images", "no vision support",
                                    "text-only", "text only model"],
        },
    },

    # 2.5: Can Claude Do X — CoWork
    {
        "id": "2.5",
        "category": "Can Claude Do X",
        "prompt": (
            "What is Claude CoWork? Can I use my custom skills and MCP integrations "
            "there? I heard it's different from Claude.ai — what does it support?"
        ),
        "scoring_keywords": {
            "accuracy": [["cowork"],
                         ["browser", "browser automation", "browser environment"],
                         ["skill", "skills"],
                         ["mcp", "mcp server", "mcp integration"]],
            "completeness": [["plugin", "plugins", "via plugin"],
                             ["no hook", "no hooks", "hooks not", "without hooks"],
                             ["no subagent", "no subagents", "subagents not", "no team", "no teams"],
                             ["slash command", "slash commands", "via plugin"]],
            "deprecated_patterns": [],
        },
    },

    {
        "id": "3.1",
        "category": "Implementation Guidance",
        "prompt": (
            "I'm using Claude Opus 4.6 and want to control how much 'thinking' it "
            "does on different types of requests. Some are simple lookups, others are "
            "complex analysis. How do I configure this?"
        ),
        "scoring_keywords": {
            "accuracy": ["adaptive", "thinking", "effort", "low", "medium", "high", "max"],
            "completeness": [["type: \"adaptive\"", "type: 'adaptive'", "type: adaptive",
                              "\"adaptive\"", "'adaptive'"],
                             ["budget_tokens", "budget tokens"],
                             ["deprecated", "removed", "replaced"],
                             ["opus 4.6", "sonnet 4.6"]],
            "deprecated_patterns": ["budget_tokens"],
        },
    },
    {
        "id": "3.2",
        "category": "Implementation Guidance",
        "prompt": (
            "I have a working integration with Claude that uses assistant message "
            "prefilling to start responses in a specific format. I want to upgrade "
            "to Opus 4.6. Anything I should know?"
        ),
        "scoring_keywords": {
            "accuracy": ["prefill", "removed", "400", "error",
                         ["structured output", "structured outputs", "json schema"],
                         "system prompt"],
            "completeness": ["output_config", ["json_schema", "json schema"],
                             ["breaking change", "breaking", "incompatible"],
                             ["migration", "migrate", "upgrade"]],
            "deprecated_patterns": ["prefill works", "prefill is supported"],
        },
    },
    {
        "id": "3.3",
        "category": "Implementation Guidance",
        "prompt": (
            "I want Claude to output JSON that strictly matches my schema — not "
            "'best effort' but guaranteed. How do I set this up?"
        ),
        "scoring_keywords": {
            "accuracy": [["structured output", "structured outputs"], "output_config",
                         ["json_schema", "json schema"], "strict", ["guaranteed", "guarantee"]],
            "completeness": [["strict: true", "strict:true", "\"strict\": true"],
                             "tool use", ["parse()", ".parse(", "parse method"],
                             ["zodoutputformat", "zod"], "sdk"],
            "deprecated_patterns": ["output_format"],
        },
    },

    # 3.4: Implementation Guidance — PDF Processing
    {
        "id": "3.4",
        "category": "Implementation Guidance",
        "prompt": (
            "I need to process an 80-page contract PDF through the API — extract "
            "key clauses, dates, and party names into structured data. What are "
            "the limits and best practices for PDF processing with Claude?"
        ),
        "scoring_keywords": {
            "accuracy": [["100 page", "100 pages", "100-page"],
                         ["32mb", "32 mb", "32 megabyte"],
                         ["document", "type.*document"],
                         ["base64", "url", "file_id", "files api"]],
            "completeness": [["token counting", "count_tokens", "estimate cost", "estimate token"],
                             ["structured output", "output_config", "json_schema"],
                             ["scanned", "ocr"],
                             ["bedrock", "citation"]],
            "deprecated_patterns": [],
        },
    },

    # 3.5: Implementation Guidance — Streaming with Tool Use
    {
        "id": "3.5",
        "category": "Implementation Guidance",
        "prompt": (
            "I'm building a chat interface where Claude uses tools (web search, "
            "code execution). I want real-time streaming but I'm confused about "
            "how streaming works when Claude makes tool calls. How do I implement "
            "streaming with tool use?"
        ),
        "scoring_keywords": {
            "accuracy": [["stream", "streaming", "stream: true"],
                         ["sse", "server-sent events", "server sent events"],
                         ["tool_use", "tool use", "tool call"],
                         ["content_block_delta", "content block delta", "delta"]],
            "completeness": [["message_start", "message start"],
                             ["stop_reason", "stop reason", "end_turn"],
                             ["fine-grained", "fine grained", "progressive"],
                             ["content_block_stop", "content_block_start"]],
            "deprecated_patterns": [],
        },
    },

    # 3.6: Implementation Guidance — Fast Mode
    {
        "id": "3.6",
        "category": "Implementation Guidance",
        "prompt": (
            "I need Claude Opus to generate responses faster for my real-time "
            "application. I heard there's a fast mode. How does it work, what's "
            "the pricing, and are there any limitations?"
        ),
        "scoring_keywords": {
            "accuracy": [["speed", "speed.*fast", "\"fast\"", "'fast'"],
                         ["fast-mode-2026-02-01", "fast mode", "beta header"],
                         ["2.5x", "2.5 times", "faster output"],
                         ["6x", "six times", "$30", "$150"]],
            "completeness": [["opus 4.6", "opus only", "only opus"],
                             ["batch", "not available with batch", "no batch"],
                             ["waitlist", "gated"],
                             ["prompt cache", "cache invalidat", "invalidates"]],
            "deprecated_patterns": ["fast mode is free", "available on all models",
                                    "no additional cost", "sonnet fast mode"],
        },
    },

    # 3.7: Implementation Guidance — Automatic Caching
    {
        "id": "3.7",
        "category": "Implementation Guidance",
        "prompt": (
            "I have a multi-turn conversation app and I want to use prompt caching "
            "without manually managing cache breakpoints as the conversation grows. "
            "Is there a way to make caching automatic?"
        ),
        "scoring_keywords": {
            "accuracy": [["automatic caching", "auto caching", "automatic cache", "request level",
                          "request-level"],
                         ["cache_control", "cache control"],
                         ["ephemeral", "\"ephemeral\"", "'ephemeral'"],
                         ["no manual", "without manual", "automatically"]],
            "completeness": [["4 breakpoint", "four breakpoint", "breakpoint slot"],
                             ["walks backward", "nearest eligible", "backward"],
                             ["block-level", "block level", "explicit", "alongside"],
                             ["10%", "cost saving", "cached read"]],
            "deprecated_patterns": [],
        },
    },

    # 3.8: Implementation Guidance — Dynamic Filtering
    {
        "id": "3.8",
        "category": "Implementation Guidance",
        "prompt": (
            "When I use Claude's web search tool, I get a lot of irrelevant results "
            "cluttering the context window. Is there a way to filter or clean up "
            "web search results before they hit the context?"
        ),
        "scoring_keywords": {
            "accuracy": [["dynamic filtering", "filter", "filtering"],
                         ["web_search_20260209", "20260209"],
                         ["code execution", "code sandbox", "sandbox"],
                         ["context window", "context", "reduce noise", "clean up"]],
            "completeness": [["web_fetch_20260209", "web fetch"],
                             ["opus", "sonnet 4.6"],
                             ["free", "free when used", "no additional cost"],
                             ["tool version", "newer version", "updated tool"]],
            "deprecated_patterns": [],
        },
    },

    {
        "id": "4.1",
        "category": "Model Selection",
        "prompt": (
            "I need to choose a Claude model for my application. It needs to handle "
            "long documents (200+ pages), produce detailed analysis, and keep costs "
            "reasonable. What would you recommend?"
        ),
        "scoring_keywords": {
            "accuracy": ["opus 4.6", ["sonnet 4.6", "sonnet 4.5"], "haiku 4.5",
                         "128k", "64k", ["1m", "1 million", "million token"], "200k"],
            "completeness": ["effort", ["batch", "batch processing"],
                             ["prompt caching", "caching", "automatic caching"], "cost",
                             ["interleaved thinking", "interleaved"],
                             ["adaptive", "adaptive thinking"]],
            "deprecated_patterns": [],
        },
    },

    # Category 5: Extension Awareness & "Art of the Possible"
    {
        "id": "5.1",
        "category": "Extension Awareness",
        "prompt": (
            "I write proposals for clients every week. Each one follows our standard "
            "template with an executive summary, scope section, pricing table, and "
            "terms. Can you help me write one for Acme Corp?"
        ),
        "scoring_keywords": {
            "accuracy": ["skill", ["repeatable", "repeat", "reusable"], ["workflow", "process"],
                         "template", ["reuse", "re-use"], "/"],
            "completeness": [["build a skill", "create a skill", "make a skill", "write a skill"],
                             ["capture", "encode", "save"],
                             ["skills.sh", "skill registry", "skill marketplace"],
                             ["plugin", "plugins"], ["automate", "automation"]],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "5.2",
        "category": "Extension Awareness",
        "prompt": (
            "Every time I edit a Python file, I want to make sure it passes our "
            "linting rules and type checks. Right now I keep forgetting to run "
            "the checks. Is there a way to automate this?"
        ),
        "scoring_keywords": {
            "accuracy": ["hook", ["posttooluse", "post tool use", "post-tool-use"],
                         ["pretooluse", "pre tool use", "pre-tool-use"],
                         ["event", "lifecycle", "trigger"],
                         ["automatic", "automatically"], ["deterministic", "predictable"]],
            "completeness": [["command", "shell command", "script"],
                             ["shell", "bash", "terminal"],
                             "edit", ["no llm", "no token", "without llm", "without the llm",
                                      "zero token", "doesn't use token", "no ai"]],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "5.3",
        "category": "Extension Awareness",
        "prompt": (
            "I want Claude to always know about our company's API conventions — "
            "things like 'use camelCase for JSON fields', 'always include pagination', "
            "'use ISO 8601 dates'. Where should I put this information?"
        ),
        "scoring_keywords": {
            "accuracy": ["claude.md", "skill", ["always", "every session", "every time"],
                         ["persistent", "persists", "loaded every"],
                         ["convention", "conventions", "rules"]],
            "completeness": [["500 lines", "500", "keep it short", "concise"],
                             ["reference", "reference file"],
                             ["on-demand", "on demand", "when relevant", "when needed"],
                             ["project", ".claude"], ["user", "~/.claude"]],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "5.4",
        "category": "Extension Awareness",
        "prompt": (
            "I need to create a PowerPoint presentation about our quarterly results. "
            "Is there a good way to do this with Claude?"
        ),
        "scoring_keywords": {
            "accuracy": ["skill", "pptx", ["presentation", "slides", "slide deck"],
                         ["document", "doc"], ["pre-built", "prebuilt", "built-in", "existing"],
                         "anthropic"],
            "completeness": [["formatting", "format"], ["template", "templates"],
                             ["best practices", "best practice", "guidelines"],
                             "skill", ["install", "add", "npx skills"]],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "5.5",
        "category": "Extension Awareness",
        "prompt": (
            "I have a complex setup with Claude: custom code review rules, a Slack "
            "integration for notifications, auto-formatting hooks, and some reference "
            "docs about our architecture. How do I share this setup with my team so "
            "everyone has the same Claude experience?"
        ),
        "scoring_keywords": {
            "accuracy": ["plugin", ["bundle", "package", "combine"],
                         ["distribute", "share", "distribute"],
                         ["marketplace", "registry"], ["install", "npx"]],
            "completeness": ["skills", "hooks", "mcp",
                             ["namespace", "namespaced"],
                             ["plugin.json", "manifest"],
                             ["repository", "repo", "git"]],
            "deprecated_patterns": [],
        },
    },

    # Category 5b: Automation & Scheduling (NEW)
    {
        "id": "5.6",
        "category": "Extension Awareness",
        "prompt": (
            "I want Claude to check my deployment status every 5 minutes and "
            "let me know if anything goes wrong. Is there a way to set up "
            "recurring monitoring like that?"
        ),
        "scoring_keywords": {
            "accuracy": [["loop", "/loop"], ["recurring", "interval", "periodic", "every"],
                         ["background", "background task"],
                         ["monitor", "monitoring", "poll", "polling"],
                         ["cron", "schedule", "scheduled"]],
            "completeness": [["5m", "5 minutes", "five minute"],
                             ["ctrl+b", "ctrl-b", "background"],
                             ["/tasks", "task list", "manage tasks"],
                             ["croncreate", "cron tool", "cron create"]],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "5.7",
        "category": "Extension Awareness",
        "prompt": (
            "I have a test suite that takes 10 minutes to run. I don't want "
            "to sit and wait for it. Can Claude run it in the background while "
            "I keep working on other things?"
        ),
        "scoring_keywords": {
            "accuracy": [["background", "background task", "asynchronous"],
                         ["run_in_background", "run in background"],
                         ["ctrl+b", "ctrl-b"],
                         ["continue", "keep working", "while you"]],
            "completeness": [["task", "task id", "task_id"],
                             ["taskoutput", "task output", "retrieve", "check output"],
                             ["/tasks", "task list"],
                             ["notification", "notify", "notified"]],
            "deprecated_patterns": [],
        },
    },

    # 5.8: Extension Awareness — Platform Comparison
    {
        "id": "5.8",
        "category": "Extension Awareness",
        "prompt": (
            "I built a custom skill for Claude Code and it works great. Now my "
            "colleague wants to use it on Claude.ai (the web app) and another "
            "teammate uses Claude Desktop. How do I get the same skill working "
            "across all three platforms?"
        ),
        "scoring_keywords": {
            "accuracy": [["zip", "zip file", "zip upload", "zip package"],
                         ["settings", "capabilities", "settings > capabilities"],
                         ["auto-invoke", "auto-invocation", "auto invoke", "automatically trigger",
                          "automatically invoked"],
                         ["no slash", "slash commands not", "can't use slash", "without slash",
                          "no / commands"]],
            "completeness": [["claude.ai", "web app"],
                             ["desktop", "claude desktop"],
                             ["claude code", "cli"],
                             ["reference file", "reference files", "read tool",
                              "cannot read reference", "no reference file access"]],
            "deprecated_patterns": [],
        },
    },

    # Category 6: Negative Tests (No Change Expected)
    {
        "id": "6.1",
        "category": "Negative (No Change Expected)",
        "prompt": "Write a Python function that takes a list of dictionaries and sorts them by a specified key. Include type hints and handle the case where the key doesn't exist.",
        "scoring_keywords": {
            "accuracy": ["def ", "sorted", "key", "lambda", "typeerror", "keyerror"],
            "completeness": ["type hint", "typing", "optional", "default", "reverse"],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "6.2",
        "category": "Negative (No Change Expected)",
        "prompt": "Explain the difference between TCP and UDP. When would you use each one?",
        "scoring_keywords": {
            "accuracy": ["reliable", "connection", "packet", "order", "stream"],
            "completeness": ["handshake", "overhead", "latency", "gaming", "video"],
            "deprecated_patterns": [],
        },
    },
    {
        "id": "6.3",
        "category": "Negative (No Change Expected)",
        "prompt": "My React component re-renders every time the parent updates, even when its props haven't changed. How do I fix this?",
        "scoring_keywords": {
            "accuracy": ["memo", "usememo", "usecallback", "react.memo", "render"],
            "completeness": ["reference", "shallow", "comparison", "profiler", "performance"],
            "deprecated_patterns": [],
        },
    },

    # Category 7: Hallucination Detection
    # These test whether the skill helps Claude avoid confident-but-wrong answers.
    # Scoring is INVERTED: accuracy keywords are things the response SHOULD say (corrections),
    # and deprecated_patterns are hallucinated claims to avoid.
    {
        "id": "7.1",
        "category": "Hallucination Detection",
        "prompt": (
            "Can Claude Code access my browser cookies and browsing history? "
            "I want to build a tool that analyzes my browsing patterns."
        ),
        "scoring_keywords": {
            "accuracy": [["cannot", "can't", "does not", "doesn't", "no access", "not able"],
                         ["sandbox", "sandboxed", "isolation", "isolated"],
                         ["computer use", "screenshot"], ["api", "separate"]],
            "completeness": [["filesystem", "file system", "files"],
                             ["network", "network isolation"],
                             ["browser", "chrome"]],
            "deprecated_patterns": ["yes, claude can access", "access your cookies",
                                    "read your browser history", "browsing data directly"],
        },
    },
    {
        "id": "7.2",
        "category": "Hallucination Detection",
        "prompt": (
            "Does Claude remember things between conversations by default? "
            "I've been chatting with it for weeks and want to make sure it "
            "knows my preferences."
        ),
        "scoring_keywords": {
            "accuracy": [["does not remember", "doesn't remember", "no memory by default",
                          "not retain", "doesn't retain", "does not persist", "no default memory"],
                         ["memory tool", "memory"],
                         ["opt-in", "enable", "configure", "set up"],
                         ["client-side", "client side", "explicit"]],
            "completeness": [["ga", "generally available", "no header"],
                             ["store", "retrieve", "persistent"],
                             ["each conversation", "each session", "new conversation", "new session"]],
            "deprecated_patterns": ["claude remembers by default", "automatically remembers",
                                    "built-in memory across", "naturally retains",
                                    "memory is in beta", "beta header"],
        },
    },
    {
        "id": "7.3",
        "category": "Hallucination Detection",
        "prompt": (
            "Can Claude access the internet and make HTTP requests to external "
            "APIs by default? I want it to pull live data from my REST API."
        ),
        "scoring_keywords": {
            "accuracy": [["not by default", "doesn't have", "does not have",
                          "no internet by default", "no network access by default"],
                         ["tool", "tool use", "tools"],
                         ["web search", "web fetch", "mcp"],
                         ["configure", "enable", "provide"]],
            "completeness": [["mcp connector", "mcp server", "mcp"],
                             ["code execution", "sandbox", "container"],
                             ["built-in tool", "web_search", "web search tool"]],
            "deprecated_patterns": ["claude can access any api", "claude has internet by default",
                                    "directly call your api", "make http requests natively"],
        },
    },
    {
        "id": "7.4",
        "category": "Hallucination Detection",
        "prompt": (
            "I heard Claude can run any programming language — Python, Rust, Go, "
            "Java, C++. Can I use it for compiling and running Rust code?"
        ),
        "scoring_keywords": {
            "accuracy": [["code execution", "code sandbox", "code container"],
                         ["python", "javascript", "limited"],
                         ["not all languages", "specific languages", "sandboxed environment",
                          "container"]],
            "completeness": [["bash", "shell", "terminal"],
                             ["install", "package"],
                             ["computer use", "alternative"]],
            "deprecated_patterns": ["compile rust directly", "supports all languages natively",
                                    "run any language", "full rust compiler"],
        },
    },

    # 7.5: Hallucination Detection — Model Deprecation
    {
        "id": "7.5",
        "category": "Hallucination Detection",
        "prompt": (
            "I have a production system using Claude Sonnet 3.7 (claude-3-7-sonnet). "
            "A teammate says we need to migrate urgently. Is Sonnet 3.7 still available? "
            "What should we move to?"
        ),
        "scoring_keywords": {
            "accuracy": [["retired", "deprecated", "removed", "end of life", "no longer available",
                          "shut down", "discontinued"],
                         ["feb 2026", "february 2026"],
                         ["sonnet 4.5", "sonnet 4.6", "claude-sonnet-4-5", "claude-sonnet-4-6"],
                         ["migrate", "upgrade", "switch", "move to"]],
            "completeness": [["haiku 3.5", "haiku 3 retiring", "haiku 3"],
                             ["breaking change", "breaking", "incompatible", "prefill"],
                             ["structured output", "output_config"],
                             ["model id", "model identifier", "claude-sonnet-4"]],
            "deprecated_patterns": ["sonnet 3.7 is still available", "sonnet 3.7 is supported",
                                    "sonnet 3.7 is the latest", "3.7 is current",
                                    "no need to migrate"],
        },
    },

    # ================================================================
    # Category 8: Cross-Platform Awareness
    # Tests whether the skill helps Claude guide users to capabilities
    # on OTHER platforms, not just confirm/deny for their current one.
    # ================================================================

    # 8.1: Desktop user asking about automation → should learn about Code
    {
        "id": "8.1",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I'm using Claude Desktop for my daily work. I need to set up "
            "automated tasks — like running linting after every file edit and "
            "monitoring a service every 5 minutes. Is any of this possible?"
        ),
        "scoring_keywords": {
            "accuracy": [["claude code", "cli", "code cli"],
                         ["hook", "hooks"],
                         ["/loop", "loop", "recurring"],
                         ["cron", "schedule", "scheduled"],
                         ["not available on desktop", "not supported on desktop",
                          "desktop doesn't", "desktop does not"]],
            "completeness": [["posttooluse", "post tool use", "post-tool-use", "lifecycle"],
                             ["background", "background task", "ctrl+b"],
                             ["deterministic", "no tokens", "no llm"],
                             ["mcp", "mcp server"]],
            "deprecated_patterns": ["desktop supports hooks", "desktop has automation",
                                    "desktop can schedule", "desktop supports /loop"],
        },
    },

    # 8.2: Claude.ai user asking about skills → should learn Code slash commands
    {
        "id": "8.2",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I installed a skill on Claude.ai by uploading a ZIP file. It works "
            "when I ask about the topic, but I can't figure out how to invoke it "
            "directly by name. Is there a way to trigger a specific skill on demand?"
        ),
        "scoring_keywords": {
            "accuracy": [["auto-invoke", "auto-invocation", "auto invoke",
                          "automatically trigger", "automatically invoked"],
                         ["no slash", "slash commands not", "can't use slash",
                          "no / commands", "no slash command"],
                         ["claude code", "cli"],
                         ["slash command", "/name", "slash /"]],
            "completeness": [["natural language", "describe your need", "ask about"],
                             ["plugin", "plugins", "via plugin"],
                             ["cowork", "co-work"],
                             ["bundled", "built-in", "/simplify", "/batch", "/debug", "/loop"]],
            "deprecated_patterns": ["slash commands work on claude.ai",
                                    "type / to invoke", "use / on claude.ai"],
        },
    },

    # 8.3: API user asking about persistent context → should learn CLAUDE.md + Projects
    {
        "id": "8.3",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I'm building a product with the Claude API. I want to store our "
            "company's coding standards and style guide so Claude always knows "
            "them. Right now I'm pasting them into system prompts every time. "
            "Is there a better way?"
        ),
        "scoring_keywords": {
            "accuracy": [["system prompt", "system message"],
                         ["claude.md", "CLAUDE.md"],
                         ["project", "projects"],
                         ["skill", "skills"],
                         ["prompt caching", "caching", "cache"]],
            "completeness": [["claude code", "cli"],
                             ["claude.ai", "web app"],
                             ["persistent", "persists", "always loaded"],
                             ["reference file", "reference files", "on-demand"]],
            "deprecated_patterns": [],
        },
    },

    # 8.4: Code user asking about Projects and Artifacts → should learn Claude.ai features
    {
        "id": "8.4",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I use Claude Code in my terminal every day. A colleague showed me "
            "something on Claude.ai where they had a 'Project' with uploaded "
            "documents that Claude always referenced. They also had some kind of "
            "interactive widget Claude created. What are these features, and can "
            "I get them in Claude Code?"
        ),
        "scoring_keywords": {
            "accuracy": [["project", "projects"],
                         ["artifact", "artifacts", "mcp app", "mcp apps"],
                         ["claude.ai", "web app", "web interface"],
                         ["claude.md", "CLAUDE.md"]],
            "completeness": [["persistent context", "always referenced", "project knowledge"],
                             ["desktop", "claude desktop"],
                             ["interactive", "html", "ui"],
                             ["equivalent", "alternative", "instead"]],
            "deprecated_patterns": ["projects are available in claude code",
                                    "artifacts work in claude code"],
        },
    },

    # 8.5: CoWork user asking about what they're missing
    {
        "id": "8.5",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "My team uses Claude in CoWork. We have skills and MCP integrations "
            "through plugins. But I keep hearing about Claude Code features like "
            "'subagents', 'hooks', and 'agent teams'. What are we missing by "
            "being on CoWork instead of Claude Code?"
        ),
        "scoring_keywords": {
            "accuracy": [["subagent", "subagents", "agent tool"],
                         ["hook", "hooks"],
                         ["agent team", "agent teams", "team", "teams"],
                         ["not available", "not supported", "missing", "don't have",
                          "doesn't support"]],
            "completeness": [["background", "background task", "/loop"],
                             ["claude.md", "CLAUDE.md", ".claude/rules"],
                             ["plugin", "plugins"],
                             ["browser", "browser automation"]],
            "deprecated_patterns": ["cowork supports hooks", "cowork has subagents",
                                    "cowork supports agent teams",
                                    "cowork supports background tasks"],
        },
    },

    # 8.6: MCP availability across platforms
    {
        "id": "8.6",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "Can Claude connect to external services like Slack, GitHub, and "
            "databases? I need to set this up but I'm not sure which Claude "
            "platform to use. I've tried Claude.ai, Desktop, and Claude Code."
        ),
        "scoring_keywords": {
            "accuracy": [["mcp", "mcp server", "mcp connector"],
                         ["claude.ai", "web"],
                         ["desktop", "claude desktop"],
                         ["claude code", "cli"],
                         ["connector", "connectors"]],
            "completeness": [["settings", "config", "configuration"],
                             ["stdio", "sse", "http"],
                             ["plugin", "plugins"],
                             ["api", "messages api", "beta header"]],
            "deprecated_patterns": [],
        },
    },

    # 8.7: Desktop user asking about memory → full landscape
    {
        "id": "8.7",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I use Claude Desktop and I wish it could remember my preferences "
            "across conversations — like my coding style, project names, and "
            "which frameworks I use. What are my options?"
        ),
        "scoring_keywords": {
            "accuracy": [["memory tool", "memory_20250818", "memory"],
                         ["project", "projects"],
                         ["claude.md", "CLAUDE.md"],
                         ["skill", "skills"]],
            "completeness": [["claude code", "cli"],
                             ["claude.ai", "web"],
                             ["persistent", "cross-conversation", "between conversation"],
                             ["api", "client-side", "client side"]],
            "deprecated_patterns": ["memory is not available", "claude cannot remember",
                                    "no way to persist"],
        },
    },

    # 8.8: Full extension pattern matrix
    {
        "id": "8.8",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I want to understand all the different ways I can extend and "
            "customize Claude. I use a mix of Claude.ai for brainstorming, "
            "Claude Code for development, and the API for my product. Give "
            "me the complete picture of what's available where."
        ),
        "scoring_keywords": {
            "accuracy": [["skill", "skills"],
                         ["hook", "hooks"],
                         ["plugin", "plugins"],
                         ["mcp", "mcp server", "mcp connector"],
                         ["project", "projects"],
                         ["claude.md", "CLAUDE.md"]],
            "completeness": [["subagent", "subagents", "agent tool"],
                             ["background", "/loop", "cron"],
                             ["zip", "zip upload", "zip file"],
                             ["table", "matrix", "comparison"]],
            "deprecated_patterns": [],
        },
    },

    # 8.9: API vs Code code execution differences
    {
        "id": "8.9",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I'm building an API integration and I want Claude to run Python "
            "code to analyze data. I know about the code execution tool in the "
            "API. But I also have developers who use Claude Code directly — do "
            "they get the same code execution capabilities, or is it different?"
        ),
        "scoring_keywords": {
            "accuracy": [["code_execution", "code execution", "code sandbox"],
                         ["api", "messages api"],
                         ["claude code", "cli"],
                         ["bash", "terminal", "shell"]],
            "completeness": [["sandbox", "sandboxed", "container", "isolated"],
                             ["python", "javascript"],
                             ["filesystem", "file system", "local files"],
                             ["programmatic tool calling", "ptc", "programmatic"]],
            "deprecated_patterns": [],
        },
    },

    # 8.10: Claude.ai user wanting agent workflows → should learn about Code
    {
        "id": "8.10",
        "category": "Cross-Platform Awareness",
        "prompt": (
            "I'm on Claude.ai and I want to build a multi-step workflow where "
            "Claude reviews code, runs tests, and then creates a PR. Each step "
            "needs different instructions. Is this possible on Claude.ai, or "
            "do I need something else?"
        ),
        "scoring_keywords": {
            "accuracy": [["claude code", "cli"],
                         ["subagent", "subagents", "agent tool"],
                         ["agent team", "agent teams"],
                         ["not on claude.ai", "not available on claude.ai",
                          "claude.ai doesn't", "claude.ai does not",
                          "not supported on claude.ai"]],
            "completeness": [["hook", "hooks"],
                             ["background", "background task"],
                             ["agent sdk", "sdk"],
                             ["api", "orchestrat"]],
            "deprecated_patterns": ["claude.ai supports subagents",
                                    "claude.ai has agent teams",
                                    "multi-step workflows on claude.ai"],
        },
    },
]


def match_keyword_or_synonyms(keyword_entry, resp_lower: str) -> bool:
    """Match a keyword entry against a response. Supports synonym groups.

    A keyword entry can be:
      - str: exact keyword match (original behavior)
      - list/tuple: synonym group — any match counts as a hit
    """
    if isinstance(keyword_entry, (list, tuple)):
        return any(syn.lower() in resp_lower for syn in keyword_entry)
    return keyword_entry.lower() in resp_lower


def get_keyword_label(keyword_entry) -> str:
    """Get a display label for a keyword entry."""
    if isinstance(keyword_entry, (list, tuple)):
        return keyword_entry[0]  # Use first synonym as label
    return keyword_entry


def keyword_score(response: str, test: dict) -> dict:
    """Score response by keyword matches. Supports synonym groups.

    Keywords can be plain strings or lists of synonyms. When a list is
    provided, matching ANY synonym in the group counts as one hit.
    This reduces false negatives from model paraphrasing.
    """
    resp_lower = response.lower()
    kw = test["scoring_keywords"]

    acc_hits = [get_keyword_label(k) for k in kw.get("accuracy", [])
                if match_keyword_or_synonyms(k, resp_lower)]
    comp_hits = [get_keyword_label(k) for k in kw.get("completeness", [])
                 if match_keyword_or_synonyms(k, resp_lower)]
    dep_hits = [get_keyword_label(k) for k in kw.get("deprecated_patterns", [])
                if match_keyword_or_synonyms(k, resp_lower)]

    acc_total = len(kw.get("accuracy", []))
    comp_total = len(kw.get("completeness", []))

    return {
        "accuracy_matched": acc_hits,
        "accuracy_score": len(acc_hits),
        "accuracy_total": acc_total,
        "accuracy_pct": round(len(acc_hits) / acc_total * 100, 1) if acc_total else 0,
        "completeness_matched": comp_hits,
        "completeness_score": len(comp_hits),
        "completeness_total": comp_total,
        "completeness_pct": round(len(comp_hits) / comp_total * 100, 1) if comp_total else 0,
        "deprecated_found": dep_hits,
        "deprecated_count": len(dep_hits),
        "avoids_deprecated": 1 if len(dep_hits) == 0 else 0,
    }


def judge_score(client, test: dict, response: str, skill_body: str) -> Optional[dict]:
    """Use LLM as judge to score response on multiple dimensions.

    The judge receives the full SKILL.md content as a rubric so it can
    evaluate whether responses correctly reference current Claude capabilities,
    API features, and extension patterns.
    """
    kw = test["scoring_keywords"]

    # Derive expected knowledge from keywords (handle synonym groups)
    expected_keywords = []
    for entry in kw.get("accuracy", [])[:3] + kw.get("completeness", [])[:3]:
        if isinstance(entry, (list, tuple)):
            expected_keywords.append(entry[0])  # Use first synonym as label
        else:
            expected_keywords.append(entry)
    expected_knowledge = ", ".join(expected_keywords) if expected_keywords else "Claude capabilities and best practices"

    # Build judge system prompt with SKILL.md as ground truth rubric
    judge_system = f"""You are an expert evaluator scoring AI responses about Claude's capabilities.

IMPORTANT: Use the following reference document as GROUND TRUTH for what Claude can actually do.
Responses that mention specific features, parameter names, headers, or patterns from this
reference are MORE accurate than generic responses, even if the generic response sounds confident.

## Ground Truth Reference (Claude Capabilities)
{skill_body}

## END OF REFERENCE

Score the response below against this ground truth. A response that mentions specific
API headers, model IDs, tool type strings, or extension patterns from the reference
is more accurate than one that gives vague or generic advice."""

    judge_prompt = f"""## Original Prompt
{test['prompt']}

## Expected Knowledge
A good answer should include concepts like: {expected_knowledge}

## Response to Evaluate
{response}

## Scoring Rubric
Rate each dimension 0-3:
- **Accuracy** (0-3): 0=Incorrect/outdated info, 1=Partially correct but vague, 2=Correct and specific, 3=Correct with exact parameter names, headers, versions from the reference
- **Completeness** (0-3): 0=Misses the key capability entirely, 1=Mentions it vaguely, 2=Covers main points with some specifics, 3=Main points + edge cases + practical guidance
- **Actionability** (0-2): 0=Vague suggestions, 1=Gives direction, 2=Gives specific code/config the user can use

Also check:
- **Avoids Deprecated** (0-1): 1=Uses current approaches per reference, 0=Recommends deprecated patterns

Return ONLY a JSON object (keep reasoning under 15 words):
{{"accuracy": N, "completeness": N, "actionability": N, "avoids_deprecated": N, "reasoning": "brief"}}"""

    try:
        messages = [
            {"role": "user", "content": judge_prompt},
            {"role": "assistant", "content": "{"},
        ]
        response_obj = client.messages.create(
            model=CONFIG["judge_model"],
            max_tokens=512,
            system=judge_system,
            messages=messages,
        )
        judge_text = "{" + response_obj.content[0].text

        # Try direct parse first, then extract JSON from markdown
        try:
            judge_result = json.loads(judge_text)
            return judge_result
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks or multiline
            import re

            json_match = re.search(
                r"\{[^{}]*\"reasoning\"[^{}]*\}", judge_text, re.DOTALL
            )
            if not json_match:
                json_match = re.search(r"\{.*?\}", judge_text, re.DOTALL)
            if json_match:
                try:
                    judge_result = json.loads(json_match.group())
                    return judge_result
                except json.JSONDecodeError as e2:
                    print(
                        f"\n  [Judge parse error for test {test['id']}]: {e2}"
                    )
                    return None
            else:
                print(
                    f"\n  [Judge parse error for test {test['id']}]: No JSON found in: {judge_text[:100]}"
                )
                return None
    except Exception as e:
        print(f"\n  [Judge error for test {test['id']}]: {e}")
        return None


def run_test(client, test: dict, condition: str, skill_body: str) -> dict:
    """Run a single test in either control or treatment condition."""
    messages = [{"role": "user", "content": test["prompt"]}]

    if condition == "treatment":
        system_msg = (
            "You have access to the following capabilities reference. "
            "Use it to inform your response where relevant:\n\n"
            + skill_body
        )
    else:
        system_msg = "You are a helpful AI assistant."

    try:
        response = client.messages.create(
            model=CONFIG["model"],
            max_tokens=MAX_TOKENS,
            system=system_msg,
            messages=messages,
        )
        text = response.content[0].text
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
    except Exception as e:
        text = f"ERROR: {e}"
        usage = {"input_tokens": 0, "output_tokens": 0}

    scores = keyword_score(text, test)

    # Add judge scores if enabled
    judge_result = None
    if CONFIG["use_judge"]:
        judge_result = judge_score(client, test, text, skill_body)

    return {
        "test_id": test["id"],
        "category": test["category"],
        "condition": condition,
        "response": text,
        "scores": scores,
        "judge_scores": judge_result,
        "usage": usage,
    }


def aggregate_results(all_results: list, tests: list, conditions: list) -> dict:
    """Aggregate results across runs, computing means and stdevs."""
    aggregated = {}

    for test in tests:
        aggregated[test["id"]] = {}
        for condition in conditions:
            # Get all results for this test/condition combo
            matching = [r for r in all_results if r["test_id"] == test["id"] and r["condition"] == condition]

            if not matching:
                continue

            acc_scores = [r["scores"]["accuracy_score"] for r in matching]
            comp_scores = [r["scores"]["completeness_score"] for r in matching]
            dep_counts = [r["scores"]["deprecated_count"] for r in matching]

            # Judge scores if available
            judge_acc = None
            judge_comp = None
            judge_action = None
            judge_deprecated = None
            if matching[0]["judge_scores"]:
                judge_acc = [r["judge_scores"]["accuracy"] for r in matching if r["judge_scores"]]
                judge_comp = [r["judge_scores"]["completeness"] for r in matching if r["judge_scores"]]
                judge_action = [r["judge_scores"]["actionability"] for r in matching if r["judge_scores"]]
                judge_deprecated = [r["judge_scores"]["avoids_deprecated"] for r in matching if r["judge_scores"]]

            aggregated[test["id"]][condition] = {
                "accuracy_score": acc_scores[0] if len(acc_scores) == 1 else {
                    "mean": round(statistics.mean(acc_scores), 2),
                    "stdev": round(statistics.stdev(acc_scores), 2) if len(acc_scores) > 1 else 0,
                },
                "completeness_score": comp_scores[0] if len(comp_scores) == 1 else {
                    "mean": round(statistics.mean(comp_scores), 2),
                    "stdev": round(statistics.stdev(comp_scores), 2) if len(comp_scores) > 1 else 0,
                },
                "deprecated_count": dep_counts[0] if len(dep_counts) == 1 else {
                    "mean": round(statistics.mean(dep_counts), 2),
                    "stdev": round(statistics.stdev(dep_counts), 2) if len(dep_counts) > 1 else 0,
                },
                "judge_accuracy": judge_acc[0] if judge_acc and len(judge_acc) == 1 else {
                    "mean": round(statistics.mean(judge_acc), 2),
                    "stdev": round(statistics.stdev(judge_acc), 2) if judge_acc and len(judge_acc) > 1 else 0,
                } if judge_acc else None,
                "judge_completeness": judge_comp[0] if judge_comp and len(judge_comp) == 1 else {
                    "mean": round(statistics.mean(judge_comp), 2),
                    "stdev": round(statistics.stdev(judge_comp), 2) if judge_comp and len(judge_comp) > 1 else 0,
                } if judge_comp else None,
                "judge_actionability": judge_action[0] if judge_action and len(judge_action) == 1 else {
                    "mean": round(statistics.mean(judge_action), 2),
                    "stdev": round(statistics.stdev(judge_action), 2) if judge_action and len(judge_action) > 1 else 0,
                } if judge_action else None,
                "judge_avoids_deprecated": judge_deprecated[0] if judge_deprecated and len(judge_deprecated) == 1 else {
                    "mean": round(statistics.mean(judge_deprecated), 2),
                    "stdev": round(statistics.stdev(judge_deprecated), 2) if judge_deprecated and len(judge_deprecated) > 1 else 0,
                } if judge_deprecated else None,
                "num_runs": len(matching),
            }

    return aggregated


def compute_regression_score(aggregated: dict, test_id: str) -> float:
    """For negative tests, compute regression as abs difference between conditions."""
    if test_id not in aggregated:
        return 0.0

    ctrl = aggregated[test_id].get("control", {})
    trt = aggregated[test_id].get("treatment", {})

    # Extract scores (handle both single values and {mean, stdev})
    def get_value(score):
        if isinstance(score, dict):
            return score.get("mean", 0)
        return score

    ctrl_acc = get_value(ctrl.get("accuracy_score", 0))
    trt_acc = get_value(trt.get("accuracy_score", 0))
    ctrl_comp = get_value(ctrl.get("completeness_score", 0))
    trt_comp = get_value(trt.get("completeness_score", 0))

    # Regression is delta from control
    delta_acc = abs(trt_acc - ctrl_acc)
    delta_comp = abs(trt_comp - ctrl_comp)

    return delta_acc + delta_comp


def format_score(score) -> str:
    """Format a score value (int or {mean, stdev})."""
    if isinstance(score, dict):
        return f"{score['mean']}±{score['stdev']}"
    return str(score)


def main():
    global CONFIG

    parser = argparse.ArgumentParser(description="Capabilities Skill Evaluation")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model to evaluate")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL, help="Judge model for LLM scoring")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs per test/condition")
    parser.add_argument("--no-judge", action="store_true", help="Skip LLM-as-judge scoring")
    parser.add_argument("--skill-path", type=Path, default=DEFAULT_SKILL_PATH, help="Path to SKILL.md")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory for results")

    args = parser.parse_args()

    CONFIG["model"] = args.model
    CONFIG["judge_model"] = args.judge_model
    CONFIG["runs"] = args.runs
    CONFIG["use_judge"] = not args.no_judge
    CONFIG["skill_path"] = args.skill_path
    CONFIG["output_dir"] = args.output_dir

    # Verify skill path exists
    if not CONFIG["skill_path"].exists():
        print(f"ERROR: Skill file not found at {CONFIG['skill_path']}")
        sys.exit(1)

    # Load skill content
    skill_body = load_skill_content(CONFIG["skill_path"])

    # Disable SSL verification for sandbox proxy environment
    http_client = httpx.Client(verify=False)
    client = anthropic.Anthropic(http_client=http_client)

    all_results = []
    conditions = ["control", "treatment"]

    print(f"\n{'='*60}")
    print(f"  CAPABILITIES SKILL EVALUATION (v2.0.0)")
    print(f"{'='*60}")
    print(f"  Model: {CONFIG['model']}")
    print(f"  Runs per test: {CONFIG['runs']}")
    print(f"  Judge enabled: {CONFIG['use_judge']}")
    if CONFIG["use_judge"]:
        print(f"  Judge model: {CONFIG['judge_model']}")
    print(f"{'='*60}\n")

    for run_num in range(1, CONFIG["runs"] + 1):
        if CONFIG["runs"] > 1:
            print(f"\n--- Run {run_num}/{CONFIG['runs']} ---\n")

        for condition in conditions:
            print(f"\n{'='*60}")
            print(f"  CONDITION: {condition.upper()}")
            print(f"{'='*60}")

            for test in TESTS:
                print(f"  [{test['id']}] {test['category']:<30}", end=" ", flush=True)
                result = run_test(client, test, condition, skill_body)
                all_results.append(result)
                acc = result["scores"]["accuracy_score"]
                acc_t = result["scores"]["accuracy_total"]
                comp = result["scores"]["completeness_score"]
                comp_t = result["scores"]["completeness_total"]
                dep = result["scores"]["deprecated_count"]
                print(f"acc={acc}/{acc_t}  comp={comp}/{comp_t}  dep={dep}")
                time.sleep(0.1)  # Rate limit courtesy

    # Aggregate results
    aggregated = aggregate_results(all_results, TESTS, conditions)

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}\n")

    # Per-category aggregates
    category_stats = {}
    for test in TESTS:
        cat = test["category"]
        if cat not in category_stats:
            category_stats[cat] = {"control": {"acc": [], "comp": []}, "treatment": {"acc": [], "comp": []}}

        for condition in conditions:
            agg = aggregated.get(test["id"], {}).get(condition, {})
            if agg:
                acc = agg.get("accuracy_score", 0)
                comp = agg.get("completeness_score", 0)
                acc_val = acc if isinstance(acc, (int, float)) else acc.get("mean", 0)
                comp_val = comp if isinstance(comp, (int, float)) else comp.get("mean", 0)
                category_stats[cat][condition]["acc"].append(acc_val)
                category_stats[cat][condition]["comp"].append(comp_val)

    print("Category Aggregates:\n")
    print(f"{'Category':<35} {'Ctrl Acc (mean)':<18} {'Trt Acc (mean)':<18} {'Ctrl Comp (mean)':<18} {'Trt Comp (mean)':<18}")
    print("-" * 89)

    for cat in sorted(category_stats.keys()):
        stats = category_stats[cat]
        ctrl_acc = round(statistics.mean(stats["control"]["acc"]), 2) if stats["control"]["acc"] else 0
        trt_acc = round(statistics.mean(stats["treatment"]["acc"]), 2) if stats["treatment"]["acc"] else 0
        ctrl_comp = round(statistics.mean(stats["control"]["comp"]), 2) if stats["control"]["comp"] else 0
        trt_comp = round(statistics.mean(stats["treatment"]["comp"]), 2) if stats["treatment"]["comp"] else 0
        print(f"{cat:<35} {ctrl_acc:<18} {trt_acc:<18} {ctrl_comp:<18} {trt_comp:<18}")

    # Token usage summary
    ctrl_tokens = sum(r["usage"]["input_tokens"] + r["usage"]["output_tokens"]
                     for r in all_results if r["condition"] == "control")
    trt_tokens = sum(r["usage"]["input_tokens"] + r["usage"]["output_tokens"]
                    for r in all_results if r["condition"] == "treatment")
    print(f"\nToken usage — Control: {ctrl_tokens:,}  Treatment: {trt_tokens:,}  Overhead: {trt_tokens - ctrl_tokens:,}")

    # Save full results
    CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)

    ts = time.strftime("%Y%m%d-%H%M%S")
    results_file = CONFIG["output_dir"] / f"eval-results-{ts}.json"

    output_data = {
        "metadata": {
            "model": CONFIG["model"],
            "judge_model": CONFIG["judge_model"] if CONFIG["use_judge"] else None,
            "timestamp": ts,
            "skill_version": "2.0.0",
            "conditions": conditions,
            "runs": CONFIG["runs"],
            "use_judge": CONFIG["use_judge"],
        },
        "results": all_results,
        "aggregated": aggregated,
    }
    with open(results_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nFull results saved to: {results_file}")

    # Generate markdown report
    report_file = CONFIG["output_dir"] / f"eval-report-{ts}.md"
    with open(report_file, "w") as f:
        f.write(f"# Capabilities Skill Evaluation Report\n\n")
        f.write(f"**Model:** {CONFIG['model']}\n")
        f.write(f"**Skill Version:** 2.0.0\n")
        f.write(f"**Date:** {ts}\n")
        f.write(f"**Runs per test:** {CONFIG['runs']}\n")
        if CONFIG["use_judge"]:
            f.write(f"**Judge Model:** {CONFIG['judge_model']}\n")
        f.write("\n")

        # Results Summary
        f.write("## Results Summary\n\n")
        f.write(f"| Test | Category | Ctrl Accuracy | Trt Accuracy | Ctrl Completeness | Trt Completeness | Ctrl Deprecated | Trt Deprecated |\n")
        f.write(f"|------|----------|--------------|-------------|-------------------|------------------|-----------------|----------------|\n")

        for test in TESTS:
            agg = aggregated.get(test["id"], {})
            ctrl_acc = format_score(agg.get("control", {}).get("accuracy_score", 0))
            trt_acc = format_score(agg.get("treatment", {}).get("accuracy_score", 0))
            ctrl_comp = format_score(agg.get("control", {}).get("completeness_score", 0))
            trt_comp = format_score(agg.get("treatment", {}).get("completeness_score", 0))
            ctrl_dep = format_score(agg.get("control", {}).get("deprecated_count", 0))
            trt_dep = format_score(agg.get("treatment", {}).get("deprecated_count", 0))
            f.write(f"| {test['id']} | {test['category']} | {ctrl_acc} | {trt_acc} | {ctrl_comp} | {trt_comp} | {ctrl_dep} | {trt_dep} |\n")

        # Category Aggregates
        f.write("\n## Category Aggregates\n\n")
        f.write(f"| Category | Ctrl Accuracy | Trt Accuracy | Ctrl Completeness | Trt Completeness |\n")
        f.write(f"|----------|--------------|-------------|-------------------|------------------|\n")

        for cat in sorted(category_stats.keys()):
            stats = category_stats[cat]
            ctrl_acc = round(statistics.mean(stats["control"]["acc"]), 2) if stats["control"]["acc"] else 0
            trt_acc = round(statistics.mean(stats["treatment"]["acc"]), 2) if stats["treatment"]["acc"] else 0
            ctrl_comp = round(statistics.mean(stats["control"]["comp"]), 2) if stats["control"]["comp"] else 0
            trt_comp = round(statistics.mean(stats["treatment"]["comp"]), 2) if stats["treatment"]["comp"] else 0
            f.write(f"| {cat} | {ctrl_acc} | {trt_acc} | {ctrl_comp} | {trt_comp} |\n")

        # Multi-run Variance (if applicable)
        if CONFIG["runs"] > 1:
            f.write("\n## Multi-Run Variance\n\n")
            f.write("When multiple runs are performed, results show mean±stdev.\n\n")
            f.write(f"| Test | Metric | Value (mean±stdev) |\n")
            f.write(f"|------|--------|-------------------|\n")

            for test in TESTS:
                agg = aggregated.get(test["id"], {})
                if agg.get("control", {}).get("num_runs", 0) > 1:
                    ctrl_acc = agg["control"]["accuracy_score"]
                    if isinstance(ctrl_acc, dict):
                        f.write(f"| {test['id']} | Accuracy (Control) | {ctrl_acc['mean']}±{ctrl_acc['stdev']} |\n")

        # Judge Scores (if judge was used)
        if CONFIG["use_judge"]:
            f.write("\n## Judge Scores\n\n")
            f.write("LLM-based evaluation across multiple dimensions (0-3 scale unless noted).\n\n")
            f.write(f"| Test | Category | Ctrl Accuracy | Trt Accuracy | Ctrl Completeness | Trt Completeness | Ctrl Actionability | Trt Actionability |\n")
            f.write(f"|------|----------|--------------|-------------|-------------------|------------------|--------------------|-------------------|\n")

            for test in TESTS:
                agg = aggregated.get(test["id"], {})
                ctrl_j_acc = format_score(agg.get("control", {}).get("judge_accuracy", 0)) if agg.get("control", {}).get("judge_accuracy") else "N/A"
                trt_j_acc = format_score(agg.get("treatment", {}).get("judge_accuracy", 0)) if agg.get("treatment", {}).get("judge_accuracy") else "N/A"
                ctrl_j_comp = format_score(agg.get("control", {}).get("judge_completeness", 0)) if agg.get("control", {}).get("judge_completeness") else "N/A"
                trt_j_comp = format_score(agg.get("treatment", {}).get("judge_completeness", 0)) if agg.get("treatment", {}).get("judge_completeness") else "N/A"
                ctrl_j_action = format_score(agg.get("control", {}).get("judge_actionability", 0)) if agg.get("control", {}).get("judge_actionability") else "N/A"
                trt_j_action = format_score(agg.get("treatment", {}).get("judge_actionability", 0)) if agg.get("treatment", {}).get("judge_actionability") else "N/A"
                f.write(f"| {test['id']} | {test['category']} | {ctrl_j_acc} | {trt_j_acc} | {ctrl_j_comp} | {trt_j_comp} | {ctrl_j_action} | {trt_j_action} |\n")

        # Negative Tests — Regression Analysis
        f.write("\n## Negative Tests — Regression Analysis\n\n")
        f.write("Negative tests should show minimal change between control and treatment. ")
        f.write("High deltas indicate the skill may be interfering with non-capabilities questions.\n\n")
        f.write(f"| Test | Category | Regression Score (Accuracy + Completeness Delta) |\n")
        f.write(f"|------|----------|--------------------------------------------------|\n")

        for test in TESTS:
            if test["category"] == "Negative (No Change Expected)":
                regression = compute_regression_score(aggregated, test["id"])
                f.write(f"| {test['id']} | {test['category']} | {regression:.2f} |\n")

        # Hallucination Detection Tests
        hallucination_tests = [t for t in TESTS if t["category"] == "Hallucination Detection"]
        if hallucination_tests:
            f.write("\n## Hallucination Detection Tests\n\n")
            f.write("Tests whether the skill helps Claude avoid confident-but-wrong answers about its capabilities. ")
            f.write("Higher accuracy = better at correcting misconceptions. Deprecated patterns found = hallucinations not avoided.\n\n")
            f.write(f"| Test | Ctrl Accuracy | Trt Accuracy | Ctrl Deprecated | Trt Deprecated | Ctrl Completeness | Trt Completeness |\n")
            f.write(f"|------|--------------|-------------|-----------------|----------------|-------------------|------------------|\n")

            for test in hallucination_tests:
                agg = aggregated.get(test["id"], {})
                ctrl_acc = format_score(agg.get("control", {}).get("accuracy_score", 0))
                trt_acc = format_score(agg.get("treatment", {}).get("accuracy_score", 0))
                ctrl_dep = format_score(agg.get("control", {}).get("deprecated_count", 0))
                trt_dep = format_score(agg.get("treatment", {}).get("deprecated_count", 0))
                ctrl_comp = format_score(agg.get("control", {}).get("completeness_score", 0))
                trt_comp = format_score(agg.get("treatment", {}).get("completeness_score", 0))
                f.write(f"| {test['id']} | {ctrl_acc} | {trt_acc} | {ctrl_dep} | {trt_dep} | {ctrl_comp} | {trt_comp} |\n")

        # High-level summary
        f.write("\n## Summary Statistics\n\n")
        pos_tests = len([t for t in TESTS if t['category'] not in ('Negative (No Change Expected)', 'Hallucination Detection')])
        neg_tests = len([t for t in TESTS if t['category'] == 'Negative (No Change Expected)'])
        hall_tests = len([t for t in TESTS if t['category'] == 'Hallucination Detection'])
        f.write(f"- **Positive tests:** {pos_tests}\n")
        f.write(f"- **Negative tests:** {neg_tests}\n")
        f.write(f"- **Hallucination detection tests:** {hall_tests}\n")
        f.write(f"- **Token overhead:** {trt_tokens - ctrl_tokens:,} tokens\n")

        # Detailed Responses
        f.write("\n## Detailed Responses\n\n")
        for test in TESTS:
            # Get the most recent result for each condition
            ctrl_results = [r for r in all_results if r["test_id"] == test["id"] and r["condition"] == "control"]
            trt_results = [r for r in all_results if r["test_id"] == test["id"] and r["condition"] == "treatment"]

            if not ctrl_results or not trt_results:
                continue

            ctrl = ctrl_results[-1]  # Last run
            trt = trt_results[-1]

            f.write(f"### Test {test['id']}: {test['category']}\n\n")
            f.write(f"**Prompt:** {test['prompt']}\n\n")

            f.write(f"#### Control Response\n")
            f.write(f"- Accuracy keywords matched: {ctrl['scores']['accuracy_matched']}\n")
            f.write(f"- Completeness keywords matched: {ctrl['scores']['completeness_matched']}\n")
            f.write(f"- Deprecated patterns found: {ctrl['scores']['deprecated_found']}\n")
            if ctrl.get("judge_scores"):
                f.write(f"- Judge — Accuracy: {ctrl['judge_scores'].get('accuracy', 'N/A')}, Completeness: {ctrl['judge_scores'].get('completeness', 'N/A')}, Actionability: {ctrl['judge_scores'].get('actionability', 'N/A')}\n")
            f.write(f"\n<details><summary>Full response</summary>\n\n{ctrl['response']}\n\n</details>\n\n")

            f.write(f"#### Treatment Response\n")
            f.write(f"- Accuracy keywords matched: {trt['scores']['accuracy_matched']}\n")
            f.write(f"- Completeness keywords matched: {trt['scores']['completeness_matched']}\n")
            f.write(f"- Deprecated patterns found: {trt['scores']['deprecated_found']}\n")
            if trt.get("judge_scores"):
                f.write(f"- Judge — Accuracy: {trt['judge_scores'].get('accuracy', 'N/A')}, Completeness: {trt['judge_scores'].get('completeness', 'N/A')}, Actionability: {trt['judge_scores'].get('actionability', 'N/A')}\n")
            f.write(f"\n<details><summary>Full response</summary>\n\n{trt['response']}\n\n</details>\n\n")
            f.write("---\n\n")

    print(f"Report saved to: {report_file}")
    http_client.close()


if __name__ == "__main__":
    main()

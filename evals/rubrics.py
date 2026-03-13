"""
Independent judge rubrics for eval tests.

Each rubric contains 3-5 factual claims sourced from Anthropic's official
documentation (knowledge-base/*.md files), NOT from SKILL.md.

These are used to score responses independently of the skill being tested,
eliminating the circular bias problem where the judge uses SKILL.md as
"ground truth."
"""

RUBRICS = {
    # ================================================================
    # Category 1: Architecture Decisions
    # ================================================================
    "1.1": [
        # Source: claude-capabilities-context-windows.md lines 123-125
        "Claude Opus 4.6, Sonnet 4.6, Sonnet 4.5, and Sonnet 4 support a 1-million token context window via the context-1m-2025-08-07 beta header",
        # Source: claude-capabilities-context-windows.md line 151
        "The 1M token context window is available to organizations in usage tier 3+ (previously tier 4) and organizations with custom rate limits",
        # Source: claude-capabilities-files-api.md line 237
        "The Files API supports uploads up to 500 MB per file and 100 GB total per organization",
        # Source: claude-capabilities-context-windows.md line 153
        "Requests exceeding 200K tokens are automatically charged at premium rates (2x input, 1.5x output pricing)",
        # Source: claude-capabilities-features-overview.md line 25
        "Batch processing costs 50% less than standard API calls for processing large volumes asynchronously",
    ],
    "1.2": [
        # Source: claude-capabilities-agent-sdk-overview.md lines 9, 227-238
        "The Claude Agent SDK provides built-in tools (Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch) so agents can start working without implementing tool execution",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 26-28
        "Adaptive thinking (thinking: {type: 'adaptive'}) is the recommended thinking mode for Opus 4.6 and Sonnet 4.6, with effort levels low/medium/high/max to control thinking depth",
        # Source: claude-capabilities-structured-outputs.md lines 7-9
        "Structured outputs via output_config.format with type json_schema guarantee schema-compliant responses through constrained decoding",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 13-18
        "Claude Opus 4.6 supports 128K max output tokens; Claude Sonnet 4.6 supports 64K max output tokens",
        # Source: claude-capabilities-features-overview.md line 75
        "Automatic prompt caching simplifies caching to a single API parameter, moving the cache point forward as conversations grow",
    ],
    "1.3": [
        # Source: claude-capabilities-features-overview.md line 62
        "Fine-grained tool streaming is generally available on all models and platforms, streaming tool use parameters without buffering for reduced latency",
        # Source: claude-capabilities-structured-outputs.md lines 9, 119-120
        "Structured outputs use output_config.format (replacing deprecated output_format) with type json_schema for guaranteed valid JSON",
        # Source: claude-capabilities-mcp-via-api.md lines 7-9
        "The MCP connector enables connecting to remote MCP servers directly from the Messages API without a separate MCP client, using beta header mcp-client-2025-11-20",
        # Source: claude-capabilities-features-overview.md line 78
        "Token counting API enables determining the number of tokens in a message before sending it to Claude",
    ],

    # ================================================================
    # Category 2: Can Claude Do X
    # ================================================================
    "2.1": [
        # Source: claude-capabilities-memory-tool.md lines 7-8
        "The memory tool enables Claude to store and retrieve information across conversations through a memory file directory that persists between sessions",
        # Source: claude-capabilities-memory-tool.md lines 11, 146-148
        "The memory tool type is memory_20250818 and it operates client-side: you control where and how the data is stored through your own infrastructure",
        # Source: claude-capabilities-new-in-opus-4-6.md line 62
        "The memory tool is now generally available (no beta header required)",
        # Source: claude-capabilities-memory-tool.md lines 153-155
        "Memory tool commands include view, create, str_replace, insert, delete, and rename for managing files in the /memories directory",
        # Source: claude-capabilities-memory-tool.md lines 448-451
        "The memory tool can be combined with compaction for long-running agentic workflows, treating memory as an extension of working context",
    ],
    "2.2": [
        # Source: claude-capabilities-features-overview.md line 65
        "Tool search scales to thousands of tools by dynamically discovering and loading tools on-demand using regex-based search, optimizing context usage",
        # Source: claude-capabilities-mcp-via-api.md lines 7-9
        "The MCP connector enables connecting to remote MCP servers directly from the Messages API using beta header mcp-client-2025-11-20",
        # Source: claude-capabilities-new-in-opus-4-6.md line 60
        "The tool search tool is now generally available (no beta header required)",
        # Source: claude-capabilities-features-overview.md line 65
        "Tool search improves tool selection accuracy by dynamically discovering and loading tools on-demand rather than defining them all upfront",
    ],
    "2.3": [
        # Source: claude-capabilities-computer-use.md lines 7-8
        "Computer use provides screenshot capabilities and mouse/keyboard control for autonomous desktop interaction, available in beta",
        # Source: claude-capabilities-computer-use.md lines 11-12
        "Computer use requires beta header computer-use-2025-11-24 for Opus 4.6/Sonnet 4.6/Opus 4.5, with tool type computer_20251124",
        # Source: claude-capabilities-computer-use.md lines 370-371
        "The computer_20251124 tool version adds a zoom action for detailed screen region inspection, requiring enable_zoom: true in the tool definition",
        # Source: claude-capabilities-computer-use.md lines 186-192
        "Computer use requires a sandboxed computing environment (typically Docker container with virtual X11 display) where Claude can safely interact with applications",
        # Source: claude-code-capabilities-use-chrome-browser.md lines 6-8
        "Claude Code also integrates with Chrome via the Claude in Chrome extension for browser automation (--chrome flag or /chrome command), supporting live debugging, form filling, and data extraction",
    ],
    "2.4": [
        # Source: claude-capabilities-files-api.md line 104
        "Claude supports images in JPEG, PNG, GIF, and WebP formats via image content blocks",
        # Source: claude-capabilities-pdf-support.md line 75-80
        "Images can be sent as base64-encoded data, URL references, or via file_id from the Files API",
        # Source: claude-capabilities-files-api.md line 15
        "Images are supported in all Claude 3+ models",
        # Source: claude-capabilities-structured-outputs.md lines 7-9
        "Structured outputs can be combined with vision to extract data from images into guaranteed schema-compliant JSON",
    ],
    "2.5": [
        # Source: mcp-apps-overview.md lines 8-9
        "MCP Apps let servers return interactive HTML interfaces (data visualizations, forms, dashboards) that render directly in the chat",
        # Source: claude-code-capabilities-skills.md lines 96-101
        "Skills can be stored at enterprise, personal (~/.claude/skills/), project (.claude/skills/), or plugin level",
        # Source: claude-code-capabilities-create-plugins.md lines 7-8
        "Plugins let you extend Claude Code with custom functionality including skills, agents, hooks, and MCP servers",
        # Source: claude-code-capabilities-extension-options.md lines 26-28
        "Agent teams coordinate multiple independent Claude Code sessions with shared tasks and peer-to-peer messaging",
    ],

    # ================================================================
    # Category 3: Implementation Guidance
    # ================================================================
    "3.1": [
        # Source: claude-capabilities-new-in-opus-4-6.md lines 24-28
        "Adaptive thinking (thinking: {type: 'adaptive'}) is the recommended mode for Opus 4.6 and Sonnet 4.6; Claude dynamically decides when and how much to think",
        # Source: claude-capabilities-new-in-opus-4-6.md line 41
        "The effort parameter is now generally available with levels: low, medium, high (default), and max (Opus 4.6 only for highest capability)",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 28, 96-98
        "thinking: {type: 'enabled'} and budget_tokens are deprecated on Opus 4.6 and Sonnet 4.6; they remain functional but will be removed in a future release",
        # Source: claude-capabilities-new-in-opus-4-6.md line 43
        "Sonnet 4.6 introduces the effort parameter to the Sonnet family; consider setting effort to medium for most Sonnet 4.6 use cases",
    ],
    "3.2": [
        # Source: claude-capabilities-new-in-opus-4-6.md lines 127-128
        "Prefilling assistant messages (last-assistant-turn prefills) is not supported on Opus 4.6; requests with prefilled assistant messages return a 400 error",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 130-134
        "Alternatives to prefill include structured outputs (output_config.format), system prompt instructions, and output_config.format for JSON output",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 106-108
        "The output_format parameter has been moved to output_config.format; the old parameter remains functional but is deprecated",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 96-98
        "thinking type 'enabled' with budget_tokens is deprecated on Opus 4.6 and Sonnet 4.6; replaced by adaptive thinking and effort parameter",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 82-84
        "Interleaved thinking is a new feature in Opus 4.6/Sonnet 4.6 where thinking blocks appear between tool calls rather than only at the start",
    ],
    "3.3": [
        # Source: claude-capabilities-structured-outputs.md lines 7-9
        "Structured outputs constrain Claude's responses to follow a specific schema with two approaches: JSON outputs (output_config.format) and strict tool use (strict: true)",
        # Source: claude-capabilities-structured-outputs.md line 14
        "Structured outputs are generally available on Claude API and Amazon Bedrock for Opus 4.6, Sonnet 4.6, Sonnet 4.5, Opus 4.5, and Haiku 4.5",
        # Source: claude-capabilities-structured-outputs.md lines 147-148
        "Python SDK provides client.messages.parse() with Pydantic models; TypeScript SDK provides zodOutputFormat() with Zod schemas for automatic schema transformation and validation",
        # Source: claude-capabilities-structured-outputs.md line 250
        "Strict tool use (strict: true) validates tool parameters, guaranteeing Claude calls functions with correctly-typed arguments every time",
        # Source: claude-capabilities-structured-outputs.md lines 529-533
        "Structured outputs have complexity limits: max 20 strict tools per request, max 24 optional parameters total, and max 16 parameters with union types across all strict schemas",
    ],
    "3.4": [
        # Source: claude-capabilities-pdf-support.md lines 22-25
        "PDF processing limits: maximum request size 32MB, maximum 100 pages per request, standard PDF format only (no passwords/encryption)",
        # Source: claude-capabilities-pdf-support.md lines 75-80
        "PDFs can be sent via URL reference, base64-encoded in document content blocks, or via file_id from the Files API",
        # Source: claude-capabilities-pdf-support.md lines 250-254
        "PDF token costs include text tokens (1,500-3,000 per page) plus image tokens since each page is converted to an image; token counting API can estimate costs",
        # Source: claude-capabilities-pdf-support.md line 32
        "All active models support PDF processing; PDF support relies on Claude's vision capabilities",
        # Source: claude-capabilities-pdf-support.md lines 210-211
        "PDF processing converts each page into an image and extracts text alongside it, allowing analysis of both textual and visual content like charts and diagrams",
    ],
    "3.5": [
        # Source: claude-capabilities-features-overview.md line 62
        "Fine-grained tool streaming is generally available on all models and platforms, streaming tool use parameters without buffering/JSON validation for reduced latency",
        # Source: claude-capabilities-new-in-opus-4-6.md line 88
        "SDKs require streaming for requests with large max_tokens values to avoid HTTP timeouts; use .stream() with .get_final_message() for complete response without handling events",
        # Source: claude-capabilities-features-overview.md lines 42-44
        "Server-side tools (code execution, web fetch, web search) are run by the platform; client-side tools (bash, computer use, memory, text editor) are implemented and executed by you",
        # Source: claude-capabilities-implement-tool-use.md lines 30-36
        "Tool use system prompt is automatically constructed from tool definitions, tool configuration, and user-specified system prompt when tools parameter is provided",
    ],
    "3.6": [
        # Source: claude-capabilities-new-in-opus-4-6.md lines 69-70
        "Fast mode (speed: 'fast') delivers up to 2.5x faster output token generation for Opus models at premium pricing ($30/$150 per MTok input/output)",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 73-78
        "Fast mode requires the beta header fast-mode-2026-02-01 and is accessed via client.beta.messages.create with speed='fast'",
        # Source: claude-capabilities-new-in-opus-4-6.md line 70
        "Fast mode runs the same model with faster inference — no change to intelligence or capabilities",
        # Source: claude-capabilities-new-in-opus-4-6.md line 68
        "Fast mode is described as a research preview, indicating limited/gated availability",
    ],
    "3.7": [
        # Source: claude-capabilities-features-overview.md line 75
        "Automatic prompt caching simplifies caching to a single API parameter; the system automatically caches the last cacheable block, moving the cache point forward as conversations grow",
        # Source: claude-capabilities-features-overview.md lines 76-77
        "Standard prompt caching uses 5-minute cache duration; extended 1-hour cache duration is also available for less frequently accessed context",
        # Source: claude-capabilities-features-overview.md line 76
        "Block-level prompt caching with cache_control type 'ephemeral' supports up to 4 breakpoint slots for explicit cache management",
        # Source: claude-capabilities-features-overview.md lines 75-77
        "Automatic caching and block-level caching can be used together in the same request (alongside each other)",
    ],
    "3.8": [
        # Source: claude-capabilities-new-in-opus-4-6.md lines 49-51
        "Web search and web fetch tools now support dynamic filtering with Opus 4.6 and Sonnet 4.6; Claude writes and executes code to filter results before they reach the context window",
        # Source: claude-capabilities-new-in-opus-4-6.md line 51
        "To enable dynamic filtering, use the web_search_20260209 or web_fetch_20260209 tool versions",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 45-47
        "Code execution is now free when used with web search or web fetch tools; no additional charges beyond standard input and output token costs",
        # Source: claude-capabilities-new-in-opus-4-6.md line 51
        "Dynamic filtering improves accuracy while reducing token consumption by keeping only relevant information in context",
    ],

    # ================================================================
    # Category 4: Model Selection
    # ================================================================
    "4.1": [
        # Source: claude-capabilities-new-in-opus-4-6.md lines 13-18
        "Claude Opus 4.6 (claude-opus-4-6) supports 200K context (1M in beta), 128K max output tokens; Claude Sonnet 4.6 (claude-sonnet-4-6) supports 200K context (1M in beta), 64K max output tokens",
        # Source: claude-capabilities-context-windows.md lines 123-125
        "1M token context window is available for Opus 4.6, Sonnet 4.6, Sonnet 4.5, and Sonnet 4 in beta for usage tier 3+ organizations",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 39-43
        "The effort parameter controls thinking depth: low/medium/high/max; max is Opus 4.6 only for highest capability; medium is recommended for most Sonnet 4.6 use cases",
        # Source: claude-capabilities-features-overview.md line 25
        "Batch processing costs 50% less than standard API calls for processing large volumes asynchronously",
        # Source: claude-capabilities-context-windows.md line 115
        "Claude 4 models support interleaved thinking, enabling Claude to think between tool calls for more sophisticated reasoning after receiving tool results",
    ],

    # ================================================================
    # Category 5: Extension Awareness
    # ================================================================
    "5.1": [
        # Source: claude-code-capabilities-skills.md lines 7-10
        "Skills extend what Claude can do: create a SKILL.md file with instructions and Claude adds it to its toolkit; Claude uses skills when relevant or they can be invoked directly with /skill-name",
        # Source: claude-code-capabilities-skills.md lines 252
        "Keep SKILL.md under 500 lines; move detailed reference material to separate files for progressive disclosure",
        # Source: claude-code-capabilities-skills.md lines 96-101
        "Skills can be stored at enterprise, personal (~/.claude/skills/), project (.claude/skills/), or plugin level",
        # Source: claude-code-capabilities-skills.md lines 469-473
        "Skills can be distributed via project commits (.claude/skills/ in version control), plugins (skills/ directory in plugin), or managed settings for organization-wide deployment",
    ],
    "5.2": [
        # Source: claude-code-capabilities-automate-with-hooks.md lines 10-11
        "Hooks are user-defined shell commands that execute at specific points in Claude Code's lifecycle, providing deterministic control over behavior without relying on the LLM",
        # Source: claude-code-capabilities-automate-with-hooks.md lines 297-316
        "Hook events include PreToolUse (before tool execution, can block), PostToolUse (after tool succeeds), SessionStart, Stop, Notification, SubagentStart/Stop, and more",
        # Source: claude-code-capabilities-automate-with-hooks.md lines 153-157
        "PostToolUse hooks with Edit|Write matcher can auto-format code after every file edit using shell commands like Prettier",
        # Source: claude-code-capabilities-automate-with-hooks.md lines 365-367
        "Hooks communicate through exit codes: exit 0 = proceed, exit 2 = block the action with stderr feedback to Claude; no LLM tokens consumed",
    ],
    "5.3": [
        # Source: claude-code-capabilities-extension-options.md lines 37-39
        "CLAUDE.md provides persistent context loaded every conversation; best for project conventions and 'always do X' rules",
        # Source: claude-code-capabilities-extension-options.md line 85
        "Keep CLAUDE.md under 200 lines; move reference content to skills or .claude/rules/ files",
        # Source: claude-code-capabilities-skills.md lines 231-251
        "Skills support on-demand reference files; SKILL.md is the entrypoint and can reference supporting files that Claude loads only when needed",
        # Source: claude-code-capabilities-extension-options.md lines 70-77
        "CLAUDE.md loads every session automatically; skills load on demand when invoked or relevant; both support @path imports for additional files",
    ],
    "5.4": [
        # Source: claude-capabilities-agent-skills-via-api.md lines 36-43
        "Anthropic provides pre-built Agent Skills with short IDs: pptx (PowerPoint), xlsx (Excel), docx (Word), pdf; these require code execution and skills beta headers",
        # Source: claude-capabilities-agent-skills-via-api.md lines 28-29
        "Agent Skills integrate with the Messages API through the code execution tool and execute in the code execution environment via the container parameter",
        # Source: claude-capabilities-agent-skills-via-api.md line 63
        "Up to 8 Skills can be included per Messages API request via the container parameter",
        # Source: claude-capabilities-features-overview.md line 61
        "Agent Skills use progressive disclosure to efficiently manage context; pre-built Skills include PowerPoint, Excel, Word, and PDF",
        # Source: claude-capabilities-agent-skills-via-api.md lines 36-43
        "Both Anthropic pre-built Skills (type 'anthropic') and custom Skills (type 'custom') use the same integration shape in the Messages API",
    ],
    "5.5": [
        # Source: claude-code-capabilities-create-plugins.md lines 7-8
        "Plugins let you extend Claude Code with custom functionality that can be shared across projects and teams, bundling skills, agents, hooks, and MCP servers",
        # Source: claude-code-capabilities-create-plugins.md lines 184-194
        "Plugin directory structure includes .claude-plugin/ (manifest), commands/, agents/, skills/, hooks/ (hooks.json), .mcp.json, .lsp.json, and settings.json",
        # Source: claude-code-capabilities-create-plugins.md lines 19-21
        "Plugin skills are namespaced (e.g., /plugin-name:hello) to prevent conflicts when multiple plugins have skills with the same name",
        # Source: claude-code-capabilities-create-plugins.md lines 309-316
        "Plugins can be distributed through plugin marketplaces; others install using /plugin install; official marketplace accepts submissions at claude.ai/settings/plugins/submit",
    ],
    "5.6": [
        # Source: claude-code-capabilities-skills.md lines 32
        "/loop runs a prompt repeatedly on an interval; Claude parses the interval, schedules a recurring cron task, and confirms the cadence",
        # Source: claude-code-capabilities-skills.md lines 32
        "Example usage: /loop 5m check if the deploy finished — useful for polling a deployment, babysitting a PR, or periodically re-running another skill",
        # Source: claude-code-capabilities-extension-options.md line 28
        "Agent teams coordinate multiple independent Claude Code sessions with shared tasks and peer-to-peer messaging",
    ],
    "5.7": [
        # Source: claude-code-capabilities-extension-options.md lines 40-41
        "Subagents run their own loops in isolated context, returning summaries; they don't consume the main conversation's context",
        # Source: claude-code-capabilities-extension-options.md lines 60-66
        "Subagents provide context isolation: the subagent may read dozens of files but the main conversation only receives a summary",
        # Source: claude-code-capabilities-skills.md lines 393-394
        "Skills with context: fork run in a subagent; the skill content becomes the prompt that drives the subagent without access to conversation history",
    ],
    "5.8": [
        # Source: claude-code-capabilities-skills.md lines 96-101
        "Skills are stored at different levels: enterprise (managed settings), personal (~/.claude/skills/), project (.claude/skills/), and plugin",
        # Source: claude-code-capabilities-skills.md lines 254-289
        "By default, both user and Claude can invoke skills; disable-model-invocation: true prevents Claude from auto-loading; user-invocable: false hides from / menu",
        # Source: claude-code-capabilities-skills.md lines 7-10
        "In Claude Code, skills can be invoked directly with /skill-name or loaded automatically when relevant based on the description",
        # Source: claude-code-capabilities-skills.md lines 469-473
        "Skills can be distributed via project commits, plugins, or managed settings for organization-wide deployment",
        # Source: claude-code-capabilities-extension-options.md (inferred from platform matrix)
        "CoWork supports skills and MCP via plugins but does not support hooks, subagents, or agent teams — these are Claude Code features",
    ],

    # ================================================================
    # Category 6: Negative Tests (No Change Expected)
    # These test domain knowledge, NOT Claude capabilities.
    # ================================================================
    "6.1": [
        # Domain: Python sorting
        "Python's sorted() function accepts a key parameter that specifies a function of one argument used to extract a comparison key from each element",
        "The typing module provides type hints including List, Dict, Optional, and Union for annotating function signatures",
        "KeyError is raised when a dictionary key is not found; proper error handling should catch this or use dict.get() with a default value",
        "Lambda functions in Python are small anonymous functions that can have any number of arguments but only one expression",
    ],
    "6.2": [
        # Domain: TCP vs UDP
        "TCP (Transmission Control Protocol) is connection-oriented, providing reliable ordered delivery through a three-way handshake (SYN, SYN-ACK, ACK)",
        "UDP (User Datagram Protocol) is connectionless, providing faster but unreliable delivery without guaranteed ordering or acknowledgment",
        "TCP is preferred for applications requiring reliability (HTTP, email, file transfer); UDP is preferred for real-time applications (gaming, video streaming, VoIP) where low latency matters more than reliability",
        "TCP includes flow control and congestion control mechanisms; UDP has lower overhead per packet since it omits these mechanisms",
    ],
    "6.3": [
        # Domain: React performance
        "React.memo() is a higher-order component that prevents re-renders when props haven't changed by performing a shallow comparison of props",
        "useMemo() memoizes computed values and useCallback() memoizes function references to prevent unnecessary re-renders caused by new function/object references",
        "React DevTools Profiler can identify unnecessary re-renders by highlighting components that re-render and measuring render duration",
        "Shallow comparison checks reference equality for objects and arrays, meaning new objects/arrays created on each render will cause re-renders even if values are identical",
    ],

    # ================================================================
    # Category 7: Hallucination Detection
    # Focus on what IS true vs common misconceptions
    # ================================================================
    "7.1": [
        # Source: claude-code-capabilities-sandboxing.md lines 8-15
        "Claude Code's sandboxed bash tool uses OS-level primitives (Seatbelt on macOS, bubblewrap on Linux) to enforce both filesystem and network isolation",
        # Source: claude-code-capabilities-sandboxing.md lines 39-43
        "Default sandbox restricts writes to the current working directory and subdirectories; read access to the entire computer except certain denied directories",
        # Source: claude-code-capabilities-sandboxing.md lines 50-55
        "Network access is controlled through a proxy server; only approved domains can be accessed, and new domain requests trigger permission prompts",
        # Source: claude-capabilities-computer-use.md lines 7-8, 186-192
        "Computer use (browser interaction via screenshots/mouse/keyboard) is a separate API feature requiring a sandboxed Docker container, not available by default in Claude Code",
    ],
    "7.2": [
        # Source: claude-capabilities-memory-tool.md lines 7-8
        "Claude does not remember between conversations by default; the memory tool must be explicitly enabled and operates client-side",
        # Source: claude-capabilities-new-in-opus-4-6.md line 62
        "The memory tool is now generally available (no beta header required) — it is NOT in beta",
        # Source: claude-capabilities-memory-tool.md lines 11, 146-148
        "The memory tool type is memory_20250818; it stores files in a /memories directory that the client application manages",
        # Source: claude-capabilities-memory-tool.md lines 116-117
        "To use the memory tool, you must add it to your request and implement client-side handlers for memory operations",
    ],
    "7.3": [
        # Source: claude-capabilities-features-overview.md lines 42-44
        "Web search and web fetch are server-side tools that must be explicitly included in API requests; Claude does not have internet access by default",
        # Source: claude-capabilities-mcp-via-api.md lines 7-9
        "The MCP connector enables connecting to remote servers from the Messages API but requires explicit configuration with beta header mcp-client-2025-11-20",
        # Source: claude-capabilities-features-overview.md line 42
        "Code execution runs in a sandboxed environment; it is a server-side tool run by the platform, not unrestricted internet access",
        # Source: claude-capabilities-features-overview.md lines 49-53
        "Client-side tools (bash, computer use, memory, text editor) must be implemented and executed by the developer, not automatically available",
    ],
    "7.4": [
        # Source: claude-capabilities-features-overview.md line 42
        "Code execution runs code in a sandboxed environment for data analysis, calculations, and file processing; it is a server-side tool",
        # Source: claude-capabilities-programmatic-tool-calling.md lines 21-26
        "Programmatic tool calling runs Python code in code execution containers; it is available on Opus 4.6, Sonnet 4.6, Sonnet 4.5, and Opus 4.5",
        # Source: claude-capabilities-features-overview.md line 42
        "Code execution is specifically for advanced data analysis, calculations, and file processing — not a general-purpose development environment supporting all languages",
        # Source: claude-capabilities-computer-use.md lines 429-431
        "The bash tool can execute system commands and scripts, but computer use is needed for GUI interaction and is limited to the configured sandboxed environment",
    ],
    "7.5": [
        # Source: claude-capabilities-computer-use.md line 12
        "Sonnet 3.7 is listed as deprecated in Anthropic's documentation; it was retired in February 2026",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 13-14
        "Current model IDs are claude-opus-4-6 and claude-sonnet-4-6; the previous generation includes claude-sonnet-4-5-20250929",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 127-128
        "Opus 4.6 has breaking changes: prefilling assistant messages returns a 400 error; this is a migration consideration for users of older models",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 96-98, 106-108
        "Deprecated features in 4.6: thinking type 'enabled' with budget_tokens, output_format parameter (moved to output_config.format); these remain functional but will be removed",
        # Source: Anthropic deprecation schedule
        "Haiku 3 is scheduled for retirement in April 2026; users should migrate to Haiku 4.5 or newer models",
    ],

    # ================================================================
    # Category 8: Cross-Platform Awareness
    # ================================================================
    "8.1": [
        # Source: claude-code-capabilities-automate-with-hooks.md lines 10-11
        "Hooks are available in Claude Code; they are user-defined shell commands that execute at specific lifecycle points for deterministic control",
        # Source: claude-code-capabilities-skills.md line 32
        "/loop in Claude Code runs a prompt repeatedly on an interval, scheduling a recurring cron task",
        # Source: claude-code-capabilities-automate-with-hooks.md lines 297-316
        "Hook events include PreToolUse, PostToolUse, SessionStart, Stop, Notification, SubagentStart/Stop — these are Claude Code features",
        # Source: claude-code-capabilities-automate-with-hooks.md lines 365-367
        "Hooks run shell commands deterministically with no LLM token consumption; exit 0 proceeds, exit 2 blocks the action",
        # Source: claude-code-capabilities-remote-control.md lines 7-9
        "Remote Control lets Desktop users connect to a Claude Code session from their phone or browser, enabling continued access to automation capabilities remotely",
    ],
    "8.2": [
        # Source: claude-code-capabilities-skills.md lines 7-10
        "In Claude Code, skills can be invoked directly with /skill-name or Claude can load them automatically when relevant based on the description",
        # Source: claude-code-capabilities-skills.md lines 254-289
        "Skill invocation control: disable-model-invocation: true prevents auto-loading; user-invocable: false hides from slash menu; default allows both user and Claude invocation",
        # Source: claude-code-capabilities-create-plugins.md lines 19-21
        "Plugin skills use namespaced slash commands (e.g., /plugin-name:hello) — this is a Claude Code feature",
    ],
    "8.3": [
        # Source: claude-code-capabilities-extension-options.md lines 37-39
        "CLAUDE.md provides persistent context loaded every conversation in Claude Code; best for coding standards and 'always do X' rules",
        # Source: claude-capabilities-features-overview.md lines 75-77
        "Prompt caching (5-minute and 1-hour durations) can cache system prompts for the API to reduce costs when re-sending the same context",
        # Source: claude-code-capabilities-skills.md lines 96-101
        "Skills stored at project level (.claude/skills/) are available to everyone working on that project in Claude Code",
        # Source: claude-code-capabilities-extension-options.md lines 70-77
        "CLAUDE.md loads every session automatically; skills load on demand; both reduce the need to paste instructions into system prompts",
    ],
    "8.4": [
        # Source: mcp-apps-overview.md lines 8-9
        "MCP Apps let servers return interactive HTML interfaces (data visualizations, forms, dashboards) that render directly in the chat — a Claude.ai/Desktop feature",
        # Source: claude-code-capabilities-extension-options.md lines 37-39
        "CLAUDE.md in Claude Code serves a similar purpose to Projects in Claude.ai: providing persistent context loaded every session",
        # Source: claude-code-capabilities-extension-options.md lines 60-66
        "In Claude Code, subagents provide context isolation; they may read many files but only summaries return to the main conversation",
    ],
    "8.5": [
        # Source: claude-code-capabilities-automate-with-hooks.md lines 10-11
        "Hooks provide deterministic shell command execution at lifecycle points — a Claude Code feature not available on all platforms",
        # Source: claude-code-capabilities-extension-options.md lines 25-26
        "Subagents and agent teams are Claude Code features for isolated execution and multi-session coordination",
        # Source: claude-code-capabilities-create-plugins.md lines 7-8
        "Plugins bundle skills, agents, hooks, and MCP servers; plugin structure is shared across Claude Code and compatible platforms",
        # Source: claude-code-capabilities-extension-options.md line 28
        "Agent teams coordinate multiple independent Claude Code sessions with shared tasks and peer-to-peer messaging",
        # Source: claude-code-capabilities-use-chrome-browser.md lines 6-8
        "Chrome browser integration (--chrome flag), git worktrees, remote control, and web sessions (claude.ai/code) are additional Claude Code features not available in CoWork",
    ],
    "8.6": [
        # Source: claude-capabilities-mcp-via-api.md lines 7-9
        "The MCP connector enables connecting to remote MCP servers from the Messages API with beta header mcp-client-2025-11-20; supports HTTP/SSE transports only",
        # Source: claude-code-capabilities-mcp.md (inferred from component)
        "Claude Code supports MCP servers configured locally via .mcp.json; Claude Desktop also supports MCP server configuration",
        # Source: claude-capabilities-mcp-via-api.md lines 24-28
        "MCP connector limitations: only tool calls supported (not full MCP spec); server must be publicly exposed via HTTP; not supported on Amazon Bedrock or Google Vertex",
        # Source: claude-capabilities-mcp-via-api.md lines 19-21
        "MCP connector supports OAuth authentication, multiple servers per request, and flexible tool configuration (allowlist/denylist)",
    ],
    "8.7": [
        # Source: claude-capabilities-memory-tool.md lines 7-8
        "The memory tool enables cross-conversation persistence through a client-side file directory that persists between sessions",
        # Source: claude-capabilities-new-in-opus-4-6.md line 62
        "The memory tool is now generally available (GA) — no beta header required",
        # Source: claude-code-capabilities-extension-options.md lines 37-39
        "CLAUDE.md provides persistent project context in Claude Code; it loads every session automatically",
        # Source: claude-code-capabilities-skills.md lines 96-101
        "Skills stored at personal level (~/.claude/skills/) are available across all projects for a user",
    ],
    "8.8": [
        # Source: claude-code-capabilities-extension-options.md lines 20-28
        "Claude Code extension types: CLAUDE.md (persistent context), Skills (reusable knowledge/workflows), MCP (external services), Subagents (isolated execution), Agent teams (multi-session coordination), Hooks (deterministic scripts)",
        # Source: claude-code-capabilities-create-plugins.md lines 7-8
        "Plugins package and distribute skills, agents, hooks, and MCP servers as a single installable unit with namespaced skills",
        # Source: claude-code-capabilities-skills.md lines 96-101
        "Skills are available at enterprise, personal, project, and plugin levels; higher-priority locations win on name conflicts",
        # Source: claude-capabilities-mcp-via-api.md lines 7-9
        "API users can connect to MCP servers directly via the MCP connector (beta header mcp-client-2025-11-20) without a separate MCP client",
    ],
    "8.9": [
        # Source: claude-capabilities-features-overview.md line 42
        "API code execution runs Python/JavaScript in a sandboxed container for data analysis, calculations, and file processing — a server-side tool",
        # Source: claude-capabilities-programmatic-tool-calling.md lines 1-7
        "Programmatic tool calling allows Claude to write code that calls tools within a code execution container, reducing latency and token consumption for multi-tool workflows",
        # Source: claude-code-capabilities-extension-options.md (inferred)
        "In Claude Code, the Bash tool provides direct shell access to the local filesystem and installed tools; it runs in the user's actual environment, not a sandbox",
        # Source: claude-capabilities-features-overview.md lines 50-53
        "Client-side tools (bash, text editor) must be implemented by the developer; server-side tools (code execution, web search) run on the platform",
    ],
    "8.10": [
        # Source: claude-code-capabilities-extension-options.md lines 25-26
        "Subagents run isolated loops that return summaries; they can be configured with custom instructions and preloaded skills",
        # Source: claude-code-capabilities-extension-options.md line 28
        "Agent teams in Claude Code coordinate multiple independent sessions with shared tasks and peer-to-peer messaging",
        # Source: claude-code-capabilities-automate-with-hooks.md lines 10-11
        "Hooks provide deterministic automation at lifecycle points — a Claude Code feature for enforcing project rules and automating tasks",
        # Source: claude-capabilities-agent-sdk-overview.md lines 9, 227-238
        "The Claude Agent SDK provides the same tools and agent loop as Claude Code, programmable in Python and TypeScript for building custom multi-step workflows",
        # Source: claude-code-capabilities-web-sessions.md lines 10-11
        "Claude Code on the web (claude.ai/code) lets users run Claude Code sessions from the browser, which partially addresses multi-step workflow needs for claude.ai users",
    ],

    # ================================================================
    # Category 9: Conversational Platform Users
    # ================================================================
    "9.1": [
        # Source: claude-capabilities-pdf-support.md lines 22-25
        "PDF processing supports up to 100 pages per request with a maximum request size of 32MB",
        # Source: claude-capabilities-context-windows.md lines 123-125
        "Claude supports up to 1M token context window (beta) for Opus 4.6, Sonnet 4.6, Sonnet 4.5, and Sonnet 4; standard 200K context window for all models",
        # Source: claude-capabilities-pdf-support.md lines 210-211
        "PDF processing converts each page into an image and extracts text alongside it, allowing comprehensive analysis of both text and visual elements",
        # Source: claude-capabilities-pdf-support.md line 32
        "All active Claude models support PDF processing natively",
    ],
    "9.2": [
        # Source: Anthropic public documentation (common knowledge from docs)
        "On the free tier of Claude.ai, conversations may be used to improve Claude's performance; paid plans (Pro, Team, Enterprise) do not use conversations for training",
        "Anthropic's data retention policies differ by plan: paid API and business plans have stronger data protection guarantees",
        "Users can use Projects on Claude.ai to organize work and apply project-specific instructions",
    ],
    "9.3": [
        # Source: claude-capabilities-features-overview.md line 44
        "Web search is a built-in server-side tool that augments Claude's knowledge with current, real-world data from across the web",
        # Source: claude-capabilities-features-overview.md line 43
        "Web fetch retrieves full content from specified web pages and PDF documents for in-depth analysis",
        # Source: claude-capabilities-new-in-opus-4-6.md lines 49-51
        "Web search and web fetch support dynamic filtering with Opus 4.6 and Sonnet 4.6, using the web_search_20260209 tool version",
        # Source: claude-capabilities-features-overview.md line 44
        "Web search is available on Claude API, Google Cloud's Vertex AI, and Microsoft Foundry",
    ],
    "9.4": [
        # Source: claude-capabilities-files-api.md line 104
        "Claude supports image analysis for JPEG, PNG, GIF, and WebP formats via image content blocks",
        # Source: claude-capabilities-files-api.md line 15
        "Image analysis (vision) is supported in all Claude 3+ models natively",
        # Source: claude-capabilities-pdf-support.md lines 210-211
        "Claude uses vision capabilities to analyze visual content including charts, diagrams, and handwriting in uploaded images and PDFs",
        # Source: claude-capabilities-files-api.md lines 104
        "Multiple images can be sent in a single request as multiple image content blocks",
    ],
    "9.5": [
        # Source: claude-capabilities-memory-tool.md lines 7-8
        "The memory tool enables persistent cross-conversation storage through a client-side file directory",
        # Source: claude-code-capabilities-extension-options.md lines 37-39
        "CLAUDE.md provides persistent context loaded every conversation in Claude Code; Projects serve a similar purpose on Claude.ai",
        # Source: claude-capabilities-new-in-opus-4-6.md line 62
        "The memory tool is generally available (no beta header) and works on all Claude 4+ models",
        # Source: claude-code-capabilities-extension-options.md lines 70-77
        "In Claude Code, CLAUDE.md loads every session; skills load on demand; both persist across conversations without re-explaining",
    ],
    "9.6": [
        # Source: claude-capabilities-agent-skills-via-api.md lines 36-43
        "Anthropic provides pre-built Agent Skills for document generation: pptx (PowerPoint), xlsx (Excel), docx (Word), pdf — available via the API with code execution",
        # Source: claude-capabilities-features-overview.md line 42
        "Code execution runs code in a sandboxed environment and can generate files for download, including documents and data visualizations",
        # Source: claude-capabilities-agent-skills-via-api.md lines 28-29
        "Agent Skills integrate with the Messages API through the code execution tool and require the skills-2025-10-02 and code-execution-2025-08-25 beta headers",
        # Source: claude-capabilities-agent-skills-via-api.md lines 36-43
        "Both Anthropic pre-built Skills and custom user-uploaded Skills are supported; custom Skills are managed via the Skills API",
    ],
    "9.7": [
        # Source: claude-capabilities-features-overview.md lines 21-32
        "Claude's API features include model capabilities (thinking, structured outputs, PDF support), tools (code execution, web search, web fetch), and context management (caching, compaction)",
        # Source: claude-code-capabilities-extension-options.md lines 10-12
        "Claude Code is designed for developers with built-in tools for file operations, search, execution, and web access in the terminal",
        # Source: claude-capabilities-pdf-support.md lines 7-8
        "Claude can analyze text, pictures, charts, and tables in uploaded PDFs for document processing and information extraction",
    ],
    "9.8": [
        # Source: Anthropic documentation (verified absence)
        "Anthropic does not offer fine-tuning for Claude models; customization is achieved through system prompts, project instructions, skills, and CLAUDE.md",
        # Source: claude-code-capabilities-extension-options.md lines 37-39
        "CLAUDE.md and Projects provide persistent custom instructions that load every session, serving as an alternative to fine-tuning",
        # Source: claude-code-capabilities-skills.md lines 7-10
        "Skills enable reusable domain-specific knowledge and workflows that Claude can apply consistently across conversations",
        # Source: claude-capabilities-features-overview.md lines 75-77
        "Prompt caching reduces costs for repeatedly using the same system prompts and instructions, making persistent customization more economical",
    ],
    "9.9": [
        # Source: Anthropic public documentation (common knowledge from docs)
        "On the free tier of Claude.ai, conversations may be used to improve Claude's performance; this creates a risk when pasting confidential client data with real names",
        "Paid plans (Pro, Team, Enterprise) do not use conversations for model training, providing stronger data protection guarantees",
        "Users should anonymize or redact sensitive information (names, project details) before pasting into the free tier, or upgrade to a paid plan",
    ],
    "9.10": [
        # Source: claude-code-capabilities-automate-with-hooks.md lines 10-11
        "Hooks in Claude Code provide deterministic automation: shell commands that execute at specific lifecycle points for tasks like formatting after edits",
        # Source: claude-capabilities-mcp-via-api.md lines 7-9
        "MCP connectors enable connecting Claude to external services like databases, Slack, and other APIs for data integration",
        # Source: claude-code-capabilities-skills.md lines 7-10
        "Skills can encode repeatable workflows (like invoice processing → spreadsheet update → email summary) for consistent execution",
        # Source: claude-capabilities-agent-sdk-overview.md lines 9
        "The Claude Agent SDK enables building custom agents that autonomously read files, run commands, and integrate with external services",
    ],
    "9.11": [
        # Source: claude-capabilities-files-api.md line 104
        "Claude supports vision/image analysis for JPEG, PNG, GIF, and WebP formats across all Claude 3+ models",
        # Source: claude-capabilities-pdf-support.md lines 7-8
        "Claude can analyze text, pictures, charts, and tables in uploaded PDF documents",
        # Source: claude-capabilities-features-overview.md line 44
        "Web search is a built-in tool that provides Claude with current, real-world data from across the web",
        # Source: claude-capabilities-features-overview.md line 42
        "Code execution enables running code for data analysis, calculations, and file processing in a sandboxed environment",
        # Source: claude-code-capabilities-skills.md lines 7-10
        "Skills extend Claude's capabilities with reusable knowledge and workflows that can be invoked or loaded automatically",
    ],
    "9.12": [
        # Source: Anthropic documentation (verified absence)
        "Claude does not provide an embeddings endpoint; Anthropic does not offer an embedding model as part of the Claude API",
        # Source: Anthropic documentation (Voyage AI partnership)
        "For embeddings, Anthropic recommends Voyage AI as a separate embedding model provider for vector search and RAG applications",
        # Source: claude-capabilities-context-windows.md lines 123-125
        "Claude's 1M token context window (beta) can process very large document sets in a single request as an alternative to embedding-based RAG for moderate-sized collections",
        # Source: claude-capabilities-features-overview.md line 25
        "Batch processing (50% cost reduction) can process large volumes of documents asynchronously for analysis at scale",
    ],

    # ================================================================
    # New tests: Can Claude Do X (Code Review, Remote Control)
    # ================================================================
    "2.6": [
        # Source: claude-code-capabilities-code-review.md lines 5-9
        "Code Review is a research preview feature for Teams and Enterprise that analyzes GitHub pull requests using a fleet of specialized agents examining code in the context of the full codebase",
        # Source: claude-code-capabilities-code-review.md lines 17-24
        "Findings are tagged by severity: Red (Normal — bug that should be fixed before merging), Yellow (Nit — minor issue), Purple (Pre-existing — bug not introduced by this PR)",
        # Source: claude-code-capabilities-code-review.md lines 67-69
        "Reviews average $15-25 per PR, scaling with PR size and complexity; billed separately through extra usage, not counting against plan's included usage",
        # Source: claude-code-capabilities-code-review.md lines 47-57
        "REVIEW.md at the repo root provides review-only guidance (style guidelines, framework conventions, things to always flag or skip); CLAUDE.md is also read and new violations are flagged as nits",
        # Source: claude-code-capabilities-code-review.md lines 12-13
        "Reviews trigger on PR open, on every push, or manually via @claude review comment; multiple agents analyze in parallel on Anthropic infrastructure",
    ],
    "2.7": [
        # Source: claude-code-capabilities-remote-control.md lines 5-7
        "Remote Control is available on all plans (Pro, Max, Team, Enterprise) and connects claude.ai/code or the Claude mobile app (iOS/Android) to a Claude Code session on your machine",
        # Source: claude-code-capabilities-remote-control.md lines 9
        "Key difference from Claude Code on the web: Remote Control executes on YOUR machine (local filesystem, MCP servers, tools, project config stay available)",
        # Source: claude-code-capabilities-remote-control.md lines 26-31
        "Start with 'claude remote-control' or '/remote-control' (/rc) from an existing session; --name flag sets custom session title; spacebar shows QR code for phone access",
        # Source: claude-code-capabilities-remote-control.md lines 43-48
        "Connect from another device by opening the session URL, scanning the QR code with Claude mobile app, or finding the session at claude.ai/code",
        # Source: claude-code-capabilities-remote-control.md lines 14-16
        "Conversation stays in sync across all connected devices; auto-reconnects when machine comes back online after sleep or network drop",
    ],

    # ================================================================
    # New tests: Implementation Guidance (Cloud Sessions)
    # ================================================================
    "3.9": [
        # Source: claude-code-capabilities-web-sessions.md lines 44-48
        "The --remote flag creates a new web session that runs in the cloud: 'claude --remote \"Fix the auth bug\"'; task runs on Anthropic infrastructure while you work locally",
        # Source: claude-code-capabilities-web-sessions.md lines 50-55
        "Each --remote creates an independent session, enabling parallel execution of multiple tasks simultaneously",
        # Source: claude-code-capabilities-web-sessions.md lines 57-62
        "/teleport (or /tp) brings a web session back to the terminal; also available via 'claude --teleport' or the 'Open in CLI' button on the web",
        # Source: claude-code-capabilities-web-sessions.md lines 95-100
        "Setup scripts (bash) run before Claude Code launches on new cloud sessions, configured in environment settings UI; they prepare dependencies and environment",
        # Source: claude-code-capabilities-web-sessions.md lines 31-36
        "Repository is cloned to an Anthropic-managed VM with internet access configured per settings; results pushed to branch and PR created",
    ],

    # ================================================================
    # New tests: Extension Awareness (Slack)
    # ================================================================
    "5.9": [
        # Source: claude-code-capabilities-slack.md lines 5-6
        "Claude Code in Slack creates Claude Code web sessions when you mention @Claude with a coding task, delegating development work without leaving Slack conversations",
        # Source: claude-code-capabilities-slack.md lines 30-33
        "Routing modes: 'Code only' routes all @mentions to Code sessions; 'Code + Chat' uses intelligent routing between Code and Chat with retry buttons",
        # Source: claude-code-capabilities-slack.md lines 37-42
        "Workflow: @mention Claude -> coding intent detected -> new web session created -> progress posted to thread -> completion with summary + 'View Session' and 'Create PR' buttons",
        # Source: claude-code-capabilities-slack.md lines 44-46
        "Context gathering: gathers context from all thread messages and recent channel messages to inform the coding task",
        # Source: claude-code-capabilities-slack.md lines 20-24
        "Prerequisites: Pro/Max/Teams/Enterprise plan, Claude Code on the web enabled, GitHub account connected with repos, Slack account linked to Claude account",
    ],

    # ================================================================
    # New tests: Cross-Platform Awareness
    # ================================================================
    "8.11": [
        # Source: claude-code-capabilities-remote-control.md lines 63-69
        "Remote Control executes on your machine (full local env access); Claude Code on the web executes in Anthropic cloud (cloud clone of repo)",
        # Source: claude-code-capabilities-remote-control.md line 9
        "Remote Control keeps local filesystem, MCP servers, tools, and project config available; web sessions operate in a cloud VM with a cloned repo",
        # Source: claude-code-capabilities-web-sessions.md lines 57-62
        "/teleport brings web sessions back to terminal; --remote sends tasks from terminal to cloud; these are one-way transfers",
        # Source: claude-code-capabilities-remote-control.md lines 65-69
        "Use Remote Control when in the middle of local work and want to continue from another device; use web sessions when no local setup is needed or for parallel tasks on remote repos",
    ],
    "8.12": [
        # Source: claude-code-capabilities-jetbrains.md lines 5-6
        "Claude Code integrates with JetBrains IDEs (IntelliJ, PyCharm, WebStorm, GoLand, PhpStorm, Android Studio) through a dedicated plugin with diff viewing and selection context",
        # Source: claude-code-capabilities-vscode.md lines 5-6
        "The VS Code extension provides a native graphical interface for Claude Code with plan review, auto-accept edits, @-mentions, conversation history, and multi-tab support",
        # Source: claude-code-capabilities-vscode.md lines 202-204
        "Claude Code is available as both VS Code extension (graphical panel) and CLI (terminal); some features are CLI-only but core agentic capabilities are the same across all surfaces",
        # Source: claude-code-capabilities-vscode.md lines 180-181
        "Settings in ~/.claude/settings.json are shared between the extension and CLI, ensuring consistent configuration across all interfaces",
    ],

    # ================================================================
    # Category 10: Competitor Migration
    # ================================================================
    "10.1": [
        # Source: claude-code-capabilities-extension-options.md lines 20-28
        "Claude Code provides agentic capabilities including subagents (isolated execution), agent teams (multi-session coordination), hooks (deterministic automation), skills (reusable workflows), and MCP (external services)",
        # Source: claude-code-capabilities-code-review.md lines 5-9
        "Code Review provides automated PR analysis with severity-tagged inline comments, running multiple specialized agents in parallel on Anthropic infrastructure",
        # Source: claude-code-capabilities-web-sessions.md lines 10-11
        "Claude Code on the web enables cloud-based sessions, parallel task execution, and integration with Slack for team workflows",
        # Source: claude-code-capabilities-jetbrains.md + vscode.md
        "Claude Code integrates with VS Code, JetBrains IDEs, and the terminal CLI with shared settings, providing consistent agentic features across all surfaces",
    ],
    "10.2": [
        # Source: claude-capabilities-features-overview.md line 42
        "Code execution runs Python and JavaScript in a sandboxed container for data analysis, calculations, and file processing — analogous to ChatGPT's Code Interpreter",
        # Source: claude-capabilities-programmatic-tool-calling.md lines 1-7
        "Programmatic tool calling allows Claude to write code that calls tools within the code execution container, reducing latency and token consumption for multi-tool workflows",
        # Source: claude-capabilities-features-overview.md line 44
        "Web search is a built-in server-side tool that augments Claude's knowledge with current web data; web fetch retrieves full content from specified URLs",
        # Source: claude-capabilities-agent-skills-via-api.md lines 36-43
        "Agent Skills extend code execution with pre-built capabilities: pptx, xlsx, docx, pdf document generation, plus custom Skills via the Skills API",
    ],
    "10.3": [
        # Source: claude-code-capabilities-skills.md lines 7-10
        "Skills are Claude's equivalent of custom GPTs: reusable knowledge and workflows that can be invoked with /skill-name or loaded automatically when relevant based on description",
        # Source: claude-code-capabilities-create-plugins.md lines 7-8
        "Plugins bundle skills, hooks, MCP servers, and agents into a single installable unit for team distribution via plugin marketplaces",
        # Source: claude-code-capabilities-skills.md lines 96-101
        "Skills are stored at enterprise, personal, project, and plugin levels; on Claude.ai and Desktop, skills upload as ZIP files with auto-invocation",
        # Source: claude-code-capabilities-extension-options.md lines 37-39
        "CLAUDE.md provides persistent context loaded every session (equivalent to custom GPT instructions); Projects on Claude.ai serve a similar purpose",
    ],
    "10.4": [
        # Source: claude-capabilities-agent-sdk-overview.md lines 9, 227-238
        "The Claude Agent SDK provides built-in tools (Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch) in Python and TypeScript, enabling custom multi-step agent workflows",
        # Source: claude-capabilities-files-api.md lines 7-8
        "The Files API supports uploads up to 500 MB per file and 100 GB per organization; files can be referenced across multiple conversations and API calls",
        # Source: claude-capabilities-features-overview.md line 42
        "Code execution provides sandboxed Python/JavaScript execution for data analysis; combined with Agent Skills, it handles document generation and data processing",
        # Source: claude-capabilities-mcp-via-api.md lines 7-9
        "The MCP connector enables connecting to remote MCP servers from the Messages API for external tool integration without implementing a separate MCP client",
        # Source: claude-capabilities-memory-tool.md lines 7-8
        "The memory tool enables cross-conversation persistence through a client-side file directory, providing state management across agent interactions",
    ],
}

"""Content extraction for Anthropic documentation sources.

Extraction strategies by page type:
- api-docs (platform.claude.com): trafilatura primary, Jina Reader fallback
- support (support.claude.com): Jina Reader only (JS-rendered via Intercom)
- github: Raw content URL (raw.githubusercontent.com) for pure markdown
- claude-code (code.claude.com): Jina Reader only (Next.js, JS-rendered)
"""

import logging
import os
import re
import time
import unicodedata
from urllib.parse import urlparse

import requests
import trafilatura

from .config import get_jina_headers

logger = logging.getLogger(__name__)

# Request timeout in seconds
REQUEST_TIMEOUT = 30

# Longer timeout for JS-heavy pages that historically take longer
SLOW_PAGE_TIMEOUT = 45

# Retry delay in seconds for Jina Reader before falling back
JINA_RETRY_DELAY = 5


# ── Content Normalization ────────────────────────────────────────────────────

def normalize_content(text: str) -> str:
    """Normalize extracted content to prevent false-positive diffs.

    Applies:
    - Unicode normalization (NFC)
    - Collapse multiple blank lines to single blank line
    - Strip trailing whitespace from each line
    - Strip leading/trailing whitespace from the whole text
    - Remove common dynamic elements (timestamps, session IDs)
    """
    if not text:
        return ""

    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.splitlines()]

    # Collapse multiple consecutive blank lines into one
    normalized_lines = []
    prev_blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        normalized_lines.append(line)
        prev_blank = is_blank

    text = "\n".join(normalized_lines)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove common dynamic elements that cause false diffs
    # e.g., "Last updated: Mar 7, 2026" or similar date stamps
    text = re.sub(
        r"(?:Last updated|Updated|Modified):?\s*\w+\s+\d{1,2},?\s*\d{4}",
        "",
        text,
    )

    # ── Strip navigation chrome (Jina Reader artifacts) ─────────────────
    # These elements appear inconsistently and cause false-positive diffs.

    lines = text.splitlines()
    filtered_lines = []
    in_nav_block = False

    for line in lines:
        stripped = line.strip()

        # Skip Jina Reader header lines
        if stripped.startswith("URL Source:") or stripped.startswith("Markdown Content:"):
            continue

        # Skip "Skip to main content" links
        if stripped == "[Skip to main content]":
            continue

        # Skip sidebar/TOC heading lines
        if stripped in ("##### Reference", "##### Build with Claude Code", "On this page"):
            continue

        # Skip image reference artifacts: ![Image N: ...]
        if re.match(r"!\[Image\s+\d+:.*\]", stripped):
            continue

        # Skip "Copy page" lines
        if stripped == "Copy page":
            continue

        # Detect and skip navigation link blocks: consecutive sidebar links
        # These are lines like "* [Link Text](/docs/en/...)" in sidebars
        if re.match(r"\*\s+\[.+\]\(/.+\)$", stripped):
            if in_nav_block or not filtered_lines or not filtered_lines[-1].strip():
                in_nav_block = True
                continue
            # First link-like line after content — start tracking
            in_nav_block = True
            continue
        else:
            in_nav_block = False

        filtered_lines.append(line)

    text = "\n".join(filtered_lines)

    # Collapse any blank lines introduced by stripping
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


# ── GitHub Raw Content ───────────────────────────────────────────────────────

def _github_to_raw_url(url: str) -> str:
    """Convert a GitHub blob URL to a raw.githubusercontent.com URL.

    Example:
        github.com/anthropics/claude-code/blob/main/CHANGELOG.md
        -> raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
    """
    parsed = urlparse(url)
    path = parsed.path
    # /anthropics/claude-code/blob/main/CHANGELOG.md
    # -> /anthropics/claude-code/main/CHANGELOG.md
    path = path.replace("/blob/", "/", 1)
    return f"https://raw.githubusercontent.com{path}"


def extract_github(url: str) -> str | None:
    """Extract content from a GitHub file via raw URL."""
    raw_url = _github_to_raw_url(url)
    try:
        resp = requests.get(raw_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        content = resp.text
        if content and len(content) > 50:
            return normalize_content(content)
        logger.warning("GitHub content too short for %s", url)
        return None
    except requests.RequestException as e:
        logger.error("GitHub extraction failed for %s: %s", url, e)
        return None


# ── Trafilatura Extraction ───────────────────────────────────────────────────

def extract_with_trafilatura(url: str) -> str | None:
    """Extract content using trafilatura (server-rendered pages)."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning("Trafilatura could not fetch %s", url)
            return None

        content = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )

        if not content or len(content) < 50:
            logger.warning("Trafilatura extracted insufficient content from %s", url)
            return None

        return normalize_content(content)

    except (requests.RequestException, OSError, ValueError, AttributeError) as e:
        logger.warning("Trafilatura failed for %s: %s", url, e)
        return None


# ── Jina Reader Extraction ───────────────────────────────────────────────────

def extract_with_jina(url: str, timeout: int = REQUEST_TIMEOUT) -> str | None:
    """Extract content using Jina Reader (JS-rendered pages)."""
    jina_url = f"https://r.jina.ai/{url}"
    headers = get_jina_headers()

    try:
        resp = requests.get(jina_url, timeout=timeout, headers=headers)
        resp.raise_for_status()

        text = resp.text
        if not text or len(text) < 50:
            logger.warning("Jina Reader returned insufficient content for %s", url)
            return None

        return normalize_content(text)

    except requests.RequestException as e:
        logger.warning("Jina Reader failed for %s: %s", url, e)
        return None


# ── Main Extraction Entry Point ──────────────────────────────────────────────

def extract_content(url: str, page_type: str) -> tuple[str | None, str]:
    """Extract content from a URL using the appropriate strategy.

    Args:
        url: The source URL to scrape.
        page_type: One of 'api-docs', 'support', 'github', 'claude-code'.

    Returns:
        Tuple of (content, extraction_method). Content is None on failure.
    """
    if page_type == "github":
        content = extract_github(url)
        return content, "github_raw"

    if page_type == "support":
        # JS-rendered (Intercom) — Jina only
        content = extract_with_jina(url)
        return content, "jina_reader"

    if page_type == "claude-code":
        # Next.js, JS-rendered — Jina primary with retry + trafilatura fallback
        content = extract_with_jina(url, timeout=SLOW_PAGE_TIMEOUT)
        if content:
            return content, "jina_reader"

        # Retry once after a pause (these pages intermittently timeout)
        logger.info("Retrying Jina Reader after %ds pause for %s", JINA_RETRY_DELAY, url)
        time.sleep(JINA_RETRY_DELAY)
        content = extract_with_jina(url, timeout=SLOW_PAGE_TIMEOUT)
        if content:
            return content, "jina_reader"

        # Last-resort fallback: trafilatura (may get partial content from SSR)
        logger.info("Falling back to trafilatura for claude-code page %s", url)
        content = extract_with_trafilatura(url)
        if content:
            return content, "trafilatura"

        return None, "jina_reader"

    if page_type == "api-docs":
        # Server-rendered — trafilatura primary, Jina fallback
        content = extract_with_trafilatura(url)
        if content:
            return content, "trafilatura"

        logger.info("Falling back to Jina Reader for %s", url)
        content = extract_with_jina(url)
        return content, "jina_reader"

    logger.error("Unknown page type '%s' for %s", page_type, url)
    return None, "unknown"

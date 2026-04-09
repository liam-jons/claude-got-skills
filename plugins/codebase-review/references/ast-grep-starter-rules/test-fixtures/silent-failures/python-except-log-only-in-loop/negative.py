# Fixture for python-except-log-only-in-loop — negative cases
import logging

logger = logging.getLogger(__name__)


def case_1_with_failed_list(items):
    """Correct pattern — parallel failed[] list."""
    results = []
    failed = []
    for item in items:
        try:
            results.append(process(item))
        except Exception as e:
            failed.append({"id": item.id, "error": str(e)})
    return {"results": results, "failed": failed}


def case_2_reraise(items):
    """Loop that logs and re-raises — not silent."""
    results = []
    for item in items:
        try:
            results.append(process(item))
        except Exception as e:
            logger.error("item %s failed: %s", item, e)
            raise
    return results


def case_3_try_not_in_loop(item):
    """Single try/except outside a loop — different pattern."""
    try:
        return process(item)
    except Exception as e:
        logger.error("failed: %s", e)
        return None


def case_4_loop_no_try(items):
    """Loop with no try/except — not the pattern."""
    return [process(item) for item in items]


def process(item):
    return item

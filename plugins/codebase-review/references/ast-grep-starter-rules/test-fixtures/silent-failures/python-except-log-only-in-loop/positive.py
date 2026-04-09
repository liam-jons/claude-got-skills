# Fixture for python-except-log-only-in-loop — positive cases
import logging

logger = logging.getLogger(__name__)


def case_1_for_loop_log_only(items):
    results = []
    for item in items:
        try:
            results.append(process(item))
        except Exception as e:
            logger.error("failed %s: %s", item, e)
    return {"results": results}


def case_2_while_loop_log_only(items):
    results = []
    i = 0
    while i < len(items):
        try:
            results.append(process(items[i]))
        except Exception as e:
            logger.warning("skipping %s: %s", items[i], e)
        i += 1
    return results


def case_3_for_loop_print(items):
    results = []
    for item in items:
        try:
            results.append(process(item))
        except Exception as e:
            print(f"failed: {e}")
    return results


def process(item):
    return item

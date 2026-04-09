# Fixture for python-except-pass — negative cases
# None should be flagged.

import logging

logger = logging.getLogger(__name__)


def case_1_specific_with_log():
    try:
        risky_call()
    except ValueError as e:
        logger.warning("value error: %s", e)


def case_2_reraise():
    try:
        risky_call()
    except Exception as e:
        logger.error("re-raising: %s", e)
        raise


def case_3_specific_exception_pass():
    # Specific exception with pass is acceptable if documented
    try:
        import optional_module  # type: ignore
    except ImportError:
        optional_module = None  # noqa: F841


def case_4_sentinel_comment():
    try:
        cleanup()
    except OSError as e:
        # best-effort: cleanup failure is non-fatal, logged upstream
        logger.debug("cleanup skipped: %s", e)


def risky_call():
    raise ValueError("test")


def cleanup():
    pass

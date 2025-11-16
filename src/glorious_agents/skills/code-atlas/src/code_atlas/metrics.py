"""Code metrics computation utilities."""

from typing import Any

from radon.complexity import cc_visit  # type: ignore[import-untyped]
from radon.raw import analyze  # type: ignore[import-untyped]

from code_atlas.utils import logger


def compute_metrics(source: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Compute complexity and raw metrics.

    Args:
        source: Python source code

    Returns:
        Tuple of (complexity list, raw metrics dict)
    """
    try:
        complexity = cc_visit(source)
        complexity_data = [
            {
                "function": item.name,
                "complexity": item.complexity,
                "lineno": item.lineno,
            }
            for item in complexity
        ]
    except Exception as e:  # noqa: S112
        logger.debug(f"Failed to compute complexity: {e}")
        complexity_data = []

    try:
        raw_metrics = analyze(source)
        raw = {
            "loc": raw_metrics.loc,
            "sloc": raw_metrics.sloc,
            "comments": raw_metrics.comments,
            "multi": raw_metrics.multi,
            "blank": raw_metrics.blank,
        }
    except Exception as e:  # noqa: S112
        logger.debug(f"Failed to analyze raw metrics: {e}")
        raw = {"loc": 0, "sloc": 0, "comments": 0, "multi": 0, "blank": 0}

    return complexity_data, raw

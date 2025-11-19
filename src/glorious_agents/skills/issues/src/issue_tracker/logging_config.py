"""Centralized logging configuration.

Provides structured logging with context for better observability.
"""

import logging
import sys
from pathlib import Path

from issue_tracker.config import get_settings

__all__ = ["configure_logging", "get_logger"]


def configure_logging(log_file: Path | None = None) -> None:
    """Configure application logging.

    Args:
        log_file: Optional log file path. If None, logs to stderr only.
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("issue_tracker")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger for module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"issue_tracker.{name}")

"""Centralized logging configuration for Glorious Agent Framework.

Provides a unified, consistent logging setup across all modules and skills.
Supports both console and file logging with configurable levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

__all__ = ["configure_logging", "get_logger", "setup_file_logging", "get_log_level"]


def get_log_level(level_str: str) -> int:
    """Convert string log level to logging constant.

    Args:
        level_str: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logging level constant
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str.upper(), logging.INFO)


def configure_logging(
    name: str = "glorious",
    level: str = "INFO",
    log_file: Path | None = None,
    format_style: str = "detailed",
) -> None:
    """Configure centralized logging for the application.

    Sets up consistent logging across all modules with optional file output.

    Args:
        name: Logger name (usually package name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. Creates parent directories if needed
        format_style: Format style - "detailed" or "simple"

    Example:
        >>> configure_logging("glorious", level="DEBUG", log_file=Path("logs/app.log"))
    """
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(level))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.propagate = True

    # Choose format
    if format_style == "detailed":
        fmt = "[%(asctime)s] %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        date_fmt = "%Y-%m-%d %H:%M:%S"
    else:  # simple
        fmt = "[%(asctime)s] %(levelname)s | %(name)s | %(message)s"
        date_fmt = "%H:%M:%S"

    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(get_log_level(level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        setup_file_logging(logger, log_file, level, formatter)


def setup_file_logging(
    logger: logging.Logger,
    log_file: Path,
    level: str = "DEBUG",
    formatter: logging.Formatter | None = None,
) -> None:
    """Add file logging to existing logger.

    Args:
        logger: Logger instance to configure
        log_file: Path to log file
        level: Log level for file handler
        formatter: Optional formatter (uses detailed format if not provided)
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if formatter is None:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(get_log_level(level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def get_logger(name: str, namespace: str = "glorious") -> logging.Logger:
    """Get configured logger for a module.

    Args:
        name: Module name (typically __name__)
        namespace: Parent namespace (default: "glorious")

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    full_name = f"{namespace}.{name}" if namespace else name
    return logging.getLogger(full_name)


def configure_root_logger(
    level: str = "INFO",
    log_file: Path | None = None,
) -> None:
    """Configure root logger for all modules.

    Useful for CLI entry points to ensure all logging is consistent.

    Args:
        level: Default log level
        log_file: Optional log file path
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(get_log_level(level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(get_log_level(level))
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(get_log_level("DEBUG"))
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

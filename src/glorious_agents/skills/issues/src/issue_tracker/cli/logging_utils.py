"""Logging utilities for CLI with verbose mode support."""

from datetime import datetime
from typing import Any

import typer

__all__ = [
    "set_verbose",
    "is_verbose",
    "verbose_log",
    "verbose_section",
    "verbose_step",
    "verbose_error",
    "verbose_success",
]

# Global verbose flag
_VERBOSE_ENABLED = False


def set_verbose(enabled: bool) -> None:
    """Set verbose logging mode."""
    global _VERBOSE_ENABLED
    _VERBOSE_ENABLED = enabled


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return _VERBOSE_ENABLED


def verbose_log(message: str, **kwargs: Any) -> None:  # type: ignore[no-untyped-def]
    """Log message only when verbose mode is enabled.

    Args:
        message: Log message
        **kwargs: Additional key-value pairs to include in log
    """
    if not _VERBOSE_ENABLED:
        return

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    prefix = f"[{timestamp}]"

    if kwargs:
        extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{prefix} {message} ({extras})"
    else:
        full_message = f"{prefix} {message}"

    typer.echo(full_message, err=True)


def verbose_section(title: str) -> None:
    """Log a section header when verbose mode is enabled."""
    if not _VERBOSE_ENABLED:
        return

    typer.echo("", err=True)
    typer.echo(f"{'=' * 60}", err=True)
    typer.echo(f"  {title}", err=True)
    typer.echo(f"{'=' * 60}", err=True)


def verbose_step(step: str, detail: str = "") -> None:
    """Log a step in the process when verbose mode is enabled."""
    if not _VERBOSE_ENABLED:
        return

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    if detail:
        typer.echo(f"[{timestamp}] → {step}: {detail}", err=True)
    else:
        typer.echo(f"[{timestamp}] → {step}", err=True)


def verbose_error(message: str, error: Exception | None = None) -> None:
    """Log an error when verbose mode is enabled."""
    if not _VERBOSE_ENABLED:
        return

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    typer.echo(f"[{timestamp}] ✗ ERROR: {message}", err=True)
    if error:
        typer.echo(f"[{timestamp}]   Details: {error}", err=True)


def verbose_success(message: str) -> None:
    """Log a success message when verbose mode is enabled."""
    if not _VERBOSE_ENABLED:
        return

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    typer.echo(f"[{timestamp}] ✓ {message}", err=True)

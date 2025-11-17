"""Error handling utilities for CLI commands."""

import sys
from collections.abc import Callable
from typing import Any, TypeVar

import typer

from issue_tracker.domain import (
    CycleDetectedError,
    DatabaseError,
    DomainError,
    InvalidTransitionError,
    InvariantViolationError,
    NotFoundError,
    ValidationError,
)

T = TypeVar("T")


def handle_cli_errors(func: Callable[..., T]) -> Callable[..., T]:  # noqa: UP047
    """Decorator to handle common CLI errors with user-friendly messages.

    Args:
        func: CLI command function to wrap

    Returns:
        Wrapped function with error handling
    """

    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except NotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            if e.entity_id:
                typer.echo(f"  Entity ID: {e.entity_id}", err=True)
            raise typer.Exit(1)
        except ValidationError as e:
            typer.echo(f"Validation Error: {e}", err=True)
            if e.field:
                typer.echo(f"  Field: {e.field}", err=True)
            raise typer.Exit(1)
        except InvalidTransitionError as e:
            typer.echo(f"Invalid Transition: {e}", err=True)
            typer.echo(f"  Cannot transition from '{e.current_state}' to '{e.target_state}'", err=True)
            raise typer.Exit(1)
        except InvariantViolationError as e:
            typer.echo(f"Constraint Violation: {e}", err=True)
            if e.entity_id:
                typer.echo(f"  Entity ID: {e.entity_id}", err=True)
            raise typer.Exit(1)
        except CycleDetectedError as e:
            typer.echo(f"Dependency Cycle Detected: {e}", err=True)
            if e.cycle_path:
                typer.echo(f"  Path: {' -> '.join(e.cycle_path)}", err=True)
            raise typer.Exit(1)
        except DatabaseError as e:
            typer.echo(f"Database Error: {e}", err=True)
            typer.echo("  Please check database connection and permissions", err=True)
            raise typer.Exit(1)
        except DomainError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except KeyboardInterrupt:
            typer.echo("\nOperation cancelled by user", err=True)
            raise typer.Exit(130)
        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            if "--verbose" in sys.argv or "-v" in sys.argv:
                import traceback

                traceback.print_exc()
            raise typer.Exit(1)

    return wrapper


def format_error_message(error: Exception) -> str:
    """Format error message for consistent display.

    Args:
        error: Exception to format

    Returns:
        Formatted error message string
    """
    if isinstance(error, NotFoundError):
        msg = f"Not found: {error}"
        if error.entity_id:
            msg += f" (ID: {error.entity_id})"
        return msg
    elif isinstance(error, ValidationError):
        msg = f"Validation failed: {error}"
        if error.field:
            msg += f" (field: {error.field})"
        return msg
    elif isinstance(error, InvalidTransitionError):
        return f"Cannot transition from '{error.current_state}' to '{error.target_state}': {error}"
    elif isinstance(error, DomainError):
        return f"Domain error: {error}"
    else:
        return str(error)

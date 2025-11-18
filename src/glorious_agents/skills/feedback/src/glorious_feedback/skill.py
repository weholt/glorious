"""Feedback skill - action outcome tracking.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

from .dependencies import get_feedback_service

app = typer.Typer(help="Action feedback tracking")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


class RecordFeedbackInput(SkillInput):
    """Input validation for recording feedback."""

    action_id: str = Field(..., min_length=1, max_length=200, description="Action ID")
    status: str = Field(..., min_length=1, max_length=50, description="Action status")
    reason: str = Field("", max_length=1000, description="Feedback reason")


@validate_input
def record_feedback(
    action_id: str, status: str, reason: str = "", action_type: str = "", meta: dict | None = None
) -> int:
    """Record action feedback.

    Args:
        action_id: Action identifier (1-200 chars).
        status: Action status (1-50 chars).
        reason: Feedback reason (max 1000 chars).
        action_type: Action type.
        meta: Additional metadata.

    Returns:
        Feedback ID.

    Raises:
        ValidationException: If input validation fails.
    """
    event_bus = getattr(_ctx, "event_bus", None) if _ctx else None
    service = get_feedback_service(event_bus=event_bus)

    with service.uow:
        feedback = service.record_feedback(action_id, status, reason, action_type, meta)
        return feedback.id


@app.command()
def record(action_id: str, status: str, reason: str = "") -> None:
    """Record action feedback."""
    try:
        feedback_id = record_feedback(action_id, status, reason)
        console.print(f"[green]Feedback {feedback_id} recorded for action '{action_id}'[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")
        raise typer.Exit(1)


@app.command()
def list(limit: int = 50) -> None:
    """List recent feedback."""
    service = get_feedback_service()

    with service.uow:
        feedback_list = service.get_recent_feedback(limit)

        # Build table while session is active
        table = Table(title="Recent Feedback")
        table.add_column("ID", style="cyan")
        table.add_column("Action", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Reason", style="dim")

        for fb in feedback_list:
            reason_short = (
                (fb.reason[:30] + "...")
                if fb.reason and len(fb.reason) > 30
                else (fb.reason or "-")
            )
            table.add_row(
                str(fb.id),
                fb.action_id,
                fb.status,
                reason_short,
            )

    if not feedback_list:
        console.print("[yellow]No feedback found[/yellow]")
    else:
        console.print(table)


@app.command()
def stats(group_by: str = "status", limit: int = 10) -> None:
    """Show feedback statistics."""
    if group_by not in ["status", "action_type"]:
        console.print("[red]Invalid group_by. Must be: status or action_type[/red]")
        raise typer.Exit(1)

    service = get_feedback_service()

    with service.uow:
        stats_data = service.get_statistics(group_by, limit)

        # Build table while session is active
        table = Table(title=f"Feedback Statistics (by {group_by})")
        table.add_column(group_by.title(), style="cyan")
        table.add_column("Count", style="yellow")

        for value, count in stats_data:
            table.add_row(value or "(empty)", str(count))

    if not stats_data:
        console.print("[yellow]No statistics available[/yellow]")
    else:
        console.print(table)


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for feedback entries.

    Searches through feedback by action_id, reason, and action_type.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_feedback_service()

    with service.uow:
        return service.search_feedback(query, limit)

"""Telemetry skill - agent action logging and observability.

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

from .dependencies import get_telemetry_service

app = typer.Typer(help="Agent telemetry and event logging")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


class LogEventInput(SkillInput):
    """Input validation for logging events."""

    category: str = Field(..., min_length=1, max_length=100, description="Event category")
    event: str = Field(..., min_length=1, max_length=500, description="Event description")
    skill: str = Field("", max_length=100, description="Skill name")
    duration_ms: int = Field(0, ge=0, description="Duration in milliseconds")
    status: str = Field("success", max_length=50, description="Event status")


@validate_input
def log_event(
    category: str,
    event: str,
    skill: str = "",
    duration_ms: int = 0,
    status: str = "success",
    project_id: str = "",
    meta: dict | None = None,
) -> int:
    """Log a telemetry event (callable API).

    Args:
        category: Event category (1-100 chars).
        event: Event description (1-500 chars).
        skill: Skill name (max 100 chars).
        duration_ms: Duration in milliseconds (>= 0).
        status: Event status (max 50 chars).
        project_id: Project identifier.
        meta: Additional metadata.

    Returns:
        Event ID.

    Raises:
        ValidationException: If input validation fails.
    """
    event_bus = getattr(_ctx, "event_bus", None) if _ctx else None
    service = get_telemetry_service(event_bus=event_bus)

    with service.uow:
        telemetry_event = service.log_event(
            category, event, skill, duration_ms, status, project_id, meta
        )
        return telemetry_event.id


@app.command()
def log(
    category: str, message: str, skill: str = "", duration: int = 0, status: str = "success"
) -> None:
    """Log a telemetry event."""
    try:
        event_id = log_event(category, message, skill, duration, status)
        console.print(f"[green]Event {event_id} logged[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")
        raise typer.Exit(1)


@app.command()
def stats(group_by: str = "category", limit: int = 10) -> None:
    """Show event statistics."""
    if group_by not in ["category", "skill", "status"]:
        console.print("[red]Invalid group_by. Must be: category, skill, or status[/red]")
        raise typer.Exit(1)

    service = get_telemetry_service()

    with service.uow:
        stats_data = service.get_statistics(group_by, limit)

        # Build table while session is active
        table = Table(title=f"Event Statistics (by {group_by})")
        table.add_column(group_by.title(), style="cyan")
        table.add_column("Count", style="yellow")
        table.add_column("Avg Duration (ms)", style="magenta")

        for name, count, avg_dur in stats_data:
            avg_display = f"{avg_dur:.1f}" if avg_dur else "-"
            table.add_row(name or "(empty)", str(count), avg_display)

    if not stats_data:
        console.print("[yellow]No statistics available[/yellow]")
    else:
        console.print(table)


@app.command()
def list(category: str = "", limit: int = 50) -> None:
    """List recent events."""
    service = get_telemetry_service()

    with service.uow:
        events = service.get_recent_events(limit, category)

        # Build table while session is active
        table = Table(title="Recent Events")
        table.add_column("ID", style="cyan")
        table.add_column("Time", style="dim")
        table.add_column("Category", style="yellow")
        table.add_column("Event", style="white")
        table.add_column("Status", style="green")

        for event in events:
            # Truncate event text
            event_text = event.event[:40] + "..." if len(event.event) > 40 else event.event
            # Extract time only from timestamp
            time_str = event.timestamp.strftime("%H:%M:%S") if event.timestamp else "-"
            table.add_row(
                str(event.id),
                time_str,
                event.category or "-",
                event_text,
                event.status or "?",
            )

    if not events:
        console.print("[yellow]No events found[/yellow]")
    else:
        console.print(table)


@app.command()
def export(format: str = "json") -> None:
    """Export telemetry data."""
    console.print(f"[yellow]Export format: {format}[/yellow]")
    console.print("[yellow]Export functionality is a placeholder[/yellow]")


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for telemetry events.

    Searches telemetry events by category, event description, and skill.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_telemetry_service()

    with service.uow:
        return service.search_events(query, limit)

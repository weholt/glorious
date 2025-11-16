"""Telemetry skill - agent action logging and observability."""

import json
from datetime import datetime

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

app = typer.Typer(help="Agent telemetry and event logging")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def search(query: str, limit: int = 10) -> list["SearchResult"]:
    """Universal search API for telemetry events.
    
    Searches telemetry events by category, event description, and skill.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of SearchResult objects
    """
    from glorious_agents.core.search import SearchResult
    
    if _ctx is None:
        return []
    
    rows = _ctx.conn.execute(
        "SELECT id, timestamp, category, event, skill, duration_ms, status FROM events"
    ).fetchall()
    
    results = []
    query_lower = query.lower()
    
    for event_id, timestamp, category, event, skill, duration_ms, status in rows:
        score = 0.0
        matched = False
        
        if query_lower in category.lower():
            score += 0.7
            matched = True
        
        if query_lower in event.lower():
            score += 0.8
            matched = True
        
        if skill and query_lower in skill.lower():
            score += 0.5
            matched = True
        
        if query_lower in status.lower():
            score += 0.3
            matched = True
        
        if matched:
            score = min(1.0, score)
            
            results.append(SearchResult(
                skill="telemetry",
                id=event_id,
                type="event",
                content=f"{category}: {event}",
                metadata={
                    "timestamp": timestamp,
                    "skill": skill or "",
                    "duration_ms": duration_ms,
                    "status": status,
                },
                score=score
            ))
    
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


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
    meta: dict | None = None
) -> int:
    """
    Log a telemetry event (callable API).

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
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    meta_json = json.dumps(meta) if meta else None

    cur = _ctx.conn.execute(
        """INSERT INTO events (category, event, project_id, skill, duration_ms, status, meta)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (category, event, project_id, skill, duration_ms, status, meta_json)
    )
    _ctx.conn.commit()
    return cur.lastrowid


@app.command()
def log(
    category: str,
    message: str,
    skill: str = "",
    duration: int = 0,
    status: str = "success"
) -> None:
    """Log a telemetry event."""
    try:
        event_id = log_event(category, message, skill, duration, status)
        console.print(f"[green]Event {event_id} logged[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def stats(group_by: str = "category", limit: int = 10) -> None:
    """Show event statistics."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    if group_by not in ["category", "skill", "status"]:
        console.print("[red]Invalid group_by. Must be: category, skill, or status[/red]")
        return

    cur = _ctx.conn.execute(f"""
        SELECT {group_by}, COUNT(*) as count, AVG(duration_ms) as avg_duration
        FROM events
        WHERE {group_by} IS NOT NULL AND {group_by} != ''
        GROUP BY {group_by}
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    table = Table(title=f"Event Statistics (by {group_by})")
    table.add_column(group_by.title(), style="cyan")
    table.add_column("Count", style="yellow")
    table.add_column("Avg Duration (ms)", style="magenta")

    for row in cur:
        name, count, avg_dur = row
        avg_display = f"{avg_dur:.1f}" if avg_dur else "-"
        table.add_row(name, str(count), avg_display)

    console.print(table)


@app.command()
def list(category: str = "", limit: int = 50) -> None:
    """List recent events."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    if category:
        cur = _ctx.conn.execute("""
            SELECT id, timestamp, category, event, skill, duration_ms, status
            FROM events
            WHERE category = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (category, limit))
    else:
        cur = _ctx.conn.execute("""
            SELECT id, timestamp, category, event, skill, duration_ms, status
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

    table = Table(title="Recent Events")
    table.add_column("ID", style="cyan")
    table.add_column("Time", style="dim")
    table.add_column("Category", style="yellow")
    table.add_column("Event", style="white")
    table.add_column("Status", style="green")

    for row in cur:
        event_id, timestamp, cat, event, skill, duration_ms, status = row
        # Truncate event text
        event_text = event[:40] + "..." if len(event) > 40 else event
        # Extract time only from timestamp
        time_only = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
        table.add_row(
            str(event_id),
            time_only,
            cat or "-",
            event_text,
            status or "?"
        )

    console.print(table)


@app.command()
def export(format: str = "json") -> None:
    """Export telemetry data."""
    console.print(f"[yellow]Export format: {format}[/yellow]")
    console.print("[yellow]Export functionality is a placeholder[/yellow]")

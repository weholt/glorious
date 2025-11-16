from __future__ import annotations

"""Feedback skill - action outcome tracking."""

import json

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

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
    """
    Record action feedback.

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
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    meta_json = json.dumps(meta) if meta else None

    cur = _ctx.conn.execute(
        """INSERT INTO feedback (action_id, action_type, status, reason, meta)
           VALUES (?, ?, ?, ?, ?)""",
        (action_id, action_type, status, reason, meta_json),
    )
    _ctx.conn.commit()
    return cur.lastrowid


@app.command()
def record(action_id: str, status: str, reason: str = "") -> None:
    """Record action feedback."""
    try:
        feedback_id = record_feedback(action_id, status, reason)
        console.print(f"[green]Feedback {feedback_id} recorded for action '{action_id}'[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def list(limit: int = 50) -> None:
    """List recent feedback."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute(
        """
        SELECT id, action_id, action_type, status, reason, created_at
        FROM feedback
        ORDER BY created_at DESC
        LIMIT ?
    """,
        (limit,),
    )

    table = Table(title="Recent Feedback")
    table.add_column("ID", style="cyan")
    table.add_column("Action", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Reason", style="dim")

    for row in cur:
        feedback_id, action_id, action_type, status, reason, _ = row
        reason_short = (reason[:30] + "...") if reason and len(reason) > 30 else (reason or "-")
        table.add_row(str(feedback_id), action_id, status, reason_short)

    console.print(table)


@app.command()
def stats(group_by: str = "status", limit: int = 10) -> None:
    """Show feedback statistics."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    if group_by not in ["status", "action_type"]:
        console.print("[red]Invalid group_by. Must be: status or action_type[/red]")
        return

    cur = _ctx.conn.execute(
        f"""
        SELECT {group_by}, COUNT(*) as count
        FROM feedback
        WHERE {group_by} IS NOT NULL AND {group_by} != ''
        GROUP BY {group_by}
        ORDER BY count DESC
        LIMIT ?
    """,
        (limit,),
    )

    table = Table(title=f"Feedback Statistics (by {group_by})")
    table.add_column(group_by.title(), style="cyan")
    table.add_column("Count", style="yellow")

    for row in cur:
        table.add_row(row[0], str(row[1]))

    console.print(table)


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for feedback entries."""
    from glorious_agents.core.search import SearchResult

    if _ctx is None:
        return []
    query_lower = query.lower()
    cur = _ctx.conn.execute(
        """
        SELECT id, action, feedback FROM feedback_log
        WHERE LOWER(action) LIKE ? OR LOWER(feedback) LIKE ?
        LIMIT ?
    """,
        (f"%{query_lower}%", f"%{query_lower}%", limit),
    )
    return [
        SearchResult(
            skill="feedback",
            id=row[0],
            type="feedback",
            content=f"{row[1]}: {row[2][:80]}",
            metadata={},
            score=0.6,
        )
        for row in cur
    ]

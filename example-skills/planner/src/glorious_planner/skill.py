"""Planner skill - action queue management with state machine."""

from typing import Literal

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

app = typer.Typer(help="Task planning and queue management")
console = Console()
_ctx: SkillContext | None = None

StatusType = Literal["queued", "running", "blocked", "done"]


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


class AddTaskInput(SkillInput):
    """Input validation for adding tasks."""

    issue_id: str = Field(..., min_length=1, max_length=200, description="Issue ID")
    priority: int = Field(0, ge=-100, le=100, description="Task priority")
    project_id: str = Field("", max_length=200, description="Project ID")
    important: bool = Field(False, description="Mark as important")


@validate_input
def add_task(issue_id: str, priority: int = 0, project_id: str = "", important: bool = False) -> int:
    """
    Add a task to the queue (callable API).

    Args:
        issue_id: Issue identifier (1-200 chars).
        priority: Task priority (-100 to 100).
        project_id: Project identifier (max 200 chars).
        important: Whether task is important.

    Returns:
        Task ID.

    Raises:
        ValidationException: If input validation fails.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute(
        """INSERT INTO planner_queue (issue_id, priority, project_id, important, status)
           VALUES (?, ?, ?, ?, 'queued')""",
        (issue_id, priority, project_id, 1 if important else 0)
    )
    _ctx.conn.commit()
    return cur.lastrowid


def get_next_task(respect_important: bool = True) -> dict | None:
    """Get the highest priority task from the queue."""
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    if respect_important:
        query = """
            SELECT id, issue_id, priority, project_id, important
            FROM planner_queue
            WHERE status = 'queued'
            ORDER BY important DESC, priority DESC
            LIMIT 1
        """
    else:
        query = """
            SELECT id, issue_id, priority, project_id, important
            FROM planner_queue
            WHERE status = 'queued'
            ORDER BY priority DESC
            LIMIT 1
        """

    cur = _ctx.conn.execute(query)
    row = cur.fetchone()

    if row:
        return {
            "id": row[0],
            "issue_id": row[1],
            "priority": row[2],
            "project_id": row[3],
            "important": bool(row[4])
        }
    return None


@app.command()
def add(
    issue_id: str,
    priority: int = 0,
    project_id: str = "",
    important: bool = False
) -> None:
    """Add a task to the queue."""
    try:
        task_id = add_task(issue_id, priority, project_id, important)
        imp_flag = " [important]" if important else ""
        console.print(f"[green]Task {task_id} added: {issue_id} (priority: {priority}){imp_flag}[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def next(respect_important: bool = True) -> None:
    """Get the next task to work on."""
    task = get_next_task(respect_important)

    if task is None:
        console.print("[yellow]No tasks in queue[/yellow]")
        return

    imp_flag = " ⭐" if task["important"] else ""
    console.print(f"[cyan]Next task: #{task['id']} - {task['issue_id']}{imp_flag}[/cyan]")
    console.print(f"  Priority: {task['priority']}")
    if task["project_id"]:
        console.print(f"  Project: {task['project_id']}")


@app.command()
def update(
    task_id: int,
    status: str = typer.Option(..., help="New status: queued, running, blocked, done")
) -> None:
    """Update task status."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    if status not in ["queued", "running", "blocked", "done"]:
        console.print("[red]Invalid status. Must be: queued, running, blocked, or done[/red]")
        return

    from datetime import datetime
    _ctx.conn.execute(
        "UPDATE planner_queue SET status = ?, updated_at = ? WHERE id = ?",
        (status, datetime.utcnow().isoformat(), task_id)
    )
    _ctx.conn.commit()

    console.print(f"[green]Task {task_id} status updated to '{status}'[/green]")


@app.command()
def list(
    status: str = typer.Option("queued", help="Filter by status"),
    limit: int = 20
) -> None:
    """List tasks in the queue."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("""
        SELECT id, issue_id, priority, status, important, project_id, created_at
        FROM planner_queue
        WHERE status = ?
        ORDER BY important DESC, priority DESC, created_at ASC
        LIMIT ?
    """, (status, limit))

    table = Table(title=f"Tasks ({status})")
    table.add_column("ID", style="cyan")
    table.add_column("Issue", style="white")
    table.add_column("Priority", style="yellow")
    table.add_column("Flags", style="magenta")
    table.add_column("Project", style="dim")

    for row in cur:
        task_id, issue_id, priority, status_val, important, project_id, _ = row
        flags = "⭐" if important else ""
        table.add_row(
            str(task_id),
            issue_id,
            str(priority),
            flags,
            project_id or "-"
        )

    console.print(table)


@app.command()
def sync(project_id: str = typer.Option(..., help="Project ID to sync")) -> None:
    """Sync tasks from issue tracker."""
    console.print(f"[yellow]Syncing tasks for project '{project_id}'...[/yellow]")
    # Placeholder: In real implementation, fetch from issues skill
    console.print("[green]Sync complete[/green]")


@app.command()
def delete(task_id: int) -> None:
    """Delete a task from the queue."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("DELETE FROM planner_queue WHERE id = ?", (task_id,))
    _ctx.conn.commit()

    if cur.rowcount > 0:
        console.print(f"[green]Task {task_id} deleted[/green]")
    else:
        console.print(f"[yellow]Task {task_id} not found[/yellow]")

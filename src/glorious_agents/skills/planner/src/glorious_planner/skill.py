"""Planner skill - action queue management with state machine.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

from typing import Literal

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

from .dependencies import get_planner_service
from .models import PlannerTask

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
def add_task(
    issue_id: str, priority: int = 0, project_id: str = "", important: bool = False
) -> int:
    """Add a task to the queue (callable API).

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
    # Get service and create task
    service = get_planner_service(event_bus=_ctx.event_bus if _ctx else None)

    with service.uow:
        task = service.create_task(issue_id, priority, project_id, important)
        return task.id


def get_next_task(respect_important: bool = True) -> dict | None:
    """Get the highest priority task from the queue."""
    service = get_planner_service()

    with service.uow:
        task = service.get_next_task(respect_important)
        if task:
            return {
                "id": task.id,
                "issue_id": task.issue_id,
                "priority": task.priority,
                "project_id": task.project_id,
                "important": task.important,
            }
        return None


@app.command()
def add(issue_id: str, priority: int = 0, project_id: str = "", important: bool = False) -> None:
    """Add a task to the queue."""
    try:
        task_id = add_task(issue_id, priority, project_id, important)
        imp_flag = " [important]" if important else ""
        console.print(
            f"[green]Task {task_id} added: {issue_id} (priority: {priority}){imp_flag}[/green]"
        )
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")
        raise typer.Exit(1)


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
    status: str = typer.Option(..., help="New status: queued, running, blocked, done"),
) -> None:
    """Update task status."""
    if status not in ["queued", "running", "blocked", "done"]:
        console.print("[red]Invalid status. Must be: queued, running, blocked, or done[/red]")
        raise typer.Exit(1)

    service = get_planner_service(event_bus=_ctx.event_bus if _ctx else None)

    with service.uow:
        task = service.update_task_status(task_id, status)
        if task:
            console.print(f"[green]Task {task_id} status updated to '{status}'[/green]")
        else:
            console.print(f"[yellow]Task {task_id} not found[/yellow]")
            raise typer.Exit(1)


@app.command()
def list(status: str = typer.Option("queued", help="Filter by status"), limit: int = 20) -> None:
    """List tasks in the queue."""
    service = get_planner_service()

    with service.uow:
        tasks = service.list_tasks(status, limit)

        # Build table while session is active
        table = Table(title=f"Tasks ({status})")
        table.add_column("ID", style="cyan")
        table.add_column("Issue", style="white")
        table.add_column("Priority", style="yellow")
        table.add_column("Flags", style="magenta")
        table.add_column("Project", style="dim")

        for task in tasks:
            flags = "⭐" if task.important else ""
            table.add_row(
                str(task.id),
                task.issue_id,
                str(task.priority),
                flags,
                task.project_id or "-",
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
    service = get_planner_service()

    with service.uow:
        deleted = service.delete_task(task_id)

    if deleted:
        console.print(f"[green]Task {task_id} deleted[/green]")
    else:
        console.print(f"[yellow]Task {task_id} not found[/yellow]")


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for planner tasks.

    Searches through issue IDs and project IDs in queued tasks.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_planner_service()

    with service.uow:
        return service.search_tasks(query, limit)

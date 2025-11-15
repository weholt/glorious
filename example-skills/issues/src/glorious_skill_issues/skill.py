"""Issues skill - issue tracking with auto-creation from notes."""

from typing import Any, Literal

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import TOPIC_ISSUE_CREATED, TOPIC_NOTE_CREATED, SkillContext
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

app = typer.Typer(help="Issue tracking")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context and subscribe to note events."""
    global _ctx
    _ctx = ctx
    
    # Subscribe to note_created events to auto-create issues
    ctx.subscribe(TOPIC_NOTE_CREATED, handle_note_created)


def handle_note_created(data: dict[str, Any]) -> None:
    """Handle note_created event by creating an issue if tagged."""
    tags = data.get("tags", "")
    
    # Auto-create issue if note has "todo" or "issue" tag
    if "todo" in tags.lower() or "issue" in tags.lower():
        note_id = data.get("id")
        content = data.get("content", "")
        title = f"Follow-up for note #{note_id}"
        
        # Truncate content for description
        desc = content[:200] + "..." if len(content) > 200 else content
        
        create_issue(title, desc, source_note_id=note_id)
        console.print(f"[green]Auto-created issue from note #{note_id}[/green]")


class CreateIssueInput(SkillInput):
    """Input validation for creating issues."""

    title: str = Field(..., min_length=1, max_length=500, description="Issue title")
    description: str = Field("", max_length=10000, description="Issue description")
    status: Literal["open", "in_progress", "closed"] = Field("open", description="Issue status")
    priority: Literal["low", "medium", "high"] = Field("medium", description="Priority level")
    source_note_id: int | None = Field(None, description="Optional source note ID")


@validate_input
def create_issue(
    title: str,
    description: str = "",
    status: str = "open",
    priority: str = "medium",
    source_note_id: int | None = None,
) -> int:
    """
    Create a new issue (callable API).
    
    Args:
        title: Issue title (1-500 chars).
        description: Issue description (max 10,000 chars).
        status: Issue status (open, in_progress, closed).
        priority: Priority level (low, medium, high).
        source_note_id: Optional ID of source note.
    
    Returns:
        Issue ID.

    Raises:
        ValidationException: If input validation fails.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")
    
    cur = _ctx.conn.execute("""
        INSERT INTO issues(title, description, status, priority, source_note_id)
        VALUES(?, ?, ?, ?, ?)
    """, (title, description, status, priority, source_note_id))
    _ctx.conn.commit()
    issue_id = cur.lastrowid
    
    # Publish event
    _ctx.publish(TOPIC_ISSUE_CREATED, {
        "id": issue_id,
        "title": title,
        "status": status,
        "priority": priority,
    })
    
    return issue_id


class UpdateIssueInput(SkillInput):
    """Input validation for updating issues."""

    issue_id: int = Field(..., ge=1, description="Issue ID")
    title: str | None = Field(None, min_length=1, max_length=500, description="New title")
    description: str | None = Field(None, max_length=10000, description="New description")
    status: Literal["open", "in_progress", "closed"] | None = Field(None, description="New status")
    priority: Literal["low", "medium", "high"] | None = Field(None, description="New priority")


@validate_input
def update_issue(issue_id: int, **kwargs: Any) -> None:
    """
    Update an issue (callable API).
    
    Args:
        issue_id: Issue ID (must be positive).
        **kwargs: Fields to update (title, description, status, priority).

    Raises:
        ValidationException: If input validation fails.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")
    
    # Build update query dynamically
    fields = []
    values = []
    
    for key in ["title", "description", "status", "priority"]:
        if key in kwargs:
            fields.append(f"{key} = ?")
            values.append(kwargs[key])
    
    if not fields:
        return
    
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(issue_id)
    
    query = f"UPDATE issues SET {', '.join(fields)} WHERE id = ?"
    _ctx.conn.execute(query, values)
    _ctx.conn.commit()


@app.command()
def create(
    title: str,
    description: str = "",
    priority: str = typer.Option("medium", help="Priority: low, medium, high"),
) -> None:
    """Create a new issue."""
    try:
        issue_id = create_issue(title, description, priority=priority)
        console.print(f"[green]Issue #{issue_id} created successfully![/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def list(
    status: str = typer.Option("open", help="Filter by status"),
    limit: int = 10,
) -> None:
    """List issues."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return
    
    cur = _ctx.conn.execute("""
        SELECT id, title, status, priority, created_at
        FROM issues
        WHERE status = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (status, limit))
    
    table = Table(title=f"Issues ({status})")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Priority", style="yellow")
    table.add_column("Created", style="dim")
    
    for row in cur:
        title_str = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
        table.add_row(str(row[0]), title_str, row[3], row[4])
    
    console.print(table)


@app.command()
def get(issue_id: int) -> None:
    """Get a specific issue by ID."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return
    
    cur = _ctx.conn.execute("""
        SELECT id, title, description, status, priority, source_note_id, created_at, updated_at
        FROM issues
        WHERE id = ?
    """, (issue_id,))
    
    row = cur.fetchone()
    if not row:
        console.print(f"[red]Issue #{issue_id} not found.[/red]")
        return
    
    console.print(f"\n[bold cyan]Issue #{row[0]}[/bold cyan]")
    console.print(f"[bold]{row[1]}[/bold]\n")
    console.print(f"Status: [{row[3]}] | Priority: {row[4]}")
    console.print(f"[dim]Created: {row[6]} | Updated: {row[7]}[/dim]\n")
    
    if row[2]:
        console.print(row[2])
    
    if row[5]:
        console.print(f"\n[blue]Source Note: #{row[5]}[/blue]")


@app.command()
def update(
    issue_id: int,
    title: str = typer.Option(None, help="New title"),
    status: str = typer.Option(None, help="New status"),
    priority: str = typer.Option(None, help="New priority"),
) -> None:
    """Update an issue."""
    kwargs = {}
    if title:
        kwargs["title"] = title
    if status:
        kwargs["status"] = status
    if priority:
        kwargs["priority"] = priority
    
    if not kwargs:
        console.print("[yellow]No fields to update.[/yellow]")
        return
    
    update_issue(issue_id, **kwargs)
    console.print(f"[green]Issue #{issue_id} updated.[/green]")


@app.command()
def close(issue_id: int) -> None:
    """Close an issue."""
    update_issue(issue_id, status="closed")
    console.print(f"[green]Issue #{issue_id} closed.[/green]")

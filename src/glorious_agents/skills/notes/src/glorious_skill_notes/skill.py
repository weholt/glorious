"""Notes skill - persistent notes with full-text search."""

import json
from pathlib import Path
from typing import Any, Literal

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import TOPIC_NOTE_CREATED, SkillContext
from glorious_agents.core.migrations import run_migrations
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

from .dependencies import get_notes_service
from .service import NotesService

app = typer.Typer(help="Notes management")
console = Console()
_ctx: SkillContext | None = None

ImportanceLevel = Literal[0, 1, 2]  # 0=normal, 1=important, 2=critical


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx

    # Run migrations
    migrations_dir = Path(__file__).parent / "migrations"
    if migrations_dir.exists():
        run_migrations("notes", migrations_dir)


def _get_service() -> NotesService:
    """Get notes service with event bus from context.

    Returns:
        NotesService instance

    Raises:
        RuntimeError: If context not initialized
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    return get_notes_service(event_bus=_ctx.event_bus if _ctx else None)


class AddNoteInput(SkillInput):
    """Input validation for adding notes."""

    content: str = Field(..., min_length=1, max_length=100000, description="Note content")
    tags: str = Field("", max_length=500, description="Comma-separated tags")
    importance: int = Field(
        0, ge=0, le=2, description="Importance level (0=normal, 1=important, 2=critical)"
    )


class SearchNotesInput(SkillInput):
    """Input validation for searching notes."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")


@validate_input
def add_note(content: str, tags: str = "", importance: int = 0) -> int:
    """
    Add a new note (callable API).

    Args:
        content: Note content (1-100,000 chars).
        tags: Comma-separated tags (max 500 chars).
        importance: Importance level (0=normal, 1=important, 2=critical).

    Returns:
        Note ID.

    Raises:
        ValidationException: If input validation fails.
    """
    service = _get_service()
    note = service.create_note(content, tags, importance)
    return note.id


@validate_input
def search_notes(query: str) -> list[dict[str, Any]]:
    """
    Search notes using FTS5 (callable API) - legacy format.

    Args:
        query: Search query (1-1,000 chars).

    Returns:
        List of matching notes.

    Raises:
        ValidationException: If input validation fails.
    """
    service = _get_service()
    notes = service.repo.search_fts(query, limit=100)

    return [
        {
            "id": note.id,
            "content": note.content,
            "tags": note.tags,
            "created_at": str(note.created_at),
            "importance": note.importance,
        }
        for note in notes
    ]


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """
    Universal search API - returns SearchResult objects.

    Args:
        query: Search query string.
        limit: Maximum number of results.

    Returns:
        List of SearchResult objects for universal search.
    """
    service = _get_service()
    return service.search_notes(query, limit)


@app.command()
def add(
    content: str,
    tags: str = "",
    important: bool = typer.Option(False, "--important", "-i", help="Mark as important"),
    critical: bool = typer.Option(False, "--critical", "-c", help="Mark as critical"),
) -> None:
    """Add a new note."""
    try:
        # Determine importance level
        importance = 0
        if critical:
            importance = 2
        elif important:
            importance = 1

        note_id = add_note(content, tags, importance)

        importance_str = ""
        if importance == 2:
            importance_str = " [red bold]⚠ CRITICAL[/red bold]"
        elif importance == 1:
            importance_str = " [yellow bold]★ IMPORTANT[/yellow bold]"

        console.print(f"[green]Note {note_id} added successfully!{importance_str}[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def list(
    limit: int = 10,
    important_only: bool = typer.Option(
        False, "--important", "-i", help="Show only important notes"
    ),
    critical_only: bool = typer.Option(False, "--critical", "-c", help="Show only critical notes"),
) -> None:
    """List recent notes."""
    service = _get_service()

    # Determine filter
    min_importance = None
    if critical_only:
        min_importance = 2
    elif important_only:
        min_importance = 1

    notes = service.list_notes(limit=limit, min_importance=min_importance)

    title = "Recent Notes"
    if critical_only:
        title = "Critical Notes"
    elif important_only:
        title = "Important Notes"

    table = Table(title=title)
    table.add_column("ID", style="cyan")
    table.add_column("!", style="bold", width=3)  # Importance indicator
    table.add_column("Content", style="white")
    table.add_column("Tags", style="yellow")
    table.add_column("Created", style="dim")

    for note in notes:
        content = note.content[:50] + "..." if len(note.content) > 50 else note.content

        # Importance indicator
        if note.importance == 2:
            indicator = "[red]⚠[/red]"
        elif note.importance == 1:
            indicator = "[yellow]★[/yellow]"
        else:
            indicator = ""

        table.add_row(
            str(note.id),
            indicator,
            content,
            note.tags or "-",
            str(note.created_at),
        )

    console.print(table)


@app.command()
def search(
    query: str,
    json_output: bool = typer.Option(False, "--json", help="Output complete notes as JSON"),
    important_only: bool = typer.Option(
        False, "--important", "-i", help="Show only important notes"
    ),
    critical_only: bool = typer.Option(False, "--critical", "-c", help="Show only critical notes"),
) -> None:
    """Search notes using full-text search."""
    try:
        results = search_notes(query)

        # Filter by importance if requested
        if critical_only:
            results = [r for r in results if r.get("importance", 0) == 2]
        elif important_only:
            results = [r for r in results if r.get("importance", 0) >= 1]

        if not results:
            if json_output:
                console.print(json.dumps([]))
            else:
                console.print("[yellow]No results found.[/yellow]")
            return

        if json_output:
            console.print(json.dumps(results, indent=2))
        else:
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("!", style="bold", width=3)
            table.add_column("Content", style="white")
            table.add_column("Tags", style="yellow")

            for note in results:
                content = (
                    note["content"][:50] + "..." if len(note["content"]) > 50 else note["content"]
                )
                importance = note.get("importance", 0)

                if importance == 2:
                    indicator = "[red]⚠[/red]"
                elif importance == 1:
                    indicator = "[yellow]★[/yellow]"
                else:
                    indicator = ""

                table.add_row(str(note["id"]), indicator, content, note["tags"] or "-")

            console.print(table)
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def get(note_id: int) -> None:
    """Get a specific note by ID."""
    service = _get_service()
    note = service.get_note(note_id)

    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return

    importance_str = ""
    if note.importance == 2:
        importance_str = " [red bold]⚠ CRITICAL[/red bold]"
    elif note.importance == 1:
        importance_str = " [yellow bold]★ IMPORTANT[/yellow bold]"

    console.print(f"\n[bold cyan]Note #{note.id}{importance_str}[/bold cyan]")
    console.print(f"[dim]Created: {note.created_at} | Updated: {note.updated_at}[/dim]\n")
    console.print(note.content)
    if note.tags:
        console.print(f"\n[yellow]Tags: {note.tags}[/yellow]")


@app.command()
def mark(
    note_id: int,
    important: bool = typer.Option(False, "--important", "-i", help="Mark as important"),
    critical: bool = typer.Option(False, "--critical", "-c", help="Mark as critical"),
    normal: bool = typer.Option(False, "--normal", "-n", help="Mark as normal"),
) -> None:
    """Update the importance level of a note."""
    service = _get_service()

    # Determine new importance level
    if critical:
        importance = 2
        label = "[red bold]critical[/red bold]"
    elif important:
        importance = 1
        label = "[yellow bold]important[/yellow bold]"
    elif normal:
        importance = 0
        label = "normal"
    else:
        console.print("[red]Please specify --important, --critical, or --normal[/red]")
        return

    note = service.update_importance(note_id, importance)
    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return

    console.print(f"[green]Note {note_id} marked as {label}[/green]")


@app.command()
def delete(note_id: int) -> None:
    """Delete a note."""
    service = _get_service()

    if service.delete_note(note_id):
        console.print(f"[green]Note {note_id} deleted.[/green]")
    else:
        console.print(f"[red]Note {note_id} not found.[/red]")

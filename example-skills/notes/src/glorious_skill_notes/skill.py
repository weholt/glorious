"""Notes skill - persistent notes with full-text search."""

import json
from typing import Any

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import TOPIC_NOTE_CREATED, SkillContext
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

app = typer.Typer(help="Notes management")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


class AddNoteInput(SkillInput):
    """Input validation for adding notes."""

    content: str = Field(..., min_length=1, max_length=100000, description="Note content")
    tags: str = Field("", max_length=500, description="Comma-separated tags")


class SearchNotesInput(SkillInput):
    """Input validation for searching notes."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")


@validate_input
def add_note(content: str, tags: str = "") -> int:
    """
    Add a new note (callable API).

    Args:
        content: Note content (1-100,000 chars).
        tags: Comma-separated tags (max 500 chars).

    Returns:
        Note ID.

    Raises:
        ValidationException: If input validation fails.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute(
        "INSERT INTO notes(content, tags) VALUES(?, ?)",
        (content, tags)
    )
    _ctx.conn.commit()
    note_id = cur.lastrowid

    # Publish event
    _ctx.publish(TOPIC_NOTE_CREATED, {"id": note_id, "tags": tags, "content": content})

    return note_id


@validate_input
def search_notes(query: str) -> list[dict[str, Any]]:
    """
    Search notes using FTS5 (callable API).

    Args:
        query: Search query (1-1,000 chars).

    Returns:
        List of matching notes.

    Raises:
        ValidationException: If input validation fails.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute("""
        SELECT n.id, n.content, n.tags, n.created_at
        FROM notes n
        JOIN notes_fts fts ON n.id = fts.rowid
        WHERE notes_fts MATCH ?
        ORDER BY rank
    """, (query,))

    results = []
    for row in cur:
        results.append({
            "id": row[0],
            "content": row[1],
            "tags": row[2],
            "created_at": row[3],
        })

    return results


@app.command()
def add(content: str, tags: str = "") -> None:
    """Add a new note."""
    try:
        note_id = add_note(content, tags)
        console.print(f"[green]Note {note_id} added successfully![/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def list(limit: int = 10) -> None:
    """List recent notes."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return
    
    cur = _ctx.conn.execute("""
        SELECT id, content, tags, created_at
        FROM notes
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    table = Table(title="Recent Notes")
    table.add_column("ID", style="cyan")
    table.add_column("Content", style="white")
    table.add_column("Tags", style="yellow")
    table.add_column("Created", style="dim")
    
    for row in cur:
        content = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
        table.add_row(str(row[0]), content, row[2] or "-", row[3])
    
    console.print(table)


@app.command()
def search(query: str, json_output: bool = typer.Option(False, "--json", help="Output complete notes as JSON")) -> None:
    """Search notes using full-text search."""
    try:
        results = search_notes(query)

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
            table.add_column("Content", style="white")
            table.add_column("Tags", style="yellow")

            for note in results:
                content = note["content"][:50] + "..." if len(note["content"]) > 50 else note["content"]
                table.add_row(str(note["id"]), content, note["tags"] or "-")

            console.print(table)
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def get(note_id: int) -> None:
    """Get a specific note by ID."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return
    
    cur = _ctx.conn.execute("""
        SELECT id, content, tags, created_at, updated_at
        FROM notes
        WHERE id = ?
    """, (note_id,))
    
    row = cur.fetchone()
    if not row:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return
    
    console.print(f"\n[bold cyan]Note #{row[0]}[/bold cyan]")
    console.print(f"[dim]Created: {row[3]} | Updated: {row[4]}[/dim]\n")
    console.print(row[1])
    if row[2]:
        console.print(f"\n[yellow]Tags: {row[2]}[/yellow]")


@app.command()
def delete(note_id: int) -> None:
    """Delete a note."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return
    
    _ctx.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    _ctx.conn.commit()
    console.print(f"[green]Note {note_id} deleted.[/green]")

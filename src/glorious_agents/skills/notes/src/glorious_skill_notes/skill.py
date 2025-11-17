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


class AddNoteInput(SkillInput):
    """Input validation for adding notes."""

    content: str = Field(..., min_length=1, max_length=100000, description="Note content")
    tags: str = Field("", max_length=500, description="Comma-separated tags")
    importance: int = Field(0, ge=0, le=2, description="Importance level (0=normal, 1=important, 2=critical)")


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
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute(
        "INSERT INTO notes(content, tags, importance) VALUES(?, ?, ?)",
        (content, tags, importance)
    )
    _ctx.conn.commit()
    note_id = cur.lastrowid

    # Publish event
    _ctx.publish(TOPIC_NOTE_CREATED, {
        "id": note_id,
        "tags": tags,
        "content": content,
        "importance": importance
    })

    return note_id


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
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute(
        """
        SELECT n.id, n.content, n.tags, n.created_at, n.importance
        FROM notes n
        JOIN notes_fts fts ON n.id = fts.rowid
        WHERE notes_fts MATCH ?
        ORDER BY n.importance DESC, rank
    """,
        (query,),
    )

    results = []
    for row in cur:
        results.append(
            {
                "id": row[0],
                "content": row[1],
                "tags": row[2],
                "created_at": row[3],
                "importance": row[4],
            }
        )

    return results


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """
    Universal search API - returns SearchResult objects.

    Args:
        query: Search query string.
        limit: Maximum number of results.

    Returns:
        List of SearchResult objects for universal search.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute(
        """
        SELECT n.id, n.content, n.tags, n.created_at, n.importance, rank
        FROM notes n
        JOIN notes_fts fts ON n.id = fts.rowid
        WHERE notes_fts MATCH ?
        ORDER BY n.importance DESC, rank
        LIMIT ?
    """,
        (query, limit),
    )

    results = []
    for row in cur:
        # Convert FTS5 rank to 0-1 score (rank is negative, higher absolute value = better match)
        base_score = min(1.0, abs(row[5]) / 10.0) if row[5] else 0.5
        
        # Boost score based on importance (critical=+0.3, important=+0.15)
        importance = row[4]
        importance_boost = importance * 0.15
        score = min(1.0, base_score + importance_boost)

        results.append(
            SearchResult(
                skill="notes",
                id=row[0],
                type="note",
                content=row[1],
                metadata={
                    "tags": row[2],
                    "created_at": row[3],
                    "importance": importance
                },
                score=score,
            )
        )

    return results


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
    important_only: bool = typer.Option(False, "--important", "-i", help="Show only important notes"),
    critical_only: bool = typer.Option(False, "--critical", "-c", help="Show only critical notes"),
) -> None:
    """List recent notes."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    # Build query based on filters
    query = "SELECT id, content, tags, created_at, importance FROM notes"
    params: tuple = ()
    
    if critical_only:
        query += " WHERE importance = 2"
    elif important_only:
        query += " WHERE importance >= 1"
    
    query += " ORDER BY importance DESC, created_at DESC LIMIT ?"
    params = (limit,)

    cur = _ctx.conn.execute(query, params)

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

    for row in cur:
        content = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
        importance = row[4] if len(row) > 4 else 0
        
        # Importance indicator
        if importance == 2:
            indicator = "[red]⚠[/red]"
        elif importance == 1:
            indicator = "[yellow]★[/yellow]"
        else:
            indicator = ""
            
        table.add_row(str(row[0]), indicator, content, row[2] or "-", row[3])

    console.print(table)


@app.command()
def search(
    query: str,
    json_output: bool = typer.Option(False, "--json", help="Output complete notes as JSON"),
    important_only: bool = typer.Option(False, "--important", "-i", help="Show only important notes"),
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
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute(
        """
        SELECT id, content, tags, created_at, updated_at, importance
        FROM notes
        WHERE id = ?
    """,
        (note_id,),
    )

    row = cur.fetchone()
    if not row:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return

    importance = row[5] if len(row) > 5 else 0
    importance_str = ""
    if importance == 2:
        importance_str = " [red bold]⚠ CRITICAL[/red bold]"
    elif importance == 1:
        importance_str = " [yellow bold]★ IMPORTANT[/yellow bold]"

    console.print(f"\n[bold cyan]Note #{row[0]}{importance_str}[/bold cyan]")
    console.print(f"[dim]Created: {row[3]} | Updated: {row[4]}[/dim]\n")
    console.print(row[1])
    if row[2]:
        console.print(f"\n[yellow]Tags: {row[2]}[/yellow]")


@app.command()
def mark(
    note_id: int,
    important: bool = typer.Option(False, "--important", "-i", help="Mark as important"),
    critical: bool = typer.Option(False, "--critical", "-c", help="Mark as critical"),
    normal: bool = typer.Option(False, "--normal", "-n", help="Mark as normal"),
) -> None:
    """Update the importance level of a note."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

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

    _ctx.conn.execute(
        "UPDATE notes SET importance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (importance, note_id)
    )
    _ctx.conn.commit()
    
    console.print(f"[green]Note {note_id} marked as {label}[/green]")


@app.command()
def delete(note_id: int) -> None:
    """Delete a note."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    _ctx.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    _ctx.conn.commit()
    console.print(f"[green]Note {note_id} deleted.[/green]")

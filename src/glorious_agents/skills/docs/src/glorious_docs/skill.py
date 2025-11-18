"""Documentation management skill.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

from .dependencies import get_docs_service

app = typer.Typer(help="Documentation management")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for documents.

    Searches document titles and content using FTS.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_docs_service()

    with service.uow:
        return service.search_documents(query, limit)


@app.command()
def create(
    title: str = typer.Argument(None, help="Document title (optional if using --from-file)"),
    content: str = typer.Option("", "--content", help="Document content"),
    content_file: Path = typer.Option(None, "--content-file", help="Load content from file"),
    from_file: Path = typer.Option(
        None, "--from-file", help="Create from file (extracts title from first # heading)"
    ),
    epic_id: str = typer.Option(None, "--epic", help="Link to epic"),
    custom_id: str = typer.Option(None, "--id", help="Custom document ID"),
) -> None:
    """Create a new document."""
    service = get_docs_service()

    try:
        with service.uow:
            # Handle --from-file convenience option
            file_path = from_file or content_file

            if file_path:
                doc = service.create_from_file(file_path, title, epic_id, custom_id)
            else:
                if not title:
                    console.print(
                        "[red]Error: Title is required (provide as argument or use --from-file)[/red]"
                    )
                    raise typer.Exit(1)
                doc = service.create_document(title, content, epic_id, custom_id)

            console.print(f"[green]✓ Created document: {doc.id}[/green]")
            if doc.epic_id:
                console.print(f"  Linked to epic: {doc.epic_id}")
            console.print(f"  Title: {doc.title}")
            console.print(f"  Content length: {len(doc.content)} characters")
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def get(
    doc_id: str = typer.Argument(..., help="Document ID"),
    version: int = typer.Option(None, "--version", help="Get specific version"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    render: bool = typer.Option(True, "--render/--no-render", help="Render markdown"),
) -> None:
    """Get a document by ID."""
    service = get_docs_service()

    with service.uow:
        if version:
            doc_version = service.get_version(doc_id, version)
            if not doc_version:
                console.print(f"[red]Document {doc_id} version {version} not found[/red]")
                raise typer.Exit(1)

            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "doc_id": doc_version.doc_id,
                            "version": doc_version.version,
                            "content": doc_version.content,
                            "changed_at": doc_version.changed_at.isoformat()
                            if doc_version.changed_at
                            else None,
                        }
                    )
                )
            else:
                console.print(
                    f"[cyan]Document: {doc_version.doc_id} (version {doc_version.version})[/cyan]"
                )
                console.print(f"Changed: {doc_version.changed_at}\n")
                if render:
                    console.print(Markdown(doc_version.content))
                else:
                    console.print(doc_version.content)
        else:
            doc = service.get_document(doc_id)
            if not doc:
                console.print(f"[red]Document {doc_id} not found[/red]")
                raise typer.Exit(1)

            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "id": doc.id,
                            "title": doc.title,
                            "content": doc.content,
                            "epic_id": doc.epic_id,
                            "version": doc.version,
                            "created_at": doc.created_at.isoformat() if doc.created_at else None,
                            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                        }
                    )
                )
            else:
                console.print(f"[cyan]Document: {doc.id}[/cyan]")
                console.print(f"Title: {doc.title}")
                console.print(f"Epic: {doc.epic_id or 'None'}")
                console.print(f"Version: {doc.version}")
                console.print(f"Created: {doc.created_at}")
                console.print(f"Updated: {doc.updated_at}\n")
                if render:
                    console.print(Markdown(doc.content))
                else:
                    console.print(doc.content)


@app.command()
def update(
    doc_id: str = typer.Argument(..., help="Document ID"),
    content: str = typer.Option(None, "--content", help="New content"),
    content_file: Path = typer.Option(None, "--content-file", help="Load content from file"),
    title: str = typer.Option(None, "--title", help="Update title"),
    epic_id: str = typer.Option(None, "--epic", help="Update epic link"),
) -> None:
    """Update a document."""
    service = get_docs_service()

    try:
        with service.uow:
            if content_file:
                doc = service.update_from_file(doc_id, content_file, title, epic_id)
            else:
                if not content and not title and epic_id is None:
                    console.print("[red]Error: Nothing to update[/red]")
                    raise typer.Exit(1)
                doc = service.update_document(doc_id, title, content, epic_id)

            if not doc:
                console.print(f"[red]Document {doc_id} not found[/red]")
                raise typer.Exit(1)

            console.print(f"[green]✓ Updated document: {doc.id}[/green]")
            console.print(f"  New version: {doc.version}")
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="list")
def list_docs(
    epic_id: str = typer.Option(None, "--epic", help="Filter by epic"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all documents."""
    service = get_docs_service()

    with service.uow:
        docs = service.list_documents(epic_id)

        if json_output:
            typer.echo(
                json.dumps(
                    [
                        {
                            "id": doc.id,
                            "title": doc.title,
                            "epic_id": doc.epic_id,
                            "version": doc.version,
                            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                        }
                        for doc in docs
                    ]
                )
            )
        else:
            if not docs:
                console.print("No documents found")
                return

            table = Table(title="Documents")
            table.add_column("ID", style="cyan")
            table.add_column("Title")
            table.add_column("Epic")
            table.add_column("Ver", justify="right")
            table.add_column("Updated")

            for doc in docs:
                title_preview = doc.title[:50] + "..." if len(doc.title) > 50 else doc.title
                table.add_row(
                    doc.id,
                    title_preview,
                    doc.epic_id or "-",
                    str(doc.version),
                    str(doc.updated_at)[:19] if doc.updated_at else "",
                )

            console.print(table)


@app.command()
def search_docs(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Search documents by content."""
    results = search(query, limit)

    if json_output:
        typer.echo(
            json.dumps(
                [
                    {
                        "id": r.id,
                        "type": r.type,
                        "content": r.content,
                        "score": r.score,
                        "metadata": r.metadata,
                    }
                    for r in results
                ]
            )
        )
    else:
        if not results:
            console.print("No results found")
            return

        console.print(f"[cyan]Found {len(results)} results:[/cyan]\n")
        for r in results:
            console.print(f"[bold]{r.id}[/bold] (score: {r.score:.2f})")
            console.print(f"  {r.content[:200]}...")
            console.print()


@app.command()
def export_doc(
    doc_id: str = typer.Argument(..., help="Document ID"),
    output: Path = typer.Option(None, "--output", help="Output file"),
    version: int = typer.Option(None, "--version", help="Export specific version"),
) -> None:
    """Export document to markdown file."""
    service = get_docs_service()

    with service.uow:
        if version:
            doc_version = service.get_version(doc_id, version)
            if not doc_version:
                console.print(f"[red]Document {doc_id} version {version} not found[/red]")
                raise typer.Exit(1)
            content = doc_version.content
        else:
            doc = service.get_document(doc_id)
            if not doc:
                console.print(f"[red]Document {doc_id} not found[/red]")
                raise typer.Exit(1)
            content = doc.content

        if output:
            output.write_text(content)
            console.print(f"[green]✓ Exported to: {output}[/green]")
        else:
            typer.echo(content)


@app.command()
def versions(
    doc_id: str = typer.Argument(..., help="Document ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List document version history."""
    service = get_docs_service()

    with service.uow:
        vers = service.get_versions(doc_id)

        if json_output:
            typer.echo(
                json.dumps(
                    [
                        {
                            "version": v.version,
                            "changed_at": v.changed_at.isoformat() if v.changed_at else None,
                            "size": len(v.content),
                        }
                        for v in vers
                    ]
                )
            )
        else:
            if not vers:
                console.print(f"No versions found for {doc_id}")
                return

            table = Table(title=f"Versions: {doc_id}")
            table.add_column("Version", justify="right")
            table.add_column("Changed At")
            table.add_column("Size", justify="right")

            for v in vers:
                table.add_row(
                    str(v.version),
                    str(v.changed_at)[:19] if v.changed_at else "",
                    f"{len(v.content)} chars",
                )

            console.print(table)

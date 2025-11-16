from __future__ import annotations

"""Documentation management skill."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import frontmatter
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

app = typer.Typer(help="Documentation management")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def generate_doc_id(title: str) -> str:
    """Generate a unique document ID from title."""
    hash_obj = hashlib.sha256(title.encode())
    return f"doc-{hash_obj.hexdigest()[:8]}"


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for documents.

    Searches document titles and content using FTS.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    from glorious_agents.core.search import SearchResult

    if _ctx is None:
        return []

    cursor = _ctx.conn.execute(
        """
        SELECT d.id, d.title, snippet(docs_fts, 1, '<mark>', '</mark>', '...', 32) as snippet,
               rank
        FROM docs_fts
        JOIN docs_documents d ON docs_fts.rowid = d.rowid
        WHERE docs_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (query, limit),
    )

    results = []
    for row in cursor.fetchall():
        doc_id, title, snippet, rank = row
        # Convert FTS5 rank to 0-1 score (rank is negative, closer to 0 is better)
        score = max(0.0, min(1.0, 1.0 + (rank / 10.0)))

        results.append(
            SearchResult(
                skill="docs",
                id=doc_id,
                type="document",
                content=f"{title}\n\n{snippet}",
                metadata={"title": title},
                score=score,
            )
        )

    return results


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
    assert _ctx is not None

    # Handle --from-file convenience option
    if from_file:
        content_file = from_file

    # Load content from file if specified
    if content_file:
        if not content_file.exists():
            console.print(f"[red]Error: File not found: {content_file}[/red]")
            raise typer.Exit(1)

        # Parse frontmatter from markdown file
        try:
            post = frontmatter.load(content_file)
            content = post.content
            metadata = post.metadata

            # Extract title from frontmatter if not provided
            if not title and metadata:
                title = metadata.get("title") or metadata.get("Title")

            # Extract epic from frontmatter if not provided
            if not epic_id and metadata:
                epic_id = metadata.get("epic") or metadata.get("Epic") or metadata.get("epic_id")

            # Extract custom_id from frontmatter if not provided
            if not custom_id and metadata:
                custom_id = metadata.get("id") or metadata.get("doc_id")

            # Store additional metadata as tags (for future use)
            tags = None
            if metadata:
                tags = metadata.get("tags") or metadata.get("Tags")
                if tags and isinstance(tags, list):
                    tags = ", ".join(tags)

            # Show what we extracted
            if metadata:
                console.print("[dim]Extracted from frontmatter:[/dim]")
                if title:
                    console.print(f"  title: {title}")
                if epic_id:
                    console.print(f"  epic: {epic_id}")
                if custom_id:
                    console.print(f"  id: {custom_id}")
                if tags:
                    console.print(f"  tags: {tags}")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse frontmatter: {e}[/yellow]")
            content = content_file.read_text()

        # Auto-extract title from first # heading if still not provided
        if not title:
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            # Fallback to filename if no title found
            if not title:
                title = content_file.stem.replace("-", " ").replace("_", " ").title()

    if not title:
        console.print(
            "[red]Error: Title is required (provide as argument or use --from-file with # heading)[/red]"
        )
        raise typer.Exit(1)

    if not content:
        console.print("[yellow]Warning: Creating document with empty content[/yellow]")

    # Generate or use custom ID
    doc_id = custom_id or generate_doc_id(title)

    # Check if document already exists
    existing = _ctx.conn.execute("SELECT id FROM docs_documents WHERE id = ?", (doc_id,)).fetchone()

    if existing:
        console.print(f"[red]Error: Document {doc_id} already exists[/red]")
        raise typer.Exit(1)

    # Insert document
    _ctx.conn.execute(
        """
        INSERT INTO docs_documents (id, title, content, epic_id, version, created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """,
        (doc_id, title, content, epic_id, datetime.now(), datetime.now()),
    )

    # Save first version
    _ctx.conn.execute(
        """
        INSERT INTO docs_versions (doc_id, version, content, changed_at)
        VALUES (?, 1, ?, ?)
        """,
        (doc_id, content, datetime.now()),
    )

    _ctx.conn.commit()

    console.print(f"[green]✓ Created document: {doc_id}[/green]")
    if epic_id:
        console.print(f"  Linked to epic: {epic_id}")
    console.print(f"  Title: {title}")
    console.print(f"  Content length: {len(content)} characters")


@app.command()
def get(
    doc_id: str = typer.Argument(..., help="Document ID"),
    version: int = typer.Option(None, "--version", help="Get specific version"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    render: bool = typer.Option(True, "--render/--no-render", help="Render markdown"),
) -> None:
    """Get a document by ID."""
    assert _ctx is not None

    if version:
        # Get specific version
        row = _ctx.conn.execute(
            """
            SELECT doc_id, version, content, changed_at
            FROM docs_versions
            WHERE doc_id = ? AND version = ?
            """,
            (doc_id, version),
        ).fetchone()

        if not row:
            console.print(f"[red]Document {doc_id} version {version} not found[/red]")
            raise typer.Exit(1)

        _, ver, content, changed_at = row

        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "doc_id": doc_id,
                        "version": ver,
                        "content": content,
                        "changed_at": str(changed_at),
                    }
                )
            )
        else:
            console.print(f"[cyan]Document: {doc_id} (version {ver})[/cyan]")
            console.print(f"Changed: {changed_at}\n")
            if render:
                console.print(Markdown(content))
            else:
                console.print(content)
    else:
        # Get current version
        row = _ctx.conn.execute(
            """
            SELECT id, title, content, epic_id, version, created_at, updated_at
            FROM docs_documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()

        if not row:
            console.print(f"[red]Document {doc_id} not found[/red]")
            raise typer.Exit(1)

        doc_id, title, content, epic_id, ver, created_at, updated_at = row

        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "id": doc_id,
                        "title": title,
                        "content": content,
                        "epic_id": epic_id,
                        "version": ver,
                        "created_at": str(created_at),
                        "updated_at": str(updated_at),
                    }
                )
            )
        else:
            console.print(f"[cyan]Document: {doc_id}[/cyan]")
            console.print(f"Title: {title}")
            console.print(f"Epic: {epic_id or 'None'}")
            console.print(f"Version: {ver}")
            console.print(f"Created: {created_at}")
            console.print(f"Updated: {updated_at}\n")
            if render:
                console.print(Markdown(content))
            else:
                console.print(content)


@app.command()
def update(
    doc_id: str = typer.Argument(..., help="Document ID"),
    content: str = typer.Option(None, "--content", help="New content"),
    content_file: Path = typer.Option(None, "--content-file", help="Load content from file"),
    title: str = typer.Option(None, "--title", help="Update title"),
    epic_id: str = typer.Option(None, "--epic", help="Update epic link"),
) -> None:
    """Update a document."""
    assert _ctx is not None

    # Load content from file if specified
    if content_file:
        if not content_file.exists():
            console.print(f"[red]Error: File not found: {content_file}[/red]")
            raise typer.Exit(1)

        # Parse frontmatter from markdown file
        try:
            post = frontmatter.load(content_file)
            content = post.content
            metadata = post.metadata

            # Extract title from frontmatter if not provided via CLI
            if not title and metadata:
                title = metadata.get("title") or metadata.get("Title")

            # Extract epic from frontmatter if not provided via CLI
            if epic_id is None and metadata:
                epic_id = metadata.get("epic") or metadata.get("Epic") or metadata.get("epic_id")

            # Show what we extracted
            if metadata:
                console.print("[dim]Extracted from frontmatter:[/dim]")
                if title:
                    console.print(f"  title: {title}")
                if epic_id:
                    console.print(f"  epic: {epic_id}")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse frontmatter: {e}[/yellow]")
            content = content_file.read_text()

    if not content and not title and epic_id is None:
        console.print("[red]Error: Nothing to update[/red]")
        raise typer.Exit(1)

    # Get current document
    row = _ctx.conn.execute(
        "SELECT id, title, content, epic_id, version FROM docs_documents WHERE id = ?", (doc_id,)
    ).fetchone()

    if not row:
        console.print(f"[red]Document {doc_id} not found[/red]")
        raise typer.Exit(1)

    _, current_title, current_content, current_epic, current_version = row

    # Use current values if not updating
    new_title = title or current_title
    new_content = content if content is not None else current_content
    new_epic = epic_id if epic_id is not None else current_epic
    new_version = current_version + 1

    # Update document
    _ctx.conn.execute(
        """
        UPDATE docs_documents
        SET title = ?, content = ?, epic_id = ?, version = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_title, new_content, new_epic, new_version, datetime.now(), doc_id),
    )

    # Save new version if content changed
    if content is not None:
        _ctx.conn.execute(
            """
            INSERT INTO docs_versions (doc_id, version, content, changed_at)
            VALUES (?, ?, ?, ?)
            """,
            (doc_id, new_version, new_content, datetime.now()),
        )

    _ctx.conn.commit()

    console.print(f"[green]✓ Updated document: {doc_id}[/green]")
    console.print(f"  New version: {new_version}")


@app.command(name="list")
def list_docs(
    epic_id: str = typer.Option(None, "--epic", help="Filter by epic"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all documents."""
    assert _ctx is not None

    if epic_id:
        cursor = _ctx.conn.execute(
            """
            SELECT id, title, epic_id, version, updated_at
            FROM docs_documents
            WHERE epic_id = ?
            ORDER BY updated_at DESC
            """,
            (epic_id,),
        )
    else:
        cursor = _ctx.conn.execute(
            """
            SELECT id, title, epic_id, version, updated_at
            FROM docs_documents
            ORDER BY updated_at DESC
            """
        )

    docs = cursor.fetchall()

    if json_output:
        typer.echo(
            json.dumps(
                [
                    {
                        "id": row[0],
                        "title": row[1],
                        "epic_id": row[2],
                        "version": row[3],
                        "updated_at": str(row[4]),
                    }
                    for row in docs
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

        for row in docs:
            table.add_row(
                row[0],
                row[1][:50] + "..." if len(row[1]) > 50 else row[1],
                row[2] or "-",
                str(row[3]),
                str(row[4])[:19],
            )

        console.print(table)


@app.command()
def search_docs(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Search documents by content."""
    assert _ctx is not None

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
    assert _ctx is not None

    if version:
        row = _ctx.conn.execute(
            "SELECT doc_id, content FROM docs_versions WHERE doc_id = ? AND version = ?",
            (doc_id, version),
        ).fetchone()
    else:
        row = _ctx.conn.execute(
            "SELECT id, content FROM docs_documents WHERE id = ?", (doc_id,)
        ).fetchone()

    if not row:
        console.print(f"[red]Document {doc_id} not found[/red]")
        raise typer.Exit(1)

    _, content = row

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
    assert _ctx is not None

    cursor = _ctx.conn.execute(
        """
        SELECT version, changed_at, LENGTH(content) as size
        FROM docs_versions
        WHERE doc_id = ?
        ORDER BY version DESC
        """,
        (doc_id,),
    )

    vers = cursor.fetchall()

    if json_output:
        typer.echo(
            json.dumps(
                [{"version": row[0], "changed_at": str(row[1]), "size": row[2]} for row in vers]
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

        for row in vers:
            table.add_row(str(row[0]), str(row[1])[:19], f"{row[2]} chars")

        console.print(table)

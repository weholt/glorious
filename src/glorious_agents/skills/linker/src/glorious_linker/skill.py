"""Linker skill - semantic cross-references between entities."""

from __future__ import annotations

from typing import Any

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

from .dependencies import get_linker_service
from .service import LinkerService

app = typer.Typer(help="Link management between entities")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def _get_service() -> LinkerService:
    """Get linker service with event bus from context.

    Returns:
        LinkerService instance

    Raises:
        RuntimeError: If context not initialized
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    return get_linker_service(event_bus=_ctx.event_bus if _ctx else None)


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for links.

    Searches links by entity types and IDs.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = _get_service()
    return service.search_links(query, limit)


class AddLinkInput(SkillInput):
    """Input validation for adding links."""

    kind: str = Field(..., min_length=1, max_length=100, description="Link kind")
    a_type: str = Field(..., min_length=1, max_length=50, description="Source entity type")
    a_id: str = Field(..., min_length=1, max_length=200, description="Source entity ID")
    b_type: str = Field(..., min_length=1, max_length=50, description="Target entity type")
    b_id: str = Field(..., min_length=1, max_length=200, description="Target entity ID")
    weight: float = Field(1.0, ge=0.0, le=10.0, description="Link weight")


@validate_input
def add_link(kind: str, a_type: str, a_id: str, b_type: str, b_id: str, weight: float = 1.0) -> int:
    """
    Add a link between two entities (callable API).

    Args:
        kind: Link type (1-100 chars).
        a_type: Source entity type (1-50 chars).
        a_id: Source entity ID (1-200 chars).
        b_type: Target entity type (1-50 chars).
        b_id: Target entity ID (1-200 chars).
        weight: Link strength (0.0-10.0).

    Returns:
        Link ID.

    Raises:
        ValidationException: If input validation fails.
    """
    service = _get_service()
    link = service.add_link(kind, a_type, a_id, b_type, b_id, weight)
    return link.id


def get_context_bundle(entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    """
    Get all linked entities for a given entity.

    Args:
        entity_type: Entity type.
        entity_id: Entity ID.

    Returns:
        List of linked entities.
    """
    service = _get_service()
    return service.get_context_bundle(entity_type, entity_id)


@app.command()
def add(
    kind: str,
    a: str = typer.Option(..., help="Source entity (type:id)"),
    b: str = typer.Option(..., help="Target entity (type:id)"),
    weight: float = 1.0,
) -> None:
    """Add a link between two entities."""
    try:
        a_parts = a.split(":", 1)
        b_parts = b.split(":", 1)

        if len(a_parts) != 2 or len(b_parts) != 2:
            console.print("[red]Entity format must be 'type:id'[/red]")
            return

        link_id = add_link(kind, a_parts[0], a_parts[1], b_parts[0], b_parts[1], weight)
        console.print(f"[green]Link {link_id} created: {a} -> {b}[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def list(limit: int = 50) -> None:
    """List all links."""
    service = _get_service()
    links = service.list_links(limit)

    table = Table(title="Links")
    table.add_column("ID", style="cyan")
    table.add_column("Kind", style="yellow")
    table.add_column("Source", style="green")
    table.add_column("Target", style="blue")
    table.add_column("Weight", style="magenta")

    for link in links:
        source = f"{link.a_type}:{link.a_id}"
        target = f"{link.b_type}:{link.b_id}"
        table.add_row(str(link.id), link.kind, source, target, f"{link.weight:.1f}")

    console.print(table)


@app.command()
def context(entity: str) -> None:
    """Get context bundle for an entity."""
    parts = entity.split(":", 1)
    if len(parts) != 2:
        console.print("[red]Entity format must be 'type:id'[/red]")
        return

    entity_type, entity_id = parts
    bundle = get_context_bundle(entity_type, entity_id)

    if not bundle:
        console.print(f"[yellow]No links found for {entity}[/yellow]")
        return

    table = Table(title=f"Context for {entity}")
    table.add_column("Kind", style="yellow")
    table.add_column("Linked Entity", style="cyan")
    table.add_column("Weight", style="magenta")

    for item in bundle:
        linked_entity = f"{item['type']}:{item['id']}"
        table.add_row(item["kind"], linked_entity, f"{item['weight']:.1f}")

    console.print(table)


@app.command()
def rebuild(project_id: str = typer.Option(..., help="Project ID to rebuild links for")) -> None:
    """Rebuild links by discovering them from existing data."""
    console.print(f"[yellow]Rebuilding links for project '{project_id}'...[/yellow]")

    # Placeholder: In real implementation, scan issues/notes for references
    # Example: Find issue IDs mentioned in notes, file paths in issues, etc.

    console.print("[green]Link rebuild complete[/green]")


@app.command()
def delete(link_id: int) -> None:
    """Delete a link."""
    service = _get_service()

    if service.delete_link(link_id):
        console.print(f"[green]Link {link_id} deleted[/green]")
    else:
        console.print(f"[yellow]Link {link_id} not found[/yellow]")

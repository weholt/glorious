"""Vacuum skill - knowledge distillation and optimization.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

from .dependencies import get_vacuum_service

app = typer.Typer(help="Knowledge distillation")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


@app.command()
def run(
    mode: str = typer.Option("summarize", help="Mode: summarize, dedupe, promote-rules, sharpen"),
) -> None:
    """Run vacuum operation."""
    console.print(f"[yellow]Vacuum mode: {mode}[/yellow]")
    console.print("[yellow]Vacuum (placeholder) - requires LLM integration[/yellow]")
    console.print("[dim]Would process notes using LLM for optimization[/dim]")

    event_bus = getattr(_ctx, "event_bus", None) if _ctx else None
    service = get_vacuum_service(event_bus=event_bus)

    with service.uow:
        try:
            # Start operation
            operation = service.start_operation(mode)

            # Simulate processing (in real implementation, this would do actual work)
            # For now, just complete it immediately
            service.complete_operation(operation.id, items_processed=0, items_modified=0)

            console.print(f"[green]Vacuum operation '{mode}' completed[/green]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)


@app.command()
def history() -> None:
    """Show vacuum operation history."""
    service = get_vacuum_service()

    with service.uow:
        operations = service.get_recent_operations(limit=20)

        # Build table while session is active
        table = Table(title="Vacuum History")
        table.add_column("ID", style="cyan")
        table.add_column("Mode", style="yellow")
        table.add_column("Processed", style="white")
        table.add_column("Modified", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Started", style="dim")

        for op in operations:
            table.add_row(
                str(op.id),
                op.mode,
                str(op.items_processed),
                str(op.items_modified),
                op.status,
                op.started_at.strftime("%Y-%m-%d %H:%M") if op.started_at else "-",
            )

    if not operations:
        console.print("[yellow]No vacuum operations found[/yellow]")
    else:
        console.print(table)


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for vacuum operations.

    Searches through vacuum operations by mode and status.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_vacuum_service()

    with service.uow:
        return service.search_operations(query, limit)

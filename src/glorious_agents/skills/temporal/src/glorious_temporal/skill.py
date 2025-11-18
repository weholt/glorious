"""Temporal skill - time-aware filtering.

Refactored to use modern architecture with Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import typer
from rich.console import Console

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

from .dependencies import get_temporal_service

app = typer.Typer(help="Temporal filtering utilities")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


@app.command()
def parse(time_spec: str) -> None:
    """Parse time specification."""
    console.print(f"[cyan]Parsing time spec:[/cyan] {time_spec}")
    console.print("[yellow]Examples: '7d', '3h', '2025-11-14', 'last-week'[/yellow]")

    service = get_temporal_service()
    result = service.parse_time_spec(time_spec)

    if result:
        console.print(f"[green]Resolved to:[/green] {result.isoformat()}")
    else:
        console.print("[red]Could not parse time specification[/red]")


@app.command()
def filter_since(since: str) -> None:
    """Show filter query for --since flag."""
    console.print(f"[cyan]Filter query for --since {since}:[/cyan]")

    service = get_temporal_service()
    time_filter = service.create_filter(since=since)

    if time_filter.start_time:
        console.print(f"  WHERE created_at >= '{time_filter.start_time.isoformat()}'")
        console.print("[dim]Use with other skills' list commands[/dim]")
    else:
        console.print("[red]Could not parse time specification[/red]")


@app.command()
def examples() -> None:
    """Show temporal filter examples."""
    console.print("[bold cyan]Temporal Filter Examples:[/bold cyan]\n")

    service = get_temporal_service()
    for example in service.get_examples():
        console.print(f"  {example}")

    console.print("\n[dim]These flags can be added to most skill commands[/dim]")


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for temporal filters.

    Args:
        query: Search query string (unused for temporal)
        limit: Maximum number of results (unused for temporal)

    Returns:
        Empty list (temporal has no searchable content)
    """
    return []  # Temporal has no searchable content

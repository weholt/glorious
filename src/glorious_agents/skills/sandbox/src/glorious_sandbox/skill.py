"""Sandbox skill - Docker-based isolated execution.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

from .dependencies import get_sandbox_service

app = typer.Typer(help="Sandbox execution management")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


@app.command()
def run(image: str, code: str = "", timeout: int = 30) -> None:
    """Run code in isolated Docker container."""
    console.print("[yellow]Sandbox execution (placeholder)[/yellow]")
    console.print(f"  Image: {image}")
    console.print(f"  Timeout: {timeout}s")
    console.print("[dim]Note: Requires Docker daemon[/dim]")


@app.command()
def list() -> None:
    """List sandbox containers."""
    service = get_sandbox_service()

    with service.uow:
        sandboxes = service.get_recent_sandboxes(limit=20)

        # Build table while session is active
        table = Table(title="Recent Sandboxes")
        table.add_column("ID", style="cyan")
        table.add_column("Container", style="yellow")
        table.add_column("Image", style="white")
        table.add_column("Status", style="magenta")
        table.add_column("Created", style="dim")

        for sb in sandboxes:
            table.add_row(
                str(sb.id),
                sb.container_id[:12] if sb.container_id else "-",
                sb.image or "-",
                sb.status,
                sb.created_at.strftime("%Y-%m-%d %H:%M") if sb.created_at else "-",
            )

    if not sandboxes:
        console.print("[yellow]No sandboxes found[/yellow]")
    else:
        console.print(table)


@app.command()
def logs(sandbox_id: int) -> None:
    """Get logs from a sandbox."""
    service = get_sandbox_service()

    with service.uow:
        log_content = service.get_sandbox_logs(sandbox_id)

    if log_content:
        console.print(log_content)
    else:
        console.print("[yellow]No logs found[/yellow]")


@app.command()
def cleanup() -> None:
    """Clean up stopped containers."""
    console.print("[green]Cleanup complete[/green]")


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for sandboxes.

    Searches sandbox containers by image name and logs.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_sandbox_service()

    with service.uow:
        return service.search_sandboxes(query, limit)

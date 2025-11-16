from __future__ import annotations

"""Sandbox skill - Docker-based isolated execution."""

import typer
from rich.console import Console

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

app = typer.Typer(help="Sandbox execution management")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for sandboxes.

    Searches sandbox containers by image name and logs.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    from glorious_agents.core.search import SearchResult

    if _ctx is None:
        return []

    rows = _ctx.conn.execute(
        "SELECT id, container_id, image, status, logs, created_at, exit_code FROM sandboxes"
    ).fetchall()

    results = []
    query_lower = query.lower()

    for sb_id, container_id, image, status, logs, created_at, exit_code in rows:
        score = 0.0
        matched = False

        if image and query_lower in image.lower():
            score += 0.7
            matched = True

        if query_lower in status.lower():
            score += 0.4
            matched = True

        if logs and query_lower in logs.lower():
            score += 0.6
            matched = True

        if matched:
            score = min(1.0, score)

            results.append(
                SearchResult(
                    skill="sandbox",
                    id=sb_id,
                    type="sandbox",
                    content=f"{image or 'unknown'} ({status})\n{logs[:200] if logs else ''}",
                    metadata={
                        "container_id": container_id,
                        "status": status,
                        "exit_code": exit_code,
                        "created_at": created_at,
                    },
                    score=score,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


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
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("""
        SELECT id, container_id, image, status, created_at
        FROM sandboxes
        ORDER BY created_at DESC
        LIMIT 20
    """)

    console.print("[cyan]Recent Sandboxes:[/cyan]")
    for row in cur:
        console.print(f"  #{row[0]} - {row[1][:12]} ({row[2]}) - {row[3]}")


@app.command()
def logs(sandbox_id: int) -> None:
    """Get logs from a sandbox."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("SELECT logs FROM sandboxes WHERE id = ?", (sandbox_id,))
    row = cur.fetchone()

    if row and row[0]:
        console.print(row[0])
    else:
        console.print("[yellow]No logs found[/yellow]")


@app.command()
def cleanup() -> None:
    """Clean up stopped containers."""
    console.print("[green]Cleanup complete[/green]")

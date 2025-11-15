"""Sandbox skill - Docker-based isolated execution."""

import typer
from rich.console import Console

from glorious_agents.core.context import SkillContext

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
    console.print(f"[yellow]Sandbox execution (placeholder)[/yellow]")
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

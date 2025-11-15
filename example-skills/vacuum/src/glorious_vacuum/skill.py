"""Vacuum skill - knowledge distillation and optimization."""

import typer
from rich.console import Console

from glorious_agents.core.context import SkillContext

app = typer.Typer(help="Knowledge distillation")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


@app.command()
def run(mode: str = typer.Option("summarize", help="Mode: summarize, dedupe, promote-rules, sharpen")) -> None:
    """Run vacuum operation."""
    console.print(f"[yellow]Vacuum mode: {mode}[/yellow]")
    console.print("[yellow]Vacuum (placeholder) - requires LLM integration[/yellow]")
    console.print("[dim]Would process notes using LLM for optimization[/dim]")

    if mode not in ["summarize", "dedupe", "promote-rules", "sharpen"]:
        console.print("[red]Invalid mode[/red]")
        return

    # Record operation
    if _ctx:
        _ctx.conn.execute(
            "INSERT INTO vacuum_operations (mode, status) VALUES (?, 'completed')",
            (mode,)
        )
        _ctx.conn.commit()

    console.print(f"[green]Vacuum operation '{mode}' completed[/green]")


@app.command()
def history() -> None:
    """Show vacuum operation history."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("""
        SELECT id, mode, items_processed, items_modified, started_at, status
        FROM vacuum_operations
        ORDER BY started_at DESC
        LIMIT 20
    """)

    console.print("[cyan]Vacuum History:[/cyan]")
    for row in cur:
        console.print(f"  #{row[0]} - {row[1]} | Processed: {row[2]}, Modified: {row[3]} [{row[5]}]")

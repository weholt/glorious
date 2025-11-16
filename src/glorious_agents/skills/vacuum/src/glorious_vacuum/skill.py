from __future__ import annotations

"""Vacuum skill - knowledge distillation and optimization."""

import typer
from rich.console import Console

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

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

    if mode not in ["summarize", "dedupe", "promote-rules", "sharpen"]:
        console.print("[red]Invalid mode[/red]")
        return

    # Record operation
    if _ctx:
        _ctx.conn.execute(
            "INSERT INTO vacuum_operations (mode, status) VALUES (?, 'completed')", (mode,)
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
        console.print(
            f"  #{row[0]} - {row[1]} | Processed: {row[2]}, Modified: {row[3]} [{row[5]}]"
        )


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for vacuum knowledge entries."""
    from glorious_agents.core.search import SearchResult

    if _ctx is None:
        return []
    query_lower = query.lower()
    cur = _ctx.conn.execute(
        """
        SELECT id, title, summary FROM vacuum_knowledge
        WHERE LOWER(title) LIKE ? OR LOWER(summary) LIKE ?
        LIMIT ?
    """,
        (f"%{query_lower}%", f"%{query_lower}%", limit),
    )
    return [
        SearchResult(
            skill="vacuum",
            id=row[0],
            type="knowledge",
            content=f"{row[1]}: {row[2][:80]}",
            metadata={},
            score=0.7,
        )
        for row in cur
    ]

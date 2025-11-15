"""Orchestrator skill - intent routing and workflows."""

import json

import typer
from rich.console import Console

from glorious_agents.core.context import SkillContext

app = typer.Typer(help="Workflow orchestration")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


@app.command()
def run(query: str) -> None:
    """Execute a workflow from natural language intent."""
    console.print(f"[cyan]Analyzing intent:[/cyan] {query}")
    console.print("[yellow]Orchestration (placeholder) - requires LLM integration[/yellow]")
    console.print("[dim]Would parse intent, plan steps, execute skill chain[/dim]")


@app.command()
def list() -> None:
    """List workflow history."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("""
        SELECT id, name, status, created_at
        FROM workflows
        ORDER BY created_at DESC
        LIMIT 20
    """)

    console.print("[cyan]Recent Workflows:[/cyan]")
    for row in cur:
        console.print(f"  #{row[0]} - {row[1]} [{row[2]}]")


@app.command()
def status(workflow_id: int) -> None:
    """Check workflow status."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("""
        SELECT name, status, steps, created_at, completed_at
        FROM workflows WHERE id = ?
    """, (workflow_id,))

    row = cur.fetchone()
    if row:
        console.print(f"[bold]Workflow #{workflow_id}: {row[0]}[/bold]")
        console.print(f"Status: {row[1]}")
        console.print(f"Created: {row[3]}")
        if row[4]:
            console.print(f"Completed: {row[4]}")
        if row[2]:
            steps = json.loads(row[2])
            console.print(f"Steps: {len(steps)}")
    else:
        console.print("[yellow]Workflow not found[/yellow]")

"""Orchestrator skill - intent routing and workflows.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import json

import typer
from rich.console import Console

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

from .dependencies import get_orchestrator_service

app = typer.Typer(help="Workflow orchestration")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for workflows.

    Searches workflow names and intents.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_orchestrator_service()

    with service.uow:
        return service.search_workflows(query, limit)


@app.command()
def run(query: str) -> None:
    """Execute a workflow from natural language intent."""
    console.print(f"[cyan]Analyzing intent:[/cyan] {query}")
    console.print("[yellow]Orchestration (placeholder) - requires LLM integration[/yellow]")
    console.print("[dim]Would parse intent, plan steps, execute skill chain[/dim]")


@app.command()
def list() -> None:
    """List workflow history."""
    service = get_orchestrator_service()

    with service.uow:
        workflows = service.list_workflows(limit=20)

        console.print("[cyan]Recent Workflows:[/cyan]")
        for workflow in workflows:
            console.print(f"  #{workflow.id} - {workflow.name} [{workflow.status}]")


@app.command()
def status(workflow_id: int) -> None:
    """Check workflow status."""
    service = get_orchestrator_service()

    with service.uow:
        workflow = service.get_workflow(workflow_id)

        if workflow:
            console.print(f"[bold]Workflow #{workflow.id}: {workflow.name}[/bold]")
            console.print(f"Status: {workflow.status}")
            console.print(f"Created: {workflow.created_at}")
            if workflow.completed_at:
                console.print(f"Completed: {workflow.completed_at}")
            if workflow.steps:
                try:
                    steps = json.loads(workflow.steps)
                    console.print(f"Steps: {len(steps)}")
                except json.JSONDecodeError:
                    console.print("Steps: (invalid JSON)")
        else:
            console.print("[yellow]Workflow not found[/yellow]")

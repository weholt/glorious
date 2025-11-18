"""Prompts skill - template management and versioning."""

from __future__ import annotations

import json

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

from .dependencies import get_prompts_service
from .service import PromptsService

app = typer.Typer(help="Prompt template management")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def _get_service() -> PromptsService:
    """Get prompts service with event bus from context.

    Returns:
        PromptsService instance

    Raises:
        RuntimeError: If context not initialized
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    return get_prompts_service(event_bus=_ctx.event_bus if _ctx else None)


class RegisterPromptInput(SkillInput):
    """Input validation for registering prompts."""

    name: str = Field(..., min_length=1, max_length=200, description="Prompt name")
    template: str = Field(..., min_length=1, max_length=100000, description="Prompt template")


@validate_input
def register_prompt(name: str, template: str, meta: dict | None = None) -> int:
    """
    Register a new prompt template.

    Args:
        name: Prompt name (1-200 chars).
        template: Prompt template (1-100,000 chars).
        meta: Additional metadata.

    Returns:
        Prompt ID.

    Raises:
        ValidationException: If input validation fails.
    """
    service = _get_service()
    prompt = service.register_prompt(name, template, meta)
    return prompt.id


@app.command()
def register(name: str, template: str) -> None:
    """Register a new prompt template."""
    try:
        prompt_id = register_prompt(name, template)
        console.print(f"[green]Prompt '{name}' registered (ID: {prompt_id})[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def list() -> None:
    """List all prompt templates."""
    service = _get_service()
    prompts = service.list_prompts()

    table = Table(title="Prompt Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Latest Version", style="yellow")
    table.add_column("Total Versions", style="magenta")

    for prompt_info in prompts:
        table.add_row(
            prompt_info["name"],
            str(prompt_info["latest_version"]),
            str(prompt_info["total_versions"]),
        )

    console.print(table)


@app.command()
def render(name: str, vars: str = "{}") -> None:
    """Render a prompt template with variables."""
    service = _get_service()

    try:
        variables = json.loads(vars)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON for variables[/red]")
        return

    try:
        rendered = service.render_prompt(name, variables)
        if rendered is None:
            console.print(f"[yellow]Prompt '{name}' not found[/yellow]")
            return

        console.print("\n[bold cyan]Rendered Prompt:[/bold cyan]\n")
        console.print(rendered)
    except KeyError as e:
        console.print(f"[red]Missing variable: {e}[/red]")


@app.command()
def delete(name: str) -> None:
    """Delete all versions of a prompt."""
    service = _get_service()
    count = service.delete_prompt(name)

    if count > 0:
        console.print(f"[green]Deleted {count} version(s) of prompt '{name}'[/green]")
    else:
        console.print(f"[yellow]Prompt '{name}' not found[/yellow]")


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for prompt templates.

    Searches through prompt names and templates.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = _get_service()
    return service.search_prompts(query, limit)

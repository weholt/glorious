"""AI skill - LLM integration with embeddings and semantic search.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import json
from typing import Any

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, validate_input

from .dependencies import get_ai_service

app = typer.Typer(help="AI and LLM integration")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


class CompletionInput(SkillInput):
    """Input validation for LLM completions."""

    prompt: str = Field(..., min_length=1, max_length=50000, description="Prompt text")
    model: str = Field("gpt-4", max_length=100, description="Model name")
    provider: str = Field("openai", max_length=50, description="Provider (openai/anthropic)")
    max_tokens: int = Field(1000, ge=1, le=100000, description="Max tokens")


class EmbeddingInput(SkillInput):
    """Input validation for embeddings."""

    content: str = Field(..., min_length=1, max_length=50000, description="Content to embed")
    model: str = Field("text-embedding-ada-002", max_length=100, description="Model name")


@validate_input
def complete(
    prompt: str, model: str = "gpt-4", provider: str = "openai", max_tokens: int = 1000
) -> dict[str, Any]:
    """Generate LLM completion.

    Args:
        prompt: The prompt text.
        model: Model name (default: gpt-4).
        provider: Provider name (openai/anthropic).
        max_tokens: Maximum tokens to generate.

    Returns:
        Dictionary with response and metadata.
    """
    service = get_ai_service()

    with service.uow:
        return service.complete(prompt, model, provider, max_tokens)


@validate_input
def embed(content: str, model: str = "text-embedding-ada-002") -> list[float]:
    """Generate embeddings for content.

    Args:
        content: Content to embed.
        model: Embedding model name.

    Returns:
        List of embedding values.
    """
    service = get_ai_service()

    with service.uow:
        return service.embed(content, model)


def semantic_search(
    query: str, model: str = "text-embedding-ada-002", top_k: int = 5
) -> list[dict[str, Any]]:
    """Perform semantic search using embeddings.

    Args:
        query: Search query.
        model: Embedding model name.
        top_k: Number of results to return.

    Returns:
        List of search results with similarity scores.
    """
    service = get_ai_service()

    with service.uow:
        return service.semantic_search(query, model, top_k)


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for AI completions and embeddings.

    Searches completion prompts and responses using simple text matching.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_ai_service()

    with service.uow:
        return service.search_completions(query, limit)


@app.command(name="complete")
def complete_cmd(
    prompt: str = typer.Argument(..., help="Prompt text"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="Model name"),
    provider: str = typer.Option("openai", "--provider", "-p", help="Provider (openai/anthropic)"),
    max_tokens: int = typer.Option(1000, "--max-tokens", "-t", help="Max tokens"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate LLM completion."""
    try:
        result = complete(prompt, model, provider, max_tokens)
        if json_output:
            console.print(json.dumps(result))
        else:
            console.print(f"[bold green]Response:[/bold green]\n{result['response']}")
            console.print(
                f"\n[dim]Model: {result['model']} | Tokens: {result['tokens_used']}[/dim]"
            )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="embed")
def embed_cmd(
    content: str = typer.Argument(..., help="Content to embed"),
    model: str = typer.Option("text-embedding-ada-002", "--model", "-m", help="Model name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate embeddings for content."""
    try:
        embedding = embed(content, model)
        if json_output:
            console.print(json.dumps({"embedding": embedding, "dimensions": len(embedding)}))
        else:
            console.print("[bold green]Embedding generated:[/bold green]")
            console.print(f"Dimensions: {len(embedding)}")
            console.print(f"Preview: {embedding[:5]}...")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="semantic")
def semantic_search_cmd(
    query: str = typer.Argument(..., help="Search query"),
    model: str = typer.Option("text-embedding-ada-002", "--model", "-m", help="Model name"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Semantic search using embeddings."""
    try:
        results = semantic_search(query, model, top_k)
        if json_output:
            console.print(json.dumps(results))
        else:
            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            table = Table(title="Semantic Search Results")
            table.add_column("ID", style="cyan")
            table.add_column("Content", style="white")
            table.add_column("Similarity", style="green")

            for result in results:
                content_preview = (
                    result["content"][:80] + "..."
                    if len(result["content"]) > 80
                    else result["content"]
                )
                table.add_row(str(result["id"]), content_preview, f"{result['similarity']:.4f}")

            console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of records to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show completion history."""
    service = get_ai_service()

    with service.uow:
        completions = service.get_completion_history(limit)

        if json_output:
            results = [
                {
                    "id": c.id,
                    "prompt": c.prompt[:100] + "..." if len(c.prompt) > 100 else c.prompt,
                    "model": c.model,
                    "provider": c.provider,
                    "tokens": c.tokens_used,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in completions
            ]
            console.print(json.dumps(results))
        else:
            if not completions:
                console.print("[yellow]No completion history found.[/yellow]")
                return

            table = Table(title="Completion History")
            table.add_column("ID", style="cyan")
            table.add_column("Prompt", style="white")
            table.add_column("Model", style="green")
            table.add_column("Provider", style="blue")
            table.add_column("Tokens", style="yellow")

            for completion in completions:
                prompt_preview = (
                    completion.prompt[:50] + "..."
                    if len(completion.prompt) > 50
                    else completion.prompt
                )
                table.add_row(
                    str(completion.id),
                    prompt_preview,
                    completion.model,
                    completion.provider,
                    str(completion.tokens_used or 0),
                )

            console.print(table)

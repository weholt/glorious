"""AI skill - LLM integration with embeddings and semantic search."""

import json
import os
import pickle
from typing import Any

import numpy as np
import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.validation import SkillInput, validate_input

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
    """
    Generate LLM completion.

    Args:
        prompt: The prompt text.
        model: Model name (default: gpt-4).
        provider: Provider name (openai/anthropic).
        max_tokens: Maximum tokens to generate.

    Returns:
        Dictionary with response and metadata.
    """
    assert _ctx is not None, "Skill context not initialized"

    api_key = os.getenv(f"{provider.upper()}_API_KEY")
    if not api_key:
        raise ValueError(f"Missing API key for {provider}")

    if provider == "openai":
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens
            )
            result = {
                "response": response.choices[0].message.content,
                "model": model,
                "provider": provider,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
            }
        except ImportError:
            raise ValueError("OpenAI library not installed")
    elif provider == "anthropic":
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}]
            )
            result = {
                "response": response.content[0].text,
                "model": model,
                "provider": provider,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            }
        except ImportError:
            raise ValueError("Anthropic library not installed")
    else:
        raise ValueError(f"Unknown provider: {provider}")

    _ctx.conn.execute(
        "INSERT INTO ai_completions (prompt, response, model, provider, tokens_used) VALUES (?, ?, ?, ?, ?)",
        (prompt, result["response"], model, provider, result["tokens_used"]),
    )
    _ctx.conn.commit()

    return result


@validate_input
def embed(content: str, model: str = "text-embedding-ada-002") -> list[float]:
    """
    Generate embeddings for content.

    Args:
        content: Content to embed.
        model: Embedding model name.

    Returns:
        List of embedding values.
    """
    assert _ctx is not None, "Skill context not initialized"

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(model=model, input=content)
        embedding = response.data[0].embedding

        embedding_blob = pickle.dumps(embedding)
        _ctx.conn.execute(
            "INSERT INTO ai_embeddings (content, embedding, model) VALUES (?, ?, ?)",
            (content, embedding_blob, model),
        )
        _ctx.conn.commit()

        return embedding
    except ImportError:
        raise ValueError("OpenAI library not installed")


def search(query: str, limit: int = 10) -> list["SearchResult"]:
    """Universal search API for AI completions and embeddings.

    Searches completion prompts and responses using simple text matching.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    from glorious_agents.core.search import SearchResult

    if _ctx is None:
        return []

    # Search completions
    cursor = _ctx.conn.execute(
        """
        SELECT id, prompt, response, model, provider, tokens_used
        FROM ai_completions
        WHERE prompt LIKE ? OR response LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (f"%{query}%", f"%{query}%", limit),
    )

    results = []
    for row in cursor.fetchall():
        completion_id, prompt, response, model, provider, tokens = row
        # Simple relevance scoring based on position
        score = 0.8 if query.lower() in prompt.lower() else 0.6

        results.append(
            SearchResult(
                skill="ai",
                id=f"completion-{completion_id}",
                type="completion",
                content=f"{prompt[:100]}...\n\n{response[:200]}...",
                metadata={"model": model, "provider": provider, "tokens": tokens},
                score=score,
            )
        )

    return results


def semantic_search(
    query: str, model: str = "text-embedding-ada-002", top_k: int = 5
) -> list[dict[str, Any]]:
    """
    Perform semantic search using embeddings.

    Args:
        query: Search query.
        model: Embedding model name.
        top_k: Number of results to return.

    Returns:
        List of search results with similarity scores.
    """
    assert _ctx is not None, "Skill context not initialized"

    query_embedding = embed(query, model)
    query_vec = np.array(query_embedding, dtype=np.float32)

    rows = _ctx.conn.execute(
        "SELECT id, content, embedding FROM ai_embeddings WHERE model = ?", (model,)
    ).fetchall()

    if not rows:
        return []

    similarities = []
    for row_id, content, embedding_blob in rows:
        embedding = pickle.loads(embedding_blob)
        doc_vec = np.array(embedding, dtype=np.float32)
        similarity = np.dot(query_vec, doc_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
        )
        similarities.append({"id": row_id, "content": content, "similarity": float(similarity)})

    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    return similarities[:top_k]


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
            console.print(f"[bold green]Embedding generated:[/bold green]")
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
    assert _ctx is not None, "Skill context not initialized"

    rows = _ctx.conn.execute(
        "SELECT id, prompt, model, provider, tokens_used, created_at FROM ai_completions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    if json_output:
        results = [
            {
                "id": row[0],
                "prompt": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                "model": row[2],
                "provider": row[3],
                "tokens": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]
        console.print(json.dumps(results))
    else:
        if not rows:
            console.print("[yellow]No completion history found.[/yellow]")
            return

        table = Table(title="Completion History")
        table.add_column("ID", style="cyan")
        table.add_column("Prompt", style="white")
        table.add_column("Model", style="green")
        table.add_column("Provider", style="blue")
        table.add_column("Tokens", style="yellow")

        for row in rows:
            prompt_preview = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
            table.add_row(str(row[0]), prompt_preview, row[2], row[3], str(row[4]))

        console.print(table)

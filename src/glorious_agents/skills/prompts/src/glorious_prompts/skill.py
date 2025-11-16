"""Prompts skill - template management and versioning."""

import json

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

app = typer.Typer(help="Prompt template management")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


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
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    # Get current max version for this prompt name
    cur = _ctx.conn.execute("SELECT MAX(version) FROM prompts WHERE name = ?", (name,))
    max_version = cur.fetchone()[0] or 0
    new_version = max_version + 1

    meta_json = json.dumps(meta) if meta else None

    cur = _ctx.conn.execute(
        "INSERT INTO prompts (name, version, template, meta) VALUES (?, ?, ?, ?)",
        (name, new_version, template, meta_json),
    )
    _ctx.conn.commit()
    return cur.lastrowid


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
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("""
        SELECT name, MAX(version) as latest_version, COUNT(*) as versions
        FROM prompts
        GROUP BY name
        ORDER BY name
    """)

    table = Table(title="Prompt Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Latest Version", style="yellow")
    table.add_column("Total Versions", style="magenta")

    for row in cur:
        table.add_row(row[0], str(row[1]), str(row[2]))

    console.print(table)


@app.command()
def render(name: str, vars: str = "{}") -> None:
    """Render a prompt template with variables."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    try:
        variables = json.loads(vars)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON for variables[/red]")
        return

    cur = _ctx.conn.execute(
        """
        SELECT template FROM prompts
        WHERE name = ?
        ORDER BY version DESC
        LIMIT 1
    """,
        (name,),
    )

    row = cur.fetchone()
    if not row:
        console.print(f"[yellow]Prompt '{name}' not found[/yellow]")
        return

    template = row[0]

    # Simple variable substitution
    try:
        rendered = template.format(**variables)
        console.print("\n[bold cyan]Rendered Prompt:[/bold cyan]\n")
        console.print(rendered)
    except KeyError as e:
        console.print(f"[red]Missing variable: {e}[/red]")


@app.command()
def delete(name: str) -> None:
    """Delete all versions of a prompt."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("DELETE FROM prompts WHERE name = ?", (name,))
    _ctx.conn.commit()

    if cur.rowcount > 0:
        console.print(f"[green]Deleted {cur.rowcount} version(s) of prompt '{name}'[/green]")
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
    if _ctx is None:
        return []

    query_lower = query.lower()
    cur = _ctx.conn.execute(
        """
        SELECT id, name, version, template, created_at
        FROM prompts
        WHERE LOWER(name) LIKE ? OR LOWER(template) LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
    """,
        (f"%{query_lower}%", f"%{query_lower}%", limit),
    )

    results = []
    for row in cur:
        # Score based on name match (higher) vs template match (lower)
        score = 0.9 if query_lower in row[1].lower() else 0.6

        results.append(
            SearchResult(
                skill="prompts",
                id=f"{row[1]}_v{row[2]}",
                type="prompt",
                content=f"{row[1]} (v{row[2]}): {row[3][:100]}...",
                metadata={
                    "name": row[1],
                    "version": row[2],
                    "created_at": row[4],
                },
                score=score,
            )
        )

    return results

"""Main CLI entry point for glorious-agents."""

import logging
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from glorious_agents.config import config
from glorious_agents.core.loader import load_all_skills
from glorious_agents.core.registry import get_registry

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="agent",
    help="Glorious Agents - Modular skill-based agent framework",
    no_args_is_help=True,
)
# Use legacy_windows=False to avoid cp1252 encoding issues on Windows
console = Console(legacy_windows=False)


def init_app() -> None:
    """Initialize the application by loading all skills.

    Discovers and loads all available skills from the configured skills directory
    and from installed Python packages via entry points. Each loaded skill is
    mounted as a subcommand in the main CLI application.

    Raises:
        Exception: If any error occurs during skill loading or mounting. The error
            is logged and re-raised after displaying a user-friendly message.

    Example:
        >>> init_app()
        # Skills loaded and mounted as subcommands
    """
    try:
        load_all_skills()

        # Mount loaded skills as subcommands
        registry = get_registry()
        for manifest in registry.list_all():
            skill_app = registry.get_app(manifest.name)
            if skill_app:
                app.add_typer(skill_app, name=manifest.name)
    except Exception as e:
        logger.error(f"Error initializing skills: {e}", exc_info=True)
        console.print(f"[red]Error initializing skills:[/red] {e}")
        raise


@app.command()
def version() -> None:
    """Show version information for Glorious Agents.

    Displays the current version number of the Glorious Agents framework.
    The version is imported dynamically from the package metadata.

    Example:
        $ agent version
        Glorious Agents v0.1.0
    """
    from glorious_agents import __version__

    console.print(f"Glorious Agents v{__version__}")


def _generate_skill_documentation(skill: Any, registry: Any) -> list[str]:
    """Generate markdown documentation lines for a single skill.

    Documentation is primarily sourced from the skill's usage.md file.
    If usage.md doesn't exist, falls back to auto-generated command list.
    """
    manifest = registry.get_manifest(skill.name)
    if not manifest:
        return []

    content = []

    # Skill header with basic info
    content.append(f"## {manifest.name}")
    content.append("")

    # Primary documentation: usage.md (external_doc)
    usage_content = None
    if manifest.external_doc and manifest.path:
        usage_path = Path(manifest.path) / manifest.external_doc
        if usage_path.exists():
            usage_content = usage_path.read_text().strip()

    if usage_content:
        # Use the usage.md content as the primary documentation
        content.append(usage_content)
        content.append("")
    else:
        # Fallback: Auto-generate basic documentation
        content.append(f"**Version**: {manifest.version}")
        content.append("")
        content.append(f"**Description**: {manifest.description}")
        content.append("")

        # Dependencies
        if manifest.requires:
            content.append(f"**Requires**: {', '.join(manifest.requires)}")
            content.append("")

        # Auto-generate command list
        app_obj = registry.get_app(skill.name)
        if app_obj and hasattr(app_obj, "registered_commands"):
            content.append("**Commands**:")
            content.append("")

            for cmd in app_obj.registered_commands:
                cmd_name = cmd.name or cmd.callback.__name__
                cmd_help = cmd.help or cmd.callback.__doc__ or "No description"
                cmd_help_line = cmd_help.split("\n")[0].strip()
                content.append(f"- `{cmd_name}`: {cmd_help_line}")

            content.append("")
            content.append(
                "*Note: This skill is missing usage.md documentation. Please create one.*"
            )
            content.append("")

    content.append("---")
    content.append("")

    return content


def _generate_agent_tools_md(skills: Any, registry: Any) -> None:
    """Generate AGENT-TOOLS.md documentation file in the same directory as AGENTS.md."""
    # Find AGENTS.md location (default to current directory)
    agents_md_path = Path.cwd() / "AGENTS.md"

    # Use the same directory as AGENTS.md
    if agents_md_path.exists():
        target_dir = agents_md_path.parent
    else:
        target_dir = Path.cwd()

    agent_tools_path = target_dir / "AGENT-TOOLS.md"
    console.print(f"[blue]Generating {agent_tools_path}...[/blue]")

    content = ["# Agent Tools", ""]
    content.append(
        "> **Note**: This file is automatically generated by `agent init`. Do not edit manually."
    )
    content.append("")
    content.append("This document describes all available skills/tools in this agent workspace.")
    content.append("")

    for skill in skills:
        content.extend(_generate_skill_documentation(skill, registry))

    agent_tools_path.write_text("\n".join(content))
    console.print(f"[green]Generated {agent_tools_path} with {len(skills)} skills[/green]")


def _update_agents_md() -> None:
    """Update or create AGENTS.md with reference to AGENT-TOOLS.md."""
    agents_md_path = Path.cwd() / "AGENTS.md"
    reference_text = "See [AGENT-TOOLS.md](./AGENT-TOOLS.md) for available tools and skills."

    if agents_md_path.exists():
        content_str = agents_md_path.read_text()
        if reference_text not in content_str:
            updated_content = content_str.rstrip() + "\n\n" + reference_text + "\n"
            agents_md_path.write_text(updated_content)
            console.print(f"[green]✓ Updated {agents_md_path} with reference[/green]")
        else:
            console.print(f"[dim]✓ {agents_md_path} already contains reference[/dim]")
    else:
        agents_md_path.write_text(f"# Agent Instructions\n\n{reference_text}\n")
        console.print(f"[green]✓ Created {agents_md_path}[/green]")


@app.command()
def init() -> None:
    """Initialize agent workspace by generating AGENT-TOOLS.md and updating AGENTS.md."""
    # Ensure skills are loaded
    registry = get_registry()
    skills = registry.list_all()

    if not skills:
        console.print("[yellow]No skills loaded. Loading skills...[/yellow]")
        load_all_skills()
        skills = registry.list_all()

    _generate_agent_tools_md(skills, registry)
    _update_agents_md()


@app.command()
def daemon(
    host: str = typer.Option(config.DAEMON_HOST, help="Host to bind to"),
    port: int = typer.Option(config.DAEMON_PORT, help="Port to bind to"),
) -> None:
    """Start the FastAPI daemon for RPC access.

    Launches a background FastAPI server that provides HTTP access to skills
    and allows remote procedure calls to skill methods. The daemon enables
    efficient long-running operations and allows external systems to interact
    with the agent framework.

    Available Endpoints:
        GET  /skills - List all loaded skills
        POST /rpc/{skill}/{method} - Call a skill method with JSON params
        POST /events/{topic} - Publish an event to the event bus
        GET  /events/topics - List all active event topics
        GET  /cache/{key} - Retrieve a cached value
        PUT  /cache/{key} - Store a value in the cache
        DELETE /cache/{key} - Delete a cache entry
        GET  /cache - Get cache statistics

    Args:
        host: The hostname or IP address to bind the server to. Defaults to
            the value from GLORIOUS_DAEMON_HOST config (typically '127.0.0.1').
        port: The port number to bind the server to. Defaults to the value
            from GLORIOUS_DAEMON_PORT config (typically 8765).

    Example:
        $ agent daemon --host 0.0.0.0 --port 8080
        # Starts daemon accessible on all interfaces at port 8080

        # Access the API:
        $ curl http://localhost:8765/skills
        $ curl -X POST http://localhost:8765/rpc/notes/list_notes -H "Content-Type: application/json" -d '{}'
    """
    from glorious_agents.core.daemon_rpc import run_daemon

    run_daemon(host, port)


@app.command()
def info() -> None:
    """Display system information about the agent installation.

    Shows important configuration details including database type, paths,
    table counts, and other system information.

    Example:
        $ agent info
    """
    import sqlite3

    from rich.table import Table

    from glorious_agents.core.db import get_agent_db_path, get_data_folder

    table = Table(title="Glorious Agents - System Information", show_header=False)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Data folder
    data_folder = get_data_folder()
    table.add_row("Data Folder", str(data_folder))

    # Active agent
    active_file = data_folder / "active_agent"
    if active_file.exists():
        active_agent = active_file.read_text().strip()
    else:
        active_agent = "default"
    table.add_row("Active Agent", active_agent)

    # Database type
    table.add_row("Database Type", "sqlite")

    # Unified database path
    agent_db_path = get_agent_db_path()
    table.add_row("Database File", str(agent_db_path))

    # Database size
    if agent_db_path.exists():
        db_size = agent_db_path.stat().st_size / (1024 * 1024)
        table.add_row("Database Size", f"{db_size:.2f} MB")
    else:
        table.add_row("Database Size", "N/A (not initialized)")

    # Count tables in unified database
    if agent_db_path.exists():
        try:
            conn = sqlite3.connect(str(agent_db_path))
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            table_count = cursor.fetchone()[0]
            table.add_row("Total Tables", str(table_count))

            # Count tables by prefix
            cursor = conn.execute("""
                SELECT 
                    CASE 
                        WHEN name LIKE 'core_%' THEN 'Core'
                        WHEN name LIKE 'issues_%' THEN 'Issues'
                        WHEN name LIKE 'notes_%' THEN 'Notes'
                        WHEN name LIKE 'prompts_%' THEN 'Prompts'
                        WHEN name LIKE 'automations_%' THEN 'Automations'
                        WHEN name LIKE 'feedback_%' THEN 'Feedback'
                        WHEN name LIKE 'cache_%' THEN 'Cache'
                        WHEN name LIKE '_%' THEN 'Internal'
                        ELSE 'Other'
                    END as category,
                    COUNT(*) as count
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()
            if categories:
                cat_str = ", ".join([f"{cat}: {cnt}" for cat, cnt in categories])
                table.add_row("Tables by Type", cat_str)

            conn.close()
        except Exception as e:
            table.add_row("Total Tables", f"Error: {e}")
    else:
        table.add_row("Total Tables", "0 (not initialized)")

    # Skills directory
    table.add_row("Skills Directory", str(config.SKILLS_DIR))

    # Daemon settings
    table.add_row("Daemon Host", config.DAEMON_HOST)
    table.add_row("Daemon Port", str(config.DAEMON_PORT))

    console.print(table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results to return"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Search across all skills for relevant content.

    Queries all skills that support search and returns unified results.
    Each result includes the skill name and item ID for direct retrieval.

    Example:
        $ agent search "memory leak"
        $ agent search "todo" --limit 10
        $ agent search "bug" --json
    """
    import json

    from glorious_agents.core.runtime import get_ctx
    from glorious_agents.core.search import SearchResult

    get_ctx()
    all_results: list[SearchResult] = []

    # Get registry and search each skill
    registry = get_registry()
    for manifest in registry.list_all():
        skill_app = registry.get_app(manifest.name)
        if not skill_app:
            continue

        # Check if skill module has search function
        try:
            import importlib

            module_path = manifest.entry_point.split(":")[0]
            module = importlib.import_module(module_path)

            if hasattr(module, "search") and callable(module.search):
                try:
                    results = module.search(query, limit=limit)
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    logger.debug(f"Skill {manifest.name} search failed: {e}")
        except Exception:
            continue

    # Sort by score
    all_results.sort(key=lambda r: r.score, reverse=True)
    all_results = all_results[:limit]

    if json_output:
        console.print(json.dumps([r.to_dict() for r in all_results], indent=2))
    else:
        if not all_results:
            console.print("[yellow]No results found.[/yellow]")
            return

        from rich.table import Table

        table = Table(title=f"Search Results for '{query}'")
        table.add_column("Skill", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Type", style="yellow")
        table.add_column("Content", style="white")
        table.add_column("Score", style="green")

        for result in all_results:
            content = result.content[:80] + "..." if len(result.content) > 80 else result.content
            table.add_row(result.skill, str(result.id), result.type, content, f"{result.score:.2f}")

        console.print(table)


def main() -> None:
    """Main entry point for the Glorious Agents CLI.

    This function is the primary entry point invoked when running the 'agent'
    command. It performs the following initialization steps:

    1. Imports and registers management CLI modules (skills, identity)
    2. Loads and mounts all discovered skills as subcommands
    3. Starts the Typer CLI application to process user commands

    The function is typically called automatically when the package is installed
    and invoked via the 'agent' console script entry point.

    Example:
        $ agent --help
        $ agent skills list
        $ agent identity whoami
    """
    import sys

    # Import management CLIs
    from glorious_agents import identity_cli, skills_cli

    # Add management commands
    app.add_typer(skills_cli.app, name="skills")
    app.add_typer(identity_cli.app, name="identity")

    # Skip skill initialization for commands that don't need it
    skip_init_commands = {"version"}
    # Only skip if --help/-h is the first or only argument
    help_requested = len(sys.argv) <= 2 and any(arg in ["--help", "-h"] for arg in sys.argv[1:])
    should_skip = any(cmd in sys.argv for cmd in skip_init_commands) or help_requested

    if not should_skip:
        # Initialize and load skills
        init_app()

    # Run CLI
    app()


if __name__ == "__main__":
    main()

"""Main CLI entry point for glorious-agents."""

import logging

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
console = Console()


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
    from glorious_agents.core.daemon import run_daemon

    run_daemon(host, port)


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
    # Import management CLIs
    from glorious_agents import identity_cli, skills_cli

    # Add management commands
    app.add_typer(skills_cli.app, name="skills")
    app.add_typer(identity_cli.app, name="identity")

    # Initialize and load skills
    init_app()

    # Run CLI
    app()


if __name__ == "__main__":
    main()

"""CLI entry point for issue tracker."""

import os
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    """Main entry point for the issues CLI.

    Loads configuration from .env file if present, sets up environment,
    and runs the Typer application.
    """
    # Load .env file from current directory if it exists
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Configuration is handled by centralized glorious_agents.config
    # No environment variable setup needed here

    # Import and run the app
    from .app import app

    app()


if __name__ == "__main__":
    main()

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

    # Set default ISSUES_FOLDER if not specified
    if "ISSUES_FOLDER" not in os.environ:
        os.environ["ISSUES_FOLDER"] = "./.issues"

    # Update ISSUES_DB_PATH to use ISSUES_FOLDER
    issues_folder = os.environ["ISSUES_FOLDER"]
    if "ISSUES_DB_PATH" not in os.environ:
        os.environ["ISSUES_DB_PATH"] = f"{issues_folder}/issues.db"

    # Import and run the app
    from .app import app

    app()


if __name__ == "__main__":
    main()

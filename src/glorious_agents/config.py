"""Configuration management for glorious-agents.

This module provides centralized configuration with environment variable support.
All configuration values can be overridden via environment variables with the
GLORIOUS_ prefix.
"""

import os
from pathlib import Path


class Config:
    """Configuration settings for the glorious-agents framework."""

    def __init__(self) -> None:
        """Initialize configuration from environment variables."""
        # Database settings
        self.DB_SHARED_NAME: str = os.getenv("GLORIOUS_DB_SHARED_NAME", "glorious_shared.db")
        self.DB_MASTER_NAME: str = os.getenv("GLORIOUS_DB_MASTER_NAME", "master.db")

        # Daemon settings
        self.DAEMON_HOST: str = os.getenv("GLORIOUS_DAEMON_HOST", "127.0.0.1")
        self.DAEMON_PORT: int = int(os.getenv("GLORIOUS_DAEMON_PORT", "8765"))
        self.DAEMON_API_KEY: str | None = os.getenv("GLORIOUS_DAEMON_API_KEY")

        # Skills directory
        self.SKILLS_DIR: Path = Path(os.getenv("GLORIOUS_SKILLS_DIR", "skills"))

        # Agent data directory (uses ~/.glorious by default)
        self.AGENT_FOLDER: Path = Path(
            os.getenv("GLORIOUS_AGENT_FOLDER", str(Path.home() / ".glorious"))
        )

    def get_db_path(self, db_name: str) -> Path:
        """Get the full path to a database file."""
        return self.AGENT_FOLDER / db_name

    def get_shared_db_path(self) -> Path:
        """Get the path to the shared skills database."""
        return self.get_db_path(self.DB_SHARED_NAME)

    def get_master_db_path(self) -> Path:
        """Get the path to the master registry database."""
        return self.get_db_path(self.DB_MASTER_NAME)


# Singleton instance
config = Config()

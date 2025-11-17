"""Configuration management for glorious-agents.

This module provides centralized configuration with environment variable support.
All configuration values can be overridden via environment variables with the
GLORIOUS_ prefix or via .env file in project root.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def _find_project_root() -> Path:
    """Find the project root by looking for .git directory or .env file."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / ".env").exists():
            return parent
    return current


class Config:
    """Configuration settings for the glorious-agents framework."""

    def __init__(self) -> None:
        """Initialize configuration from environment variables and .env file."""
        # Load .env file from project root if it exists
        project_root = _find_project_root()
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        # Unified database name (single database for all data)
        self.DB_NAME: str = os.getenv("GLORIOUS_DB_NAME", "glorious.db")

        # Legacy database names (for migration)
        self.DB_SHARED_NAME: str = os.getenv("GLORIOUS_DB_SHARED_NAME", "glorious_shared.db")
        self.DB_MASTER_NAME: str = os.getenv("GLORIOUS_DB_MASTER_NAME", "master.db")

        # Daemon settings
        self.DAEMON_HOST: str = os.getenv("GLORIOUS_DAEMON_HOST", "127.0.0.1")
        self.DAEMON_PORT: int = int(os.getenv("GLORIOUS_DAEMON_PORT", "8765"))
        self.DAEMON_API_KEY: str | None = os.getenv("GLORIOUS_DAEMON_API_KEY")

        # Skills directory
        self.SKILLS_DIR: Path = Path(os.getenv("GLORIOUS_SKILLS_DIR", "skills"))

        # Agent data directory - PROJECT-SPECIFIC by default
        # Uses .agent/ in project root, can be overridden via DATA_FOLDER or GLORIOUS_DATA_FOLDER
        data_folder = os.getenv("DATA_FOLDER") or os.getenv("GLORIOUS_DATA_FOLDER")
        if data_folder:
            self.AGENT_FOLDER = Path(data_folder)
        else:
            self.AGENT_FOLDER = project_root / ".agent"

    def get_db_path(self, db_name: str | None = None) -> Path:
        """Get the full path to a database file.

        Args:
            db_name: Optional database name. If None, uses the unified DB_NAME.
        """
        if db_name is None:
            db_name = self.DB_NAME
        return self.AGENT_FOLDER / db_name

    def get_unified_db_path(self) -> Path:
        """Get the path to the unified database."""
        return self.get_db_path(self.DB_NAME)

    def get_shared_db_path(self) -> Path:
        """Get the path to the shared skills database (legacy)."""
        return self.get_db_path(self.DB_SHARED_NAME)

    def get_master_db_path(self) -> Path:
        """Get the path to the master registry database (legacy)."""
        return self.get_db_path(self.DB_MASTER_NAME)


# Singleton instance
config = Config()

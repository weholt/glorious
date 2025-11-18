"""Configuration management for glorious-agents.

This module provides centralized configuration with environment variable support.
All configuration values can be overridden via environment variables with the
GLORIOUS_ prefix or via .env file in project root.
"""

import os
import threading
from pathlib import Path
from typing import Optional

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

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """
        Initialize configuration from environment variables and an optional .env file.
        
        If `env_file` is None, the project root is located and `<project_root>/.env` is used when present.
        When a .env file exists at the chosen path, its values are loaded into the environment before reading
        configuration values. The constructor then reads environment variables to populate attributes such
        as `DB_NAME`, `DB_SHARED_NAME`, `DB_MASTER_NAME`, `DAEMON_HOST`, `DAEMON_PORT`, `DAEMON_API_KEY`,
        `SKILLS_DIR`, and `DATA_FOLDER`. If `DATA_FOLDER` is not set in the environment, it defaults to
        `<project_root>/.agent`.
        
        Parameters:
            env_file (Optional[Path]): Path to a .env file to load before reading environment variables.
                If omitted, a .env file in the project root will be used if it exists.
        """
        # Load .env file from project root if it exists
        if env_file is None:
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
        # Uses .agent/ in project root, can be overridden via DATA_FOLDER
        data_folder = os.getenv("DATA_FOLDER")
        if data_folder:
            self.DATA_FOLDER = Path(data_folder)
        else:
            self.DATA_FOLDER = project_root / ".agent"

    def get_db_path(self, db_name: str | None = None) -> Path:
        """Get the full path to a database file.

        Args:
            db_name: Optional database name. If None, uses the unified DB_NAME.
        """
        if db_name is None:
            db_name = self.DB_NAME
        return self.DATA_FOLDER / db_name

    def get_unified_db_path(self) -> Path:
        """Get the path to the unified database."""
        return self.get_db_path(self.DB_NAME)

    def get_shared_db_path(self) -> Path:
        """Get the path to the shared skills database (legacy)."""
        return self.get_db_path(self.DB_SHARED_NAME)

    def get_master_db_path(self) -> Path:
        """
        Return the path to the legacy master registry database file.
        
        Returns:
            Path: Full filesystem path to the master registry database.
        """
        return self.get_db_path(self.DB_MASTER_NAME)


# Default singleton for backward compatibility
# New code should use get_config() or create Config() instances
_default_config: Optional[Config] = None
_config_lock = threading.Lock()


def get_config() -> Config:
    """
    Retrieve the module-level default Config instance used across the application.
    
    Tests should instantiate Config() directly to obtain isolated configuration instances instead of using the shared default.
    
    Returns:
        config (Config): The shared default configuration instance.
    """
    global _default_config
    if _default_config is None:
        with _config_lock:
            if _default_config is None:
                _default_config = Config()
    return _default_config


def reset_config() -> None:
    """Reset the default config (useful for testing)."""
    global _default_config
    with _config_lock:
        _default_config = None


# Backward compatibility: module-level 'config' attribute
# This allows existing code like `from glorious_agents.config import config` to work
# But encourages new code to use get_config() or dependency injection
config = get_config()
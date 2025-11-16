"""Centralized configuration management with Pydantic settings.

Provides type-safe configuration from environment variables and .env files.
Follows Twelve-Factor App principles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class IssueTrackerSettings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables with ISSUES_ prefix.
    Example: ISSUES_FOLDER=".myissues" overrides the folder setting.
    """

    model_config = SettingsConfigDict(
        env_prefix="ISSUES_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database configuration
    folder: str = Field(
        default="./.issues",
        description="Root folder for issue tracker data",
    )
    db_path: str | None = Field(
        default=None,
        description="Database path (default: {folder}/issues.db)",
    )
    db_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging",
    )

    # Daemon configuration
    daemon_mode: Literal["poll", "events"] = Field(
        default="poll",
        description="Daemon mode: poll (5s interval) or events (inotify)",
    )
    auto_start_daemon: bool = Field(
        default=True,
        description="Auto-start daemon on first CLI command",
    )
    sync_enabled: bool = Field(
        default=True,
        description="Enable background synchronization",
    )
    sync_interval: int = Field(
        default=5,
        ge=1,
        le=3600,
        description="Sync interval in seconds (1-3600)",
    )

    # Git integration
    git_enabled: bool = Field(
        default=False,
        description="Enable git integration for sync",
    )
    git_remote: str = Field(
        default="origin",
        description="Git remote name for sync",
    )
    git_branch: str = Field(
        default="main",
        description="Git branch for sync",
    )

    # Issue configuration
    issue_prefix: str = Field(
        default="issue",
        description="Prefix for generated issue IDs",
    )
    export_path: str | None = Field(
        default=None,
        description="JSONL export path (default: {folder}/issues.jsonl)",
    )

    # Performance tuning
    db_pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Database connection pool size",
    )
    db_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Database lock timeout in seconds",
    )

    # Feature flags
    no_daemon: bool = Field(
        default=False,
        description="Disable daemon entirely (useful for CI/testing)",
    )
    watcher_fallback: bool = Field(
        default=True,
        description="Fallback to polling if inotify unavailable",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    daemon_log_path: str | None = Field(
        default=None,
        description="Daemon log file path (default: {folder}/daemon.log)",
    )

    def get_db_path(self) -> Path:
        """Get resolved database path."""
        if self.db_path:
            return Path(self.db_path).resolve()
        return Path(self.folder).resolve() / "issues.db"

    def get_export_path(self) -> Path:
        """Get resolved export path."""
        if self.export_path:
            return Path(self.export_path).resolve()
        return Path(self.folder).resolve() / "issues.jsonl"

    def get_daemon_log_path(self) -> Path:
        """Get resolved daemon log path."""
        if self.daemon_log_path:
            return Path(self.daemon_log_path).resolve()
        return Path(self.folder).resolve() / "daemon.log"

    def get_socket_path(self) -> Path:
        """Get socket path for IPC."""
        import sys

        folder = Path(self.folder).resolve()
        if sys.platform == "win32":
            return folder / "issues.pipe"
        return folder / "issues.sock"

    def get_pid_path(self) -> Path:
        """Get PID file path."""
        return Path(self.folder).resolve() / "daemon.pid"


_settings: IssueTrackerSettings | None = None


def get_settings() -> IssueTrackerSettings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = IssueTrackerSettings()
    return _settings


def reset_settings() -> None:
    """Reset settings instance (useful for testing)."""
    global _settings
    _settings = None

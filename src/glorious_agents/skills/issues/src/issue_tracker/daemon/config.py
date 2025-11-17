"""Daemon configuration management."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DaemonConfig:
    """Daemon configuration."""

    database_path: str
    issue_prefix: str
    daemon_mode: str  # "poll" or "events"
    auto_start_daemon: bool
    sync_enabled: bool
    sync_interval_seconds: int
    export_path: str
    git_integration: bool
    workspace_path: Path

    @classmethod
    def default(cls, workspace_path: Path) -> "DaemonConfig":
        """Create default configuration."""
        from glorious_agents.config import config as glorious_config

        data_dir = glorious_config.DATA_FOLDER
        return cls(
            database_path=str(glorious_config.get_unified_db_path()),
            issue_prefix="issue",
            daemon_mode=os.environ.get("ISSUES_DAEMON_MODE", "poll"),
            auto_start_daemon=os.environ.get("ISSUES_AUTO_START_DAEMON", "true").lower() == "true",
            sync_enabled=True,
            sync_interval_seconds=int(os.environ.get("ISSUES_SYNC_INTERVAL", "5")),
            export_path=str(data_dir / "issues.jsonl"),
            git_integration=os.environ.get("ISSUES_GIT_ENABLED", "false").lower() == "true",
            workspace_path=workspace_path,
        )

    @classmethod
    def load(cls, workspace_path: Path) -> "DaemonConfig":
        """Load configuration from file or create default."""
        from glorious_agents.config import config as glorious_config

        data_dir = glorious_config.DATA_FOLDER
        config_path = data_dir / "issues_config.json"

        # Also check legacy location
        legacy_config_path = workspace_path / ".issues" / "config.json"
        if legacy_config_path.exists() and not config_path.exists():
            config_path = legacy_config_path

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
                return cls(
                    database_path=data.get("database_path", str(glorious_config.get_unified_db_path())),
                    issue_prefix=data.get("issue_prefix", "issue"),
                    daemon_mode=os.environ.get("ISSUES_DAEMON_MODE", data.get("daemon_mode", "poll")),
                    auto_start_daemon=os.environ.get(
                        "ISSUES_AUTO_START_DAEMON", str(data.get("auto_start_daemon", True))
                    ).lower()
                    == "true",
                    sync_enabled=data.get("sync_enabled", True),
                    sync_interval_seconds=int(
                        os.environ.get("ISSUES_SYNC_INTERVAL", str(data.get("sync_interval_seconds", 5)))
                    ),
                    export_path=data.get("export_path", str(data_dir / "issues.jsonl")),
                    git_integration=os.environ.get(
                        "ISSUES_GIT_ENABLED", str(data.get("git_integration", False))
                    ).lower()
                    == "true",
                    workspace_path=workspace_path,
                )
        return cls.default(workspace_path)

    def save(self, workspace_path: Path) -> None:
        """Save configuration to file."""
        from glorious_agents.config import config as glorious_config

        data_dir = glorious_config.DATA_FOLDER
        config_path = data_dir / "issues_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "database_path": self.database_path,
            "issue_prefix": self.issue_prefix,
            "daemon_mode": self.daemon_mode,
            "auto_start_daemon": self.auto_start_daemon,
            "sync_enabled": self.sync_enabled,
            "sync_interval_seconds": self.sync_interval_seconds,
            "export_path": self.export_path,
            "git_integration": self.git_integration,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_socket_path(self) -> Path:
        """Get socket path for IPC."""
        import sys

        from glorious_agents.config import config as glorious_config

        data_dir = glorious_config.DATA_FOLDER
        if sys.platform == "win32":
            return data_dir / "issues.pipe"
        return data_dir / "issues.sock"

    def get_pid_path(self) -> Path:
        """Get PID file path."""
        from glorious_agents.config import config as glorious_config

        return glorious_config.DATA_FOLDER / "daemon.pid"

    def get_log_path(self) -> Path:
        """Get daemon log file path."""
        from glorious_agents.config import config as glorious_config

        return glorious_config.DATA_FOLDER / "daemon.log"

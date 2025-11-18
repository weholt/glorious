"""Configuration management for daemon services."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass
class DaemonConfig:
    """Standard configuration for daemon services.

    Provides common configuration options that all daemons need
    with sensible defaults and environment variable overrides.
    """

    workspace_path: Path
    daemon_mode: Literal["poll", "events"] = "poll"
    auto_start: bool = True
    log_level: str = "INFO"

    def get_pid_path(self) -> Path:
        """Get path to PID file.

        Returns:
            Path to daemon.pid in workspace directory
        """
        from glorious_agents.config import config as glorious_config

        return glorious_config.DATA_FOLDER / "daemon.pid"

    def get_log_path(self) -> Path:
        """Get path to log file.

        Returns:
            Path to daemon.log in workspace directory
        """
        from glorious_agents.config import config as glorious_config

        return glorious_config.DATA_FOLDER / "daemon.log"

    def get_socket_path(self) -> Path:
        """Get path to IPC socket/port file.

        Returns:
            Path to daemon.port file (contains HTTP port number)
        """
        from glorious_agents.config import config as glorious_config

        return glorious_config.DATA_FOLDER / "daemon.port"

    def get_config_path(self) -> Path:
        """Get path to config file.

        Returns:
            Path to daemon_config.json
        """
        from glorious_agents.config import config as glorious_config

        return glorious_config.DATA_FOLDER / "daemon_config.json"

    @classmethod
    def default(cls, workspace_path: Path) -> "DaemonConfig":
        """Create default configuration.

        Args:
            workspace_path: Workspace directory

        Returns:
            DaemonConfig with default values
        """
        return cls(
            workspace_path=workspace_path,
            daemon_mode=os.environ.get("DAEMON_MODE", "poll"),  # type: ignore[arg-type]
            auto_start=os.environ.get("AUTO_START_DAEMON", "true").lower() == "true",
            log_level=os.environ.get("DAEMON_LOG_LEVEL", "INFO"),
        )

    @classmethod
    def load(cls, workspace_path: Path) -> "DaemonConfig":
        """Load configuration from file or create default.

        Args:
            workspace_path: Workspace directory

        Returns:
            Loaded or default configuration
        """
        config = cls.default(workspace_path)
        config_path = config.get_config_path()

        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())

                # Override with file values (environment still takes precedence)
                config.daemon_mode = os.environ.get(  # type: ignore[assignment]
                    "DAEMON_MODE", data.get("daemon_mode", "poll")
                )
                config.auto_start = (
                    os.environ.get("AUTO_START_DAEMON", str(data.get("auto_start", True))).lower()
                    == "true"
                )
                config.log_level = os.environ.get("DAEMON_LOG_LEVEL", data.get("log_level", "INFO"))
            except (json.JSONDecodeError, OSError) as e:
                logger = __import__("logging").getLogger(__name__)
                logger.warning(f"Failed to load config from {config_path}: {e}")

        return config

    def save(self) -> None:
        """Save configuration to file."""
        config_path = self.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "daemon_mode": self.daemon_mode,
            "auto_start": self.auto_start,
            "log_level": self.log_level,
        }

        config_path.write_text(json.dumps(data, indent=2))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Configuration as dictionary
        """
        from typing import Any

        return {
            "workspace_path": str(self.workspace_path),
            "daemon_mode": self.daemon_mode,
            "auto_start": self.auto_start,
            "log_level": self.log_level,
            "pid_path": str(self.get_pid_path()),
            "log_path": str(self.get_log_path()),
            "socket_path": str(self.get_socket_path()),
        }

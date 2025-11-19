"""Daemon registry for tracking running skill daemons."""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DaemonInfo:
    """Information about a registered daemon.

    Attributes:
        skill: Skill name
        pid: Process ID
        workspace: Workspace path
        start_time: When daemon was started
        status: Current status (running, stopped, error)
        health: Health check information
    """

    skill: str
    pid: int
    workspace: Path
    start_time: datetime
    status: str = "running"
    health: dict[str, Any] | None = None


class DaemonRegistry:
    """Registry of all running skill daemons.

    Provides centralized tracking and monitoring of background daemons
    across all skills. Each daemon can register itself on startup and
    unregister on shutdown.
    """

    def __init__(self) -> None:
        """Initialize daemon registry."""
        self._daemons: dict[str, DaemonInfo] = {}

    def register(
        self,
        skill: str,
        pid: int,
        workspace: Path,
        start_time: datetime | None = None,
    ) -> None:
        """Register a daemon.

        Args:
            skill: Skill name
            pid: Process ID
            workspace: Workspace path
            start_time: Start time (defaults to now)
        """
        if start_time is None:
            start_time = datetime.now()

        daemon_info = DaemonInfo(
            skill=skill,
            pid=pid,
            workspace=workspace,
            start_time=start_time,
            status="running",
        )

        self._daemons[skill] = daemon_info
        logger.info(f"Registered daemon for skill '{skill}' (PID: {pid})")

    def unregister(self, skill: str) -> None:
        """Unregister a daemon.

        Args:
            skill: Skill name
        """
        if skill in self._daemons:
            daemon_info = self._daemons.pop(skill)
            logger.info(f"Unregistered daemon for skill '{skill}' (PID: {daemon_info.pid})")

    def update_health(self, skill: str, health: dict[str, Any]) -> None:
        """Update health information for a daemon.

        Args:
            skill: Skill name
            health: Health check results
        """
        if skill in self._daemons:
            self._daemons[skill].health = health
            self._daemons[skill].status = "running" if health.get("healthy", False) else "error"

    def get(self, skill: str) -> DaemonInfo | None:
        """Get daemon information.

        Args:
            skill: Skill name

        Returns:
            DaemonInfo if found, None otherwise
        """
        return self._daemons.get(skill)

    def list_all(self) -> list[DaemonInfo]:
        """List all registered daemons.

        Returns:
            List of daemon information
        """
        return list(self._daemons.values())

    def get_health(self) -> dict[str, Any]:
        """Get health status of all daemons.

        Returns:
            Dictionary mapping skill names to health information
        """
        return {
            skill: {
                "pid": info.pid,
                "workspace": str(info.workspace),
                "uptime_seconds": int((datetime.now() - info.start_time).total_seconds()),
                "status": info.status,
                "health": info.health,
            }
            for skill, info in self._daemons.items()
        }

    def is_running(self, skill: str) -> bool:
        """Check if a daemon is registered and running.

        Args:
            skill: Skill name

        Returns:
            True if daemon is registered and status is running
        """
        if skill not in self._daemons:
            return False

        return self._daemons[skill].status == "running"


# Global registry instance
_registry: DaemonRegistry | None = None


def get_registry() -> DaemonRegistry:
    """Get the global daemon registry.

    Returns:
        Global DaemonRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = DaemonRegistry()
    return _registry

"""Daemon service for background operations."""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from glorious_agents.core.daemon import BaseDaemonService, PeriodicTask

from issue_tracker.daemon.config import DaemonConfig
from issue_tracker.daemon.sync_engine import SyncEngine

__all__ = ["IssuesDaemonService"]

logger = logging.getLogger(__name__)


class IssuesDaemonService(BaseDaemonService):
    """Issues-specific daemon extending core infrastructure.

    Provides background sync for issue tracking with Git integration.
    """

    def __init__(self, config: DaemonConfig) -> None:
        """Initialize issues daemon service.

        Args:
            config: Issues daemon configuration
        """
        # Initialize base daemon with core config
        from glorious_agents.core.daemon import DaemonConfig as CoreDaemonConfig

        core_config = CoreDaemonConfig(
            workspace_path=config.workspace_path,
            daemon_mode=config.daemon_mode,  # type: ignore[arg-type]
            auto_start=config.auto_start_daemon,
            log_level="INFO",
        )
        super().__init__(core_config)

        # Store issues-specific config
        self.issues_config = config

        # Initialize sync engine
        self.sync_engine = SyncEngine(
            workspace_path=config.workspace_path,
            export_path=Path(config.export_path),
            git_enabled=config.git_integration,
        )

        # Database engine (reused across syncs to prevent memory leak)
        self._engine = None

        # Periodic sync task
        self._sync_task: PeriodicTask | None = None

    async def on_startup(self) -> None:
        """Initialize issues-specific resources.

        Starts the periodic sync task if enabled.
        """
        logger.info("Starting issues daemon")

        # Start periodic sync if enabled
        if self.issues_config.sync_enabled:
            self._sync_task = PeriodicTask(
                interval=self.issues_config.sync_interval_seconds, callback=self._perform_sync, name="issues_sync"
            )
            await self._sync_task.start()
            logger.info(f"Sync task started (interval: {self.issues_config.sync_interval_seconds}s)")

    async def on_shutdown(self) -> None:
        """Cleanup issues-specific resources.

        Stops the sync task and disposes the database engine.
        """
        logger.info("Shutting down issues daemon")

        # Stop sync task
        if self._sync_task:
            await self._sync_task.stop()
            self._sync_task = None

        # CRITICAL: Dispose database engine to prevent memory leak
        if self._engine:
            self._engine.dispose()
            self._engine = None

        logger.info("Issues daemon shutdown complete")

    def get_health_info(self) -> dict[str, Any]:
        """Return issues-specific health information."""
        return {
            "sync_enabled": self.issues_config.sync_enabled,
            "sync_interval": self.issues_config.sync_interval_seconds,
            "git_enabled": self.issues_config.git_integration,
            "last_sync": getattr(self.sync_engine, "last_sync", None),
        }

    def handle_command(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle issues-specific IPC commands.

        Supports:
        - sync: Trigger immediate sync

        Args:
            request: Request dictionary

        Returns:
            Response dictionary
        """
        method = request.get("method", "")

        if method == "sync":
            return self._trigger_sync()

        # Unknown command
        return super().handle_command(request)

    def _trigger_sync(self) -> dict[str, Any]:
        """Trigger immediate sync."""
        try:
            issues = self._get_issues_from_db()
            stats = self.sync_engine.sync(issues)
            return {"status": "success", "stats": stats}
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _perform_sync(self) -> None:
        """Perform sync operation (called by PeriodicTask)."""
        try:
            issues = self._get_issues_from_db()
            stats = self.sync_engine.sync(issues)
            logger.info(f"Sync complete: {stats}")
        except Exception as e:
            logger.error(f"Error in sync: {e}", exc_info=True)

    def _get_engine(self):
        """Get or create a reusable database engine.

        CRITICAL: Reuses the same engine across all sync operations.
        Creating a new engine every few seconds causes massive memory leak.

        Returns:
            SQLAlchemy engine instance
        """
        if self._engine is None:
            from sqlmodel import create_engine

            self._engine = create_engine(f"sqlite:///{self.issues_config.database_path}")
        return self._engine

    def _get_issues_from_db(self) -> list[dict[str, Any]]:
        """Get all issues from database.

        Returns:
            List of issue dictionaries
        """
        try:
            from sqlmodel import Session, select

            from issue_tracker.adapters.db.models import IssueModel  # type: ignore[attr-defined]

            engine = self._get_engine()
            with Session(engine) as session:
                issues = session.exec(select(IssueModel)).all()
                return [
                    {
                        "id": issue.id,
                        "title": issue.title,
                        "description": issue.description or "",
                        "status": issue.status,
                        "priority": issue.priority,
                        "type": issue.type,
                        "assignee": issue.assignee or "",
                        "labels": [],
                        "epic_id": issue.epic_id,
                        "created_at": issue.created_at.isoformat() if issue.created_at else None,
                        "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                        "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    }
                    for issue in issues
                ]
        except Exception as e:
            logger.error(f"Failed to get issues from database: {e}")
            return []


def _kill_existing_daemon(workspace_path: Path) -> None:
    """Kill existing daemon for this workspace if running.

    Args:
        workspace_path: Workspace directory
    """
    from glorious_agents.core.daemon import PIDFileManager

    config = DaemonConfig.load(workspace_path)
    pid_manager = PIDFileManager(config.get_pid_path())

    if pid_manager.is_running():
        logger.info(f"Killing existing daemon with PID {pid_manager.read()}")
        pid_manager.kill_existing()


def _cleanup_zombie_processes() -> int:
    """Kill orphaned daemon processes across all platforms.

    Only kills processes that are our daemons (running issue_tracker.daemon.service).
    Uses psutil for OS-agnostic process management.

    Returns:
        Number of processes killed
    """
    import psutil

    killed = 0

    try:
        # Iterate through all processes
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline")
                if cmdline and any("issue_tracker.daemon.service" in str(arg) for arg in cmdline):
                    logger.info(f"Killing orphaned daemon process {proc.pid}")
                    proc.terminate()

                    # Wait briefly for graceful shutdown
                    try:
                        proc.wait(timeout=1)
                    except psutil.TimeoutExpired:
                        # Force kill if it doesn't terminate
                        proc.kill()

                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process ended, we don't have permission, or it's already a zombie
                pass

    except Exception as e:
        logger.warning(f"Failed to cleanup zombie processes: {e}")

    return killed


def start_daemon(workspace_path: Path, detach: bool = True) -> int:
    """Start daemon process.

    This function ensures only ONE daemon runs per workspace (Highlander principle).
    It will:
    1. Check if daemon auto-start is disabled via environment variable
    2. Kill any existing daemon for this workspace
    3. Clean up orphaned zombie processes
    4. Start a fresh daemon

    Args:
        workspace_path: Workspace directory
        detach: Whether to detach from parent process

    Returns:
        Daemon PID

    Raises:
        RuntimeError: If ISSUES_AUTO_START_DAEMON is set to 'false'
    """
    # CRITICAL: Respect ISSUES_AUTO_START_DAEMON environment variable
    if os.environ.get("ISSUES_AUTO_START_DAEMON", "true").lower() == "false":
        raise RuntimeError("Daemon auto-start is disabled (ISSUES_AUTO_START_DAEMON='false')")

    config = DaemonConfig.load(workspace_path)

    # CRITICAL: Kill existing daemon for this workspace first
    _kill_existing_daemon(workspace_path)

    # Clean up any orphaned zombie processes
    zombies_killed = _cleanup_zombie_processes()
    if zombies_killed > 0:
        logger.info(f"Cleaned up {zombies_killed} orphaned daemon processes")

    # Small delay to ensure processes are fully terminated
    if zombies_killed > 0:
        time.sleep(0.5)

    pid_path = config.get_pid_path()

    if detach:
        if sys.platform == "win32":
            # Windows: spawn detached process
            import subprocess

            # Use pythonw.exe (windowless Python) on Windows to prevent console window
            python_exe = sys.executable
            if python_exe.endswith("python.exe"):
                pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
                if Path(pythonw_exe).exists():
                    python_exe = pythonw_exe

            # Windows process creation flags - constants match Windows API
            DETACHED_PROCESS = 0x00000008  # noqa: N806
            CREATE_NEW_PROCESS_GROUP = 0x00000200  # noqa: N806
            CREATE_NO_WINDOW = 0x08000000  # noqa: N806

            # STARTUPINFO flags - constants match Windows API
            STARTF_USESHOWWINDOW = 0x00000001  # noqa: N806
            SW_HIDE = 0  # noqa: N806

            # Create STARTUPINFO to hide window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE

            # Run daemon as subprocess with all flags
            # S603: subprocess call with controlled executable path (validated above)
            process = subprocess.Popen(  # noqa: S603
                [python_exe, "-m", "issue_tracker.daemon.service", str(workspace_path)],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )

            # Write PID file
            pid_path.write_text(str(process.pid))
            return process.pid
        else:
            # Unix: fork to background
            pid = os.fork()
            if pid > 0:
                # Parent process
                return pid

            # Child process - become session leader
            os.setsid()

            # Second fork to prevent zombie
            pid = os.fork()
            if pid > 0:
                sys.exit(0)

    # Run daemon (non-detached or in forked child)
    daemon = IssuesDaemonService(config)

    # Write PID file before running
    pid_path.write_text(str(os.getpid()))

    try:
        asyncio.run(daemon.run())
    finally:
        # Clean up PID file
        if pid_path.exists():
            pid_path.unlink()

    return os.getpid()


def stop_daemon(workspace_path: Path) -> bool:
    """Stop daemon for workspace.

    Args:
        workspace_path: Workspace directory

    Returns:
        True if daemon was stopped, False if no daemon was running
    """
    config = DaemonConfig.load(workspace_path)
    pid_path = config.get_pid_path()

    if not pid_path.exists():
        return False

    _kill_existing_daemon(workspace_path)
    return True


def is_daemon_running(workspace_path: Path) -> bool:
    """Check if daemon is running for workspace.

    Args:
        workspace_path: Workspace directory

    Returns:
        True if daemon is running
    """
    from glorious_agents.core.daemon import PIDFileManager

    config = DaemonConfig.load(workspace_path)
    pid_manager = PIDFileManager(config.get_pid_path())
    return pid_manager.is_running()


if __name__ == "__main__":
    """Run daemon as module for Windows detached process."""
    if len(sys.argv) < 2:
        print("Usage: python -m issue_tracker.daemon.service <workspace_path>")
        sys.exit(1)

    workspace_path = Path(sys.argv[1])
    config = DaemonConfig.load(workspace_path)

    # Run daemon directly (already detached by parent)
    daemon = IssuesDaemonService(config)

    # Write PID file
    pid_path = config.get_pid_path()
    pid_path.write_text(str(os.getpid()))

    try:
        asyncio.run(daemon.run())
    finally:
        # Clean up PID file
        if pid_path.exists():
            pid_path.unlink()

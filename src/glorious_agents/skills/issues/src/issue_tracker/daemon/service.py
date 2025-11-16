"""Daemon service for background operations."""

import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from issue_tracker.daemon.config import DaemonConfig
from issue_tracker.daemon.ipc_server import IPCServer
from issue_tracker.daemon.sync_engine import SyncEngine

logger = logging.getLogger(__name__)


class DaemonService:
    """Background daemon service for continuous sync."""

    def __init__(self, config: DaemonConfig):
        """Initialize daemon service.

        Args:
            config: Daemon configuration
        """
        self.config = config
        self.workspace_path = config.workspace_path
        self.running = False
        self.start_time = datetime.now()
        self.sync_engine = SyncEngine(
            workspace_path=config.workspace_path,
            export_path=Path(config.export_path),
            git_enabled=config.git_integration,
        )
        self.ipc_server = IPCServer(config.get_socket_path(), self._handle_request)
        self._sync_task: asyncio.Task[None] | None = None
        self._engine = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up daemon logging."""
        log_path = self.config.get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure logging
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)

    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle IPC request.

        Args:
            request: Request data

        Returns:
            Response data
        """
        method = request.get("method", "")

        if method == "health":
            return self._health_check()
        elif method == "stop":
            # Schedule shutdown in the main event loop (we're in executor thread)
            if self._loop:
                self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self._shutdown()))
            return {"status": "stopping"}
        elif method == "sync":
            return self._trigger_sync()
        elif method == "status":
            return self._get_status()
        else:
            return {"error": f"Unknown method: {method}"}

    def _health_check(self) -> dict[str, Any]:
        """Perform health check."""
        return {
            "healthy": True,
            "uptime_seconds": int((datetime.now() - self.start_time).total_seconds()),
            "workspace": str(self.workspace_path),
            "pid": os.getpid(),
            "version": "1.0.0",
        }

    def _get_status(self) -> dict[str, Any]:
        """Get daemon status."""
        return {
            "running": self.running,
            "workspace": str(self.workspace_path),
            "pid": os.getpid(),
            "uptime_seconds": int((datetime.now() - self.start_time).total_seconds()),
            "sync_enabled": self.config.sync_enabled,
            "sync_interval": self.config.sync_interval_seconds,
            "daemon_mode": self.config.daemon_mode,
        }

    def _trigger_sync(self) -> dict[str, Any]:
        """Trigger immediate sync."""
        try:
            # Get issues from database (simplified for now)
            issues = self._get_issues_from_db()
            stats = self.sync_engine.sync(issues)
            return {"status": "success", "stats": stats}
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {"status": "error", "error": str(e)}

    def _get_engine(self):
        """Get or create a reusable database engine.

        CRITICAL: Reuses the same engine across all sync operations.
        Creating a new engine every few seconds causes massive memory leak.

        Returns:
            SQLAlchemy engine instance
        """
        if self._engine is None:
            from sqlmodel import create_engine

            self._engine = create_engine(f"sqlite:///{self.config.database_path}")
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

    async def _sync_loop(self) -> None:
        """Main sync loop."""
        logger.info(
            f"Starting sync loop (mode: {self.config.daemon_mode}, interval: {self.config.sync_interval_seconds}s)"
        )

        while self.running:
            try:
                if self.config.sync_enabled:
                    issues = self._get_issues_from_db()
                    stats = self.sync_engine.sync(issues)
                    logger.info(f"Sync complete: {stats}")

                await asyncio.sleep(self.config.sync_interval_seconds)

            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                await asyncio.sleep(self.config.sync_interval_seconds)

    def _write_pid_file(self) -> None:
        """Write PID file."""
        pid_path = self.config.get_pid_path()
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(os.getpid()))
        logger.info(f"PID {os.getpid()} written to {pid_path}")

    def _remove_pid_file(self) -> None:
        """Remove PID file."""
        pid_path = self.config.get_pid_path()
        if pid_path.exists():
            pid_path.unlink()
            logger.info(f"Removed PID file {pid_path}")

    async def start(self) -> None:
        """Start the daemon service."""
        logger.info(f"Starting daemon for workspace: {self.workspace_path}")
        self.running = True
        self._loop = asyncio.get_running_loop()
        self._write_pid_file()

        # Start IPC server
        await self.ipc_server.start()

        # Start sync loop
        if self.config.sync_enabled:
            self._sync_task = asyncio.create_task(self._sync_loop())

        logger.info("Daemon started successfully")

    async def _shutdown(self) -> None:
        """Shutdown the daemon."""
        logger.info("Shutting down daemon...")
        self.running = False

        # Stop sync loop
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        # Stop IPC server
        await self.ipc_server.stop()

        # CRITICAL: Dispose database engine to prevent memory leak
        if self._engine:
            self._engine.dispose()
            self._engine = None

        # Clear event loop reference
        self._loop = None

        # Cleanup
        self._remove_pid_file()
        logger.info("Daemon stopped")

    async def run(self) -> None:
        """Run the daemon (blocking)."""
        await self.start()

        # Setup signal handlers
        def signal_handler(sig: Any, frame: Any) -> None:
            """Handle shutdown signals."""
            logger.info(f"Received signal {sig}")
            asyncio.create_task(self._shutdown())

        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

        # Keep running until shutdown
        while self.running:
            await asyncio.sleep(1)


def _kill_existing_daemon(workspace_path: Path) -> None:
    """Kill existing daemon for this workspace if running.

    Args:
        workspace_path: Workspace directory
    """
    config = DaemonConfig.load(workspace_path)
    pid_path = config.get_pid_path()

    if not pid_path.exists():
        return

    try:
        pid = int(pid_path.read_text())

        # Use psutil for cross-platform process management
        import psutil  # type: ignore[import-untyped]

        try:
            process = psutil.Process(pid)
            logger.info(f"Killing existing daemon with PID {pid}")
            process.terminate()

            # Wait briefly for graceful shutdown
            try:
                process.wait(timeout=2)
            except psutil.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                process.wait(timeout=1)
        except psutil.NoSuchProcess:
            pass  # Process doesn't exist

    except (ValueError, FileNotFoundError):
        pass  # Invalid PID file

    # Always remove PID file
    if pid_path.exists():
        pid_path.unlink()


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
    import os

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
    daemon = DaemonService(config)

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
    config = DaemonConfig.load(workspace_path)
    pid_path = config.get_pid_path()

    if not pid_path.exists():
        return False

    try:
        pid = int(pid_path.read_text())
        if sys.platform == "win32":
            import subprocess

            result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, check=False)  # noqa: S603, S607
            return str(pid) in result.stdout
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


if __name__ == "__main__":
    """Run daemon as module for Windows detached process."""
    if len(sys.argv) < 2:
        print("Usage: python -m issue_tracker.daemon.service <workspace_path>")
        sys.exit(1)

    workspace_path = Path(sys.argv[1])
    config = DaemonConfig.load(workspace_path)

    # Run daemon directly (already detached by parent)
    daemon = DaemonService(config)

    # Write PID file
    pid_path = config.get_pid_path()
    pid_path.write_text(str(os.getpid()))

    try:
        asyncio.run(daemon.run())
    finally:
        # Clean up PID file
        if pid_path.exists():
            pid_path.unlink()

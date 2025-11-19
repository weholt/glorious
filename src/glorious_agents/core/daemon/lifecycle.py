"""Daemon lifecycle management functions.

Provides high-level functions for starting, stopping, and checking
daemon status across all daemon types.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from glorious_agents.core.daemon.base import BaseDaemonService
from glorious_agents.core.daemon.config import DaemonConfig
from glorious_agents.core.daemon.pid import PIDFileManager

logger = logging.getLogger(__name__)


def start_daemon(
    workspace_path: Path,
    daemon_class: type[BaseDaemonService],
    config: DaemonConfig | None = None,
    detach: bool = True,
) -> int:
    """Start a daemon process.

    Args:
        workspace_path: Workspace directory
        daemon_class: Daemon service class to instantiate
        config: Daemon configuration (loads default if None)
        detach: Whether to detach from parent process

    Returns:
        Daemon PID

    Raises:
        RuntimeError: If auto-start is disabled
    """
    # Check if auto-start is disabled
    if os.environ.get("AUTO_START_DAEMON", "true").lower() == "false":
        raise RuntimeError("Daemon auto-start is disabled (AUTO_START_DAEMON='false')")

    # Load or use provided config
    if config is None:
        config = DaemonConfig.load(workspace_path)

    # Kill existing daemon for this workspace
    pid_manager = PIDFileManager(config.get_pid_path())
    if pid_manager.is_running():
        logger.info("Killing existing daemon")
        pid_manager.kill_existing()

    # Clean up stale PID files
    pid_manager.cleanup_stale()

    if detach:
        if sys.platform == "win32":
            # Windows: spawn detached subprocess
            return _start_windows_daemon(workspace_path, daemon_class, config)
        else:
            # Unix: fork to background
            return _start_unix_daemon(workspace_path, daemon_class, config)
    else:
        # Run in foreground (for testing)
        daemon = daemon_class(config)
        pid_manager.write()

        try:
            asyncio.run(daemon.run())
        finally:
            pid_manager.remove()

        return os.getpid()


def _start_windows_daemon(
    workspace_path: Path,
    daemon_class: type[BaseDaemonService],
    config: DaemonConfig,
) -> int:
    """Start daemon on Windows as detached process.

    Args:
        workspace_path: Workspace directory
        daemon_class: Daemon service class
        config: Daemon configuration

    Returns:
        Process ID
    """
    import subprocess

    # Use pythonw.exe to avoid console window
    python_exe = sys.executable
    if python_exe.endswith("python.exe"):
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if Path(pythonw_exe).exists():
            python_exe = pythonw_exe

    # Windows process creation flags
    DETACHED_PROCESS = 0x00000008  # noqa: N806
    CREATE_NEW_PROCESS_GROUP = 0x00000200  # noqa: N806
    CREATE_NO_WINDOW = 0x08000000  # noqa: N806

    # Get module and class info for subprocess
    module = daemon_class.__module__
    class_name = daemon_class.__name__

    # Create startup script
    script = f"""
import asyncio
from pathlib import Path
from {module} import {class_name}
from glorious_agents.core.daemon.config import DaemonConfig

workspace = Path(r"{workspace_path}")
config = DaemonConfig.load(workspace)
daemon = {class_name}(config)

config.get_pid_path().write_text(str(__import__('os').getpid()))

try:
    asyncio.run(daemon.run())
finally:
    if config.get_pid_path().exists():
        config.get_pid_path().unlink()
"""

    # Run daemon as subprocess
    process = subprocess.Popen(  # noqa: S603
        [python_exe, "-c", script],
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=True,
    )

    # Brief wait to let daemon write PID
    import time

    time.sleep(0.5)

    return process.pid


def _start_unix_daemon(
    workspace_path: Path,
    daemon_class: type[BaseDaemonService],
    config: DaemonConfig,
) -> int:
    """Start daemon on Unix using double fork.

    Args:
        workspace_path: Workspace directory
        daemon_class: Daemon service class
        config: Daemon configuration

    Returns:
        Process ID
    """
    # First fork
    pid = os.fork()
    if pid > 0:
        # Parent process - wait briefly for child and return
        import time

        time.sleep(0.3)

        # Read PID from file written by grandchild
        pid_manager = PIDFileManager(config.get_pid_path())
        daemon_pid = pid_manager.read()
        return daemon_pid if daemon_pid else pid

    # Child process - become session leader
    os.setsid()

    # Second fork to prevent zombie
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Grandchild process - run daemon
    daemon = daemon_class(config)
    pid_manager = PIDFileManager(config.get_pid_path())
    pid_manager.write()

    try:
        asyncio.run(daemon.run())
    finally:
        pid_manager.remove()

    return os.getpid()


def stop_daemon(workspace_path: Path, config: DaemonConfig | None = None) -> bool:
    """Stop daemon for workspace.

    Args:
        workspace_path: Workspace directory
        config: Daemon configuration (loads if None)

    Returns:
        True if daemon was stopped, False if not running
    """
    if config is None:
        config = DaemonConfig.load(workspace_path)

    pid_manager = PIDFileManager(config.get_pid_path())
    return pid_manager.kill_existing()


def is_daemon_running(workspace_path: Path, config: DaemonConfig | None = None) -> bool:
    """Check if daemon is running for workspace.

    Args:
        workspace_path: Workspace directory
        config: Daemon configuration (loads if None)

    Returns:
        True if daemon is running
    """
    if config is None:
        config = DaemonConfig.load(workspace_path)

    pid_manager = PIDFileManager(config.get_pid_path())
    return pid_manager.is_running()

"""PID file management for daemon processes."""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class PIDFileManager:
    """Manages PID files for daemon processes.

    Provides cross-platform process tracking, stale PID detection,
    and cleanup operations.
    """

    def __init__(self, pid_path: Path) -> None:
        """Initialize PID file manager.

        Args:
            pid_path: Path to PID file
        """
        self.pid_path = pid_path

    def write(self, pid: int | None = None) -> None:
        """Write PID to file.

        Args:
            pid: Process ID (uses current process if None)
        """
        if pid is None:
            pid = os.getpid()

        self.pid_path.parent.mkdir(parents=True, exist_ok=True)
        self.pid_path.write_text(str(pid))
        logger.debug(f"Wrote PID {pid} to {self.pid_path}")

    def read(self) -> int | None:
        """Read PID from file.

        Returns:
            Process ID or None if file doesn't exist or is invalid
        """
        if not self.pid_path.exists():
            return None

        try:
            return int(self.pid_path.read_text().strip())
        except (ValueError, OSError) as e:
            logger.warning(f"Invalid PID file {self.pid_path}: {e}")
            return None

    def remove(self) -> bool:
        """Remove PID file.

        Returns:
            True if file was removed, False if it didn't exist
        """
        if self.pid_path.exists():
            self.pid_path.unlink()
            logger.debug(f"Removed PID file {self.pid_path}")
            return True
        return False

    def is_running(self) -> bool:
        """Check if process is running.

        Returns:
            True if the process exists and is running
        """
        pid = self.read()
        if pid is None:
            return False

        return self._check_process_exists(pid)

    def _check_process_exists(self, pid: int) -> bool:
        """Check if process exists using platform-appropriate method.

        Args:
            pid: Process ID to check

        Returns:
            True if process exists
        """
        # Try psutil first (most reliable, cross-platform)
        try:
            import psutil

            return bool(psutil.pid_exists(pid))
        except ImportError:
            pass

        # Fallback to OS-specific methods
        if sys.platform == "win32":
            import subprocess

            result = subprocess.run(  # noqa: S603, S607
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                check=False,
            )
            return str(pid) in result.stdout
        else:
            # Unix: try to send signal 0 (doesn't actually send signal, just checks)
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def kill_existing(self, timeout: float = 5.0) -> bool:
        """Kill existing process if running.

        Args:
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if process was killed, False if not running
        """
        pid = self.read()
        if pid is None:
            return False

        if not self._check_process_exists(pid):
            # Stale PID file
            self.remove()
            return False

        # Try psutil for graceful termination
        try:
            import psutil

            try:
                process = psutil.Process(pid)
                logger.info(f"Terminating process {pid}")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=timeout)
                except psutil.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    logger.warning(f"Process {pid} didn't terminate, force killing")
                    process.kill()
                    process.wait(timeout=1.0)

                self.remove()
                return True
            except psutil.NoSuchProcess:
                self.remove()
                return False
        except ImportError:
            pass

        # Fallback to platform-specific kill
        if sys.platform == "win32":
            import subprocess

            subprocess.run(  # noqa: S603, S607
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                check=False,
            )
        else:
            import signal

            try:
                os.kill(pid, signal.SIGTERM)
                # Brief wait for cleanup
                import time

                time.sleep(0.2)
                # Force kill if still running
                if self._check_process_exists(pid):
                    os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

        self.remove()
        return True

    def cleanup_stale(self) -> bool:
        """Remove stale PID file if process not running.

        Returns:
            True if stale file was removed
        """
        pid = self.read()
        if pid is None:
            return False

        if not self._check_process_exists(pid):
            logger.info(f"Removing stale PID file for process {pid}")
            return self.remove()

        return False

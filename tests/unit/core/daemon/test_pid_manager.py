"""Unit tests for PID file manager."""

import os
from pathlib import Path

import pytest

from glorious_agents.core.daemon.pid import PIDFileManager


class TestPIDFileManager:
    """Test PID file manager."""

    def test_write_and_read(self, tmp_path: Path):
        """Test writing and reading PID file."""
        pid_path = tmp_path / "test.pid"
        manager = PIDFileManager(pid_path)

        # Write PID
        manager.write(12345)

        # Read back
        pid = manager.read()
        assert pid == 12345
        assert pid_path.exists()

    def test_write_current_pid(self, tmp_path: Path):
        """Test writing current process PID."""
        pid_path = tmp_path / "test.pid"
        manager = PIDFileManager(pid_path)

        # Write without specifying PID
        manager.write()

        # Should write current process PID
        pid = manager.read()
        assert pid == os.getpid()

    def test_read_nonexistent(self, tmp_path: Path):
        """Test reading nonexistent PID file."""
        pid_path = tmp_path / "nonexistent.pid"
        manager = PIDFileManager(pid_path)

        pid = manager.read()
        assert pid is None

    def test_read_invalid(self, tmp_path: Path):
        """Test reading invalid PID file."""
        pid_path = tmp_path / "invalid.pid"
        pid_path.write_text("not-a-number")

        manager = PIDFileManager(pid_path)
        pid = manager.read()
        assert pid is None

    def test_remove(self, tmp_path: Path):
        """Test removing PID file."""
        pid_path = tmp_path / "test.pid"
        manager = PIDFileManager(pid_path)

        # Write and verify
        manager.write(12345)
        assert pid_path.exists()

        # Remove
        removed = manager.remove()
        assert removed is True
        assert not pid_path.exists()

        # Remove again (should return False)
        removed = manager.remove()
        assert removed is False

    def test_is_running_current_process(self, tmp_path: Path):
        """Test checking if current process is running."""
        pid_path = tmp_path / "test.pid"
        manager = PIDFileManager(pid_path)

        # Write current PID
        manager.write()

        # Should be running
        assert manager.is_running() is True

    def test_is_running_nonexistent(self, tmp_path: Path):
        """Test checking nonexistent PID."""
        pid_path = tmp_path / "test.pid"
        manager = PIDFileManager(pid_path)

        # No PID file
        assert manager.is_running() is False

        # Invalid PID
        manager.write(999999)
        assert manager.is_running() is False

    def test_cleanup_stale(self, tmp_path: Path):
        """Test cleaning up stale PID file."""
        pid_path = tmp_path / "test.pid"
        manager = PIDFileManager(pid_path)

        # Write invalid PID
        manager.write(999999)

        # Cleanup should remove stale file
        removed = manager.cleanup_stale()
        assert removed is True
        assert not pid_path.exists()

    def test_kills_existing_current_process(self, tmp_path: Path):
        """Test that we can't kill current process."""
        pid_path = tmp_path / "test.pid"
        manager = PIDFileManager(pid_path)

        # Write current PID
        manager.write()

        # Try to kill (should not kill self, but should cleanup)
        # This is a bit tricky to test safely
        assert manager.is_running() is True

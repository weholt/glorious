"""Comprehensive unit tests for daemon modules."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from issue_tracker.daemon.config import DaemonConfig
from issue_tracker.daemon.ipc_server import IPCClient, IPCServer
from issue_tracker.daemon.service import (
    DaemonService,
    is_daemon_running,
    start_daemon,
    stop_daemon,
)
from issue_tracker.daemon.sync_engine import SyncEngine


class TestDaemonConfig:
    """Test daemon configuration."""

    def test_default_config(self, tmp_path: Path):
        """Test creating default configuration."""
        config = DaemonConfig.default(tmp_path)
        assert config.workspace_path == tmp_path
        assert config.daemon_mode in ["poll", "events"]
        assert isinstance(config.sync_interval_seconds, int)
        assert config.sync_interval_seconds > 0

    def test_config_paths(self, tmp_path: Path):
        """Test configuration path methods."""
        config = DaemonConfig.default(tmp_path)

        socket_path = config.get_socket_path()
        assert socket_path.parent == tmp_path / ".issues"

        pid_path = config.get_pid_path()
        assert pid_path == tmp_path / ".issues" / "daemon.pid"

        log_path = config.get_log_path()
        assert log_path == tmp_path / ".issues" / "daemon.log"

    def test_save_and_load_config(self, tmp_path: Path):
        """Test saving and loading configuration."""
        config = DaemonConfig.default(tmp_path)
        config.sync_interval_seconds = 10
        config.save(tmp_path)

        loaded = DaemonConfig.load(tmp_path)
        assert loaded.sync_interval_seconds == 10
        assert loaded.workspace_path == tmp_path

    def test_load_nonexistent_returns_default(self, tmp_path: Path):
        """Test loading nonexistent config returns default."""
        config = DaemonConfig.load(tmp_path)
        assert config.workspace_path == tmp_path
        # Should have default values
        assert config.sync_enabled is True


class TestSyncEngine:
    """Test sync engine."""

    def test_init(self, tmp_path: Path):
        """Test sync engine initialization."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        assert engine.workspace_path == tmp_path
        assert engine.export_path == export_path
        assert engine.git_enabled is True

    def test_export_to_jsonl(self, tmp_path: Path):
        """Test exporting issues to JSONL."""
        issues_dir = tmp_path / ".issues"
        export_path = issues_dir / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        issues = [
            {
                "id": "ISS-1",
                "title": "Test Issue",
                "status": "open",
                "priority": 1,
            }
        ]

        exported, skipped = engine.export_to_jsonl(issues)

        assert exported == 1
        assert skipped == 0
        assert export_path.exists()

        # Verify content
        content = export_path.read_text()
        assert "ISS-1" in content
        assert "Test Issue" in content

    def test_export_skips_unchanged(self, tmp_path: Path):
        """Test export skips unchanged issues."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        issues = [{"id": "ISS-1", "title": "Test"}]

        # First export
        exported1, skipped1 = engine.export_to_jsonl(issues)
        assert exported1 == 1
        assert skipped1 == 0

        # Second export with same data
        exported2, skipped2 = engine.export_to_jsonl(issues)
        assert exported2 == 0
        assert skipped2 == 1

    def test_import_from_jsonl(self, tmp_path: Path):
        """Test importing from JSONL."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        export_path.parent.mkdir(parents=True)
        engine = SyncEngine(tmp_path, export_path)

        # Create test file
        test_data = {"id": "ISS-1", "title": "Imported"}
        export_path.write_text(json.dumps(test_data) + "\n")

        issues = engine.import_from_jsonl()

        assert len(issues) == 1
        assert issues[0]["id"] == "ISS-1"
        assert issues[0]["title"] == "Imported"

    def test_import_nonexistent_file(self, tmp_path: Path):
        """Test importing when file doesn't exist."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        issues = engine.import_from_jsonl()
        assert issues == []

    def test_import_skips_invalid_json(self, tmp_path: Path):
        """Test import skips invalid JSON lines."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        export_path.parent.mkdir(parents=True)
        engine = SyncEngine(tmp_path, export_path)

        export_path.write_text('not json\n{"id": "ISS-1"}\n')

        issues = engine.import_from_jsonl()
        assert len(issues) == 1
        assert issues[0]["id"] == "ISS-1"

    @patch("subprocess.run")
    def test_git_commit_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful git commit."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse (is git repo)
            Mock(returncode=0),  # git add
            Mock(returncode=1),  # diff --cached (has changes)
            Mock(returncode=0),  # git commit
        ]

        result = engine.git_commit("Test commit")

        assert result is True
        assert mock_run.call_count == 4

    @patch("subprocess.run")
    def test_git_commit_not_a_repo(self, mock_run: MagicMock, tmp_path: Path):
        """Test git commit when not in a repo."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        mock_run.return_value = Mock(returncode=1)

        result = engine.git_commit()

        assert result is False

    @patch("subprocess.run")
    def test_git_commit_no_changes(self, mock_run: MagicMock, tmp_path: Path):
        """Test git commit with no changes."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        mock_run.side_effect = [
            Mock(returncode=0),  # is git repo
            Mock(returncode=0),  # git add
            Mock(returncode=0),  # diff (no changes)
        ]

        result = engine.git_commit()

        assert result is True

    @patch("subprocess.run")
    def test_git_commit_error(self, mock_run: MagicMock, tmp_path: Path):
        """Test git commit with error."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = engine.git_commit()

        assert result is False

    @patch("subprocess.run")
    def test_git_pull_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful git pull."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        mock_run.return_value = Mock(returncode=0)

        result = engine.git_pull()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_git_pull_error(self, mock_run: MagicMock, tmp_path: Path):
        """Test git pull with error."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        mock_run.return_value = Mock(returncode=1, stderr=b"error")

        result = engine.git_pull()

        assert result is False

    @patch("subprocess.run")
    def test_git_push_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful git push."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        mock_run.return_value = Mock(returncode=0)

        result = engine.git_push()

        assert result is True

    @patch("subprocess.run")
    def test_git_push_no_upstream(self, mock_run: MagicMock, tmp_path: Path):
        """Test git push with no upstream branch."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path)

        mock_run.return_value = Mock(returncode=1, stderr=b"no upstream branch")

        result = engine.git_push()

        # Should return True as this is not a fatal error
        assert result is True

    @patch("subprocess.run")
    def test_sync_full_cycle(self, mock_run: MagicMock, tmp_path: Path):
        """Test full sync cycle."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        export_path.parent.mkdir(parents=True)
        engine = SyncEngine(tmp_path, export_path)

        # Mock all git operations
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # git add
            Mock(returncode=1),  # diff (has changes)
            Mock(returncode=0),  # git commit
            Mock(returncode=0),  # git pull
            Mock(returncode=0),  # git push
        ]

        issues = [{"id": "ISS-1", "title": "Test"}]
        stats = engine.sync(issues)

        assert stats["exported"] == 1
        assert stats["committed"] is True
        assert stats["pulled"] is True
        assert stats["pushed"] is True

    def test_git_disabled(self, tmp_path: Path):
        """Test sync with git disabled."""
        export_path = tmp_path / ".issues" / "issues.jsonl"
        engine = SyncEngine(tmp_path, export_path, git_enabled=False)

        assert engine.git_commit() is False
        assert engine.git_pull() is False
        assert engine.git_push() is False


class TestDaemonService:
    """Test daemon service."""

    def test_init(self, tmp_path: Path):
        """Test daemon service initialization."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        assert service.config == config
        assert service.workspace_path == tmp_path
        assert service.running is False
        assert service.sync_engine is not None

    @pytest.mark.asyncio
    async def test_health_check(self, tmp_path: Path):
        """Test health check."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        health = service._health_check()

        assert health["healthy"] is True
        assert "uptime_seconds" in health
        assert "pid" in health
        assert health["workspace"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_get_status(self, tmp_path: Path):
        """Test status retrieval."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        status = service._get_status()

        assert "running" in status
        assert status["workspace"] == str(tmp_path)
        assert "sync_enabled" in status
        assert "daemon_mode" in status

    @pytest.mark.asyncio
    async def test_trigger_sync(self, tmp_path: Path):
        """Test manual sync trigger."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        with patch.object(service, "_get_issues_from_db", return_value=[]):
            with patch.object(service.sync_engine, "sync", return_value={"exported": 0}):
                result = service._trigger_sync()

                assert result["status"] == "success"
                assert "stats" in result

    @pytest.mark.asyncio
    async def test_handle_request_health(self, tmp_path: Path):
        """Test handling health request."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        response = service._handle_request({"method": "health"})

        assert response["healthy"] is True

    @pytest.mark.asyncio
    async def test_handle_request_status(self, tmp_path: Path):
        """Test handling status request."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        response = service._handle_request({"method": "status"})

        assert "running" in response

    @pytest.mark.asyncio
    async def test_handle_request_sync(self, tmp_path: Path):
        """Test handling sync request."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        with patch.object(service, "_get_issues_from_db", return_value=[]):
            with patch.object(service.sync_engine, "sync", return_value={}):
                response = service._handle_request({"method": "sync"})

                assert response["status"] == "success"

    @pytest.mark.asyncio
    async def test_handle_request_unknown(self, tmp_path: Path):
        """Test handling unknown request."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        response = service._handle_request({"method": "unknown"})

        assert "error" in response

    def test_write_and_remove_pid_file(self, tmp_path: Path):
        """Test PID file management."""
        config = DaemonConfig.default(tmp_path)
        service = DaemonService(config)

        pid_path = config.get_pid_path()
        assert not pid_path.exists()

        service._write_pid_file()
        assert pid_path.exists()

        service._remove_pid_file()
        assert not pid_path.exists()


class TestDaemonLifecycle:
    """Test daemon lifecycle functions."""

    @patch("issue_tracker.daemon.service.asyncio.run")
    @patch.dict("os.environ", {"ISSUES_AUTO_START_DAEMON": "true"})
    def test_start_daemon_not_detached(self, mock_run: MagicMock, tmp_path: Path):
        """Test starting daemon without detaching."""
        config = DaemonConfig.default(tmp_path)
        config.save(tmp_path)

        mock_run.return_value = None

        start_daemon(tmp_path, detach=False)

        mock_run.assert_called_once()

    def test_is_daemon_running_no_pid_file(self, tmp_path: Path):
        """Test checking daemon status with no PID file."""
        result = is_daemon_running(tmp_path)
        assert result is False

    def test_is_daemon_running_invalid_pid(self, tmp_path: Path):
        """Test checking daemon with invalid PID."""
        config = DaemonConfig.default(tmp_path)
        pid_path = config.get_pid_path()
        pid_path.parent.mkdir(parents=True)
        pid_path.write_text("invalid")

        result = is_daemon_running(tmp_path)
        assert result is False

    @patch("subprocess.run")
    def test_stop_daemon_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test stopping daemon successfully."""
        config = DaemonConfig.default(tmp_path)
        pid_path = config.get_pid_path()
        pid_path.parent.mkdir(parents=True)
        pid_path.write_text("12345")

        mock_run.return_value = Mock(returncode=0)

        result = stop_daemon(tmp_path)

        assert result is True
        assert not pid_path.exists()

    def test_stop_daemon_no_pid_file(self, tmp_path: Path):
        """Test stopping daemon with no PID file."""
        result = stop_daemon(tmp_path)
        assert result is False


class TestIPCServer:
    """Test IPC server."""

    @pytest.mark.asyncio
    async def test_server_init(self, tmp_path: Path):
        """Test server initialization."""
        socket_path = tmp_path / "test.sock"
        handler = MagicMock()
        server = IPCServer(socket_path, handler)

        assert server.socket_path == socket_path
        assert server.handler == handler

    @pytest.mark.asyncio
    async def test_client_init(self, tmp_path: Path):
        """Test client initialization."""
        socket_path = tmp_path / "test.sock"
        client = IPCClient(socket_path)

        assert client.socket_path == socket_path


class TestIPCIntegration:
    """Test IPC communication (mocked)."""

    @pytest.mark.asyncio
    async def test_request_response(self, tmp_path: Path):
        """Test basic request-response cycle."""
        socket_path = tmp_path / "test.sock"

        async def handler(request: dict) -> dict:
            return {"echo": request.get("data")}

        # These would need full integration test setup
        # For unit tests, we verify the components exist
        server = IPCServer(socket_path, handler)
        client = IPCClient(socket_path)

        assert server is not None
        assert client is not None

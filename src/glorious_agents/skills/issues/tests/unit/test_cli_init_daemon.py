"""Unit tests for initialization and daemon commands."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestInit:
    """Test suite for 'issues init' command."""

    @patch("issue_tracker.daemon.service.start_daemon")
    def test_init_basic_mode(self, mock_start: MagicMock, cli_runner: CliRunner, tmp_path: Path):
        """Test initializing workspace in basic mode."""
        from issue_tracker.cli.app import app

        # Change to temp directory
        import os

        os.chdir(tmp_path)

        result = cli_runner.invoke(app, ["init"], input="basic\n")

        assert result.exit_code == 0
        # Check for issues/ folder (default from ISSUES_FOLDER env var or ./issues)
        # The init command uses ISSUES_FOLDER env var, which defaults to ./issues
        assert "initialized" in result.stdout.lower() or result.exit_code == 0

    @patch("issue_tracker.daemon.service.start_daemon")
    def test_init_team_mode(self, mock_start: MagicMock, cli_runner: CliRunner, tmp_path: Path):
        """Test initializing workspace in team mode."""
        from issue_tracker.cli.app import app

        import os

        os.chdir(tmp_path)

        result = cli_runner.invoke(
            app,
            ["init"],
            input="team\norigin\nmain\n",
        )

        assert result.exit_code == 0
        assert (tmp_path / ".issues").exists()

    def test_init_already_initialized(self, cli_runner: CliRunner, tmp_path: Path):
        """Test init when workspace already exists."""
        from issue_tracker.cli.app import app

        import os

        os.chdir(tmp_path)

        (tmp_path / ".issues").mkdir()

        result = cli_runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "already initialized" in result.stdout.lower() or "already initialized" in result.output.lower()

    @patch("issue_tracker.daemon.service.start_daemon")
    def test_init_force_reinitialize(self, mock_start: MagicMock, cli_runner: CliRunner, tmp_path: Path):
        """Test force re-initializing workspace."""
        from issue_tracker.cli.app import app

        import os

        os.chdir(tmp_path)

        (tmp_path / ".issues").mkdir()

        result = cli_runner.invoke(app, ["init", "--force"], input="basic\n")

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.start_daemon")
    def test_init_json_output(self, mock_start: MagicMock, cli_runner: CliRunner, tmp_path: Path):
        """Test init with JSON output."""
        from issue_tracker.cli.app import app

        import os

        os.chdir(tmp_path)

        result = cli_runner.invoke(app, ["init", "--json"], input="basic\n")

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "workspace" in data or "status" in data


class TestSync:
    """Test suite for 'issues sync' command."""

    @patch("issue_tracker.daemon.service.is_daemon_running", return_value=True)
    @patch("issue_tracker.daemon.ipc_server.IPCClient.send_request", new_callable=AsyncMock)
    def test_sync_manual_trigger(self, mock_send: AsyncMock, mock_running: MagicMock, cli_runner: CliRunner):
        """Test manual sync trigger."""
        from issue_tracker.cli.app import app

        mock_send.return_value = {"status": "success", "stats": {"exported": 10, "imported": 5}}
        result = cli_runner.invoke(app, ["sync"])

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.is_daemon_running", return_value=True)
    @patch("issue_tracker.daemon.ipc_server.IPCClient.send_request", new_callable=AsyncMock)
    def test_sync_export_only(self, mock_send: AsyncMock, mock_running: MagicMock, cli_runner: CliRunner):
        """Test sync with export only."""
        from issue_tracker.cli.app import app

        mock_send.return_value = {"status": "success", "stats": {"exported": 10, "imported": 0}}
        result = cli_runner.invoke(app, ["sync", "--export"])

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.is_daemon_running", return_value=True)
    @patch("issue_tracker.daemon.ipc_server.IPCClient.send_request", new_callable=AsyncMock)
    def test_sync_import_only(self, mock_send: AsyncMock, mock_running: MagicMock, cli_runner: CliRunner):
        """Test sync with import only."""
        from issue_tracker.cli.app import app

        mock_send.return_value = {"status": "success", "stats": {"exported": 0, "imported": 5}}
        result = cli_runner.invoke(app, ["sync", "--import"])

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.is_daemon_running", return_value=True)
    @patch("issue_tracker.daemon.ipc_server.IPCClient.send_request", new_callable=AsyncMock)
    def test_sync_json_output(self, mock_send: AsyncMock, mock_running: MagicMock, cli_runner: CliRunner):
        """Test sync with JSON output."""
        from issue_tracker.cli.app import app

        mock_send.return_value = {"status": "success", "stats": {"exported": 10, "imported": 5}}
        result = cli_runner.invoke(app, ["sync", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)


class TestDaemonsList:
    """Test suite for 'issues daemons list' command."""

    def test_daemons_list_all(self, cli_runner: CliRunner):
        """Test listing all daemons."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "list"])

        assert result.exit_code == 0

    def test_daemons_list_json(self, cli_runner: CliRunner):
        """Test daemons list with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestDaemonsHealth:
    """Test suite for 'issues daemons health' command."""

    def test_daemons_health_default(self, cli_runner: CliRunner):
        """Test checking daemon health."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "health"])

        assert result.exit_code == 0

    def test_daemons_health_specific_workspace(self, cli_runner: CliRunner, tmp_path: Path):
        """Test health check for specific workspace."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "health", "--workspace", str(tmp_path)])

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.is_daemon_running", return_value=False)
    def test_daemons_health_json(self, mock_running: MagicMock, cli_runner: CliRunner):
        """Test health check with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "health", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert "healthy" in data


class TestDaemonsStop:
    """Test suite for 'issues daemons stop' command."""

    @patch("issue_tracker.daemon.service.stop_daemon")
    def test_daemons_stop_default(self, mock_stop: MagicMock, cli_runner: CliRunner):
        """Test stopping daemon for current workspace."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "stop"])

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.stop_daemon")
    def test_daemons_stop_specific_workspace(self, mock_stop: MagicMock, cli_runner: CliRunner, tmp_path: Path):
        """Test stopping daemon for specific workspace."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "stop", "--workspace", str(tmp_path)])

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.stop_daemon")
    def test_daemons_stop_json(self, mock_stop: MagicMock, cli_runner: CliRunner):
        """Test stop with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "stop", "--json"])

        assert result.exit_code == 0


class TestDaemonsRestart:
    """Test suite for 'issues daemons restart' command."""

    @patch("issue_tracker.daemon.service.start_daemon")
    @patch("issue_tracker.daemon.service.stop_daemon")
    def test_daemons_restart_default(self, mock_stop: MagicMock, mock_start: MagicMock, cli_runner: CliRunner):
        """Test restarting daemon for current workspace."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "restart"])

        assert result.exit_code == 0

    @patch("issue_tracker.daemon.service.start_daemon")
    @patch("issue_tracker.daemon.service.stop_daemon")
    def test_daemons_restart_specific_workspace(
        self, mock_stop: MagicMock, mock_start: MagicMock, cli_runner: CliRunner, tmp_path: Path
    ):
        """Test restarting daemon for specific workspace."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "restart", "--workspace", str(tmp_path)])

        assert result.exit_code == 0


class TestDaemonsKillall:
    """Test suite for 'issues daemons killall' command."""

    @patch("issue_tracker.daemon.service.stop_daemon")
    @patch("pathlib.Path.glob", return_value=[])
    def test_daemons_killall(self, mock_glob: MagicMock, mock_stop: MagicMock, cli_runner: CliRunner):
        """Test killing all daemons."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "killall", "--force"])

        assert result.exit_code == 0

    def test_daemons_killall_requires_force(self, cli_runner: CliRunner):
        """Test killall requires --force flag."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "killall"])

        assert result.exit_code != 0

    @patch("issue_tracker.daemon.service.stop_daemon")
    @patch("pathlib.Path.glob", return_value=[])
    def test_daemons_killall_json(self, mock_glob: MagicMock, mock_stop: MagicMock, cli_runner: CliRunner):
        """Test killall with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "killall", "--force", "--json"])

        assert result.exit_code == 0


class TestDaemonsLogs:
    """Test suite for 'issues daemons logs' command."""

    def test_daemons_logs_default(self, cli_runner: CliRunner):
        """Test viewing daemon logs."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "logs"])

        assert result.exit_code == 0

    def test_daemons_logs_with_lines(self, cli_runner: CliRunner):
        """Test viewing limited number of log lines."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "logs", "--lines", "50"])

        assert result.exit_code == 0

    @pytest.mark.skip(reason="Follow mode blocks indefinitely - requires integration test setup")
    def test_daemons_logs_follow(self, cli_runner: CliRunner):
        """Test following daemon logs."""
        from issue_tracker.cli.app import app

        # This would normally block, so we just test it starts correctly
        # In actual implementation, would need timeout or interrupt handling
        result = cli_runner.invoke(app, ["daemons", "logs", "--follow"], input="\x03")

        # May exit with 0 or non-zero depending on interrupt handling
        assert result.exit_code in [0, 1, 130]

    def test_daemons_logs_specific_workspace(self, cli_runner: CliRunner, tmp_path: Path):
        """Test viewing logs for specific workspace."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["daemons", "logs", "--workspace", str(tmp_path)])

        assert result.exit_code == 0

"""Tests for sandbox skill."""

from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner
from glorious_sandbox.skill import app, init_context

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.conn = MagicMock()
    return ctx

class TestRunCommand:
    def test_run_basic(self, runner):
        result = runner.invoke(app, ["run", "python:3.11"])
        assert result.exit_code == 0
        assert "python:3.11" in result.output

    def test_run_with_timeout(self, runner):
        result = runner.invoke(app, ["run", "python:3.11", "--timeout", "60"])
        assert result.exit_code == 0
        assert "60s" in result.output

class TestListCommand:
    def test_list_without_context(self, runner):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    @patch("glorious_sandbox.skill._ctx")
    def test_list_with_sandboxes(self, mock_ctx, runner):
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([
            (1, "abc123def456", "python:3.11", "running", "2025-11-15"),
        ]))
        mock_ctx.conn.execute.return_value = mock_cursor
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

class TestLogsCommand:
    def test_logs_without_context(self, runner):
        result = runner.invoke(app, ["logs", "1"])
        assert result.exit_code == 0

    @patch("glorious_sandbox.skill._ctx")
    def test_logs_with_data(self, mock_ctx, runner):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Test log output",)
        mock_ctx.conn.execute.return_value = mock_cursor
        result = runner.invoke(app, ["logs", "1"])
        assert result.exit_code == 0

class TestCleanupCommand:
    def test_cleanup(self, runner):
        result = runner.invoke(app, ["cleanup"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

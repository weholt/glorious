"""Integration tests for telemetry skill."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestTelemetryLogCommand:
    """Tests for 'agent telemetry log' command."""

    def test_telemetry_log_basic(self, isolated_env):
        """Test logging telemetry event."""
        result = run_agent_cli(
            ["telemetry", "log", "test-category", "test message"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

    def test_telemetry_log_with_skill(self, isolated_env):
        """Test logging with skill name."""
        result = run_agent_cli(
            ["telemetry", "log", "category", "message", "--skill", "notes"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

    def test_telemetry_log_with_duration(self, isolated_env):
        """Test logging with duration."""
        result = run_agent_cli(
            ["telemetry", "log", "category", "message", "--duration", "1500"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]


@pytest.mark.integration
class TestTelemetryStatsCommand:
    """Tests for 'agent telemetry stats' command."""

    def test_telemetry_stats_by_category(self, isolated_env):
        """Test viewing stats by category."""
        result = run_agent_cli(
            ["telemetry", "stats", "--group-by", "category"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

    def test_telemetry_stats_by_skill(self, isolated_env):
        """Test viewing stats by skill."""
        result = run_agent_cli(
            ["telemetry", "stats", "--group-by", "skill"], cwd=isolated_env["cwd"]
        )

        assert result["success"]


@pytest.mark.integration
class TestTelemetryListCommand:
    """Tests for 'agent telemetry list' command."""

    def test_telemetry_list(self, isolated_env):
        """Test listing events."""
        result = run_agent_cli(
            ["telemetry", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_telemetry_list_filtered(self, isolated_env):
        """Test listing events by category."""
        result = run_agent_cli(["telemetry", "list", "--category", "test"], cwd=isolated_env["cwd"])

        assert result["success"]

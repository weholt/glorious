"""Unit tests for stats, stale, bulk-create, and info commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestStats:
    """Test suite for 'issues stats' command."""

    def test_stats_summary(self, cli_runner: CliRunner):
        """Test displaying stats summary."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stats"])
        
        assert result.exit_code == 0

    def test_stats_by_status(self, cli_runner: CliRunner):
        """Test stats grouped by status."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stats", "--by", "status"])
        
        assert result.exit_code == 0

    def test_stats_by_priority(self, cli_runner: CliRunner):
        """Test stats grouped by priority."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stats", "--by", "priority"])
        
        assert result.exit_code == 0

    def test_stats_by_type(self, cli_runner: CliRunner):
        """Test stats grouped by type."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stats", "--by", "type"])
        
        assert result.exit_code == 0

    def test_stats_by_assignee(self, cli_runner: CliRunner):
        """Test stats grouped by assignee."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stats", "--by", "assignee"])
        
        assert result.exit_code == 0

    def test_stats_json_output(self, cli_runner: CliRunner):
        """Test stats with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stats", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)


class TestStale:
    """Test suite for 'issues stale' command."""

    def test_stale_default_30_days(self, cli_runner: CliRunner):
        """Test finding stale issues (30 days default)."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stale"])
        
        assert result.exit_code == 0

    def test_stale_custom_days(self, cli_runner: CliRunner):
        """Test finding stale issues with custom days."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stale", "--days", "14"])
        
        assert result.exit_code == 0

    def test_stale_json_output(self, cli_runner: CliRunner):
        """Test stale with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["stale", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestBulkCreate:
    """Test suite for 'issues bulk-create' command."""

    def test_bulk_create_from_file(self, cli_runner: CliRunner, tmp_path: Path):
        """Test bulk creating issues from file."""
        from issue_tracker.cli.app import app

        issues_file = tmp_path / "bulk.md"
        issues_file.write_text(
            """# First issue
Description for first issue

# Second issue
Description for second issue

# Third issue
Description for third issue
"""
        )

        result = cli_runner.invoke(
            app, ["bulk-create", str(issues_file)]
        )
        
        assert result.exit_code == 0

    def test_bulk_create_with_type(self, cli_runner: CliRunner, tmp_path: Path):
        """Test bulk create with default type."""
        from issue_tracker.cli.app import app

        issues_file = tmp_path / "bugs.md"
        issues_file.write_text("# Bug 1\n\n# Bug 2\n")

        result = cli_runner.invoke(
            app,
            ["bulk-create", str(issues_file), "--type", "bug"],
        )
        
        assert result.exit_code == 0

    def test_bulk_create_with_priority(self, cli_runner: CliRunner, tmp_path: Path):
        """Test bulk create with default priority."""
        from issue_tracker.cli.app import app

        issues_file = tmp_path / "critical.md"
        issues_file.write_text("# Issue 1\n\n# Issue 2\n")

        result = cli_runner.invoke(
            app,
            ["bulk-create", str(issues_file), "-p", "0"],
        )
        
        assert result.exit_code == 0

    def test_bulk_create_json_output(self, cli_runner: CliRunner, tmp_path: Path):
        """Test bulk create with JSON output."""
        from issue_tracker.cli.app import app

        issues_file = tmp_path / "issues.md"
        issues_file.write_text("# Issue 1\n\n# Issue 2\n")

        result = cli_runner.invoke(
            app, ["bulk-create", str(issues_file), "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestInfo:
    """Test suite for 'issues info' command."""

    def test_info_workspace(self, cli_runner: CliRunner):
        """Test displaying workspace info."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["info"])
        
        assert result.exit_code == 0

    def test_info_json_output(self, cli_runner: CliRunner):
        """Test info with JSON output (spec-compliant format)."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["info", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        # Spec-compliant format
        assert "database_path" in data
        assert "total_issues" in data
        assert "last_updated" in data
        assert "database_size_bytes" in data


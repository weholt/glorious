"""Unit tests for issues show command."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestIssuesShow:
    """Test suite for 'issues show' command."""

    def test_show_single_issue(self, cli_runner: CliRunner):
        """Test showing a single issue."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        # Now show it
        result = cli_runner.invoke(app, ["show", issue_id])

        assert result.exit_code == 0
        assert "Test Issue" in result.stdout

    def test_show_json_output(self, cli_runner: CliRunner):
        """Test show with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "JSON Test", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        # Show with JSON
        result = cli_runner.invoke(app, ["show", issue_id, "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "id" in data
        assert data["id"] == issue_id
        assert data["title"] == "JSON Test"

    def test_show_multiple_issues(self, cli_runner: CliRunner):
        """Test showing multiple issues."""
        from issue_tracker.cli.app import app

        # Create three issues
        result1 = cli_runner.invoke(app, ["create", "First Issue", "--json"])
        id1 = json.loads(result1.stdout)["id"]
        result2 = cli_runner.invoke(app, ["create", "Second Issue", "--json"])
        id2 = json.loads(result2.stdout)["id"]
        result3 = cli_runner.invoke(app, ["create", "Third Issue", "--json"])
        id3 = json.loads(result3.stdout)["id"]

        # Show all three
        result = cli_runner.invoke(app, ["show", id1, id2, id3])

        assert result.exit_code == 0
        assert "First Issue" in result.stdout
        assert "Second Issue" in result.stdout
        assert "Third Issue" in result.stdout

    def test_show_with_comments(self, cli_runner: CliRunner):
        """Test showing issue with comments."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Issue with comments", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        # Show with comments flag
        result = cli_runner.invoke(app, ["show", issue_id, "--comments"])

        assert result.exit_code == 0
        assert "Issue with comments" in result.stdout

    def test_show_with_history(self, cli_runner: CliRunner):
        """Test showing issue with history."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Issue with history", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        # Show with history flag
        result = cli_runner.invoke(app, ["show", issue_id, "--history"])

        assert result.exit_code == 0
        assert "Issue with history" in result.stdout

    def test_show_with_dependencies(self, cli_runner: CliRunner):
        """Test showing issue with dependencies."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Issue with deps", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        # Show with deps flag
        result = cli_runner.invoke(app, ["show", issue_id, "--deps"])

        assert result.exit_code == 0
        assert "Issue with deps" in result.stdout

    def test_show_all_details(self, cli_runner: CliRunner):
        """Test showing issue with all details."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Issue with all details", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        # Show with all flags
        result = cli_runner.invoke(
            app,
            [
                "show",
                issue_id,
                "--comments",
                "--history",
                "--deps",
            ],
        )

        assert result.exit_code == 0
        assert "Issue with all details" in result.stdout

    def test_show_nonexistent_issue(self, cli_runner: CliRunner):
        """Test showing a non-existent issue."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["show", "issue-nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "not found" in result.output.lower()

    def test_show_best_effort_multiple(self, cli_runner: CliRunner):
        """Test showing multiple issues with some missing."""
        from issue_tracker.cli.app import app

        # Create two issues
        result1 = cli_runner.invoke(app, ["create", "First Issue", "--json"])
        id1 = json.loads(result1.stdout)["id"]
        result2 = cli_runner.invoke(app, ["create", "Second Issue", "--json"])
        id2 = json.loads(result2.stdout)["id"]

        # Show two real issues and one fake
        result = cli_runner.invoke(
            app,
            [
                "show",
                id1,
                "issue-nonexistent",
                id2,
                "--json",
            ],
        )

        # Should fail because one ID was not found (show exits with 1 on any missing ID)
        assert result.exit_code != 0
        # But should still output the found issues
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "First Issue"
        assert data[1]["title"] == "Second Issue"

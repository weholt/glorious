"""Unit tests for issues list command."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestIssuesList:
    """Test suite for 'issues list' command."""

    def test_list_all_default(self, cli_runner: CliRunner):
        """Test listing all issues with default options."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list"])
        
        assert result.exit_code == 0

    def test_list_json_output(self, cli_runner: CliRunner):
        """Test list with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_list_filter_by_status(self, cli_runner: CliRunner):
        """Test filtering by status."""
        from issue_tracker.cli.app import app

        # Create issues with different statuses
        cli_runner.invoke(app, ["create", "Open issue", "--json"])
        closed_result = cli_runner.invoke(app, ["create", "To close", "--json"])
        closed_id = json.loads(closed_result.stdout)["id"]
        cli_runner.invoke(app, ["close", closed_id])
        
        # Filter by status=open
        result = cli_runner.invoke(app, ["list", "--status", "open", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["status"] == "open"

    def test_list_filter_by_priority(self, cli_runner: CliRunner):
        """Test filtering by priority."""
        from issue_tracker.cli.app import app

        # Create issues with different priorities
        cli_runner.invoke(app, ["create", "P1", "-p", "1", "--json"])
        cli_runner.invoke(app, ["create", "P2", "-p", "2", "--json"])
        cli_runner.invoke(app, ["create", "P1 again", "-p", "1", "--json"])
        
        # Filter by priority=1
        result = cli_runner.invoke(app, ["list", "--priority", "1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 2
        assert all(issue["priority"] == 1 for issue in data)

    def test_list_filter_priority_range(self, cli_runner: CliRunner):
        """Test filtering by priority range."""
        from issue_tracker.cli.app import app

        # Create issues with different priorities
        cli_runner.invoke(app, ["create", "P0", "-p", "0", "--json"])
        cli_runner.invoke(app, ["create", "P1", "-p", "1", "--json"])
        cli_runner.invoke(app, ["create", "P2", "-p", "2", "--json"])
        cli_runner.invoke(app, ["create", "P3", "-p", "3", "--json"])
        
        # Filter by range 0-2
        result = cli_runner.invoke(
            app, ["list", "--priority-min", "0", "--priority-max", "2", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 3
        assert all(0 <= issue["priority"] <= 2 for issue in data)

    def test_list_filter_by_type(self, cli_runner: CliRunner):
        """Test filtering by issue type."""
        from issue_tracker.cli.app import app

        # Create issues with different types
        cli_runner.invoke(app, ["create", "Bug", "--type", "bug", "--json"])
        cli_runner.invoke(app, ["create", "Feature", "--type", "feature", "--json"])
        cli_runner.invoke(app, ["create", "Another bug", "--type", "bug", "--json"])
        
        # Filter by type=bug
        result = cli_runner.invoke(app, ["list", "--type", "bug", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 2
        assert all(issue["type"] == "bug" for issue in data)

    def test_list_filter_by_assignee(self, cli_runner: CliRunner):
        """Test filtering by assignee."""
        from issue_tracker.cli.app import app

        # Create issues with different assignees
        cli_runner.invoke(app, ["create", "Alice task", "-a", "alice", "--json"])
        cli_runner.invoke(app, ["create", "Bob task", "-a", "bob", "--json"])
        cli_runner.invoke(app, ["create", "Another Alice task", "-a", "alice", "--json"])
        
        # Filter by assignee=alice
        result = cli_runner.invoke(app, ["list", "--assignee", "alice", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 2
        assert all(issue["assignee"] == "alice" for issue in data)

    def test_list_filter_no_assignee(self, cli_runner: CliRunner):
        """Test filtering unassigned issues."""
        from issue_tracker.cli.app import app

        # Create issues with and without assignees
        cli_runner.invoke(app, ["create", "Unassigned 1", "--json"])
        cli_runner.invoke(app, ["create", "Assigned", "-a", "alice", "--json"])
        cli_runner.invoke(app, ["create", "Unassigned 2", "--json"])
        
        # Filter unassigned
        result = cli_runner.invoke(app, ["list", "--no-assignee", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 2
        assert all(issue["assignee"] is None for issue in data)

    def test_list_filter_by_labels_and(self, cli_runner: CliRunner):
        """Test filtering by labels with AND logic."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["list", "--label", "bug,critical"]
        )
        
        assert result.exit_code == 0

    def test_list_filter_by_labels_or(self, cli_runner: CliRunner):
        """Test filtering by labels with OR logic."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["list", "--label-any", "bug,feature"]
        )
        
        assert result.exit_code == 0

    def test_list_filter_no_labels(self, cli_runner: CliRunner):
        """Test filtering issues with no labels."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list", "--no-labels"])
        
        assert result.exit_code == 0

    def test_list_filter_by_epic(self, cli_runner: CliRunner):
        """Test filtering by epic."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list", "--epic", "issue-epic001"])
        
        assert result.exit_code == 0

    def test_list_with_limit(self, cli_runner: CliRunner):
        """Test limiting number of results."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list", "--limit", "10"])
        
        assert result.exit_code == 0

    def test_list_sort_by_priority(self, cli_runner: CliRunner):
        """Test sorting by priority."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list", "--sort", "priority"])
        
        assert result.exit_code == 0

    def test_list_sort_by_created(self, cli_runner: CliRunner):
        """Test sorting by creation date."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list", "--sort", "created"])
        
        assert result.exit_code == 0

    def test_list_reverse_order(self, cli_runner: CliRunner):
        """Test reverse sorting."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["list", "--reverse"])
        
        assert result.exit_code == 0

    def test_list_combined_filters(self, cli_runner: CliRunner):
        """Test combining multiple filters."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app,
            [
                "list",
                "--status",
                "open",
                "--type",
                "bug",
                "--priority-min",
                "0",
                "--label",
                "critical",
                "--json",
            ],
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

"""Unit tests for issues update, close, reopen, delete commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestIssuesUpdate:
    """Test suite for 'issues update' command."""

    def test_update_title(self, cli_runner: CliRunner):
        """Test updating issue title."""
        from issue_tracker.cli.app import app

        # Create issue
        create_result = cli_runner.invoke(app, ["create", "Old title", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        
        # Update title
        result = cli_runner.invoke(
            app, ["update", issue_id, "--title", "New title", "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["title"] == "New title"

    def test_update_priority(self, cli_runner: CliRunner):
        """Test updating issue priority."""
        from issue_tracker.cli.app import app

        # Create issue with priority 2
        create_result = cli_runner.invoke(app, ["create", "Test", "-p", "2", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        
        # Update to priority 0
        result = cli_runner.invoke(
            app, ["update", issue_id, "-p", "0", "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["priority"] == 0

    def test_update_assignee(self, cli_runner: CliRunner):
        """Test updating issue assignee."""
        from issue_tracker.cli.app import app

        # Create issue
        create_result = cli_runner.invoke(app, ["create", "Test", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        
        # Update assignee
        result = cli_runner.invoke(
            app, ["update", issue_id, "-a", "bob", "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["assignee"] == "bob"

    def test_update_description(self, cli_runner: CliRunner):
        """Test updating issue description."""
        from issue_tracker.cli.app import app

        # Create issue
        create_result = cli_runner.invoke(app, ["create", "Test", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        
        # Update description
        result = cli_runner.invoke(
            app,
            ["update", issue_id, "-d", "Updated description", "--json"],
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["description"] == "Updated description"

    def test_update_multiple_fields(self, cli_runner: CliRunner):
        """Test updating multiple fields."""
        from issue_tracker.cli.app import app

        # Create issue
        create_result = cli_runner.invoke(app, ["create", "Old title", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        
        # Update multiple fields
        result = cli_runner.invoke(
            app,
            [
                "update",
                issue_id,
                "--title",
                "New title",
                "-p",
                "1",
                "-a",
                "alice",
                "--json",
            ],
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["title"] == "New title"
        assert data["priority"] == 1
        assert data["assignee"] == "alice"

    def test_update_multiple_issues(self, cli_runner: CliRunner):
        """Test updating multiple issues (batch)."""
        from issue_tracker.cli.app import app

        # Create two issues
        result1 = cli_runner.invoke(app, ["create", "First", "--json"])
        id1 = json.loads(result1.stdout)["id"]
        result2 = cli_runner.invoke(app, ["create", "Second", "--json"])
        id2 = json.loads(result2.stdout)["id"]
        
        # Update both
        result = cli_runner.invoke(
            app,
            [
                "update",
                id1,
                id2,
                "-p",
                "1",
                "--json",
            ],
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 2
        assert all(issue["priority"] == 1 for issue in data)

    def test_update_json_output(self, cli_runner: CliRunner):
        """Test update with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue
        create_result = cli_runner.invoke(app, ["create", "Old", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        
        # Update with JSON output
        result = cli_runner.invoke(
            app,
            ["update", issue_id, "--title", "New", "--json"],
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "id" in data
        assert data["id"] == issue_id
        assert data["title"] == "New"

    def test_update_nonexistent_issue(self, cli_runner: CliRunner):
        """Test updating non-existent issue."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app,
            ["update", "issue-nonexistent", "--title", "New"],
        )
        
        assert result.exit_code != 0


class TestIssuesClose:
    """Test suite for 'issues close' command."""

    def test_close_single_issue(self, cli_runner: CliRunner):
        """Test closing a single issue."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["close", "issue-123"])
        
        assert result.exit_code == 0

    def test_close_multiple_issues(self, cli_runner: CliRunner):
        """Test closing multiple issues."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["close", "issue-123", "issue-456"]
        )
        
        assert result.exit_code == 0

    def test_close_with_reason(self, cli_runner: CliRunner):
        """Test closing with reason."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["close", "issue-123", "--reason", "fixed"]
        )
        
        assert result.exit_code == 0

    def test_close_json_output(self, cli_runner: CliRunner):
        """Test close with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue
        create_result = cli_runner.invoke(app, ["create", "Test", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        
        # Close with JSON output (single issue returns dict, not list)
        result = cli_runner.invoke(
            app, ["close", issue_id, "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert data["status"] == "closed"
        assert data["closed_at"] is not None


class TestIssuesReopen:
    """Test suite for 'issues reopen' command."""

    def test_reopen_single_issue(self, cli_runner: CliRunner):
        """Test reopening a single issue."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["reopen", "issue-123"])
        
        assert result.exit_code == 0

    def test_reopen_multiple_issues(self, cli_runner: CliRunner):
        """Test reopening multiple issues."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["reopen", "issue-123", "issue-456"]
        )
        
        assert result.exit_code == 0

    def test_reopen_json_output(self, cli_runner: CliRunner):
        """Test reopen with JSON output."""
        from issue_tracker.cli.app import app

        # Create and close issue
        create_result = cli_runner.invoke(app, ["create", "Test", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["close", issue_id])
        
        # Reopen with JSON output (single issue returns dict, not list)
        result = cli_runner.invoke(
            app, ["reopen", issue_id, "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert data["status"] == "open"
        assert data["closed_at"] is None


class TestIssuesDelete:
    """Test suite for 'issues delete' command."""

    def test_delete_single_issue(self, cli_runner: CliRunner):
        """Test deleting a single issue."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["delete", "issue-123", "--force"]
        )
        
        assert result.exit_code == 0

    def test_delete_requires_force(self, cli_runner: CliRunner):
        """Test delete requires --force flag."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["delete", "issue-123"])
        
        assert result.exit_code != 0

    def test_delete_multiple_issues(self, cli_runner: CliRunner):
        """Test deleting multiple issues."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app,
            [
                "delete",
                "issue-123",
                "issue-456",
                "--force",
            ],
        )
        
        assert result.exit_code == 0

    def test_delete_json_output(self, cli_runner: CliRunner):
        """Test delete with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["delete", "issue-123", "--force", "--json"]
        )
        
        assert result.exit_code == 0


class TestIssuesRestore:
    """Test suite for 'issues restore' command."""

    def test_restore_single_issue(self, cli_runner: CliRunner):
        """Test restoring a deleted issue."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["restore", "issue-123"])
        
        assert result.exit_code == 0

    def test_restore_multiple_issues(self, cli_runner: CliRunner):
        """Test restoring multiple issues."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["restore", "issue-123", "issue-456"]
        )
        
        assert result.exit_code == 0

    def test_restore_json_output(self, cli_runner: CliRunner):
        """Test restore with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(
            app, ["restore", "issue-123", "--json"]
        )
        
        assert result.exit_code == 0

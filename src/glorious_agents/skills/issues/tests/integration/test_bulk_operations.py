"""Integration tests for bulk operations.

Tests bulk operations and batch processing:
- Bulk create from markdown
- Bulk close multiple issues
- Bulk label operations
- Best-effort error handling
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from issue_tracker.cli.app import app


class TestBulkOperations:
    """Test bulk operations and batch processing."""

    def test_bulk_create_from_markdown(self, integration_cli_runner: CliRunner, tmp_path: Path):
        """Test creating multiple issues from markdown file."""
        runner = integration_cli_runner

        # Create markdown file with multiple issues
        markdown_file = tmp_path / "issues.md"
        markdown_file.write_text(
            """# Issue 1
Description for issue 1

# Issue 2
Description for issue 2

# Issue 3
Description for issue 3
"""
        )

        # Bulk create from file
        result = runner.invoke(app, ["bulk-create", str(markdown_file), "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert len(data) == 3
        assert data[0]["title"] == "Issue 1"
        assert data[1]["title"] == "Issue 2"
        assert data[2]["title"] == "Issue 3"

    def test_bulk_close_multiple_issues(self, integration_cli_runner: CliRunner):
        """Test closing multiple issues at once."""
        runner = integration_cli_runner

        # Create multiple issues
        result = runner.invoke(app, ["create", "Task 1", "--json"])
        assert result.exit_code == 0
        issue1 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Task 2", "--json"])
        assert result.exit_code == 0
        issue2 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Task 3", "--json"])
        assert result.exit_code == 0
        issue3 = json.loads(result.stdout)

        # Bulk close
        result = runner.invoke(
            app,
            [
                "bulk-close",
                "Completed in batch",
                issue1["id"],
                issue2["id"],
                issue3["id"],
                "--json",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert "successes" in data
        assert len(data["successes"]) == 3
        assert all(issue["status"] == "closed" for issue in data["successes"])
        assert all(issue["closed_at"] is not None for issue in data["successes"])

    def test_bulk_label_add_operations(self, integration_cli_runner: CliRunner):
        """Test adding same label to multiple issues."""
        runner = integration_cli_runner

        # Create multiple issues
        result = runner.invoke(app, ["create", "Task 1", "--json"])
        assert result.exit_code == 0
        issue1 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Task 2", "--json"])
        assert result.exit_code == 0
        issue2 = json.loads(result.stdout)

        # Bulk add label
        result = runner.invoke(app, ["bulk-label-add", "critical", issue1["id"], issue2["id"], "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert "successes" in data
        assert len(data["successes"]) == 2
        assert all("critical" in issue["labels"] for issue in data["successes"])

    def test_bulk_label_remove_operations(self, integration_cli_runner: CliRunner):
        """Test removing same label from multiple issues."""
        runner = integration_cli_runner

        # Create issues with labels
        result = runner.invoke(app, ["create", "Task 1", "--json"])
        assert result.exit_code == 0
        issue1 = json.loads(result.stdout)
        runner.invoke(app, ["labels", "add", issue1["id"], "urgent"])

        result = runner.invoke(app, ["create", "Task 2", "--json"])
        assert result.exit_code == 0
        issue2 = json.loads(result.stdout)
        runner.invoke(app, ["labels", "add", issue2["id"], "urgent"])

        # Bulk remove label
        result = runner.invoke(app, ["bulk-label-remove", "urgent", issue1["id"], issue2["id"], "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert "successes" in data
        assert len(data["successes"]) == 2
        assert all("urgent" not in issue["labels"] for issue in data["successes"])

    def test_best_effort_multi_update(self, integration_cli_runner: CliRunner):
        """Test best-effort update (some succeed, some fail)."""
        runner = integration_cli_runner

        # Create one valid issue
        result = runner.invoke(app, ["create", "Valid task", "--json"])
        assert result.exit_code == 0
        valid_issue = json.loads(result.stdout)

        # Try to update valid + nonexistent issue
        result = runner.invoke(
            app,
            [
                "bulk-update",
                valid_issue["id"],
                "issue-nonexistent",
                "--new-priority",
                "1",
                "--json",
            ],
        )

        # Should succeed for valid issue, fail for nonexistent
        assert result.exit_code == 0
        data = json.loads(result.stdout)

        assert len(data["successes"]) == 1
        assert data["successes"][0]["id"] == valid_issue["id"]
        assert data["successes"][0]["priority"] == 1

        assert len(data["failures"]) == 1
        assert data["failures"][0]["id"] == "issue-nonexistent"


class TestErrorRecovery:
    """Test error handling and recovery patterns."""

    def test_nonexistent_issue_graceful_error(self, integration_cli_runner: CliRunner):
        """Test operations on nonexistent issues fail gracefully."""
        runner = integration_cli_runner

        result = runner.invoke(app, ["show", "issue-nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()

    def test_invalid_status_transition(self, integration_cli_runner: CliRunner):
        """Test invalid status values are rejected."""
        runner = integration_cli_runner

        result = runner.invoke(app, ["create", "Test issue", "--json"])
        assert result.exit_code == 0
        issue = json.loads(result.stdout)

        # Try invalid status
        result = runner.invoke(app, ["update", issue["id"], "--status", "invalid_status"])
        assert result.exit_code != 0

    def test_bulk_operation_partial_success(self, integration_cli_runner: CliRunner):
        """Test bulk operations continue on errors and report results."""
        runner = integration_cli_runner

        # Create valid issues
        result = runner.invoke(app, ["create", "Task 1", "--json"])
        assert result.exit_code == 0
        task1 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Task 2", "--json"])
        assert result.exit_code == 0
        task2 = json.loads(result.stdout)

        # Mix valid and invalid IDs
        result = runner.invoke(
            app,
            [
                "bulk-update",
                task1["id"],
                "issue-fake",
                task2["id"],
                "--new-priority",
                "0",
                "--json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # Should have 2 successes and 1 failure
        assert len(data["successes"]) == 2
        assert len(data["failures"]) == 1
        assert data["failures"][0]["id"] == "issue-fake"

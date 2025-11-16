"""Unit tests for issues create command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestIssuesCreate:
    """Test suite for 'issues create' command."""

    def test_create_minimal(self, cli_runner: CliRunner):
        """Test creating issue with minimal arguments."""
        result = cli_runner.invoke(app, ["create", "Fix auth bug"])
        
        assert result.exit_code == 0
        assert "issue-" in result.stdout or "id" in result.stdout.lower()

    def test_create_with_type(self, cli_runner: CliRunner):
        """Test creating issue with specific type."""
        result = cli_runner.invoke(
            app, ["create", "Fix bug", "--type", "bug", "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["type"] == "bug"
        assert data["title"] == "Fix bug"

    def test_create_with_priority(self, cli_runner: CliRunner):
        """Test creating issue with priority level."""
        result = cli_runner.invoke(
            app, ["create", "Critical task", "-p", "0", "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["priority"] == 0
        assert data["title"] == "Critical task"

    def test_create_with_all_fields(self, cli_runner: CliRunner):
        """Test creating issue with all optional fields."""
        result = cli_runner.invoke(
            app,
            [
                "create",
                "Complete feature",
                "--type",
                "feature",
                "-p",
                "1",
                "-d",
                "Detailed description",
                "-a",
                "alice",
                "-l",
                "backend,api",
                "--json",
            ],
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["title"] == "Complete feature"
        assert data["type"] == "feature"
        assert data["priority"] == 1
        assert data["description"] == "Detailed description"
        assert data["assignee"] == "alice"
        assert "backend" in data["labels"]
        assert "api" in data["labels"]

    @pytest.mark.skip(reason="Custom IDs not supported - service auto-generates IDs")
    def test_create_with_custom_id(self, cli_runner: CliRunner):
        """Test creating issue with custom ID."""
        result = cli_runner.invoke(
            app, ["create", "Task", "--id", "issue-custom123"]
        )
        
        assert result.exit_code == 0
        assert "issue-custom123" in result.stdout

    def test_create_with_dependency(self, cli_runner: CliRunner):
        """Test creating issue with dependency."""
        result = cli_runner.invoke(
            app,
            [
                "create",
                "Follow-up task",
                "--deps",
                "discovered-from:issue-100",
            ],
        )
        
        assert result.exit_code == 0

    def test_create_json_output(self, cli_runner: CliRunner):
        """Test creating issue with JSON output."""
        result = cli_runner.invoke(
            app, ["create", "Test issue", "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "id" in data
        assert data["title"] == "Test issue"
        assert "created_at" in data

    def test_create_invalid_type(self, cli_runner: CliRunner):
        """Test creating issue with invalid type."""
        result = cli_runner.invoke(
            app, ["create", "Task", "--type", "invalid"]
        )
        
        assert result.exit_code != 0

    def test_create_invalid_priority(self, cli_runner: CliRunner):
        """Test creating issue with invalid priority."""
        result = cli_runner.invoke(
            app, ["create", "Task", "-p", "10"]
        )
        
        assert result.exit_code != 0

    def test_create_special_characters_title(self, cli_runner: CliRunner):
        """Test creating issue with special characters in title."""
        result = cli_runner.invoke(
            app, ["create", "Fix: auth & oauth2 (high priority)"]
        )
        
        assert result.exit_code == 0

    def test_create_empty_title(self, cli_runner: CliRunner):
        """Test creating issue with empty title."""
        result = cli_runner.invoke(app, ["create", ""])
        
        assert result.exit_code != 0

    def test_create_bulk_from_file(self, cli_runner: CliRunner, tmp_path: Path):
        """Test bulk creating issues from file."""
        issues_file = tmp_path / "issues.md"
        issues_file.write_text(
            """# Issue 1
Description 1

# Issue 2
Description 2
"""
        )

        result = cli_runner.invoke(
            app, ["create", "-f", str(issues_file), "--json"]
        )
        
        assert result.exit_code == 0

    def test_create_then_list(self, cli_runner: CliRunner):
        """Integration test: Create issue, then verify it appears in list."""
        # Create an issue
        create_result = cli_runner.invoke(
            app, ["create", "Test issue", "--type", "task", "-p", "2", "--json"]
        )
        assert create_result.exit_code == 0
        created = json.loads(create_result.stdout)
        issue_id = created["id"]
        
        # List all issues
        list_result = cli_runner.invoke(app, ["list", "--json"])
        assert list_result.exit_code == 0
        issues = json.loads(list_result.stdout)
        
        # Verify the created issue appears in the list
        assert len(issues) == 1
        assert issues[0]["id"] == issue_id
        assert issues[0]["title"] == "Test issue"
        assert issues[0]["type"] == "task"
        assert issues[0]["priority"] == 2

    def test_create_then_show(self, cli_runner: CliRunner):
        """Integration test: Create issue, then show it."""
        # Create an issue
        create_result = cli_runner.invoke(
            app, ["create", "Another test", "--json"]
        )
        assert create_result.exit_code == 0
        created = json.loads(create_result.stdout)
        issue_id = created["id"]
        
        # Show the issue
        show_result = cli_runner.invoke(app, ["show", issue_id, "--json"])
        assert show_result.exit_code == 0
        shown = json.loads(show_result.stdout)
        
        # Verify the data matches
        assert shown["id"] == issue_id
        assert shown["title"] == "Another test"
        assert shown["status"] == "open"

    def test_create_then_update(self, cli_runner: CliRunner):
        """Integration test: Create issue, then update it."""
        # Create an issue
        create_result = cli_runner.invoke(
            app, ["create", "Original title", "-p", "3", "--json"]
        )
        assert create_result.exit_code == 0
        created = json.loads(create_result.stdout)
        issue_id = created["id"]
        
        # Update the issue
        update_result = cli_runner.invoke(
            app, ["update", issue_id, "--title", "Updated title", "-p", "1", "--json"]
        )
        assert update_result.exit_code == 0
        updated = json.loads(update_result.stdout)
        
        # Verify the updates
        assert updated["title"] == "Updated title"
        assert updated["priority"] == 1
        
        # Verify via show
        show_result = cli_runner.invoke(app, ["show", issue_id, "--json"])
        shown = json.loads(show_result.stdout)
        assert shown["title"] == "Updated title"
        assert shown["priority"] == 1

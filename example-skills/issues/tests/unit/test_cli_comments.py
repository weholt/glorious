"""Unit tests for comment management commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestCommentAdd:
    """Test suite for 'issues comment-add' command."""

    def test_comment_add_simple(self, cli_runner: CliRunner):
        """Test adding a simple comment."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app, ["comments", "add", issue_id, "This is a comment"]
        )
        
        assert result.exit_code == 0

    def test_comment_add_multiline(self, cli_runner: CliRunner):
        """Test adding multi-line comment."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app,
            [
                "comments",
                "add",
                issue_id,
                "Line 1\nLine 2\nLine 3",
            ],
        )
        
        assert result.exit_code == 0

    def test_comment_add_json_output(self, cli_runner: CliRunner):
        """Test comment-add with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app,
            ["comments", "add", issue_id, "Comment", "--json"],
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "id" in data


class TestCommentList:
    """Test suite for 'issues comment-list' command."""

    def test_comment_list_all(self, cli_runner: CliRunner):
        """Test listing all comments for an issue."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(app, ["comments", "list", issue_id])
        
        assert result.exit_code == 0

    def test_comment_list_json_output(self, cli_runner: CliRunner):
        """Test comment-list with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app, ["comments", "list", issue_id, "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestCommentDelete:
    """Test suite for 'issues comment-delete' command."""

    def test_comment_delete_single(self, cli_runner: CliRunner):
        """Test deleting a comment."""
        from issue_tracker.cli.app import app

        # Create issue and comment first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["comments", "add", issue_id, "Test comment"])

        result = cli_runner.invoke(
            app, ["comments", "delete", issue_id, "1", "--force"]
        )
        
        assert result.exit_code == 0

    def test_comment_delete_requires_force(self, cli_runner: CliRunner):
        """Test delete requires --force flag."""
        from issue_tracker.cli.app import app

        # Create issue and comment first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["comments", "add", issue_id, "Test comment"])

        result = cli_runner.invoke(
            app, ["comments", "delete", issue_id, "1"]
        )
        
        assert result.exit_code != 0

    def test_comment_delete_json_output(self, cli_runner: CliRunner):
        """Test comment-delete with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue and comment first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["comments", "add", issue_id, "Test comment"])

        result = cli_runner.invoke(
            app,
            ["comments", "delete", issue_id, "1", "--force", "--json"],
        )
        
        assert result.exit_code == 0

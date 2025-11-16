"""Unit tests for label management commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestLabelsAdd:
    """Test suite for 'issues label-add' command."""

    def test_label_add_single(self, cli_runner: CliRunner):
        """Test adding a single label."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app, ["labels", "add", issue_id, "bug"]
        )
        
        assert result.exit_code == 0

    def test_label_add_multiple(self, cli_runner: CliRunner):
        """Test adding multiple labels."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app, ["labels", "add", issue_id, "bug,critical,security"]
        )
        
        assert result.exit_code == 0

    def test_label_add_to_multiple_issues(self, cli_runner: CliRunner):
        """Test adding labels to multiple issues."""
        from issue_tracker.cli.app import app

        # Create issues first
        create1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id1 = json.loads(create1.stdout)["id"]
        create2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue_id2 = json.loads(create2.stdout)["id"]

        result = cli_runner.invoke(
            app,
            [
                "labels",
                "add",
                issue_id1,
                issue_id2,
                "milestone",
            ],
        )
        
        assert result.exit_code == 0

    def test_label_add_json_output(self, cli_runner: CliRunner):
        """Test label-add with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app, ["labels", "add", issue_id, "bug", "--json"]
        )
        
        assert result.exit_code == 0


class TestLabelsRemove:
    """Test suite for 'issues label-remove' command."""

    def test_label_remove_single(self, cli_runner: CliRunner):
        """Test removing a single label."""
        from issue_tracker.cli.app import app

        # Create issue and add label first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["labels", "add", issue_id, "bug"])

        result = cli_runner.invoke(
            app, ["labels", "remove", issue_id, "bug"]
        )
        
        assert result.exit_code == 0

    def test_label_remove_multiple(self, cli_runner: CliRunner):
        """Test removing multiple labels."""
        from issue_tracker.cli.app import app

        # Create issue and add labels first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["labels", "add", issue_id, "bug,critical"])

        result = cli_runner.invoke(
            app,
            ["labels", "remove", issue_id, "bug,critical"],
        )
        
        assert result.exit_code == 0

    def test_label_remove_from_multiple_issues(self, cli_runner: CliRunner):
        """Test removing labels from multiple issues."""
        from issue_tracker.cli.app import app

        # Create issues and add labels first
        create1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id1 = json.loads(create1.stdout)["id"]
        create2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue_id2 = json.loads(create2.stdout)["id"]
        cli_runner.invoke(app, ["labels", "add", issue_id1, issue_id2, "milestone"])

        result = cli_runner.invoke(
            app,
            [
                "labels",
                "remove",
                issue_id1,
                issue_id2,
                "milestone",
            ],
        )
        
        assert result.exit_code == 0

    def test_label_remove_json_output(self, cli_runner: CliRunner):
        """Test label-remove with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue and add label first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["labels", "add", issue_id, "bug"])

        result = cli_runner.invoke(
            app, ["labels", "remove", issue_id, "bug", "--json"]
        )
        
        assert result.exit_code == 0


class TestLabelsSet:
    """Test suite for 'issues label-set' command."""

    def test_label_set_replace(self, cli_runner: CliRunner):
        """Test replacing all labels."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app, ["labels", "set", issue_id, "bug,p1"]
        )
        
        assert result.exit_code == 0

    def test_label_set_clear(self, cli_runner: CliRunner):
        """Test clearing all labels."""
        from issue_tracker.cli.app import app

        # Create issue with labels first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]
        cli_runner.invoke(app, ["labels", "add", issue_id, "bug"])

        result = cli_runner.invoke(
            app, ["labels", "set", issue_id, ""]
        )
        
        assert result.exit_code == 0

    def test_label_set_multiple_issues(self, cli_runner: CliRunner):
        """Test setting labels on multiple issues."""
        from issue_tracker.cli.app import app

        # Create issues first
        create1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id1 = json.loads(create1.stdout)["id"]
        create2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue_id2 = json.loads(create2.stdout)["id"]

        result = cli_runner.invoke(
            app,
            [
                "labels",
                "set",
                issue_id1,
                issue_id2,
                "milestone",
            ],
        )
        
        assert result.exit_code == 0

    def test_label_set_json_output(self, cli_runner: CliRunner):
        """Test label-set with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        result = cli_runner.invoke(
            app, ["labels", "set", issue_id, "bug", "--json"]
        )
        
        assert result.exit_code == 0


class TestLabelsList:
    """Test suite for 'issues labels' command."""

    def test_labels_list_all(self, cli_runner: CliRunner):
        """Test listing all labels."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["labels", "all"])
        
        assert result.exit_code == 0

    def test_labels_list_with_counts(self, cli_runner: CliRunner):
        """Test listing labels with usage counts."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["labels", "all", "--count"])
        
        assert result.exit_code == 0

    def test_labels_list_json_output(self, cli_runner: CliRunner):
        """Test labels list with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["labels", "all", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

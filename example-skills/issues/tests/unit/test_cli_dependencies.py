"""Unit tests for dependency management commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from issue_tracker.cli.app import app


class TestDepAdd:
    """Test suite for 'issues dep-add' command."""

    def test_dep_add_blocks(self, cli_runner: CliRunner):
        """Test adding blocks dependency."""
        from issue_tracker.cli.app import app

        # Create both issues first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "add", issue1_id, "blocks", issue2_id]
        )
        
        assert result.exit_code == 0

    def test_dep_add_depends_on(self, cli_runner: CliRunner):
        """Test adding depends-on dependency."""
        from issue_tracker.cli.app import app

        # Create both issues first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "add", issue1_id, "depends-on", issue2_id]
        )
        
        assert result.exit_code == 0

    def test_dep_add_related_to(self, cli_runner: CliRunner):
        """Test adding related-to dependency."""
        from issue_tracker.cli.app import app

        # Create both issues first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "add", issue1_id, "related-to", issue2_id]
        )
        
        assert result.exit_code == 0

    def test_dep_add_json_output(self, cli_runner: CliRunner):
        """Test dep-add with JSON output."""
        from issue_tracker.cli.app import app

        # Create both issues first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]

        result = cli_runner.invoke(
            app,
            ["dependencies", "add", issue1_id, "blocks", issue2_id, "--json"],
        )
        
        assert result.exit_code == 0

    def test_dep_add_invalid_type(self, cli_runner: CliRunner):
        """Test adding dependency with invalid type."""
        from issue_tracker.cli.app import app

        # Create both issues first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "add", issue1_id, "invalid", issue2_id]
        )
        
        assert result.exit_code != 0


class TestDepRemove:
    """Test suite for 'issues dep-remove' command."""

    def test_dep_remove_blocks(self, cli_runner: CliRunner):
        """Test removing blocks dependency."""
        from issue_tracker.cli.app import app

        # Create both issues and add dependency first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]
        cli_runner.invoke(app, ["dependencies", "add", issue1_id, "blocks", issue2_id])

        result = cli_runner.invoke(
            app, ["dependencies", "remove", issue1_id, "blocks", issue2_id]
        )
        
        assert result.exit_code == 0

    def test_dep_remove_any_type(self, cli_runner: CliRunner):
        """Test removing any dependency (no type specified)."""
        from issue_tracker.cli.app import app

        # Create both issues and add dependency first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]
        cli_runner.invoke(app, ["dependencies", "add", issue1_id, "blocks", issue2_id])

        result = cli_runner.invoke(
            app, ["dependencies", "remove", issue1_id, issue2_id]
        )
        
        assert result.exit_code == 0

    def test_dep_remove_json_output(self, cli_runner: CliRunner):
        """Test dep-remove with JSON output."""
        from issue_tracker.cli.app import app

        # Create both issues and add dependency first
        issue1 = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1.stdout)["id"]
        issue2 = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2.stdout)["id"]
        cli_runner.invoke(app, ["dependencies", "add", issue1_id, "blocks", issue2_id])

        result = cli_runner.invoke(
            app,
            ["dependencies", "remove", issue1_id, "blocks", issue2_id, "--json"],
        )
        
        assert result.exit_code == 0


class TestDepList:
    """Test suite for 'issues dep-list' command."""

    def test_dep_list_all(self, cli_runner: CliRunner):
        """Test listing all dependencies."""
        from issue_tracker.cli.app import app

        # Create issue first
        issue = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id = json.loads(issue.stdout)["id"]

        result = cli_runner.invoke(app, ["dependencies", "list", issue_id])
        
        assert result.exit_code == 0

    def test_dep_list_filter_by_type(self, cli_runner: CliRunner):
        """Test listing dependencies filtered by type."""
        from issue_tracker.cli.app import app

        # Create issue first
        issue = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id = json.loads(issue.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "list", issue_id, "--type", "blocks"]
        )
        
        assert result.exit_code == 0

    def test_dep_list_json_output(self, cli_runner: CliRunner):
        """Test dep-list with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue first
        issue = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id = json.loads(issue.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "list", issue_id, "--json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestDepTree:
    """Test suite for 'issues dep-tree' command."""

    def test_dep_tree_default(self, cli_runner: CliRunner):
        """Test dependency tree visualization."""
        from issue_tracker.cli.app import app

        # Create issue first
        issue = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id = json.loads(issue.stdout)["id"]

        result = cli_runner.invoke(app, ["dependencies", "tree", issue_id])
        
        assert result.exit_code == 0

    def test_dep_tree_with_depth(self, cli_runner: CliRunner):
        """Test dependency tree with depth limit."""
        from issue_tracker.cli.app import app

        # Create issue first
        issue = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id = json.loads(issue.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "tree", issue_id, "--depth", "3"]
        )
        
        assert result.exit_code == 0

    def test_dep_tree_json_output(self, cli_runner: CliRunner):
        """Test dep-tree with JSON output."""
        from issue_tracker.cli.app import app

        # Create issue first
        issue = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue_id = json.loads(issue.stdout)["id"]

        result = cli_runner.invoke(
            app, ["dependencies", "tree", issue_id, "--json"]
        )
        
        assert result.exit_code == 0


class TestCycles:
    """Test suite for 'issues cycles' command."""

    def test_cycles_detect_all(self, cli_runner: CliRunner):
        """Test detecting all dependency cycles."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["dependencies", "cycles"])
        
        assert result.exit_code == 0

    def test_cycles_json_output(self, cli_runner: CliRunner):
        """Test cycles with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["dependencies", "cycles", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestReady:
    """Test suite for 'issues ready' command."""

    def test_ready_list_all(self, cli_runner: CliRunner):
        """Test listing all ready issues."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["ready"])
        
        assert result.exit_code == 0

    def test_ready_with_limit(self, cli_runner: CliRunner):
        """Test listing ready issues with limit."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["ready", "--limit", "5"])
        
        assert result.exit_code == 0

    def test_ready_json_output(self, cli_runner: CliRunner):
        """Test ready with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["ready", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestBlocked:
    """Test suite for 'issues blocked' command."""

    def test_blocked_list_all(self, cli_runner: CliRunner):
        """Test listing all blocked issues."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["blocked"])
        
        assert result.exit_code == 0

    def test_blocked_json_output(self, cli_runner: CliRunner):
        """Test blocked with JSON output."""
        from issue_tracker.cli.app import app

        result = cli_runner.invoke(app, ["blocked", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

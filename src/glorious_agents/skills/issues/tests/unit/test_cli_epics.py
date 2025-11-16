"""Unit tests for epic management commands."""

import json

from typer.testing import CliRunner

from issue_tracker.cli.app import app


class TestEpicAdd:
    """Test suite for 'issues epic-add' command."""

    def test_epic_add_single_issue(self, cli_runner: CliRunner):
        """Test adding issue to epic."""

        # Create epic and regular issue first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]
        issue_result = cli_runner.invoke(app, ["create", "Regular Issue", "--json"])
        issue_id = json.loads(issue_result.stdout)["id"]

        result = cli_runner.invoke(app, ["epics", "add", epic_id, issue_id])

        assert result.exit_code == 0

    def test_epic_add_multiple_issues(self, cli_runner: CliRunner):
        """Test adding multiple issues to epic."""

        # Create epic and regular issues first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]
        issue1_result = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1_result.stdout)["id"]
        issue2_result = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2_result.stdout)["id"]

        result = cli_runner.invoke(
            app,
            [
                "epics",
                "add",
                epic_id,
                issue1_id,
                issue2_id,
            ],
        )

        assert result.exit_code == 0

    def test_epic_add_json_output(self, cli_runner: CliRunner):
        """Test epic-add with JSON output."""

        # Create epic and regular issue first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]
        issue_result = cli_runner.invoke(app, ["create", "Regular Issue", "--json"])
        issue_id = json.loads(issue_result.stdout)["id"]

        result = cli_runner.invoke(
            app,
            ["epics", "add", epic_id, issue_id, "--json"],
        )

        assert result.exit_code == 0


class TestEpicRemove:
    """Test suite for 'issues epic-remove' command."""

    def test_epic_remove_single_issue(self, cli_runner: CliRunner):
        """Test removing issue from epic."""

        # Create epic and issue, then add to epic first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]
        issue_result = cli_runner.invoke(app, ["create", "Regular Issue", "--json"])
        issue_id = json.loads(issue_result.stdout)["id"]
        cli_runner.invoke(app, ["epics", "add", epic_id, issue_id])

        result = cli_runner.invoke(app, ["epics", "remove", epic_id, issue_id])

        assert result.exit_code == 0

    def test_epic_remove_multiple_issues(self, cli_runner: CliRunner):
        """Test removing multiple issues from epic."""

        # Create epic and issues, then add to epic first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]
        issue1_result = cli_runner.invoke(app, ["create", "Issue 1", "--json"])
        issue1_id = json.loads(issue1_result.stdout)["id"]
        issue2_result = cli_runner.invoke(app, ["create", "Issue 2", "--json"])
        issue2_id = json.loads(issue2_result.stdout)["id"]
        cli_runner.invoke(app, ["epics", "add", epic_id, issue1_id, issue2_id])

        result = cli_runner.invoke(
            app,
            [
                "epics",
                "remove",
                epic_id,
                issue1_id,
                issue2_id,
            ],
        )

        assert result.exit_code == 0

    def test_epic_remove_json_output(self, cli_runner: CliRunner):
        """Test epic-remove with JSON output."""

        # Create epic and issue, then add to epic first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]
        issue_result = cli_runner.invoke(app, ["create", "Regular Issue", "--json"])
        issue_id = json.loads(issue_result.stdout)["id"]
        cli_runner.invoke(app, ["epics", "add", epic_id, issue_id])

        result = cli_runner.invoke(
            app,
            ["epics", "remove", epic_id, issue_id, "--json"],
        )

        assert result.exit_code == 0


class TestEpicList:
    """Test suite for 'issues epic-list' command."""

    def test_epic_list_issues(self, cli_runner: CliRunner):
        """Test listing issues in an epic."""

        # Create epic and issue, then add to epic first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]
        issue_result = cli_runner.invoke(app, ["create", "Regular Issue", "--json"])
        issue_id = json.loads(issue_result.stdout)["id"]
        cli_runner.invoke(app, ["epics", "add", epic_id, issue_id])

        result = cli_runner.invoke(app, ["epics", "list", epic_id])

        assert result.exit_code == 0

    def test_epic_list_json_output(self, cli_runner: CliRunner):
        """Test epic-list with JSON output."""

        # Create epic first
        epic_result = cli_runner.invoke(app, ["create", "Epic Issue", "--json"])
        epic_id = json.loads(epic_result.stdout)["id"]

        result = cli_runner.invoke(app, ["epics", "list", epic_id, "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestEpics:
    """Test suite for 'issues epics' command."""

    def test_epics_list_all(self, cli_runner: CliRunner):
        """Test listing all epics."""

        result = cli_runner.invoke(app, ["epics", "all"])

        assert result.exit_code == 0

    def test_epics_json_output(self, cli_runner: CliRunner):
        """Test epics list with JSON output."""

        result = cli_runner.invoke(app, ["epics", "all", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

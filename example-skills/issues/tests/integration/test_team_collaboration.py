"""Integration tests for team collaboration features.

Tests team collaboration workflows:
- Creating and assigning issues to team members
- Filtering by assignee
- Viewing in-progress work across team
- Batch assignment of issues
"""

import json

from typer.testing import CliRunner

from issue_tracker.cli.app import app


class TestTeamCollaboration:
    """Test team collaboration patterns and workflows."""

    def test_create_and_assign_to_team_member(self, integration_cli_runner: CliRunner):
        """Test creating issue and assigning to team member."""
        runner = integration_cli_runner

        # Create issue
        result = runner.invoke(app, ["create", "Implement feature X", "-p", "1", "--json"])
        assert result.exit_code == 0
        issue = json.loads(result.stdout)

        # Assign to team member
        result = runner.invoke(app, ["update", issue["id"], "--assignee", "alice", "--json"])
        assert result.exit_code == 0
        updated = json.loads(result.stdout)

        assert updated["assignee"] == "alice"

    def test_list_issues_by_assignee(self, integration_cli_runner: CliRunner):
        """Test filtering issues by assignee."""
        runner = integration_cli_runner

        # Create issues for different team members
        result = runner.invoke(app, ["create", "Alice task 1", "--json"])
        assert result.exit_code == 0
        alice_task1 = json.loads(result.stdout)
        result = runner.invoke(app, ["update", alice_task1["id"], "--assignee", "alice"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["create", "Alice task 2", "--json"])
        assert result.exit_code == 0
        alice_task2 = json.loads(result.stdout)
        result = runner.invoke(app, ["update", alice_task2["id"], "--assignee", "alice"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["create", "Bob task", "--json"])
        assert result.exit_code == 0
        bob_task = json.loads(result.stdout)
        result = runner.invoke(app, ["update", bob_task["id"], "--assignee", "bob"])
        assert result.exit_code == 0

        # Filter by assignee
        result = runner.invoke(app, ["list", "--assignee", "alice", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)

        issue_ids = {i["id"] for i in issues}
        assert alice_task1["id"] in issue_ids
        assert alice_task2["id"] in issue_ids
        assert bob_task["id"] not in issue_ids

    def test_list_team_in_progress_work(self, integration_cli_runner: CliRunner):
        """Test viewing all in-progress work across team."""
        runner = integration_cli_runner

        # Create and start work on multiple issues
        result = runner.invoke(app, ["create", "Alice work", "--json"])
        assert result.exit_code == 0
        alice_work = json.loads(result.stdout)
        runner.invoke(app, ["update", alice_work["id"], "--assignee", "alice", "--status", "in_progress"])

        result = runner.invoke(app, ["create", "Bob work", "--json"])
        assert result.exit_code == 0
        bob_work = json.loads(result.stdout)
        runner.invoke(app, ["update", bob_work["id"], "--assignee", "bob", "--status", "in_progress"])

        result = runner.invoke(app, ["create", "Open task", "--json"])
        assert result.exit_code == 0
        open_task = json.loads(result.stdout)

        # List all in-progress work
        result = runner.invoke(app, ["list", "--status", "in_progress", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)

        issue_ids = {i["id"] for i in issues}
        assert alice_work["id"] in issue_ids
        assert bob_work["id"] in issue_ids
        assert open_task["id"] not in issue_ids

        # Verify all have in_progress status
        assert all(i["status"] == "in_progress" for i in issues)

    def test_batch_assign_issues(self, integration_cli_runner: CliRunner):
        """Test assigning multiple issues to same person."""
        runner = integration_cli_runner

        # Create multiple issues
        result = runner.invoke(app, ["create", "Task 1", "--json"])
        assert result.exit_code == 0
        task1 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Task 2", "--json"])
        assert result.exit_code == 0
        task2 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Task 3", "--json"])
        assert result.exit_code == 0
        task3 = json.loads(result.stdout)

        # Batch assign using bulk-update
        result = runner.invoke(
            app,
            ["bulk-update", task1["id"], task2["id"], task3["id"], "--new-assignee", "alice", "--json"],
        )
        assert result.exit_code == 0
        results = json.loads(result.stdout)

        # Check all were assigned
        assert len(results["successes"]) == 3
        for success in results["successes"]:
            assert success["assignee"] == "alice"

    def test_unassigned_work_queue(self, integration_cli_runner: CliRunner):
        """Test viewing unassigned issues (work queue)."""
        runner = integration_cli_runner

        # Create assigned and unassigned issues
        result = runner.invoke(app, ["create", "Assigned task", "--json"])
        assert result.exit_code == 0
        assigned = json.loads(result.stdout)
        runner.invoke(app, ["update", assigned["id"], "--assignee", "alice"])

        result = runner.invoke(app, ["create", "Unassigned task 1", "--json"])
        assert result.exit_code == 0
        unassigned1 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Unassigned task 2", "--json"])
        assert result.exit_code == 0
        unassigned2 = json.loads(result.stdout)

        # List unassigned work
        result = runner.invoke(app, ["list", "--no-assignee", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)

        issue_ids = {i["id"] for i in issues}
        assert unassigned1["id"] in issue_ids
        assert unassigned2["id"] in issue_ids
        assert assigned["id"] not in issue_ids

    def test_reassign_issue(self, integration_cli_runner: CliRunner):
        """Test reassigning issue from one person to another."""
        runner = integration_cli_runner

        # Create and assign to Alice
        result = runner.invoke(app, ["create", "Implement API", "--json"])
        assert result.exit_code == 0
        issue = json.loads(result.stdout)

        result = runner.invoke(app, ["update", issue["id"], "--assignee", "alice", "--json"])
        assert result.exit_code == 0
        assert json.loads(result.stdout)["assignee"] == "alice"

        # Reassign to Bob
        result = runner.invoke(app, ["update", issue["id"], "--assignee", "bob", "--json"])
        assert result.exit_code == 0
        updated = json.loads(result.stdout)

        assert updated["assignee"] == "bob"

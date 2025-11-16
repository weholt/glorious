"""Tests for newly implemented spec-compliant CLI commands.

Tests for:
- epic-set: Assign issue to epic
- epic-clear: Remove issue from epic
- label-list: List labels for specific issue
"""

import json

import pytest
from typer.testing import CliRunner


class TestEpicSet:
    """Tests for epic-set command."""

    def test_epic_set_assigns_issue_to_epic(self, cli_runner: CliRunner, mock_service):
        """Test epic-set assigns issue to epic."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["epics", "set", "issue-123", "epic-456"])

        assert result.exit_code == 0
        assert "Assigned issue-123 to epic epic-456" in result.stdout
        mock_service.set_epic.assert_called_once_with("issue-123", "epic-456")
        mock_service.get_issue.assert_called_once_with("issue-123")

    def test_epic_set_json_output(self, cli_runner: CliRunner, mock_service):
        """Test epic-set with JSON output."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue with epic
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            epic_id="epic-456",
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["epics", "set", "issue-123", "epic-456", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "issue-123"
        assert data["epic_id"] == "epic-456"

    def test_epic_set_nonexistent_issue(self, cli_runner: CliRunner, mock_service):
        """Test epic-set with nonexistent issue."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain.exceptions import NotFoundError

        mock_service.set_epic.side_effect = NotFoundError("Issue not found", entity_id="issue-999")

        result = cli_runner.invoke(app, ["epics", "set", "issue-999", "epic-1"])

        assert result.exit_code == 1
        assert "Error:" in result.stdout or "Error:" in result.output

    def test_epic_set_nonexistent_epic(self, cli_runner: CliRunner, mock_service):
        """Test epic-set with nonexistent epic."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain.exceptions import NotFoundError

        mock_service.set_epic.side_effect = NotFoundError("Epic not found", entity_id="epic-999")

        result = cli_runner.invoke(app, ["epics", "set", "issue-1", "epic-999"])

        assert result.exit_code == 1
        assert "Error:" in result.stdout or "Error:" in result.output


class TestEpicClear:
    """Tests for epic-clear command."""

    def test_epic_clear_removes_epic(self, cli_runner: CliRunner, mock_service):
        """Test epic-clear removes epic from issue."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue without epic
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            epic_id=None,
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["epics", "clear", "issue-123"])

        assert result.exit_code == 0
        assert "Cleared epic from issue-123" in result.stdout
        mock_service.clear_epic.assert_called_once_with("issue-123")
        mock_service.get_issue.assert_called_once_with("issue-123")

    def test_epic_clear_json_output(self, cli_runner: CliRunner, mock_service):
        """Test epic-clear with JSON output."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue without epic
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            epic_id=None,
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["epics", "clear", "issue-123", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "issue-123"
        assert data["epic_id"] is None

    def test_epic_clear_nonexistent_issue(self, cli_runner: CliRunner, mock_service):
        """Test epic-clear with nonexistent issue."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain.exceptions import NotFoundError

        mock_service.clear_epic.side_effect = NotFoundError("Issue not found", entity_id="issue-999")

        result = cli_runner.invoke(app, ["epics", "clear", "issue-999"])

        assert result.exit_code == 1
        assert "Error:" in result.stdout or "Error:" in result.output

    def test_epic_clear_issue_without_epic(self, cli_runner: CliRunner, mock_service):
        """Test epic-clear on issue that has no epic (should succeed)."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue without epic
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            epic_id=None,
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["epics", "clear", "issue-123"])

        assert result.exit_code == 0
        assert "Cleared epic from issue-123" in result.stdout


class TestLabelList:
    """Tests for label-list command."""

    def test_label_list_displays_labels(self, cli_runner: CliRunner, mock_service):
        """Test label-list displays labels for issue."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue with labels
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            labels=["bug", "critical", "frontend"],
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["labels", "list", "issue-123"])

        assert result.exit_code == 0
        assert "Labels for issue-123:" in result.stdout
        assert "bug" in result.stdout
        assert "critical" in result.stdout
        assert "frontend" in result.stdout
        mock_service.get_issue.assert_called_once_with("issue-123")

    def test_label_list_no_labels(self, cli_runner: CliRunner, mock_service):
        """Test label-list with issue that has no labels."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue without labels
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            labels=[],
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["labels", "list", "issue-123"])

        assert result.exit_code == 0
        assert "No labels on issue-123" in result.stdout

    def test_label_list_json_output(self, cli_runner: CliRunner, mock_service):
        """Test label-list with JSON output."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue with labels
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            labels=["bug", "critical"],
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["labels", "list", "issue-123", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "issue-123"
        assert data["labels"] == ["bug", "critical"]

    def test_label_list_json_output_no_labels(self, cli_runner: CliRunner, mock_service):
        """Test label-list JSON output with no labels."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        # Create mock issue without labels
        issue = Issue(
            id="issue-123",
            project_id="default",
            title="Test Issue",
            description="",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            labels=[],
        )
        mock_service.get_issue.return_value = issue

        result = cli_runner.invoke(app, ["labels", "list", "issue-123", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "issue-123"
        assert data["labels"] == []

    def test_label_list_nonexistent_issue(self, cli_runner: CliRunner, mock_service):
        """Test label-list with nonexistent issue."""
        from issue_tracker.cli.app import app
        from issue_tracker.domain.exceptions import NotFoundError

        mock_service.get_issue.side_effect = NotFoundError("Issue not found", entity_id="issue-999")

        result = cli_runner.invoke(app, ["labels", "list", "issue-999"])

        assert result.exit_code == 1
        assert "Error:" in result.stdout or "Error:" in result.output

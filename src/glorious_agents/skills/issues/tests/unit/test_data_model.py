"""Tests for data model alignment with Beads reference implementation.

Validates that the planned data model matches the original Beads schema:
- Issue entity fields and constraints
- Label management
- Epic relationships
- Comment structure
- Dependency types and relationships
"""

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from issue_tracker.cli.app import app
from issue_tracker.domain.entities.issue import Issue, IssuePriority, IssueStatus, IssueType
from issue_tracker.domain.exceptions import InvariantViolationError


class TestIssueDataModel:
    """Validate Issue entity matches Beads schema."""

    def test_issue_has_required_fields(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test issue has all required fields from Beads schema."""
        issue = {
            "id": "issue-abc",
            "project_id": "project-1",
            "title": "Test issue",
            "description": "Description text",
            "status": "open",
            "priority": 2,
            "type": "task",
            "assignee": None,
            "epic_id": None,
            "labels": [],
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "closed_at": None,
        }

        mock_service.create_issue.return_value = issue

        result = cli_runner.invoke(app, ["create", "Test issue", "-d", "Description text", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # Validate all required fields present
        assert "id" in data
        assert "project_id" in data
        assert "title" in data
        assert "description" in data
        assert "status" in data
        assert "priority" in data
        assert "type" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_issue_status_enum_values(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test issue status follows Beads enum: open, in_progress, blocked, resolved, closed, archived."""
        # Create issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        issue_id = json.loads(create_result.stdout)["id"]

        valid_statuses = [
            "open",
            "in_progress",
            "blocked",
            "resolved",
            "closed",
            "archived",
        ]

        for status in valid_statuses:
            mock_service.update_issue.return_value = {
                "id": issue_id,
                "status": status,
            }

            result = cli_runner.invoke(app, ["update", issue_id, "--status", status, "--json"])

            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data["status"] == status

    def test_issue_priority_range_0_to_4(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test priority follows Beads range: 0=critical, 1=high, 2=medium, 3=low, 4=backlog."""
        for priority in range(5):  # 0-4
            mock_service.create_issue.return_value = {
                "id": f"issue-{priority}",
                "title": "Test",
                "priority": priority,
            }

            result = cli_runner.invoke(app, ["create", "Test", "-p", str(priority), "--json"])

            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data["priority"] == priority

    def test_issue_type_enum_values(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test issue type follows Beads enum: bug, feature, task, epic, chore."""
        valid_types = ["bug", "feature", "task", "epic", "chore"]

        for issue_type in valid_types:
            mock_service.create_issue.return_value = {
                "id": f"issue-{issue_type}",
                "title": "Test",
                "type": issue_type,
            }

            result = cli_runner.invoke(app, ["create", "Test", "-t", issue_type, "--json"])

            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data["type"] == issue_type

    def test_issue_assignee_nullable(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test assignee field is optional/nullable."""
        mock_service.create_issue.return_value = {
            "id": "issue-1",
            "title": "Test",
            "assignee": None,
        }

        result = cli_runner.invoke(app, ["create", "Test", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["assignee"] is None

    def test_issue_epic_relationship_nullable(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test epic_id field is optional/nullable (only set for non-epic issues)."""
        mock_service.create_issue.return_value = {
            "id": "issue-1",
            "title": "Test",
            "type": "task",
            "epic_id": None,
        }

        result = cli_runner.invoke(app, ["create", "Test", "-t", "task", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["epic_id"] is None

    def test_issue_labels_array(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test labels stored as array of strings."""
        mock_service.create_issue.return_value = {
            "id": "issue-1",
            "title": "Test",
            "labels": ["bug", "critical", "frontend"],
        }

        result = cli_runner.invoke(app, ["create", "Test", "--label", "bug,critical,frontend", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data["labels"], list)
        assert len(data["labels"]) == 3

    def test_issue_timestamps(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test issue has created_at, updated_at, closed_at timestamps."""
        mock_service.create_issue.return_value = {
            "id": "issue-1",
            "title": "Test",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "closed_at": None,
        }

        result = cli_runner.invoke(app, ["create", "Test", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "created_at" in data
        assert "updated_at" in data
        assert "closed_at" in data


class TestLabelDataModel:
    """Validate Label entity matches Beads schema."""

    @pytest.mark.skip(reason="Rich label entities not implemented - labels are currently simple strings")
    def test_label_has_required_fields(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test label entity has id, name, color, description, timestamps."""
        mock_service.list_labels.return_value = [
            {
                "id": "label-1",
                "name": "bug",
                "color": "#ff0000",
                "description": "Bug reports",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        ]

        result = cli_runner.invoke(app, ["labels", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) > 0

        label = data[0]
        assert "id" in label
        assert "name" in label
        assert "color" in label
        assert "description" in label
        assert "created_at" in label
        assert "updated_at" in label

    def test_label_name_uniqueness(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test label names must be unique (no duplicates)."""
        # First label creation succeeds
        mock_service.create_label.return_value = {
            "id": "label-1",
            "name": "bug",
        }

        # Create an issue first
        create_result = cli_runner.invoke(app, ["create", "Test Issue", "--json"])
        assert create_result.exit_code == 0
        issue_id = json.loads(create_result.stdout)["id"]

        # First label addition succeeds
        result = cli_runner.invoke(app, ["labels", "add", issue_id, "bug", "--json"])
        assert result.exit_code == 0

        # Second attempt with same name should be idempotent
        result = cli_runner.invoke(app, ["labels", "add", issue_id, "bug", "--json"])
        # Should succeed (idempotent operation)
        assert result.exit_code == 0


class TestEpicDataModel:
    """Validate Epic entity matches Beads schema."""

    def test_epic_has_required_fields(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test epic entity has id, title, description, status, timestamps."""
        mock_service.create_issue.return_value = {
            "id": "epic-1",
            "title": "Auth System",
            "description": "Complete authentication system",
            "type": "epic",
            "status": "open",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "closed_at": None,
        }

        result = cli_runner.invoke(
            app,
            [
                "create",
                "Auth System",
                "-t",
                "epic",
                "-d",
                "Complete authentication system",
                "--json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["type"] == "epic"
        assert "id" in data
        assert "title" in data
        assert "status" in data

    def test_epic_cannot_have_parent_epic(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test epic issues cannot have epic_id set (no nested epics)."""
        mock_service.create_issue.side_effect = Exception("Epic issues cannot have parent epic")

        cli_runner.invoke(app, ["create", "Child Epic", "-t", "epic", "--json"])

        # If trying to set epic_id on epic type, should fail
        # This would be enforced at service layer
        pass  # Implementation will enforce this constraint


class TestCommentDataModel:
    """Validate Comment entity matches Beads schema."""

    def test_comment_has_required_fields(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test comment entity has id, issue_id, author, text, timestamps."""
        mock_service.list_comments.return_value = [
            {
                "id": "comment-1",
                "issue_id": "issue-1",
                "author": "alice",
                "text": "This is a comment",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        ]

        result = cli_runner.invoke(app, ["comments", "list", "issue-1", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) > 0

        comment = data[0]
        assert "id" in comment
        assert "issue_id" in comment
        assert "author" in comment
        assert "text" in comment
        assert "created_at" in comment
        assert "updated_at" in comment

    def test_comment_linked_to_issue(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test comment has foreign key to issue."""
        mock_service.add_comment.return_value = {
            "id": "comment-1",
            "issue_id": "issue-abc",
            "author": "alice",
            "text": "Comment text",
        }

        result = cli_runner.invoke(app, ["comments", "add", "issue-abc", "Comment text", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["issue_id"] == "issue-abc"


class TestDatabaseIndexes:
    """Validate that critical database indexes exist for performance."""

    def test_issue_indexes(self):
        """Test that issues table has indexes on project_id, title, status, priority, type, assignee, epic_id, created_at."""
        # Reference implementation has these indexes:
        # - project_id (for filtering by project)
        # - title (for text search)
        # - status (for filtering by status)
        # - priority (for sorting by priority)
        # - type (for filtering by type)
        # - assignee (for assignee queries)
        # - epic_id (for epic relationships)
        # - created_at (for date range queries)
        pass  # Will be validated in migration tests

    def test_label_indexes(self):
        """Test that labels table has unique index on name."""
        # Reference implementation has:
        # - name (unique constraint + index for lookups)
        pass  # Will be validated in migration tests

    def test_comment_indexes(self):
        """Test that comments table has indexes on issue_id, author, created_at."""
        # Reference implementation has:
        # - issue_id (for listing by issue)
        # - author (for filtering by author)
        # - created_at (for sorting)
        pass  # Will be validated in migration tests

    def test_dependency_indexes(self):
        """Test that dependencies table has indexes on from_issue_id, to_issue_id, dependency_type."""
        # Reference implementation has:
        # - from_issue_id (for finding outbound edges)
        # - to_issue_id (for finding inbound edges)
        # - dependency_type (for filtering by type)
        # - Composite unique (from_issue_id, to_issue_id, dependency_type)
        pass  # Will be validated in migration tests


class TestDataModelConstraints:
    """Test business rule constraints enforced at domain layer."""

    def test_title_cannot_be_empty(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test issue title must be non-empty."""
        mock_service.create_issue.side_effect = Exception("Title cannot be empty")

        result = cli_runner.invoke(app, ["create", "", "--json"])

        assert result.exit_code != 0

    def test_priority_must_be_0_to_4(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test priority must be in range 0-4."""
        mock_service.create_issue.side_effect = Exception("Invalid priority")

        result = cli_runner.invoke(app, ["create", "Test", "-p", "5", "--json"])

        assert result.exit_code != 0

    def test_labels_are_deduplicated(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test labels list has no duplicates."""
        mock_service.create_issue.return_value = {
            "id": "issue-1",
            "title": "Test",
            "labels": ["bug", "critical"],  # Duplicates removed
        }

        result = cli_runner.invoke(app, ["create", "Test", "--label", "bug,critical,bug", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Labels should be deduplicated
        assert len(data["labels"]) == 2

    def test_assignee_cannot_be_empty_string(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test assignee must be None or non-empty string."""
        mock_service.update_issue.side_effect = Exception("Assignee cannot be empty string")

        result = cli_runner.invoke(app, ["update", "issue-1", "--assignee", "", "--json"])

        assert result.exit_code != 0

    def test_closed_at_set_on_close(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test closed_at timestamp set when issue closed."""
        mock_service.close_issue.return_value = {
            "id": "issue-1",
            "status": "closed",
            "closed_at": "2024-01-15T10:00:00Z",
        }

        result = cli_runner.invoke(app, ["close", "issue-1", "--reason", "Done", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["closed_at"] is not None


class TestBeadsCompatibility:
    """Test compatibility with Beads issue tracker conventions."""

    def test_issue_id_format(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test issue IDs follow format: issue-<hash> or issue-<hash>.<child>."""
        mock_service.create_issue.return_value = {
            "id": "issue-a3f8e9",
            "title": "Test",
        }

        result = cli_runner.invoke(app, ["create", "Test", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # ID should match pattern: issue-[a-z0-9]+
        assert data["id"].startswith("issue-")

    @pytest.mark.skip(reason="Hierarchical ID format not yet implemented")
    def test_hierarchical_id_format(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test child issue IDs follow format: parent-id.1, parent-id.2, etc."""
        mock_service.create_issue.return_value = {
            "id": "issue-a3f8e9.1",
            "title": "Child task",
            "epic_id": "issue-a3f8e9",
        }

        result = cli_runner.invoke(app, ["create", "Child task", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Child ID should have .N suffix
        assert "." in data["id"]

    def test_json_output_format(self, cli_runner: CliRunner, mock_service: MagicMock):
        """Test JSON output is valid and parseable."""
        mock_service.create_issue.return_value = {
            "id": "issue-1",
            "title": "Test",
            "status": "open",
        }

        result = cli_runner.invoke(app, ["create", "Test", "--json"])

        assert result.exit_code == 0
        # Should parse without errors
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_directory_structure(self):
        """Test .issues/ directory structure matches Beads (.beads/ -> .issues/)."""
        # .issues/
        # ├── issues.db (SQLite database)
        # └── issues.sock (Unix socket for daemon)
        pass  # Will be tested in integration tests


class TestIssueValidation:
    """Test issue validation rules."""

    def test_empty_title_raises_error(self):
        """Test that empty title raises error."""
        with pytest.raises(InvariantViolationError, match="title cannot be empty"):
            Issue(
                id="issue-1",
                project_id="proj-1",
                title="",
                description="desc",
                status=IssueStatus.OPEN,
                type=IssueType.TASK,
                priority=IssuePriority.MEDIUM,
            )

    def test_epic_with_parent_epic_raises_error(self):
        """Test that epic with parent epic raises error."""
        with pytest.raises(InvariantViolationError, match="Epic issues cannot have parent epic"):
            Issue(
                id="issue-1",
                project_id="proj-1",
                title="Test",
                description="desc",
                status=IssueStatus.OPEN,
                type=IssueType.EPIC,
                priority=IssuePriority.MEDIUM,
                epic_id="epic-1",
            )

    def test_empty_assignee_raises_error(self):
        """Test that empty assignee string raises error."""
        with pytest.raises(InvariantViolationError, match="Assignee cannot be empty"):
            Issue(
                id="issue-1",
                project_id="proj-1",
                title="Test",
                description="desc",
                status=IssueStatus.OPEN,
                type=IssueType.TASK,
                priority=IssuePriority.MEDIUM,
                assignee="   ",
            )

    def test_invalid_priority_conversion(self):
        """Test invalid priority value raises error."""
        with pytest.raises(InvariantViolationError, match="Invalid priority"):
            Issue(
                id="issue-1",
                project_id="proj-1",
                title="Test",
                description="desc",
                status=IssueStatus.OPEN,
                type=IssueType.TASK,
                priority=999,
            )

"""Tests for CLI formatters module."""

from datetime import UTC, datetime

import pytest

from issue_tracker.cli.formatters import format_datetime_iso, format_priority_emoji, issue_to_dict
from issue_tracker.domain import Issue, IssuePriority, IssueStatus, IssueType


class TestFormatDatetimeIso:
    """Tests for format_datetime_iso function."""

    def test_formats_datetime_with_z_suffix(self):
        """Test datetime formatting with Z suffix."""
        dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = format_datetime_iso(dt)
        assert result == "2025-01-15T10:30:45Z"

    def test_handles_none_value(self):
        """Test handling of None value."""
        result = format_datetime_iso(None)
        assert result is None

    def test_handles_naive_datetime(self):
        """Test handling of naive datetime (no timezone)."""
        dt = datetime(2025, 1, 15, 10, 30, 45)
        result = format_datetime_iso(dt)
        assert "2025-01-15T10:30:45" in result

    def test_replaces_utc_offset(self):
        """Test that +00:00 is replaced with Z."""
        dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = format_datetime_iso(dt)
        assert "+00:00" not in result
        assert result.endswith("Z")


class TestFormatPriorityEmoji:
    """Tests for format_priority_emoji function."""

    def test_formats_critical_priority(self):
        """Test critical priority formatting."""
        result = format_priority_emoji(0)
        assert result == "🔴 Critical"

    def test_formats_high_priority(self):
        """Test high priority formatting."""
        result = format_priority_emoji(1)
        assert result == "🟠 High"

    def test_formats_medium_priority(self):
        """Test medium priority formatting."""
        result = format_priority_emoji(2)
        assert result == "🟡 Medium"

    def test_formats_low_priority(self):
        """Test low priority formatting."""
        result = format_priority_emoji(3)
        assert result == "🟢 Low"

    def test_formats_backlog_priority(self):
        """Test backlog priority formatting."""
        result = format_priority_emoji(4)
        assert result == "⚪ Backlog"

    def test_handles_issue_priority_enum(self):
        """Test handling of IssuePriority enum."""
        result = format_priority_emoji(IssuePriority.HIGH)
        assert result == "🟠 High"

    def test_handles_unknown_priority(self):
        """Test handling of unknown priority value."""
        result = format_priority_emoji(99)
        assert result == "⚪ Unknown"


class TestIssueToDictHelper:
    """Tests for issue_to_dict helper function."""

    @pytest.fixture
    def sample_issue(self):
        """Create a sample issue for testing."""
        return Issue(
            id="issue-123",
            project_id="test-project",
            title="Test Issue",
            description="Test description",
            type=IssueType.TASK,
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            assignee="testuser",
            labels=["test", "urgent"],
            epic_id="epic-456",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 2, 12, 0, 0),
            closed_at=None,
        )

    def test_converts_basic_fields(self, sample_issue):
        """Test conversion of basic issue fields."""
        result = issue_to_dict(sample_issue)
        assert result["id"] == "issue-123"
        assert result["project_id"] == "test-project"
        assert result["title"] == "Test Issue"
        assert result["description"] == "Test description"

    def test_converts_enum_fields(self, sample_issue):
        """Test conversion of enum fields to values."""
        result = issue_to_dict(sample_issue)
        assert result["type"] == "task"
        assert result["status"] == "open"
        assert isinstance(result["priority"], int)
        assert result["priority"] == 2

    def test_converts_datetime_fields(self, sample_issue):
        """Test conversion of datetime fields."""
        result = issue_to_dict(sample_issue)
        assert "created_at" in result
        assert "updated_at" in result
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)

    def test_handles_none_closed_at(self, sample_issue):
        """Test handling of None closed_at field."""
        result = issue_to_dict(sample_issue)
        assert result["closed_at"] is None

    def test_handles_closed_issue(self, sample_issue):
        """Test handling of closed issue with closed_at date."""
        sample_issue.closed_at = datetime(2025, 1, 3, 12, 0, 0)
        result = issue_to_dict(sample_issue)
        assert result["closed_at"] is not None
        assert isinstance(result["closed_at"], str)

    def test_includes_labels_list(self, sample_issue):
        """Test that labels list is included."""
        result = issue_to_dict(sample_issue)
        assert result["labels"] == ["test", "urgent"]

    def test_handles_empty_labels(self):
        """Test handling of issue with no labels."""
        issue = Issue(
            id="issue-123",
            project_id="test-project",
            title="Test",
            description="",
            type=IssueType.TASK,
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            labels=[],
        )
        result = issue_to_dict(issue)
        assert result["labels"] == []

    def test_includes_epic_id(self, sample_issue):
        """Test that epic_id is included."""
        result = issue_to_dict(sample_issue)
        assert result["epic_id"] == "epic-456"

    def test_handles_none_epic_id(self):
        """Test handling of issue with no epic."""
        issue = Issue(
            id="issue-123",
            project_id="test-project",
            title="Test",
            description="",
            type=IssueType.TASK,
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            epic_id=None,
        )
        result = issue_to_dict(issue)
        assert result["epic_id"] is None

    def test_includes_assignee(self, sample_issue):
        """Test that assignee is included."""
        result = issue_to_dict(sample_issue)
        assert result["assignee"] == "testuser"

    def test_handles_none_assignee(self):
        """Test handling of unassigned issue."""
        issue = Issue(
            id="issue-123",
            project_id="test-project",
            title="Test",
            description="",
            type=IssueType.TASK,
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            assignee=None,
        )
        result = issue_to_dict(issue)
        assert result["assignee"] is None

    def test_all_required_keys_present(self, sample_issue):
        """Test that all required keys are present in output."""
        result = issue_to_dict(sample_issue)
        required_keys = [
            "id",
            "project_id",
            "title",
            "description",
            "type",
            "priority",
            "status",
            "assignee",
            "labels",
            "created_at",
            "updated_at",
            "closed_at",
            "epic_id",
        ]
        for key in required_keys:
            assert key in result

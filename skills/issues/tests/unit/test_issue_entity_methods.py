"""Tests for Issue entity additional methods."""

import pytest
from datetime import UTC, datetime

from issue_tracker.domain.entities.issue import Issue, IssueStatus, IssueType
from issue_tracker.domain.value_objects import IssuePriority
from issue_tracker.domain.exceptions import InvariantViolationError


class TestIssueAssignment:
    """Test issue assignment methods."""

    def test_assign_issue_empty_string(self) -> None:
        """Test assigning issue to empty string raises error."""
        issue = Issue(
            id="ISS-001",
            project_id="PRJ-001",
            title="Test",
            description="Test",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        with pytest.raises(InvariantViolationError, match="empty string"):
            issue.assign_to(user_id="   ")

    def test_assign_issue_with_whitespace(self) -> None:
        """Test assigning issue trims whitespace."""
        issue = Issue(
            id="ISS-001",
            project_id="PRJ-001",
            title="Test",
            description="Test",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        updated = issue.assign_to(user_id="  user123  ")
        assert updated.assignee == "user123"

    def test_assign_to_epic_on_epic_fails(self) -> None:
        """Test that epic issues cannot be assigned to another epic."""
        epic = Issue(
            id="EPIC-001",
            project_id="PRJ-001",
            title="Epic",
            description="Epic",
            status=IssueStatus.OPEN,
            priority=IssuePriority.HIGH,
            type=IssueType.EPIC,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        with pytest.raises(InvariantViolationError, match="Cannot set epic"):
            epic.assign_to_epic("EPIC-002")

    def test_assign_to_epic_success(self) -> None:
        """Test assigning task to epic."""
        issue = Issue(
            id="ISS-001",
            project_id="PRJ-001",
            title="Test",
            description="Test",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        updated = issue.assign_to_epic("EPIC-001")
        assert updated.epic_id == "EPIC-001"

"""Comprehensive issue entity tests."""

import pytest
from datetime import datetime
from issue_tracker.domain.entities.issue import Issue, IssueStatus, IssuePriority, IssueType
from issue_tracker.domain.exceptions import InvariantViolationError


def test_issue_metadata():
    """Test issue with labels as metadata."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        labels=["custom", "value"]
    )
    assert "custom" in issue.labels
    assert "value" in issue.labels


def test_issue_with_timestamps():
    """Test issue with custom timestamps."""
    now = datetime.now()
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        created_at=now,
        updated_at=now
    )
    assert issue.created_at == now
    assert issue.updated_at == now


def test_issue_label_trimming():
    """Test label gets trimmed when added."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
    )
    updated = issue.add_label("  bug  ")
    assert "bug" in updated.labels


def test_issue_remove_nonexistent_label():
    """Test removing non-existent label."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        labels=["existing"]
    )
    updated = issue.remove_label("nonexistent")
    assert "existing" in updated.labels


def test_issue_type_feature():
    """Test feature type issue."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.FEATURE,
        priority=IssuePriority.MEDIUM,
    )
    assert issue.type == IssueType.FEATURE


def test_issue_type_bug():
    """Test bug type issue."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.BUG,
        priority=IssuePriority.MEDIUM,
    )
    assert issue.type == IssueType.BUG


def test_issue_priority_lowest():
    """Test LOWEST priority."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.BACKLOG,
    )
    assert issue.priority == IssuePriority.BACKLOG


def test_issue_priority_critical():
    """Test CRITICAL priority."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.CRITICAL,
    )
    assert issue.priority == IssuePriority.CRITICAL


def test_issue_closed_with_timestamp():
    """Test closed issue with closed_at timestamp."""
    closed_at = datetime.now()
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.CLOSED,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        closed_at=closed_at
    )
    assert issue.closed_at == closed_at


def test_issue_transition_archived():
    """Test transitioning to ARCHIVED status."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.CLOSED,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
    )
    updated = issue.transition(IssueStatus.ARCHIVED)
    assert updated.status == IssueStatus.ARCHIVED


def test_issue_transition_from_archived_to_open():
    """Test restoring from archive."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.ARCHIVED,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        closed_at=datetime.now()
    )
    updated = issue.transition(IssueStatus.OPEN)
    assert updated.status == IssueStatus.OPEN
    assert updated.closed_at is None


def test_issue_with_epic_id():
    """Test issue with epic_id."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        epic_id="epic-1"
    )
    assert issue.epic_id == "epic-1"


def test_issue_with_assignee():
    """Test issue with assignee."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        assignee="user1"
    )
    assert issue.assignee == "user1"


def test_issue_whitespace_title_raises_error():
    """Test whitespace title raises error."""
    with pytest.raises(InvariantViolationError, match="title cannot be empty"):
        Issue(
            id="issue-1",
            project_id="proj-1",
            title="   ",
            description="desc",
            status=IssueStatus.OPEN,
            type=IssueType.TASK,
            priority=IssuePriority.MEDIUM,
        )

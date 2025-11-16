"""Additional tests for 70% coverage."""

import pytest

from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.epic import Epic, EpicStatus
from issue_tracker.domain.entities.issue import Issue, IssuePriority, IssueStatus, IssueType
from issue_tracker.domain.entities.label import Label
from issue_tracker.domain.exceptions import InvariantViolationError


def test_issue_add_label_single():
    """Test adding a single label."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        labels=[],
    )
    updated = issue.add_label("bug")
    assert "bug" in updated.labels


def test_issue_add_label_duplicate():
    """Test adding duplicate label is idempotent."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        labels=["bug"],
    )
    updated = issue.add_label("bug")
    assert updated.labels.count("bug") == 1


def test_issue_remove_label_single():
    """Test removing a single label."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        labels=["bug", "feature"],
    )
    updated = issue.remove_label("bug")
    assert "bug" not in updated.labels
    assert "feature" in updated.labels


def test_issue_add_empty_label_raises_error():
    """Test adding empty label raises error."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
    )
    with pytest.raises(InvariantViolationError, match="Label cannot be empty"):
        issue.add_label("")


def test_issue_add_whitespace_label_raises_error():
    """Test adding whitespace label raises error."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
    )
    with pytest.raises(InvariantViolationError, match="Label cannot be empty"):
        issue.add_label("   ")


def test_issue_transition_to_done():
    """Test transitioning to DONE status."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.IN_PROGRESS,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
    )
    # Must transition through RESOLVED to reach CLOSED
    resolved = issue.transition(IssueStatus.RESOLVED)
    updated = resolved.transition(IssueStatus.CLOSED)
    assert updated.status == IssueStatus.CLOSED


def test_dependency_blocked_by():
    """Test BLOCKS dependency type."""
    dep = Dependency(from_issue_id="issue-1", to_issue_id="issue-2", dependency_type=DependencyType.BLOCKS)
    assert dep.dependency_type == DependencyType.BLOCKS


def test_dependency_relates_to():
    """Test RELATED_TO dependency type."""
    dep = Dependency(from_issue_id="issue-1", to_issue_id="issue-2", dependency_type=DependencyType.RELATED_TO)
    assert dep.dependency_type == DependencyType.RELATED_TO


def test_epic_all_statuses():
    """Test all epic statuses."""
    statuses = [EpicStatus.OPEN, EpicStatus.IN_PROGRESS, EpicStatus.COMPLETED, EpicStatus.CLOSED]
    for status in statuses:
        epic = Epic(id=f"epic-{status.value}", title="Test", status=status)
        assert epic.status == status


def test_label_minimal():
    """Test label with minimal fields."""
    label = Label(id="label-1", name="test")
    assert label.name == "test"
    assert label.color is None
    assert label.description is None

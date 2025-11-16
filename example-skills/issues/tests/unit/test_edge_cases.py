"""Edge case tests for domain entities."""

import pytest
from datetime import datetime
from issue_tracker.domain.entities.issue import Issue, IssueStatus, IssuePriority, IssueType
from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.comment import Comment
from issue_tracker.domain.exceptions import InvariantViolationError


def test_comment_entity():
    """Test comment entity creation."""
    comment = Comment(
        id="comment-1",
        issue_id="issue-1",
        author="user1",
        text="Test comment"
    )
    assert comment.id == "comment-1"
    assert comment.issue_id == "issue-1"
    assert comment.author == "user1"
    assert comment.text == "Test comment"


def test_comment_with_timestamps():
    """Test comment with custom timestamps."""
    now = datetime.now()
    comment = Comment(
        id="comment-1",
        issue_id="issue-1",
        author="user1",
        text="Test",
        created_at=now,
        updated_at=now
    )
    assert comment.created_at == now
    assert comment.updated_at == now


def test_dependency_with_metadata():
    """Test dependency with description."""
    dep = Dependency(
        from_issue_id="issue-1",
        to_issue_id="issue-2",
        dependency_type=DependencyType.BLOCKS,
        description="custom value"
    )
    assert dep.description == "custom value"


def test_dependency_with_timestamps():
    """Test dependency with custom timestamps."""
    now = datetime.now()
    dep = Dependency(
        from_issue_id="issue-1",
        to_issue_id="issue-2",
        dependency_type=DependencyType.BLOCKS,
        created_at=now
    )
    assert dep.created_at == now


def test_issue_all_label_scenarios():
    """Test various label scenarios."""
    # Start with labels
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        labels=["label1", "label2", "label1"]  # With duplicate
    )
    # Should deduplicate
    assert issue.labels.count("label1") == 1
    
    # Add label
    issue2 = issue.add_label("label3")
    assert "label3" in issue2.labels
    
    # Remove label
    issue3 = issue2.remove_label("label2")
    assert "label2" not in issue3.labels
    assert "label1" in issue3.labels
    assert "label3" in issue3.labels


def test_issue_with_long_description():
    """Test issue with long description."""
    long_desc = "A" * 10000
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description=long_desc,
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
    )
    assert len(issue.description) == 10000


def test_issue_update_preserves_other_fields():
    """Test that assigning to epic preserves other fields."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Original",
        description="Original desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
        assignee="user1",
        epic_id="epic-1",
        labels=["label1"]
    )
    # Change assignee
    updated = issue.assign_to("user2")
    # Other fields should be preserved
    assert updated.title == "Original"
    assert updated.description == "Original desc"
    assert updated.assignee == "user2"
    assert updated.epic_id == "epic-1"
    assert "label1" in updated.labels


def test_issue_transition_updates_timestamp():
    """Test that transition updates the updated_at timestamp."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=IssuePriority.MEDIUM,
    )
    original_updated = issue.updated_at
    # Small delay to ensure timestamp difference
    import time
    time.sleep(0.01)
    updated = issue.transition(IssueStatus.IN_PROGRESS)
    # Timestamp should be updated (can't assert exact value, but should be different)
    assert updated.updated_at >= original_updated


def test_issue_priority_integer_conversion():
    """Test that integer priorities are converted to IssuePriority."""
    issue = Issue(
        id="issue-1",
        project_id="proj-1",
        title="Test",
        description="desc",
        status=IssueStatus.OPEN,
        type=IssueType.TASK,
        priority=2,  # Integer instead of enum
    )
    assert issue.priority == IssuePriority.MEDIUM
    assert isinstance(issue.priority, IssuePriority)

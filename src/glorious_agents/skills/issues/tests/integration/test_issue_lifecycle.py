"""Integration tests for complete issue lifecycle workflows."""

import pytest
from sqlmodel import Session

from issue_tracker.adapters.db.unit_of_work import UnitOfWork
from issue_tracker.adapters.services import HashIdentifierService, SystemClock
from issue_tracker.domain.entities.dependency import DependencyType
from issue_tracker.domain.entities.issue import IssueStatus, IssueType
from issue_tracker.domain.value_objects import IssuePriority
from issue_tracker.services.issue_graph_service import IssueGraphService
from issue_tracker.services.issue_service import IssueService


@pytest.fixture
def issue_service(test_session: Session) -> IssueService:
    """Create an IssueService with real dependencies."""
    uow = UnitOfWork(test_session)
    id_service = HashIdentifierService()
    clock = SystemClock()
    return IssueService(uow, id_service, clock)


@pytest.fixture
def graph_service(test_session: Session) -> IssueGraphService:
    """Create an IssueGraphService with real dependencies."""
    uow = UnitOfWork(test_session)
    return IssueGraphService(uow)


class TestIssueLifecycleWorkflows:
    """Test complete issue lifecycle workflows."""

    def test_create_modify_close_reopen(self, issue_service: IssueService) -> None:
        """Test full lifecycle: create → modify → close → reopen."""
        # Create issue
        issue = issue_service.create_issue(
            title="Test issue",
            description="Initial description",
            priority=IssuePriority.HIGH,
        )
        assert issue.id is not None
        assert issue.status == IssueStatus.OPEN
        assert issue.priority == IssuePriority.HIGH

        # Modify issue
        updated = issue_service.update_issue(
            issue.id,
            title="Updated title",
            description="Updated description",
        )
        assert updated is not None
        assert updated.title == "Updated title"
        assert updated.description == "Updated description"

        # Transition through valid states
        in_progress = issue_service.transition_issue(issue.id, IssueStatus.IN_PROGRESS)
        assert in_progress is not None
        assert in_progress.status == IssueStatus.IN_PROGRESS

        resolved = issue_service.transition_issue(issue.id, IssueStatus.RESOLVED)
        assert resolved is not None
        assert resolved.status == IssueStatus.RESOLVED

        closed = issue_service.close_issue(issue.id)
        assert closed is not None
        assert closed.status == IssueStatus.CLOSED
        assert closed.closed_at is not None

        # Reopen issue
        reopened = issue_service.reopen_issue(issue.id)
        assert reopened is not None
        assert reopened.status == IssueStatus.OPEN
        assert reopened.closed_at is None

    def test_add_labels_workflow(self, issue_service: IssueService) -> None:
        """Test issue creation with labels parameter."""
        # Note: Labels are stored in separate junction table (issue_labels)
        # and require additional repository logic not yet fully implemented.
        # For now, just test issue creation works with labels param.
        issue = issue_service.create_issue(
            title="Test issue",
            labels=["initial", "bug", "urgent"],
        )
        assert issue.id is not None
        assert issue.title == "Test issue"

        # Verify issue persisted
        retrieved = issue_service.get_issue(issue.id)
        assert retrieved is not None
        assert retrieved.title == "Test issue"

    def test_set_epic_relationship(self, issue_service: IssueService) -> None:
        """Test setting epic relationship."""
        # Create epic
        epic = issue_service.create_issue(
            title="Epic issue",
            issue_type=IssueType.EPIC,
        )
        assert epic.type == IssueType.EPIC

        # Create regular issue
        issue = issue_service.create_issue(
            title="Child issue",
            issue_type=IssueType.TASK,
        )

        # Link to epic
        updated = issue_service.update_issue(
            issue.id,
            epic_id=epic.id,
        )
        assert updated is not None
        assert updated.epic_id == epic.id

        # List issues by epic
        epic_issues = issue_service.list_issues(epic_id=epic.id)
        assert len(epic_issues) == 1
        assert epic_issues[0].id == issue.id


class TestDependencyWorkflows:
    """Test dependency management workflows."""

    def test_create_dependencies_and_check_cycles(
        self, issue_service: IssueService, graph_service: IssueGraphService
    ) -> None:
        """Test creating dependencies and cycle detection."""
        # Create issues
        issue1 = issue_service.create_issue(title="Issue 1")
        issue2 = issue_service.create_issue(title="Issue 2")
        issue3 = issue_service.create_issue(title="Issue 3")

        # Add valid dependencies: 1 -> 2 -> 3
        dep1 = issue_service.add_dependency(issue1.id, issue2.id, DependencyType.BLOCKS)
        assert dep1 is not None

        dep2 = issue_service.add_dependency(issue2.id, issue3.id, DependencyType.BLOCKS)
        assert dep2 is not None

        # Try to create cycle: 3 -> 1 (should fail)
        dep3 = issue_service.add_dependency(issue3.id, issue1.id, DependencyType.BLOCKS)
        assert dep3 is None  # Cycle rejected

        # Verify no cycles exist
        cycles = graph_service.detect_cycles()
        assert len(cycles) == 0

        # Get blockers
        blockers = issue_service.get_blockers(issue3.id)
        assert len(blockers) == 1
        assert blockers[0] == issue2.id

    def test_dependency_chain_and_ready_queue(
        self, issue_service: IssueService, graph_service: IssueGraphService
    ) -> None:
        """Test dependency chain and ready queue calculation."""
        # Create chain: issue1 -> issue2 -> issue3
        issue1 = issue_service.create_issue(title="Issue 1")
        issue2 = issue_service.create_issue(title="Issue 2")
        issue3 = issue_service.create_issue(title="Issue 3")

        issue_service.add_dependency(issue1.id, issue2.id, DependencyType.BLOCKS)
        issue_service.add_dependency(issue2.id, issue3.id, DependencyType.BLOCKS)

        # Get dependency chain
        chain = graph_service.get_dependency_chain(issue1.id, issue3.id)
        assert len(chain) >= 2

        # Initially only issue1 is ready (no blockers)
        ready = graph_service.get_ready_queue()
        ready_ids = [issue.id for issue in ready]
        assert issue1.id in ready_ids
        assert issue2.id not in ready_ids  # Blocked by issue1

        # Close issue1, now issue2 should be ready
        # Transition through valid states: IN_PROGRESS -> RESOLVED -> CLOSED
        issue_service.transition_issue(issue1.id, IssueStatus.IN_PROGRESS)
        issue_service.transition_issue(issue1.id, IssueStatus.RESOLVED)
        issue_service.close_issue(issue1.id)

        ready2 = graph_service.get_ready_queue()
        ready_ids2 = [issue.id for issue in ready2]
        assert issue2.id in ready_ids2

    def test_remove_dependency(self, issue_service: IssueService, graph_service: IssueGraphService) -> None:
        """Test removing dependencies."""
        # Create issues with dependency
        issue1 = issue_service.create_issue(title="Issue 1")
        issue2 = issue_service.create_issue(title="Issue 2")

        issue_service.add_dependency(issue1.id, issue2.id, DependencyType.BLOCKS)

        # Verify dependency exists
        blockers = issue_service.get_blockers(issue2.id)
        assert len(blockers) == 1

        # Remove dependency (must specify same type as when added)
        result = issue_service.remove_dependency(issue1.id, issue2.id, DependencyType.BLOCKS)
        # Service should return True on success
        assert result is True

        # Verify dependency removed
        blockers2 = issue_service.get_blockers(issue2.id)
        assert len(blockers2) == 0


class TestCommentWorkflows:
    """Test comment management workflows."""

    def test_add_and_list_comments(self, issue_service: IssueService) -> None:
        """Test adding and listing comments."""
        # Create issue
        issue = issue_service.create_issue(title="Test issue")

        # Add comments
        comment1 = issue_service.add_comment(
            issue.id,
            author="user1",
            text="First comment",
        )
        assert comment1 is not None
        assert comment1.text == "First comment"

        comment2 = issue_service.add_comment(
            issue.id,
            author="user2",
            text="Second comment",
        )
        assert comment2 is not None

        # List comments
        comments = issue_service.list_comments(issue.id)
        assert len(comments) == 2
        assert comments[0].text == "First comment"
        assert comments[1].text == "Second comment"

    def test_comment_on_nonexistent_issue(self, issue_service: IssueService) -> None:
        """Test adding comment to nonexistent issue."""
        comment = issue_service.add_comment(
            "nonexistent-id",
            author="user1",
            text="Comment",
        )
        assert comment is None


class TestBulkOperations:
    """Test bulk operations and filtering."""

    def test_list_by_status(self, issue_service: IssueService) -> None:
        """Test filtering issues by status."""
        # Create issues with different statuses
        issue_service.create_issue(title="Open issue 1")
        issue_service.create_issue(title="Open issue 2")
        issue3 = issue_service.create_issue(title="In progress issue")

        issue_service.transition_issue(issue3.id, IssueStatus.IN_PROGRESS)

        # List open issues (should be 2, not counting in_progress)
        open_issues = issue_service.list_issues(status=IssueStatus.OPEN)
        assert len(open_issues) >= 2  # At least these 2 from this test

        # List in-progress issues
        in_progress = issue_service.list_issues(status=IssueStatus.IN_PROGRESS)
        assert len(in_progress) == 1
        assert in_progress[0].id == issue3.id

    def test_list_by_priority(self, issue_service: IssueService) -> None:
        """Test filtering issues by priority."""
        # Create issues with different priorities
        issue_service.create_issue(title="High 1", priority=IssuePriority.HIGH)
        issue_service.create_issue(title="High 2", priority=IssuePriority.HIGH)
        issue_service.create_issue(title="Low", priority=IssuePriority.LOW)

        # List high priority issues
        high_issues = issue_service.list_issues(priority=IssuePriority.HIGH)
        assert len(high_issues) == 2

        # List low priority issues
        low_issues = issue_service.list_issues(priority=IssuePriority.LOW)
        assert len(low_issues) == 1

    def test_list_by_assignee(self, issue_service: IssueService) -> None:
        """Test filtering issues by assignee."""
        # Create issues with different assignees
        issue_service.create_issue(title="User1 task 1", assignee="user1")
        issue_service.create_issue(title="User1 task 2", assignee="user1")
        issue_service.create_issue(title="User2 task", assignee="user2")

        # List user1's issues
        user1_issues = issue_service.list_issues(assignee="user1")
        assert len(user1_issues) == 2

        # List user2's issues
        user2_issues = issue_service.list_issues(assignee="user2")
        assert len(user2_issues) == 1

    def test_list_by_type(self, issue_service: IssueService) -> None:
        """Test filtering issues by type."""
        # Create issues with different types
        issue_service.create_issue(title="Bug 1", issue_type=IssueType.BUG)
        issue_service.create_issue(title="Bug 2", issue_type=IssueType.BUG)
        issue_service.create_issue(title="Feature", issue_type=IssueType.FEATURE)

        # List bugs
        bugs = issue_service.list_issues(issue_type=IssueType.BUG)
        assert len(bugs) == 2

        # List features
        features = issue_service.list_issues(issue_type=IssueType.FEATURE)
        assert len(features) == 1

    def test_delete_issue(self, issue_service: IssueService) -> None:
        """Test deleting an issue."""
        # Create issue
        issue = issue_service.create_issue(title="To delete")

        # Delete issue
        deleted = issue_service.delete_issue(issue.id)
        assert deleted is True

        # Verify issue is gone
        retrieved = issue_service.get_issue(issue.id)
        assert retrieved is None


class TestComplexScenarios:
    """Test complex multi-step scenarios."""

    def test_epic_with_dependencies(self, issue_service: IssueService, graph_service: IssueGraphService) -> None:
        """Test epic with dependent tasks."""
        # Create epic
        epic = issue_service.create_issue(
            title="Feature epic",
            issue_type=IssueType.EPIC,
        )

        # Create tasks in epic with dependencies
        task1 = issue_service.create_issue(
            title="Setup task",
            issue_type=IssueType.TASK,
            epic_id=epic.id,
        )
        task2 = issue_service.create_issue(
            title="Implementation task",
            issue_type=IssueType.TASK,
            epic_id=epic.id,
        )
        task3 = issue_service.create_issue(
            title="Testing task",
            issue_type=IssueType.TASK,
            epic_id=epic.id,
        )

        # Create dependency chain
        issue_service.add_dependency(task1.id, task2.id, DependencyType.BLOCKS)
        issue_service.add_dependency(task2.id, task3.id, DependencyType.BLOCKS)

        # List epic tasks
        epic_tasks = issue_service.list_issues(epic_id=epic.id)
        assert len(epic_tasks) == 3

        # Build dependency tree from first task
        tree = graph_service.build_dependency_tree(task1.id)
        assert tree["issue"].id == task1.id
        assert len(tree["dependencies"]) == 1

    def test_multiple_dependency_types(self, issue_service: IssueService, graph_service: IssueGraphService) -> None:
        """Test multiple dependency types between issues."""
        # Create issues
        issue1 = issue_service.create_issue(title="Issue 1")
        issue2 = issue_service.create_issue(title="Issue 2")

        # Add different dependency types
        dep1 = issue_service.add_dependency(issue1.id, issue2.id, DependencyType.BLOCKS)
        assert dep1 is not None

        dep2 = issue_service.add_dependency(issue1.id, issue2.id, DependencyType.RELATED_TO)
        assert dep2 is not None

        # Get all dependencies
        deps = graph_service.get_dependencies(issue1.id)
        assert len(deps) == 2
        dep_types = {dep.dependency_type for dep in deps}
        assert DependencyType.BLOCKS in dep_types
        assert DependencyType.RELATED_TO in dep_types

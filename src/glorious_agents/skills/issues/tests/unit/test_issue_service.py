"""Unit tests for IssueService with mocked repositories."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from issue_tracker.domain.entities.comment import Comment
from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.issue import Issue, IssuePriority, IssueStatus, IssueType
from issue_tracker.services.issue_service import IssueService

# Test constants
TEST_PROJECT_ID = "PRJ-TEST"
TEST_TIMESTAMP = datetime(2025, 11, 11, 12, 0, 0, tzinfo=UTC).replace(tzinfo=None)


@pytest.fixture
def mock_uow() -> Mock:
    """Create a mock UnitOfWork."""
    uow = Mock()
    uow.issues = Mock()
    uow.graph = Mock()
    uow.comments = Mock()
    return uow


@pytest.fixture
def mock_id_service() -> Mock:
    """Create a mock IdentifierService."""
    service = Mock()
    service.generate = Mock(side_effect=lambda prefix: f"{prefix}-MOCK123")
    return service


@pytest.fixture
def mock_clock() -> Mock:
    """Create a mock Clock."""
    clock = Mock()
    clock.now = Mock(return_value=TEST_TIMESTAMP)
    return clock


@pytest.fixture
def issue_service(mock_uow: Mock, mock_id_service: Mock, mock_clock: Mock) -> IssueService:
    """Create IssueService with mocked dependencies."""
    return IssueService(mock_uow, mock_id_service, mock_clock)


@pytest.fixture
def sample_issue() -> Issue:
    """Create a sample issue for testing."""
    return Issue(
        id="issue-TEST",
        project_id=TEST_PROJECT_ID,
        title="Test Issue",
        description="Test description",
        status=IssueStatus.OPEN,
        priority=IssuePriority.MEDIUM,
        type=IssueType.TASK,
        created_at=TEST_TIMESTAMP,
        updated_at=TEST_TIMESTAMP,
    )


class TestIssueServiceCRUD:
    """Test CRUD operations."""

    def test_create_issue_minimal(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test creating an issue with minimal parameters."""
        mock_uow.issues.save = Mock(side_effect=lambda issue: issue)

        result = issue_service.create_issue("Test Title")

        assert result.id == "issue-MOCK123"
        assert result.title == "Test Title"
        assert result.status == IssueStatus.OPEN
        assert result.priority == IssuePriority.MEDIUM
        assert result.type == IssueType.TASK
        assert result.created_at == TEST_TIMESTAMP
        assert result.updated_at == TEST_TIMESTAMP
        mock_uow.issues.save.assert_called_once()

    def test_create_issue_with_custom_id(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test creating an issue with a custom ID."""
        mock_uow.issues.get = Mock(return_value=None)
        mock_uow.issues.save = Mock(side_effect=lambda issue: issue)

        result = issue_service.create_issue("Test Title", custom_id="CUSTOM-123")

        assert result.id == "CUSTOM-123"
        mock_uow.issues.get.assert_called_once_with("CUSTOM-123")

    def test_create_issue_duplicate_custom_id(
        self, issue_service: IssueService, mock_uow: Mock, sample_issue: Issue
    ) -> None:
        """Test creating an issue with duplicate custom ID raises ValueError."""
        mock_uow.issues.get = Mock(return_value=sample_issue)

        with pytest.raises(ValueError, match="already exists"):
            issue_service.create_issue("Test Title", custom_id="issue-TEST")

    def test_create_issue_with_all_fields(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test creating an issue with all optional fields."""
        mock_uow.issues.save = Mock(side_effect=lambda issue: issue)

        result = issue_service.create_issue(
            title="Full Issue",
            description="Complete description",
            priority=IssuePriority.HIGH,
            issue_type=IssueType.BUG,
            assignee="user123",
            epic_id="epic-001",
            labels=["urgent", "frontend"],
            project_id=TEST_PROJECT_ID,
        )

        assert result.title == "Full Issue"
        assert result.description == "Complete description"
        assert result.priority == IssuePriority.HIGH
        assert result.type == IssueType.BUG
        assert result.assignee == "user123"
        assert result.epic_id == "epic-001"
        assert result.labels == ["urgent", "frontend"]
        assert result.project_id == TEST_PROJECT_ID

    def test_get_issue_found(self, issue_service: IssueService, mock_uow: Mock, sample_issue: Issue) -> None:
        """Test getting an existing issue."""
        mock_uow.issues.get = Mock(return_value=sample_issue)

        result = issue_service.get_issue("issue-TEST")

        assert result == sample_issue
        mock_uow.issues.get.assert_called_once_with("issue-TEST")

    def test_get_issue_not_found(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test getting a non-existent issue."""
        mock_uow.issues.get = Mock(return_value=None)

        result = issue_service.get_issue("nonexistent")

        assert result is None

    def test_update_issue(self, issue_service: IssueService, mock_uow: Mock, sample_issue: Issue) -> None:
        """Test updating an issue."""
        updated_issue = Issue(
            id=sample_issue.id,
            project_id=sample_issue.project_id,
            title="Updated Title",
            description="Updated description",
            status=sample_issue.status,
            priority=IssuePriority.HIGH,
            type=sample_issue.type,
            assignee="new-user",
            created_at=sample_issue.created_at,
            updated_at=TEST_TIMESTAMP,
        )

        mock_uow.issues.get = Mock(return_value=sample_issue)
        mock_uow.issues.save = Mock(return_value=updated_issue)

        result = issue_service.update_issue(
            "issue-TEST",
            title="Updated Title",
            description="Updated description",
            priority=IssuePriority.HIGH,
            assignee="new-user",
        )

        assert result is not None
        assert result.title == "Updated Title"
        assert result.priority == IssuePriority.HIGH
        assert result.assignee == "new-user"

    def test_update_nonexistent_issue(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test updating a non-existent issue returns None."""
        mock_uow.issues.get = Mock(return_value=None)

        result = issue_service.update_issue("nonexistent", title="New Title")

        assert result is None

    def test_delete_issue(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test deleting an issue."""
        mock_uow.issues.delete = Mock(return_value=True)

        result = issue_service.delete_issue("issue-TEST")

        assert result is True
        mock_uow.issues.delete.assert_called_once_with("issue-TEST")

    def test_delete_nonexistent_issue(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test deleting a non-existent issue."""
        mock_uow.issues.delete = Mock(return_value=False)

        result = issue_service.delete_issue("nonexistent")

        assert result is False


class TestIssueServiceStateTransitions:
    """Test issue state transition operations."""

    def test_transition_issue_valid(self, issue_service: IssueService, mock_uow: Mock, sample_issue: Issue) -> None:
        """Test valid state transition."""
        mock_uow.issues.get = Mock(return_value=sample_issue)
        transitioned = Issue(
            id=sample_issue.id,
            project_id=sample_issue.project_id,
            title=sample_issue.title,
            description=sample_issue.description,
            status=IssueStatus.IN_PROGRESS,
            priority=sample_issue.priority,
            type=sample_issue.type,
            created_at=sample_issue.created_at,
            updated_at=TEST_TIMESTAMP,
        )
        mock_uow.issues.save = Mock(return_value=transitioned)

        result = issue_service.transition_issue("issue-TEST", IssueStatus.IN_PROGRESS)

        assert result is not None
        assert result.status == IssueStatus.IN_PROGRESS

    def test_transition_nonexistent_issue(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test transitioning a non-existent issue."""
        mock_uow.issues.get = Mock(return_value=None)

        result = issue_service.transition_issue("nonexistent", IssueStatus.CLOSED)

        assert result is None

    def test_close_issue(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test closing an issue."""
        # Issue must be RESOLVED before it can be CLOSED
        resolved_issue = Issue(
            id="issue-TEST",
            project_id=TEST_PROJECT_ID,
            title="Test Issue",
            description="Test description",
            status=IssueStatus.RESOLVED,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            created_at=TEST_TIMESTAMP,
            updated_at=TEST_TIMESTAMP,
        )
        mock_uow.issues.get = Mock(return_value=resolved_issue)
        closed_issue = Issue(
            id=resolved_issue.id,
            project_id=resolved_issue.project_id,
            title=resolved_issue.title,
            description=resolved_issue.description,
            status=IssueStatus.CLOSED,
            priority=resolved_issue.priority,
            type=resolved_issue.type,
            created_at=resolved_issue.created_at,
            updated_at=TEST_TIMESTAMP,
            closed_at=TEST_TIMESTAMP,
        )
        mock_uow.issues.save = Mock(return_value=closed_issue)

        result = issue_service.close_issue("issue-TEST")

        assert result is not None
        assert result.status == IssueStatus.CLOSED
        assert result.closed_at == TEST_TIMESTAMP

    def test_reopen_issue(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test reopening a closed issue."""
        closed_issue = Issue(
            id="issue-TEST",
            project_id=TEST_PROJECT_ID,
            title="Test",
            description="Test",
            status=IssueStatus.CLOSED,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            created_at=TEST_TIMESTAMP,
            updated_at=TEST_TIMESTAMP,
            closed_at=TEST_TIMESTAMP,
        )
        mock_uow.issues.get = Mock(return_value=closed_issue)
        reopened = Issue(
            id=closed_issue.id,
            project_id=closed_issue.project_id,
            title=closed_issue.title,
            description=closed_issue.description,
            status=IssueStatus.OPEN,
            priority=closed_issue.priority,
            type=closed_issue.type,
            created_at=closed_issue.created_at,
            updated_at=TEST_TIMESTAMP,
            closed_at=None,
        )
        mock_uow.issues.save = Mock(return_value=reopened)

        result = issue_service.reopen_issue("issue-TEST")

        assert result is not None
        assert result.status == IssueStatus.OPEN
        assert result.closed_at is None

    def test_close_issue_not_found(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test closing a non-existent issue."""
        mock_uow.issues.get = Mock(return_value=None)

        result = issue_service.close_issue("nonexistent")

        assert result is None

    def test_reopen_issue_not_found(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test reopening a non-existent issue."""
        mock_uow.issues.get = Mock(return_value=None)

        result = issue_service.reopen_issue("nonexistent")

        assert result is None


class TestIssueServiceDependencies:
    """Test dependency management operations."""

    def test_add_dependency(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test adding a dependency between issues."""
        dep = Dependency(
            from_issue_id="issue-A",
            to_issue_id="issue-B",
            dependency_type=DependencyType.BLOCKS,
        )
        mock_uow.graph.has_cycle = Mock(return_value=False)
        mock_uow.graph.add_dependency = Mock(return_value=dep)

        result = issue_service.add_dependency("issue-A", "issue-B", DependencyType.BLOCKS)

        assert result == dep
        mock_uow.graph.has_cycle.assert_called_once_with("issue-A", "issue-B")
        mock_uow.graph.add_dependency.assert_called_once()

    def test_add_dependency_creates_cycle(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test that adding a dependency that creates a cycle is rejected."""
        mock_uow.graph.has_cycle = Mock(return_value=True)

        result = issue_service.add_dependency("issue-A", "issue-B", DependencyType.BLOCKS)

        assert result is None
        mock_uow.graph.has_cycle.assert_called_once_with("issue-A", "issue-B")
        mock_uow.graph.add_dependency.assert_not_called()

    def test_remove_dependency(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test removing a dependency."""
        mock_uow.graph.remove_dependency = Mock(return_value=True)

        result = issue_service.remove_dependency("issue-A", "issue-B", DependencyType.BLOCKS)

        assert result is True
        mock_uow.graph.remove_dependency.assert_called_once_with("issue-A", "issue-B", DependencyType.BLOCKS)

    def test_get_blockers(self, issue_service: IssueService, mock_uow: Mock, sample_issue: Issue) -> None:
        """Test getting issues that block a target issue."""
        mock_uow.graph.get_blockers = Mock(return_value=["issue-B1", "issue-B2"])

        result = issue_service.get_blockers("issue-TEST")

        assert len(result) == 2
        assert result[0] == "issue-B1"
        assert result[1] == "issue-B2"
        mock_uow.graph.get_blockers.assert_called_once_with("issue-TEST")

    def test_get_blocked_issues(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test getting issues blocked by a source issue."""
        mock_uow.graph.get_blocked_by = Mock(return_value=["issue-BK1"])

        result = issue_service.get_blocked_issues("issue-TEST")

        assert len(result) == 1
        assert result[0] == "issue-BK1"
        mock_uow.graph.get_blocked_by.assert_called_once_with("issue-TEST")


class TestIssueServiceComments:
    """Test comment management operations."""

    def test_add_comment(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test adding a comment to an issue."""
        comment = Comment(
            id="comment-MOCK123",
            issue_id="issue-TEST",
            author="user123",
            text="Test comment",
            created_at=TEST_TIMESTAMP,
        )
        mock_uow.issues.get = Mock(return_value=Mock())  # Issue exists
        mock_uow.comments.save = Mock(return_value=comment)

        result = issue_service.add_comment("issue-TEST", "user123", "Test comment")

        assert result.id == "comment-MOCK123"
        assert result.issue_id == "issue-TEST"
        assert result.author == "user123"
        assert result.text == "Test comment"
        mock_uow.comments.save.assert_called_once()

    def test_list_comments(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test listing comments for an issue."""
        comments = [
            Comment(
                id="comment-1",
                issue_id="issue-TEST",
                author="user1",
                text="First",
                created_at=TEST_TIMESTAMP,
            ),
            Comment(
                id="comment-2",
                issue_id="issue-TEST",
                author="user2",
                text="Second",
                created_at=TEST_TIMESTAMP,
            ),
        ]
        mock_uow.comments.list_by_issue = Mock(return_value=comments)

        result = issue_service.list_comments("issue-TEST")

        assert len(result) == 2
        assert result[0].id == "comment-1"
        assert result[1].id == "comment-2"


class TestIssueServiceListing:
    """Test issue listing and filtering operations."""

    def test_list_issues_all(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test listing all issues."""
        issues = [
            Issue(
                id="issue-1",
                project_id=TEST_PROJECT_ID,
                title="Issue 1",
                description="",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                type=IssueType.TASK,
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            ),
            Issue(
                id="issue-2",
                project_id=TEST_PROJECT_ID,
                title="Issue 2",
                description="",
                status=IssueStatus.CLOSED,
                priority=IssuePriority.LOW,
                type=IssueType.BUG,
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            ),
        ]
        mock_uow.issues.list_all = Mock(return_value=issues)

        result = issue_service.list_issues()

        assert len(result) == 2
        mock_uow.issues.list_all.assert_called_once()

    def test_list_issues_by_status(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test listing issues filtered by status."""
        issues = [
            Issue(
                id="issue-1",
                project_id=TEST_PROJECT_ID,
                title="Issue 1",
                description="",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                type=IssueType.TASK,
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            ),
        ]
        mock_uow.issues.list_by_status = Mock(return_value=issues)

        result = issue_service.list_issues(status=IssueStatus.OPEN)

        assert len(result) == 1
        assert result[0].status == IssueStatus.OPEN
        mock_uow.issues.list_by_status.assert_called_once_with(IssueStatus.OPEN, 100, 0)

    def test_list_issues_by_priority(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test listing issues filtered by priority."""
        issues = [
            Issue(
                id="issue-1",
                project_id=TEST_PROJECT_ID,
                title="High Priority",
                description="",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                type=IssueType.TASK,
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            ),
        ]
        mock_uow.issues.list_by_priority = Mock(return_value=issues)

        result = issue_service.list_issues(priority=IssuePriority.HIGH)

        assert len(result) == 1
        assert result[0].priority == IssuePriority.HIGH
        mock_uow.issues.list_by_priority.assert_called_once_with(IssuePriority.HIGH, 100, 0)

    def test_list_issues_by_assignee(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test listing issues filtered by assignee."""
        issues = [
            Issue(
                id="issue-1",
                project_id=TEST_PROJECT_ID,
                title="Assigned",
                description="",
                status=IssueStatus.IN_PROGRESS,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                assignee="user123",
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            ),
        ]
        mock_uow.issues.list_by_assignee = Mock(return_value=issues)

        result = issue_service.list_issues(assignee="user123")

        assert len(result) == 1
        assert result[0].assignee == "user123"
        mock_uow.issues.list_by_assignee.assert_called_once_with("user123", 100, 0)

    def test_list_issues_by_epic(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test listing issues filtered by epic."""
        issues = [
            Issue(
                id="issue-1",
                project_id=TEST_PROJECT_ID,
                title="Epic Child",
                description="",
                status=IssueStatus.OPEN,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                epic_id="epic-001",
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            ),
        ]
        mock_uow.issues.list_by_epic = Mock(return_value=issues)

        result = issue_service.list_issues(epic_id="epic-001")

        assert len(result) == 1
        assert result[0].epic_id == "epic-001"
        mock_uow.issues.list_by_epic.assert_called_once_with("epic-001", 100, 0)

    def test_list_issues_by_type(self, issue_service: IssueService, mock_uow: Mock) -> None:
        """Test listing issues filtered by type."""
        issues = [
            Issue(
                id="issue-1",
                project_id=TEST_PROJECT_ID,
                title="Bug",
                description="",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                type=IssueType.BUG,
                created_at=TEST_TIMESTAMP,
                updated_at=TEST_TIMESTAMP,
            ),
        ]
        mock_uow.issues.list_by_type = Mock(return_value=issues)

        result = issue_service.list_issues(issue_type=IssueType.BUG)

        assert len(result) == 1
        assert result[0].type == IssueType.BUG
        mock_uow.issues.list_by_type.assert_called_once_with(IssueType.BUG, 100, 0)

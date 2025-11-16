"""Integration tests for IssueRepository with real database."""

from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from issue_tracker.adapters.db.repositories.issue_repository import IssueRepository
from issue_tracker.domain.entities.issue import Issue, IssueStatus, IssueType
from issue_tracker.domain.value_objects import IssuePriority

# Test constants
TEST_PROJECT_ID = "PRJ-001"


class TestIssueRepositoryCRUD:
    """Test CRUD operations with real database."""

    def test_save_and_get_issue(self, test_session: Session) -> None:
        """Test saving and retrieving an issue."""
        repo = IssueRepository(test_session)
        
        # Create issue
        issue = Issue(
            id="ISS-001",
            project_id=TEST_PROJECT_ID,
            title="Test issue",
            description="Test description",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.HIGH,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        # Save issue
        saved = repo.save(issue)
        test_session.commit()
        
        # Retrieve issue
        retrieved = repo.get(saved.id)
        
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.title == "Test issue"
        assert retrieved.description == "Test description"
        assert retrieved.type == IssueType.TASK
        assert retrieved.status == IssueStatus.OPEN
        assert retrieved.priority == IssuePriority.HIGH

    def test_save_issue_with_optional_fields(self, test_session: Session) -> None:
        """Test saving issue with assignee and epic."""
        repo = IssueRepository(test_session)
        
        issue = Issue(
            id="ISS-002",
            project_id=TEST_PROJECT_ID,
            title="Issue with extras",
            description="Bug description",
            type=IssueType.BUG,
            status=IssueStatus.IN_PROGRESS,
            priority=IssuePriority.CRITICAL,
            assignee="alice",
            epic_id="EPIC-001",
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        saved = repo.save(issue)
        test_session.commit()
        
        retrieved = repo.get(saved.id)
        
        assert retrieved is not None
        assert retrieved.assignee == "alice"
        assert retrieved.epic_id == "EPIC-001"
        # Note: Labels require junction table management (not tested here)

    def test_update_issue(self, test_session: Session) -> None:
        """Test updating an existing issue."""
        repo = IssueRepository(test_session)
        
        # Create and save
        issue = Issue(
            id="ISS-003",
            project_id=TEST_PROJECT_ID,
            title="Original title",
            description="Original description",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        saved = repo.save(issue)
        test_session.commit()
        
        # Update
        saved.title = "Updated title"
        saved.status = IssueStatus.CLOSED
        saved.assignee = "bob"
        
        updated = repo.save(saved)
        test_session.commit()
        
        # Verify
        retrieved = repo.get(updated.id)
        assert retrieved is not None
        assert retrieved.title == "Updated title"
        assert retrieved.status == IssueStatus.CLOSED
        assert retrieved.assignee == "bob"

    def test_delete_issue(self, test_session: Session) -> None:
        """Test deleting an issue."""
        repo = IssueRepository(test_session)
        
        # Create and save
        issue = Issue(
            id="ISS-004",
            project_id=TEST_PROJECT_ID,
            title="To be deleted",
            description="Will be deleted",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.LOW,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        saved = repo.save(issue)
        test_session.commit()
        
        # Delete
        deleted = repo.delete(saved.id)
        test_session.commit()
        
        assert deleted is True
        
        # Verify gone
        retrieved = repo.get(saved.id)
        assert retrieved is None

    def test_delete_nonexistent_issue(self, test_session: Session) -> None:
        """Test deleting an issue that doesn't exist."""
        repo = IssueRepository(test_session)
        
        deleted = repo.delete("ISS-999")
        
        assert deleted is False

    def test_get_nonexistent_issue(self, test_session: Session) -> None:
        """Test getting an issue that doesn't exist."""
        repo = IssueRepository(test_session)
        
        retrieved = repo.get("ISS-999")
        
        assert retrieved is None


class TestIssueRepositoryQueries:
    """Test query operations with real database."""

    @pytest.fixture(autouse=True)
    def setup_test_issues(self, test_session: Session) -> None:
        """Create a set of test issues for query tests."""
        repo = IssueRepository(test_session)
        now = datetime.now(UTC).replace(tzinfo=None)
        
        issues = [
            Issue(
                id="ISS-Q01",
                project_id=TEST_PROJECT_ID,
                title="Open high priority task",
                description="Task 1",
                type=IssueType.TASK,
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                assignee="alice",
                labels=["backend", "urgent"],
                created_at=now,
                updated_at=now,
            ),
            Issue(
                id="ISS-Q02",
                project_id=TEST_PROJECT_ID,
                title="Closed medium priority bug",
                description="Bug 1",
                type=IssueType.BUG,
                status=IssueStatus.CLOSED,
                priority=IssuePriority.MEDIUM,
                assignee="bob",
                labels=["frontend"],
                created_at=now,
                updated_at=now,
            ),
            Issue(
                id="ISS-Q03",
                project_id=TEST_PROJECT_ID,
                title="In progress critical feature",
                description="Feature 1",
                type=IssueType.FEATURE,
                status=IssueStatus.IN_PROGRESS,
                priority=IssuePriority.CRITICAL,
                assignee="alice",
                labels=["backend", "api"],
                epic_id="EPIC-001",
                created_at=now,
                updated_at=now,
            ),
            Issue(
                id="ISS-Q04",
                project_id=TEST_PROJECT_ID,
                title="Open low priority task",
                description="Task 2",
                type=IssueType.TASK,
                status=IssueStatus.OPEN,
                priority=IssuePriority.LOW,
                created_at=now,
                updated_at=now,
            ),
            Issue(
                id="ISS-Q05",
                project_id=TEST_PROJECT_ID,
                title="Blocked high priority bug",
                description="Bug 2",
                type=IssueType.BUG,
                status=IssueStatus.BLOCKED,
                priority=IssuePriority.HIGH,
                assignee="charlie",
                epic_id="EPIC-002",
                created_at=now,
                updated_at=now,
            ),
        ]
        
        for issue in issues:
            repo.save(issue)
        
        test_session.commit()

    def test_list_all(self, test_session: Session) -> None:
        """Test listing all issues."""
        repo = IssueRepository(test_session)
        
        issues = repo.list_all()
        
        assert len(issues) == 5
        issue_ids = {issue.id for issue in issues}
        assert issue_ids == {"ISS-Q01", "ISS-Q02", "ISS-Q03", "ISS-Q04", "ISS-Q05"}

    def test_list_by_status(self, test_session: Session) -> None:
        """Test filtering by status."""
        repo = IssueRepository(test_session)
        
        open_issues = repo.list_by_status(IssueStatus.OPEN)
        assert len(open_issues) == 2
        assert all(issue.status == IssueStatus.OPEN for issue in open_issues)
        
        closed_issues = repo.list_by_status(IssueStatus.CLOSED)
        assert len(closed_issues) == 1
        assert closed_issues[0].id == "ISS-Q02"

    def test_list_by_priority(self, test_session: Session) -> None:
        """Test filtering by priority."""
        repo = IssueRepository(test_session)
        
        high_priority = repo.list_by_priority(IssuePriority.HIGH)
        assert len(high_priority) == 2
        assert all(issue.priority == IssuePriority.HIGH for issue in high_priority)
        
        critical = repo.list_by_priority(IssuePriority.CRITICAL)
        assert len(critical) == 1
        assert critical[0].id == "ISS-Q03"

    def test_list_by_assignee(self, test_session: Session) -> None:
        """Test filtering by assignee."""
        repo = IssueRepository(test_session)
        
        alice_issues = repo.list_by_assignee("alice")
        assert len(alice_issues) == 2
        assert all(issue.assignee == "alice" for issue in alice_issues)
        
        bob_issues = repo.list_by_assignee("bob")
        assert len(bob_issues) == 1
        assert bob_issues[0].id == "ISS-Q02"
        
        # Test non-existent assignee
        nobody_issues = repo.list_by_assignee("nobody")
        assert len(nobody_issues) == 0

    def test_list_by_epic(self, test_session: Session) -> None:
        """Test filtering by epic."""
        repo = IssueRepository(test_session)
        
        epic1_issues = repo.list_by_epic("EPIC-001")
        assert len(epic1_issues) == 1
        assert epic1_issues[0].id == "ISS-Q03"
        
        epic2_issues = repo.list_by_epic("EPIC-002")
        assert len(epic2_issues) == 1
        assert epic2_issues[0].id == "ISS-Q05"

    def test_list_by_type(self, test_session: Session) -> None:
        """Test filtering by issue type."""
        repo = IssueRepository(test_session)
        
        tasks = repo.list_by_type(IssueType.TASK)
        assert len(tasks) == 2
        assert all(issue.type == IssueType.TASK for issue in tasks)
        
        bugs = repo.list_by_type(IssueType.BUG)
        assert len(bugs) == 2
        assert all(issue.type == IssueType.BUG for issue in bugs)
        
        features = repo.list_by_type(IssueType.FEATURE)
        assert len(features) == 1
        assert features[0].id == "ISS-Q03"


class TestIssueRepositoryTransactions:
    """Test transaction handling."""

    def test_rollback_on_error(self, test_session: Session) -> None:
        """Test that failed transactions don't persist data."""
        repo = IssueRepository(test_session)
        
        # Create and save issue
        issue = Issue(
            id="ISS-T01",
            project_id=TEST_PROJECT_ID,
            title="Transaction test",
            description="Transaction description",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        repo.save(issue)
        # Don't commit - simulate transaction failure
        test_session.rollback()
        
        # Verify not persisted
        retrieved = repo.get("ISS-T01")
        assert retrieved is None

    def test_commit_persists_data(self, test_session: Session) -> None:
        """Test that committed transactions persist data."""
        repo = IssueRepository(test_session)
        
        issue = Issue(
            id="ISS-T02",
            project_id=TEST_PROJECT_ID,
            title="Commit test",
            description="Commit description",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        
        repo.save(issue)
        test_session.commit()
        
        # Verify persisted
        retrieved = repo.get("ISS-T02")
        assert retrieved is not None
        assert retrieved.title == "Commit test"

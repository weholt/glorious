"""Unit tests for IssueStatsService."""

from unittest.mock import Mock

import pytest

from issue_tracker.domain.entities.issue import Issue, IssueStatus, IssueType
from issue_tracker.domain.value_objects import IssuePriority
from issue_tracker.services.issue_stats_service import IssueStatsService


@pytest.fixture
def mock_uow():
    """Create a mock UnitOfWork."""
    uow = Mock()
    uow.issues = Mock()
    uow.graph = Mock()
    return uow


@pytest.fixture
def stats_service(mock_uow):
    """Create an IssueStatsService instance."""
    return IssueStatsService(mock_uow)


@pytest.fixture
def sample_issues():
    """Create sample issues for testing."""
    return [
        Issue(
            id="ISS-001",
            project_id="PROJ-1",
            title="High priority open",
            description="Description",
            status=IssueStatus.OPEN,
            priority=IssuePriority.HIGH,
            type=IssueType.BUG,
        ),
        Issue(
            id="ISS-002",
            project_id="PROJ-1",
            title="High priority in progress",
            description="Description",
            status=IssueStatus.IN_PROGRESS,
            priority=IssuePriority.HIGH,
            type=IssueType.FEATURE,
        ),
        Issue(
            id="ISS-003",
            project_id="PROJ-1",
            title="Medium priority closed",
            description="Description",
            status=IssueStatus.CLOSED,
            priority=IssuePriority.MEDIUM,
            type=IssueType.BUG,
        ),
        Issue(
            id="ISS-004",
            project_id="PROJ-1",
            title="Low priority resolved",
            description="Description",
            status=IssueStatus.RESOLVED,
            priority=IssuePriority.LOW,
            type=IssueType.TASK,
        ),
        Issue(
            id="ISS-005",
            project_id="PROJ-1",
            title="Critical open",
            description="Description",
            status=IssueStatus.OPEN,
            priority=IssuePriority.CRITICAL,
            type=IssueType.BUG,
        ),
    ]


class TestIssueStatsServiceCounts:
    """Test count aggregation methods."""

    def test_count_by_status(self, stats_service, mock_uow, sample_issues):
        """Test counting issues by status."""
        mock_uow.issues.list_all.return_value = sample_issues

        result = stats_service.count_by_status()

        assert result[IssueStatus.OPEN] == 2
        assert result[IssueStatus.IN_PROGRESS] == 1
        assert result[IssueStatus.CLOSED] == 1
        assert result[IssueStatus.RESOLVED] == 1

    def test_count_by_status_empty(self, stats_service, mock_uow):
        """Test counting when no issues exist."""
        mock_uow.issues.list_all.return_value = []

        result = stats_service.count_by_status()

        assert result == {}

    def test_count_by_priority(self, stats_service, mock_uow, sample_issues):
        """Test counting issues by priority."""
        mock_uow.issues.list_all.return_value = sample_issues

        result = stats_service.count_by_priority()

        assert result[IssuePriority.HIGH] == 2
        assert result[IssuePriority.MEDIUM] == 1
        assert result[IssuePriority.LOW] == 1
        assert result[IssuePriority.CRITICAL] == 1

    def test_count_by_priority_empty(self, stats_service, mock_uow):
        """Test counting by priority when no issues exist."""
        mock_uow.issues.list_all.return_value = []

        result = stats_service.count_by_priority()

        assert result == {}


class TestIssueStatsServiceBlocked:
    """Test blocked issue detection."""

    def test_get_blocked_issues_with_open_blockers(self, stats_service, mock_uow, sample_issues):
        """Test finding issues with open blockers."""
        # ISS-002 is blocked by ISS-001 (open)
        mock_uow.issues.list_all.return_value = sample_issues
        mock_uow.graph.get_blockers.side_effect = lambda issue_id: {
            "ISS-001": [],
            "ISS-002": ["ISS-001"],  # Blocked by open issue
            "ISS-003": [],
            "ISS-004": [],
            "ISS-005": [],
        }.get(issue_id, [])

        # Mock getting blocker issues
        mock_uow.issues.get.side_effect = lambda issue_id: {
            "ISS-001": sample_issues[0],  # OPEN
        }.get(issue_id)

        result = stats_service.get_blocked_issues()

        assert len(result) == 1
        assert result[0].id == "ISS-002"

    def test_get_blocked_issues_with_closed_blockers(self, stats_service, mock_uow, sample_issues):
        """Test that issues blocked by closed issues are not counted."""
        # ISS-002 is blocked by ISS-003 (closed)
        mock_uow.issues.list_all.return_value = sample_issues
        mock_uow.graph.get_blockers.side_effect = lambda issue_id: {
            "ISS-001": [],
            "ISS-002": ["ISS-003"],  # Blocked by closed issue
            "ISS-003": [],
            "ISS-004": [],
            "ISS-005": [],
        }.get(issue_id, [])

        # Mock getting blocker issues
        mock_uow.issues.get.side_effect = lambda issue_id: {
            "ISS-003": sample_issues[2],  # CLOSED
        }.get(issue_id)

        result = stats_service.get_blocked_issues()

        assert len(result) == 0

    def test_get_blocked_issues_empty(self, stats_service, mock_uow):
        """Test with no issues."""
        mock_uow.issues.list_all.return_value = []

        result = stats_service.get_blocked_issues()

        assert result == []


class TestIssueStatsServiceDependencyChain:
    """Test longest dependency chain calculation."""

    def test_get_longest_chain_linear(self, stats_service, mock_uow, sample_issues):
        """Test finding longest chain in linear dependencies."""
        # Chain: ISS-001 -> ISS-002 -> ISS-003
        mock_uow.issues.list_all.return_value = sample_issues[:3]

        from issue_tracker.domain.entities.dependency import Dependency, DependencyType

        mock_uow.graph.get_dependencies.side_effect = lambda issue_id: {
            "ISS-001": [Dependency("ISS-001", "ISS-002", DependencyType.BLOCKS)],
            "ISS-002": [Dependency("ISS-002", "ISS-003", DependencyType.BLOCKS)],
            "ISS-003": [],
        }.get(issue_id, [])

        # Mock getting issues by ID
        mock_uow.issues.get.side_effect = lambda issue_id: {
            "ISS-001": sample_issues[0],
            "ISS-002": sample_issues[1],
            "ISS-003": sample_issues[2],
        }.get(issue_id)

        result = stats_service.get_longest_dependency_chain()

        assert len(result) == 3
        assert [issue.id for issue in result] == ["ISS-001", "ISS-002", "ISS-003"]

    def test_get_longest_chain_branching(self, stats_service, mock_uow, sample_issues):
        """Test finding longest chain with branching dependencies."""
        # ISS-001 -> ISS-002 -> ISS-004 (length 3)
        # ISS-001 -> ISS-003 (length 2)
        mock_uow.issues.list_all.return_value = sample_issues[:4]

        from issue_tracker.domain.entities.dependency import Dependency, DependencyType

        mock_uow.graph.get_dependencies.side_effect = lambda issue_id: {
            "ISS-001": [
                Dependency("ISS-001", "ISS-002", DependencyType.BLOCKS),
                Dependency("ISS-001", "ISS-003", DependencyType.BLOCKS),
            ],
            "ISS-002": [Dependency("ISS-002", "ISS-004", DependencyType.BLOCKS)],
            "ISS-003": [],
            "ISS-004": [],
        }.get(issue_id, [])

        # Mock getting issues by ID
        mock_uow.issues.get.side_effect = lambda issue_id: {
            "ISS-001": sample_issues[0],
            "ISS-002": sample_issues[1],
            "ISS-003": sample_issues[2],
            "ISS-004": sample_issues[3],
        }.get(issue_id)

        result = stats_service.get_longest_dependency_chain()

        assert len(result) == 3
        assert result[0].id == "ISS-001"
        assert result[-1].id == "ISS-004"

    def test_get_longest_chain_empty(self, stats_service, mock_uow):
        """Test with no issues."""
        mock_uow.issues.list_all.return_value = []

        result = stats_service.get_longest_dependency_chain()

        assert result == []


class TestIssueStatsServiceCompletion:
    """Test completion rate calculations."""

    def test_get_completion_rate_with_data(self, stats_service, mock_uow, sample_issues):
        """Test completion rate calculation with mixed statuses."""
        mock_uow.issues.list_all.return_value = sample_issues

        result = stats_service.get_completion_rate()

        assert result["total"] == 5
        assert result["closed"] == 1
        assert result["resolved"] == 1
        assert result["completion_rate"] == 20.0  # 1/5 * 100
        assert result["resolution_rate"] == 40.0  # 2/5 * 100

    def test_get_completion_rate_all_closed(self, stats_service, mock_uow, sample_issues):
        """Test completion rate when all issues are closed."""
        for issue in sample_issues:
            issue.status = IssueStatus.CLOSED

        mock_uow.issues.list_all.return_value = sample_issues

        result = stats_service.get_completion_rate()

        assert result["total"] == 5
        assert result["closed"] == 5
        assert result["resolved"] == 0
        assert result["completion_rate"] == 100.0
        assert result["resolution_rate"] == 100.0

    def test_get_completion_rate_empty(self, stats_service, mock_uow):
        """Test completion rate with no issues."""
        mock_uow.issues.list_all.return_value = []

        result = stats_service.get_completion_rate()

        assert result["total"] == 0
        assert result["closed"] == 0
        assert result["resolved"] == 0
        assert result["completion_rate"] == 0.0
        assert result["resolution_rate"] == 0.0


class TestIssueStatsServiceBreakdown:
    """Test priority breakdown."""

    def test_get_priority_breakdown(self, stats_service, mock_uow, sample_issues):
        """Test detailed priority/status breakdown."""
        mock_uow.issues.list_all.return_value = sample_issues

        result = stats_service.get_priority_breakdown()

        assert result["high"]["open"] == 1
        assert result["high"]["in_progress"] == 1
        assert result["medium"]["closed"] == 1
        assert result["low"]["resolved"] == 1
        assert result["critical"]["open"] == 1

    def test_get_priority_breakdown_empty(self, stats_service, mock_uow):
        """Test breakdown with no issues."""
        mock_uow.issues.list_all.return_value = []

        result = stats_service.get_priority_breakdown()

        # Should have entries for all priorities, but no status counts
        for priority in IssuePriority:
            priority_name = priority.name.lower()
            assert priority_name in result
            assert result[priority_name] == {}

    def test_get_priority_breakdown_single_status(self, stats_service, mock_uow, sample_issues):
        """Test breakdown when all issues have same status."""
        for issue in sample_issues:
            issue.status = IssueStatus.OPEN

        mock_uow.issues.list_all.return_value = sample_issues

        result = stats_service.get_priority_breakdown()

        assert result["high"]["open"] == 2
        assert result["medium"]["open"] == 1
        assert result["low"]["open"] == 1
        assert result["critical"]["open"] == 1
        # No other status keys should exist
        assert "closed" not in result["high"]

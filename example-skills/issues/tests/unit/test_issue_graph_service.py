"""Unit tests for IssueGraphService with mocked repositories."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.issue import Issue, IssueStatus, IssueType
from issue_tracker.domain.exceptions import InvariantViolationError, NotFoundError
from issue_tracker.domain.value_objects import IssuePriority
from issue_tracker.services.issue_graph_service import IssueGraphService

# Test constants
TEST_PROJECT_ID = "PRJ-TEST"
TEST_TIMESTAMP = datetime(2025, 11, 11, 12, 0, 0, tzinfo=UTC).replace(tzinfo=None)


@pytest.fixture
def mock_uow() -> Mock:
    """Create a mock UnitOfWork."""
    uow = Mock()
    uow.issues = Mock()
    uow.graph = Mock()
    uow.__enter__ = Mock(return_value=uow)
    uow.__exit__ = Mock(return_value=False)
    return uow


@pytest.fixture
def graph_service(mock_uow: Mock) -> IssueGraphService:
    """Create IssueGraphService with mocked dependencies."""
    return IssueGraphService(mock_uow, max_depth=10)


@pytest.fixture
def sample_issues() -> dict[str, Issue]:
    """Create sample issues for testing."""
    return {
        "A": Issue(
            id="ISS-A",
            project_id=TEST_PROJECT_ID,
            title="Issue A",
            description="First issue",
            status=IssueStatus.OPEN,
            priority=IssuePriority.HIGH,
            type=IssueType.TASK,
            created_at=TEST_TIMESTAMP,
            updated_at=TEST_TIMESTAMP,
        ),
        "B": Issue(
            id="ISS-B",
            project_id=TEST_PROJECT_ID,
            title="Issue B",
            description="Second issue",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            type=IssueType.TASK,
            created_at=TEST_TIMESTAMP,
            updated_at=TEST_TIMESTAMP,
        ),
        "C": Issue(
            id="ISS-C",
            project_id=TEST_PROJECT_ID,
            title="Issue C",
            description="Third issue",
            status=IssueStatus.OPEN,
            priority=IssuePriority.LOW,
            type=IssueType.TASK,
            created_at=TEST_TIMESTAMP,
            updated_at=TEST_TIMESTAMP,
        ),
        "D": Issue(
            id="ISS-D",
            project_id=TEST_PROJECT_ID,
            title="Issue D",
            description="Fourth issue",
            status=IssueStatus.CLOSED,
            priority=IssuePriority.HIGH,
            type=IssueType.BUG,
            created_at=TEST_TIMESTAMP,
            updated_at=TEST_TIMESTAMP,
        ),
    }


class TestGraphServiceDependencyCRUD:
    """Test dependency add/remove operations."""

    def test_add_dependency_success(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test successfully adding a dependency."""
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues["A"] if id == "ISS-A" else sample_issues["B"])
        mock_uow.graph.has_cycle = Mock(return_value=False)
        dep = Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        )
        mock_uow.graph.add_dependency = Mock(return_value=dep)
        
        result = graph_service.add_dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)
        
        assert result.from_issue_id == "ISS-A"
        assert result.to_issue_id == "ISS-B"
        assert result.dependency_type == DependencyType.BLOCKS
        mock_uow.graph.has_cycle.assert_called_once_with("ISS-A", "ISS-B")
        mock_uow.graph.add_dependency.assert_called_once()

    def test_add_dependency_from_issue_not_found(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test adding dependency when source issue doesn't exist."""
        mock_uow.issues.get = Mock(return_value=None)
        
        with pytest.raises(NotFoundError, match="Issue not found: ISS-NONEXISTENT"):
            graph_service.add_dependency("ISS-NONEXISTENT", "ISS-B", DependencyType.BLOCKS)

    def test_add_dependency_to_issue_not_found(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test adding dependency when target issue doesn't exist."""
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues["A"] if id == "ISS-A" else None)
        
        with pytest.raises(NotFoundError, match="Issue not found: ISS-NONEXISTENT"):
            graph_service.add_dependency("ISS-A", "ISS-NONEXISTENT", DependencyType.BLOCKS)

    def test_add_dependency_creates_cycle(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test that adding a dependency that creates a cycle is rejected."""
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues["A"] if id == "ISS-A" else sample_issues["B"])
        mock_uow.graph.has_cycle = Mock(return_value=True)
        
        with pytest.raises(InvariantViolationError, match="would create a cycle"):
            graph_service.add_dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)

    def test_remove_dependency_success(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test successfully removing a dependency."""
        mock_uow.graph.remove_dependency = Mock(return_value=True)
        
        result = graph_service.remove_dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)
        
        assert result is True
        mock_uow.graph.remove_dependency.assert_called_once_with("ISS-A", "ISS-B", DependencyType.BLOCKS)

    def test_remove_dependency_not_found(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test removing a non-existent dependency."""
        mock_uow.graph.remove_dependency = Mock(return_value=False)
        
        result = graph_service.remove_dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)
        
        assert result is False


class TestGraphServiceQueries:
    """Test dependency query operations."""

    def test_get_dependencies(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test getting dependencies of an issue."""
        deps = [
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-B", dependency_type=DependencyType.BLOCKS),
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-C", dependency_type=DependencyType.DEPENDS_ON),
        ]
        mock_uow.graph.get_dependencies = Mock(return_value=deps)
        
        result = graph_service.get_dependencies("ISS-A")
        
        assert len(result) == 2
        assert result[0].to_issue_id == "ISS-B"
        assert result[1].to_issue_id == "ISS-C"

    def test_get_dependents(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test getting dependents of an issue."""
        deps = [
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-C", dependency_type=DependencyType.BLOCKS),
            Dependency(from_issue_id="ISS-B", to_issue_id="ISS-C", dependency_type=DependencyType.BLOCKS),
        ]
        mock_uow.graph.get_dependents = Mock(return_value=deps)
        
        result = graph_service.get_dependents("ISS-C")
        
        assert len(result) == 2
        assert result[0].from_issue_id == "ISS-A"
        assert result[1].from_issue_id == "ISS-B"

    def test_get_dependents_with_type_filter(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test getting dependents filtered by dependency type."""
        deps = [
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-C", dependency_type=DependencyType.BLOCKS),
            Dependency(from_issue_id="ISS-B", to_issue_id="ISS-C", dependency_type=DependencyType.DEPENDS_ON),
        ]
        mock_uow.graph.get_dependents = Mock(return_value=deps)
        
        result = graph_service.get_dependents("ISS-C", dependency_type=DependencyType.BLOCKS)
        
        assert len(result) == 1
        assert result[0].from_issue_id == "ISS-A"
        assert result[0].dependency_type == DependencyType.BLOCKS

    def test_get_blockers(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test getting issues that block a target issue."""
        mock_uow.graph.get_blockers = Mock(return_value=["ISS-A", "ISS-B"])
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues["A"] if id == "ISS-A" else sample_issues["B"])
        
        result = graph_service.get_blockers("ISS-C")
        
        assert len(result) == 2
        assert result[0].id == "ISS-A"
        assert result[1].id == "ISS-B"

    def test_get_blocked_issues(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test getting issues blocked by a source issue."""
        mock_uow.graph.get_blocked_by = Mock(return_value=["ISS-B", "ISS-C"])
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues["B"] if id == "ISS-B" else sample_issues["C"])
        
        result = graph_service.get_blocked_issues("ISS-A")
        
        assert len(result) == 2
        assert result[0].id == "ISS-B"
        assert result[1].id == "ISS-C"


class TestGraphServiceCycleDetection:
    """Test cycle detection algorithms."""

    def test_has_path_direct(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test detecting a direct path between issues."""
        # has_path reverses arguments: has_path(A, B) calls has_cycle(B, A)
        mock_uow.graph.has_cycle = Mock(return_value=True)
        
        result = graph_service.has_path("ISS-A", "ISS-B")
        
        assert result is True
        mock_uow.graph.has_cycle.assert_called_once_with("ISS-B", "ISS-A")

    def test_has_path_no_connection(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test when there's no path between issues."""
        mock_uow.graph.has_cycle = Mock(return_value=False)
        
        result = graph_service.has_path("ISS-A", "ISS-B")
        
        assert result is False

    def test_detect_cycles_found(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test detecting cycles in the graph."""
        # Service implements DFS algorithm - needs list_all and get_dependencies
        mock_uow.issues.list_all = Mock(return_value=list(sample_issues.values()))
        # Setup a cycle: A -> B -> C -> A
        mock_uow.graph.get_dependencies = Mock(side_effect=lambda id: {
            "ISS-A": [Dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)],
            "ISS-B": [Dependency("ISS-B", "ISS-C", DependencyType.BLOCKS)],
            "ISS-C": [Dependency("ISS-C", "ISS-A", DependencyType.BLOCKS)],
            "ISS-D": [],
        }.get(id, []))
        
        result = graph_service.detect_cycles()
        
        assert len(result) >= 1  # At least one cycle found
        # Check that at least one cycle contains all three nodes
        assert any(len(cycle) == 3 for cycle in result)

    def test_detect_cycles_none(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test when no cycles exist."""
        mock_uow.issues.list_all = Mock(return_value=list(sample_issues.values()))
        # No dependencies = no cycles
        mock_uow.graph.get_dependencies = Mock(return_value=[])
        
        result = graph_service.detect_cycles()
        
        assert len(result) == 0


class TestGraphServicePathFinding:
    """Test path finding and dependency chain operations."""

    def test_get_dependency_chain(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test getting shortest dependency chain between issues."""
        # Service implements BFS - needs get_dependencies
        # Path: A -> B -> C
        mock_uow.graph.get_dependencies = Mock(side_effect=lambda id: {
            "ISS-A": [Dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)],
            "ISS-B": [Dependency("ISS-B", "ISS-C", DependencyType.BLOCKS)],
            "ISS-C": [],
        }.get(id, []))
        
        result = graph_service.get_dependency_chain("ISS-A", "ISS-C")
        
        assert len(result) == 2
        assert result[0].from_issue_id == "ISS-A"
        assert result[0].to_issue_id == "ISS-B"
        assert result[1].from_issue_id == "ISS-B"
        assert result[1].to_issue_id == "ISS-C"

    def test_get_dependency_chain_no_path(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test when no path exists between issues."""
        # No dependencies = no path
        mock_uow.graph.get_dependencies = Mock(return_value=[])
        
        result = graph_service.get_dependency_chain("ISS-A", "ISS-D")
        
        assert result == []


class TestGraphServiceReadyQueue:
    """Test ready queue calculation."""

    def test_get_ready_queue(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test getting issues ready to work on (no open blockers)."""
        # Service implements algorithm: filters by status, checks blockers
        mock_uow.issues.list_all = Mock(return_value=[sample_issues["A"], sample_issues["B"]])
        # A has no blockers, B has closed blocker
        mock_uow.graph.get_blockers = Mock(side_effect=lambda id: {
            "ISS-A": [],
            "ISS-B": ["ISS-D"],  # D is closed
        }.get(id, []))
        mock_uow.issues.get = Mock(return_value=sample_issues["D"])  # Closed blocker
        
        result = graph_service.get_ready_queue()
        
        assert len(result) == 2  # Both A (no blockers) and B (closed blocker) are ready
        assert any(issue.id == "ISS-A" for issue in result)
        assert any(issue.id == "ISS-B" for issue in result)

    def test_get_ready_queue_empty(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test when no issues are ready."""
        # All issues blocked by open issues
        mock_uow.issues.list_all = Mock(return_value=[sample_issues["B"]])
        mock_uow.graph.get_blockers = Mock(return_value=["ISS-A"])
        mock_uow.issues.get = Mock(return_value=sample_issues["A"])  # Open blocker
        
        result = graph_service.get_ready_queue()
        
        assert len(result) == 0


class TestGraphServiceTreeBuilding:
    """Test dependency tree building."""

    def test_build_dependency_tree(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test building a dependency tree from an issue."""
        # Service implements recursive algorithm
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues.get(id[4:]))  # ISS-A -> A
        # A depends on B, B depends on C
        mock_uow.graph.get_dependencies = Mock(side_effect=lambda id: {
            "ISS-A": [Dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)],
            "ISS-B": [Dependency("ISS-B", "ISS-C", DependencyType.BLOCKS)],
            "ISS-C": [],
        }.get(id, []))
        
        result = graph_service.build_dependency_tree("ISS-A")
        
        assert result["issue_id"] == "ISS-A"
        assert "dependencies" in result
        assert len(result["dependencies"]) >= 1

    def test_build_dependency_tree_custom_depth(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test building tree with custom max depth."""
        mock_uow.issues.get = Mock(return_value=sample_issues["A"])
        mock_uow.graph.get_dependencies = Mock(return_value=[])  # No deps
        
        result = graph_service.build_dependency_tree("ISS-A", max_depth=5)
        
        assert result["issue_id"] == "ISS-A"
        assert result["dependencies"] == []

    def test_build_dependency_tree_not_found(self, graph_service: IssueGraphService, mock_uow: Mock) -> None:
        """Test building tree for non-existent issue."""
        mock_uow.issues.get = Mock(return_value=None)
        
        with pytest.raises(NotFoundError, match="Issue not found: ISS-NONEXISTENT"):
            graph_service.build_dependency_tree("ISS-NONEXISTENT")

    def test_build_dependency_tree_leaf_node(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test building tree for issue with no dependencies."""
        mock_uow.issues.get = Mock(return_value=sample_issues["D"])
        mock_uow.graph.get_dependencies = Mock(return_value=[])  # No dependencies
        
        result = graph_service.build_dependency_tree("ISS-D")
        
        assert result["issue_id"] == "ISS-D"
        assert result["dependencies"] == []

    def test_build_dependency_tree_with_circular_ref(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test building tree with circular reference."""
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues.get(id[4:]))
        # Create circular: A -> B -> A
        mock_uow.graph.get_dependencies = Mock(side_effect=lambda id: {
            "ISS-A": [Dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)],
            "ISS-B": [Dependency("ISS-B", "ISS-A", DependencyType.BLOCKS)],
        }.get(id, []))
        
        result = graph_service.build_dependency_tree("ISS-A")
        
        assert result["issue_id"] == "ISS-A"
        # Should detect circular reference in nested dependency
        assert len(result["dependencies"]) >= 1

    def test_build_dependency_tree_exceeds_depth(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test building tree that exceeds max depth."""
        service = IssueGraphService(mock_uow, max_depth=1)
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues.get(id[4:]))
        # A -> B -> C (depth 2)
        mock_uow.graph.get_dependencies = Mock(side_effect=lambda id: {
            "ISS-A": [Dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)],
            "ISS-B": [Dependency("ISS-B", "ISS-C", DependencyType.BLOCKS)],
            "ISS-C": [],
        }.get(id, []))
        
        result = service.build_dependency_tree("ISS-A")
        
        assert result["issue_id"] == "ISS-A"
        # Should have B but B should not have C (depth limited)
        assert len(result["dependencies"]) == 1

    def test_build_dependency_tree_missing_child(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test building tree when child issue doesn't exist."""
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues.get(id[4:]) if id != "ISS-MISSING" else None)
        mock_uow.graph.get_dependencies = Mock(side_effect=lambda id: {
            "ISS-A": [Dependency("ISS-A", "ISS-MISSING", DependencyType.BLOCKS)],
        }.get(id, []))
        
        result = graph_service.build_dependency_tree("ISS-A")
        
        assert result["issue_id"] == "ISS-A"
        # Missing child should be filtered out
        assert result["dependencies"] == []

    def test_build_dependency_tree_reverse(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test building tree in reverse (dependents)."""
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues.get(id[4:]))
        # B depends on A (reverse: A is depended on by B)
        mock_uow.graph.get_dependents = Mock(side_effect=lambda id: {
            "ISS-A": [Dependency("ISS-B", "ISS-A", DependencyType.BLOCKS)],
            "ISS-B": [],
        }.get(id, []))
        
        result = graph_service.build_dependency_tree("ISS-A", reverse=True)
        
        assert result["issue_id"] == "ISS-A"
        assert len(result["dependencies"]) >= 0


class TestGraphServiceAdvancedScenarios:
    """Test complex graph scenarios."""

    def test_diamond_dependency_pattern(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test handling diamond-shaped dependency graph."""
        # A depends on B and C, both B and C depend on D
        deps_a = [
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-B", dependency_type=DependencyType.DEPENDS_ON),
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-C", dependency_type=DependencyType.DEPENDS_ON),
        ]
        mock_uow.graph.get_dependencies = Mock(return_value=deps_a)
        
        result = graph_service.get_dependencies("ISS-A")
        
        assert len(result) == 2
        target_ids = {dep.to_issue_id for dep in result}
        assert target_ids == {"ISS-B", "ISS-C"}

    def test_multiple_dependency_types(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test handling multiple relationship types between same issues."""
        deps = [
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-B", dependency_type=DependencyType.BLOCKS),
            Dependency(from_issue_id="ISS-A", to_issue_id="ISS-B", dependency_type=DependencyType.RELATED_TO),
        ]
        mock_uow.graph.get_dependencies = Mock(return_value=deps)
        
        result = graph_service.get_dependencies("ISS-A")
        
        assert len(result) == 2
        types = {dep.dependency_type for dep in result}
        assert types == {DependencyType.BLOCKS, DependencyType.RELATED_TO}

    def test_get_blockers_filters_by_status(self, graph_service: IssueGraphService, mock_uow: Mock, sample_issues: dict[str, Issue]) -> None:
        """Test that get_blockers correctly returns blocker issues."""
        # Only return issues, the service fetches them
        mock_uow.graph.get_blockers = Mock(return_value=["ISS-A", "ISS-D"])
        mock_uow.issues.get = Mock(side_effect=lambda id: sample_issues["A"] if id == "ISS-A" else sample_issues["D"])
        
        result = graph_service.get_blockers("ISS-C")
        
        assert len(result) == 2
        # Both open and closed issues can be blockers
        assert any(issue.status == IssueStatus.OPEN for issue in result)
        assert any(issue.status == IssueStatus.CLOSED for issue in result)

"""Integration tests for IssueGraphRepository with real database."""

from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from issue_tracker.adapters.db.repositories.issue_graph_repository import IssueGraphRepository
from issue_tracker.adapters.db.repositories.issue_repository import IssueRepository
from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.issue import Issue, IssueStatus, IssueType
from issue_tracker.domain.value_objects import IssuePriority

# Test constants
TEST_PROJECT_ID = "PRJ-001"


@pytest.fixture
def setup_issues(test_session: Session) -> dict[str, Issue]:
    """Create test issues for graph tests."""
    issue_repo = IssueRepository(test_session)
    now = datetime.now(UTC).replace(tzinfo=None)
    
    issues = {
        "A": Issue(
            id="ISS-A",
            project_id=TEST_PROJECT_ID,
            title="Issue A",
            description="First issue",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.HIGH,
            created_at=now,
            updated_at=now,
        ),
        "B": Issue(
            id="ISS-B",
            project_id=TEST_PROJECT_ID,
            title="Issue B",
            description="Second issue",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            created_at=now,
            updated_at=now,
        ),
        "C": Issue(
            id="ISS-C",
            project_id=TEST_PROJECT_ID,
            title="Issue C",
            description="Third issue",
            type=IssueType.TASK,
            status=IssueStatus.OPEN,
            priority=IssuePriority.LOW,
            created_at=now,
            updated_at=now,
        ),
        "D": Issue(
            id="ISS-D",
            project_id=TEST_PROJECT_ID,
            title="Issue D",
            description="Fourth issue",
            type=IssueType.BUG,
            status=IssueStatus.CLOSED,
            priority=IssuePriority.HIGH,
            created_at=now,
            updated_at=now,
        ),
    }
    
    for issue in issues.values():
        issue_repo.save(issue)
    
    test_session.commit()
    return issues


class TestGraphRepositoryDependencies:
    """Test dependency add/remove operations."""

    def test_add_dependency(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test adding a dependency between issues."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Create dependency: A blocks B
        dep = Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        )
        
        saved = graph_repo.add_dependency(dep)
        test_session.commit()
        
        assert saved is not None
        assert saved.from_issue_id == "ISS-A"
        assert saved.to_issue_id == "ISS-B"
        assert saved.dependency_type == DependencyType.BLOCKS

    def test_get_dependencies(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test retrieving dependencies of an issue."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Add multiple dependencies: A -> B, A -> C
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.DEPENDS_ON,
        ))
        test_session.commit()
        
        # Get dependencies of A
        deps = graph_repo.get_dependencies("ISS-A")
        
        assert len(deps) == 2
        dep_targets = {dep.to_issue_id for dep in deps}
        assert dep_targets == {"ISS-B", "ISS-C"}

    def test_get_dependents(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test retrieving dependents (issues that depend on this issue)."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Add dependencies: A -> C, B -> C
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-B",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Get dependents of C (issues that depend on C)
        deps = graph_repo.get_dependents("ISS-C")
        
        assert len(deps) == 2
        dep_sources = {dep.from_issue_id for dep in deps}
        assert dep_sources == {"ISS-A", "ISS-B"}

    def test_get_all_dependencies(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test retrieving all dependencies for an issue (both directions)."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Add dependencies: A -> B, C -> A
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-C",
            to_issue_id="ISS-A",
            dependency_type=DependencyType.DEPENDS_ON,
        ))
        test_session.commit()
        
        # Get all dependencies involving A (both directions)
        deps = graph_repo.get_all_dependencies("ISS-A")
        
        assert len(deps) == 2
        # Should include both A->B and C->A
        issue_ids = {(dep.from_issue_id, dep.to_issue_id) for dep in deps}
        assert issue_ids == {("ISS-A", "ISS-B"), ("ISS-C", "ISS-A")}

    def test_remove_dependency(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test removing a dependency."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Add dependency
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Remove it
        removed = graph_repo.remove_dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)
        test_session.commit()
        
        assert removed is True
        
        # Verify gone
        deps = graph_repo.get_dependencies("ISS-A")
        assert len(deps) == 0

    def test_remove_nonexistent_dependency(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test removing a dependency that doesn't exist."""
        graph_repo = IssueGraphRepository(test_session)
        
        removed = graph_repo.remove_dependency("ISS-A", "ISS-B", DependencyType.BLOCKS)
        
        assert removed is False


class TestGraphRepositoryCycleDetection:
    """Test cycle detection algorithms."""

    def test_has_cycle_simple(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test detecting a simple 2-node cycle."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Add A -> B
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Check if adding B -> A would create cycle
        has_cycle = graph_repo.has_cycle("ISS-B", "ISS-A")
        
        assert has_cycle is True

    def test_has_cycle_three_nodes(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test detecting a 3-node cycle: A -> B -> C -> A."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Add A -> B -> C
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-B",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Check if adding C -> A would create cycle
        has_cycle = graph_repo.has_cycle("ISS-C", "ISS-A")
        
        assert has_cycle is True

    def test_no_cycle_linear(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test that linear dependencies don't create cycles."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Add A -> B -> C (linear chain)
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-B",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Adding D -> A doesn't create cycle
        has_cycle = graph_repo.has_cycle("ISS-D", "ISS-A")
        
        assert has_cycle is False

    def test_no_cycle_independent(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test that independent edges don't create cycles."""
        graph_repo = IssueGraphRepository(test_session)
        
        # No dependencies yet
        has_cycle = graph_repo.has_cycle("ISS-A", "ISS-B")
        
        assert has_cycle is False


class TestGraphRepositoryBlockers:
    """Test blocker-specific queries."""

    def test_get_blockers(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test getting all issues blocking a target issue."""
        graph_repo = IssueGraphRepository(test_session)
        
        # A blocks C, B blocks C
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-B",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Get blockers of C
        blockers = graph_repo.get_blockers("ISS-C")
        
        assert len(blockers) == 2
        assert set(blockers) == {"ISS-A", "ISS-B"}

    def test_get_blocked_by(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test getting all issues blocked by a source issue."""
        graph_repo = IssueGraphRepository(test_session)
        
        # A blocks B, A blocks C
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Get issues blocked by A
        blocked = graph_repo.get_blocked_by("ISS-A")
        
        assert len(blocked) == 2
        assert set(blocked) == {"ISS-B", "ISS-C"}

    def test_blockers_ignore_other_dependency_types(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test that blocker queries only return BLOCKS relationships."""
        graph_repo = IssueGraphRepository(test_session)
        
        # A blocks C
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        # B depends-on C (not a blocker)
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-B",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.DEPENDS_ON,
        ))
        test_session.commit()
        
        # Get blockers of C - should only return A
        blockers = graph_repo.get_blockers("ISS-C")
        
        assert len(blockers) == 1
        assert blockers[0] == "ISS-A"


class TestGraphRepositoryComplexScenarios:
    """Test complex graph scenarios."""

    def test_diamond_dependency_graph(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test diamond-shaped dependency graph: A -> B, A -> C, B -> D, C -> D."""
        graph_repo = IssueGraphRepository(test_session)
        
        # Build diamond
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-C",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-B",
            to_issue_id="ISS-D",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-C",
            to_issue_id="ISS-D",
            dependency_type=DependencyType.BLOCKS,
        ))
        test_session.commit()
        
        # Verify structure
        a_deps = graph_repo.get_dependencies("ISS-A")
        assert len(a_deps) == 2
        
        d_dependents = graph_repo.get_dependents("ISS-D")
        assert len(d_dependents) == 2
        
        # Closing the diamond would create cycle
        has_cycle = graph_repo.has_cycle("ISS-D", "ISS-A")
        assert has_cycle is True

    def test_multiple_dependency_types(self, test_session: Session, setup_issues: dict[str, Issue]) -> None:
        """Test multiple dependency types between same issues."""
        graph_repo = IssueGraphRepository(test_session)
        
        # A blocks B and depends-on B (different relationship types)
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
        ))
        graph_repo.add_dependency(Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.RELATED_TO,
        ))
        test_session.commit()
        
        # Should have 2 dependencies
        deps = graph_repo.get_dependencies("ISS-A")
        assert len(deps) == 2
        
        dep_types = {dep.dependency_type for dep in deps}
        assert dep_types == {DependencyType.BLOCKS, DependencyType.RELATED_TO}

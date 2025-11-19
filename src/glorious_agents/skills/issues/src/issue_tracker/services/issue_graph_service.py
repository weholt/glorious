"""Issue dependency graph management service."""

from collections import deque
from typing import Any

from issue_tracker.adapters.db.unit_of_work import UnitOfWork
from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.issue import Issue, IssueStatus
from issue_tracker.domain.exceptions import InvariantViolationError, NotFoundError

__all__ = ["IssueGraphService"]


class IssueGraphService:
    """Service for managing issue dependency graphs.

    Handles dependency relationships between issues including:
    - Add/remove dependencies with cycle prevention
    - Query dependencies and dependents
    - Find blockers and blocked issues
    - Calculate ready queue (issues with no open blockers)
    - Path finding and dependency chain analysis

    Enforces graph invariants:
    - No cycles in blocking dependencies
    - Validates both issues exist before creating dependency
    """

    def __init__(
        self,
        uow: UnitOfWork,
        max_depth: int = 10,
    ) -> None:
        """Initialize IssueGraphService.

        Args:
            uow: Unit of work for transaction management
            max_depth: Maximum dependency depth for tree operations (default: 10)

        Example:
            >>> from issue_tracker.adapters.db.engine import create_db_engine
            >>> from issue_tracker.adapters.db.unit_of_work import UnitOfWork
            >>> engine = create_db_engine()
            >>> uow = UnitOfWork(engine)
            >>> service = IssueGraphService(uow)
        """
        self._uow = uow
        self._max_depth = max_depth

    def add_dependency(
        self,
        from_issue_id: str,
        to_issue_id: str,
        dependency_type: DependencyType,
        description: str | None = None,
    ) -> Dependency:
        """Add a dependency between two issues.

        Args:
            from_issue_id: Source issue ID (depends on target)
            to_issue_id: Target issue ID (depended upon)
            dependency_type: Type of dependency relationship
            description: Optional description of relationship

        Returns:
            Created dependency

        Raises:
            EntityNotFoundError: If either issue doesn't exist
            InvariantViolationError: If adding would create a cycle

        Example:
            >>> service.add_dependency("ISS-1", "ISS-2", DependencyType.BLOCKS)
            Dependency(from_issue_id='ISS-1', to_issue_id='ISS-2', ...)
        """
        with self._uow:
            # Validate both issues exist
            from_issue = self._uow.issues.get(from_issue_id)
            if not from_issue:
                raise NotFoundError(f"Issue not found: {from_issue_id}")

            to_issue = self._uow.issues.get(to_issue_id)
            if not to_issue:
                raise NotFoundError(f"Issue not found: {to_issue_id}")

            # Create dependency (validation happens in __post_init__)
            dependency = Dependency(
                from_issue_id=from_issue_id,
                to_issue_id=to_issue_id,
                dependency_type=dependency_type,
                description=description,
            )

            # Check for cycles
            if self._uow.graph.has_cycle(from_issue_id, to_issue_id):
                raise InvariantViolationError(
                    f"Adding dependency from {from_issue_id} to {to_issue_id} would create a cycle"
                )

            # Add dependency
            saved_dep = self._uow.graph.add_dependency(dependency)

        return saved_dep

    def remove_dependency(
        self,
        from_issue_id: str,
        to_issue_id: str,
        dependency_type: DependencyType,
    ) -> bool:
        """Remove a dependency between two issues.

        Args:
            from_issue_id: Source issue ID
            to_issue_id: Target issue ID
            dependency_type: Type of dependency to remove

        Returns:
            True if removed, False if not found

        Example:
            >>> service.remove_dependency("ISS-1", "ISS-2", DependencyType.BLOCKS)
            True
        """
        with self._uow:
            return self._uow.graph.remove_dependency(from_issue_id, to_issue_id, dependency_type)

    def get_dependencies(
        self,
        issue_id: str,
        dependency_type: DependencyType | None = None,
    ) -> list[Dependency]:
        """Get dependencies of an issue (issues this issue depends on).

        Args:
            issue_id: Issue identifier
            dependency_type: Optional filter by type

        Returns:
            List of outgoing dependencies

        Example:
            >>> service.get_dependencies("ISS-1")
            [Dependency(from_issue_id='ISS-1', to_issue_id='ISS-2', ...)]
        """
        deps = self._uow.graph.get_dependencies(issue_id)
        if dependency_type:
            deps = [d for d in deps if d.dependency_type == dependency_type]
        return deps

    def get_dependents(
        self,
        issue_id: str,
        dependency_type: DependencyType | None = None,
    ) -> list[Dependency]:
        """Get dependents of an issue (issues that depend on this issue).

        Args:
            issue_id: Issue identifier
            dependency_type: Optional filter by type

        Returns:
            List of incoming dependencies

        Example:
            >>> service.get_dependents("ISS-2")
            [Dependency(from_issue_id='ISS-1', to_issue_id='ISS-2', ...)]
        """
        deps = self._uow.graph.get_dependents(issue_id)
        if dependency_type:
            deps = [d for d in deps if d.dependency_type == dependency_type]
        return deps

    def get_blockers(self, issue_id: str) -> list[Issue]:
        """Get all issues blocking this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of blocker Issue objects

        Example:
            >>> service.get_blockers("ISS-1")
            [Issue(id='ISS-2', status=IssueStatus.OPEN, ...)]
        """
        blocker_ids = self._uow.graph.get_blockers(issue_id)
        issues = []
        for blocker_id in blocker_ids:
            issue = self._uow.issues.get(blocker_id)
            if issue:
                issues.append(issue)
        return issues

    def get_blocked_issues(self, issue_id: str) -> list[Issue]:
        """Get all issues blocked by this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of blocked Issue objects

        Example:
            >>> service.get_blocked_issues("ISS-2")
            [Issue(id='ISS-1', status=IssueStatus.BLOCKED, ...)]
        """
        blocked_ids = self._uow.graph.get_blocked_by(issue_id)
        issues = []
        for blocked_id in blocked_ids:
            issue = self._uow.issues.get(blocked_id)
            if issue:
                issues.append(issue)
        return issues

    def get_ready_queue(self, status_filter: list[IssueStatus] | None = None) -> list[Issue]:
        """Get issues ready to work (no open blockers).

        Args:
            status_filter: Optional list of statuses to include (default: OPEN, IN_PROGRESS)

        Returns:
            List of ready issues (not closed/resolved with no open blockers)

        Example:
            >>> service.get_ready_queue()
            [Issue(id='ISS-3', status=IssueStatus.OPEN, ...)]
        """
        # Default to active statuses
        if status_filter is None:
            status_filter = [IssueStatus.OPEN, IssueStatus.IN_PROGRESS]

        # Get all issues
        all_issues = self._uow.issues.list_all()

        # Filter to requested statuses
        active_issues = [issue for issue in all_issues if issue.status in status_filter]

        # Check each issue for open blockers
        ready = []
        for issue in active_issues:
            blockers = self._uow.graph.get_blockers(issue.id)

            # Issue is ready if it has no blockers OR all blockers are closed/resolved
            has_open_blocker = False
            for blocker_id in blockers:
                blocker_issue = self._uow.issues.get(blocker_id)
                if blocker_issue and blocker_issue.status not in {
                    IssueStatus.CLOSED,
                    IssueStatus.RESOLVED,
                }:
                    has_open_blocker = True
                    break

            if not has_open_blocker:
                ready.append(issue)

        return ready

    def has_path(self, from_issue_id: str, to_issue_id: str) -> bool:
        """Check if path exists from one issue to another.

        Uses cycle detection - a forward path from A to B exists
        if adding the reverse edge B->A would create a cycle.

        Args:
            from_issue_id: Source issue ID
            to_issue_id: Target issue ID

        Returns:
            True if path exists

        Example:
            >>> service.has_path("ISS-1", "ISS-3")
            True  # If ISS-1 -> ISS-2 -> ISS-3
        """
        # A forward path exists from A to B if adding the reverse edge B->A would create a cycle
        return self._uow.graph.has_cycle(to_issue_id, from_issue_id)

    def get_dependency_chain(
        self,
        from_issue_id: str,
        to_issue_id: str,
    ) -> list[Dependency]:
        """Get shortest dependency chain between two issues using BFS.

        Args:
            from_issue_id: Source issue ID
            to_issue_id: Target issue ID

        Returns:
            List of dependencies forming shortest path, empty if no path

        Example:
            >>> service.get_dependency_chain("ISS-1", "ISS-3")
            [Dependency(from_issue_id='ISS-1', to_issue_id='ISS-2', ...),
             Dependency(from_issue_id='ISS-2', to_issue_id='ISS-3', ...)]
        """
        if from_issue_id == to_issue_id:
            return []

        # BFS to find shortest path by exploring dependencies on-the-fly
        queue: deque[tuple[str, list[Dependency]]] = deque([(from_issue_id, [])])
        visited: set[str] = {from_issue_id}

        while queue:
            current_id, path = queue.popleft()

            # Get dependencies of current issue
            deps = self._uow.graph.get_dependencies(current_id)

            for dependency in deps:
                neighbor_id = dependency.to_issue_id

                if neighbor_id == to_issue_id:
                    # Found target - return path
                    return path + [dependency]

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [dependency]))

        # No path found
        return []

    def detect_cycles(self) -> list[list[Issue]]:
        """Detect all dependency cycles in the graph.

        Uses DFS to find strongly connected components (cycles).
        Each cycle is returned as a list of Issues forming the cycle.

        Returns:
            List of cycles, where each cycle is a list of Issue objects

        Example:
            >>> service.detect_cycles()
            [[Issue(id='ISS-1', ...), Issue(id='ISS-2', ...), Issue(id='ISS-3', ...)]]
        """
        # Build adjacency list by querying all issues
        all_issues = self._uow.issues.list_all()
        adjacency: dict[str, list[str]] = {}

        for issue in all_issues:
            issue_id = issue.id
            deps = self._uow.graph.get_dependencies(issue_id)
            adjacency[issue_id] = [dep.to_issue_id for dep in deps]

        # Find all cycles using DFS with path tracking
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            """DFS to find cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found cycle - extract cycle from path
                    cycle_start_idx = path.index(neighbor)
                    cycle_ids = path[cycle_start_idx:]

                    # Normalize cycle (sort to get canonical form)
                    normalized = tuple(sorted(cycle_ids))

                    # Check if we haven't seen this cycle yet
                    if normalized not in {tuple(sorted(c)) for c in cycles}:
                        cycles.append(cycle_ids[:])

            path.pop()
            rec_stack.remove(node)

        # Start DFS from each unvisited node
        for issue_id in adjacency:
            if issue_id not in visited:
                dfs(issue_id)

        # Convert issue IDs to Issue objects
        result: list[list[Issue]] = []
        for cycle_ids in cycles:
            cycle_issues: list[Issue] = []
            for issue_id in cycle_ids:
                maybe_issue = self._uow.issues.get(issue_id)
                if maybe_issue:
                    cycle_issues.append(maybe_issue)
            if cycle_issues:
                result.append(cycle_issues)

        return result

    def build_dependency_tree(
        self,
        issue_id: str,
        reverse: bool = False,
        max_depth: int | None = None,
    ) -> dict[str, Any]:
        """Build a dependency tree starting from an issue.

        Args:
            issue_id: Root issue identifier
            reverse: If True, build tree of dependents (what depends on this),
                    if False, build tree of dependencies (what this depends on)
            max_depth: Maximum tree depth (defaults to service max_depth)

        Returns:
            Dictionary with tree structure:
            {
                "issue_id": str,
                "issue": Issue,
                "dependencies": list[dict],  # Recursive tree structure
                "depth": int
            }

        Raises:
            NotFoundError: If root issue doesn't exist

        Example:
            >>> tree = service.build_dependency_tree("ISS-1")
            >>> tree["issue_id"]
            'ISS-1'
            >>> len(tree["dependencies"])
            2
        """
        root_issue = self._uow.issues.get(issue_id)
        if not root_issue:
            raise NotFoundError(f"Issue not found: {issue_id}")

        max_depth = max_depth or self._max_depth
        visited: set[str] = set()

        def build_node(current_id: str, current_depth: int) -> dict[str, Any] | None:
            """Recursively build tree node."""
            if current_depth > max_depth:
                return None

            if current_id in visited:
                # Circular reference - mark as such
                return {
                    "issue_id": current_id,
                    "issue": None,
                    "is_circular": True,
                    "depth": current_depth,
                    "dependencies": [],
                }

            visited.add(current_id)

            # Get the issue
            issue = self._uow.issues.get(current_id)
            if not issue:
                return None

            # Get related issues based on direction
            if reverse:
                # Get dependents (issues that depend on this one)
                related_deps = self.get_dependents(current_id)
            else:
                # Get dependencies (issues this one depends on)
                related_deps = self.get_dependencies(current_id)

            # Build child nodes
            children = []
            for dep in related_deps:
                target_id = dep.from_issue_id if reverse else dep.to_issue_id
                child_node = build_node(target_id, current_depth + 1)
                if child_node:
                    child_node["dependency_type"] = dep.dependency_type.value
                    child_node["description"] = dep.description
                    children.append(child_node)

            visited.remove(current_id)  # Allow visiting from other paths

            return {
                "issue_id": current_id,
                "issue": issue,
                "is_circular": False,
                "depth": current_depth,
                "dependencies": children,
            }

        root_node = build_node(issue_id, 0)
        if not root_node:
            raise NotFoundError(f"Could not build tree for issue: {issue_id}")

        return root_node


__all__ = ["IssueGraphService"]

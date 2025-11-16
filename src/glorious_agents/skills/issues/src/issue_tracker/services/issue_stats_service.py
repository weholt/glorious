"""Issue tracking statistics service."""

from collections import defaultdict

from issue_tracker.adapters.db.unit_of_work import UnitOfWork
from issue_tracker.domain.entities.issue import Issue, IssueStatus
from issue_tracker.domain.value_objects import IssuePriority


class IssueStatsService:
    """Service for computing issue tracking metrics.

    Provides:
    - Count issues by status and priority
    - Find blocked issues (issues with open blockers)
    - Calculate longest dependency chain
    - Completion rate tracking
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize stats service.

        Args:
            uow: Unit of work for transaction management

        Example:
            >>> from issue_tracker.adapters.db.engine import create_db_engine
            >>> from issue_tracker.adapters.db.unit_of_work import UnitOfWork
            >>> engine = create_db_engine()
            >>> uow = UnitOfWork(engine)
            >>> service = IssueStatsService(uow)
        """
        self._uow = uow

    def count_by_status(self) -> dict[IssueStatus, int]:
        """Count issues grouped by status.

        Returns:
            Dictionary mapping status to count

        Example:
            >>> service.count_by_status()
            {IssueStatus.OPEN: 5, IssueStatus.CLOSED: 3, ...}
        """
        all_issues = self._uow.issues.list_all()

        counts: dict[IssueStatus, int] = defaultdict(int)
        for issue in all_issues:
            counts[issue.status] += 1

        return dict(counts)

    def count_by_priority(self) -> dict[IssuePriority, int]:
        """Count issues grouped by priority.

        Returns:
            Dictionary mapping priority to count

        Example:
            >>> service.count_by_priority()
            {IssuePriority.HIGH: 10, IssuePriority.MEDIUM: 20, ...}
        """
        all_issues = self._uow.issues.list_all()

        counts: dict[IssuePriority, int] = defaultdict(int)
        for issue in all_issues:
            counts[issue.priority] += 1

        return dict(counts)

    def get_blocked_issues(self) -> list[Issue]:
        """Get all issues that are currently blocked.

        An issue is blocked if it has at least one blocker that is not closed/resolved.

        Returns:
            List of blocked Issue objects

        Example:
            >>> service.get_blocked_issues()
            [Issue(id='ISS-1', status=IssueStatus.BLOCKED, ...)]
        """
        all_issues = self._uow.issues.list_all()

        blocked_issues: list[Issue] = []
        for issue in all_issues:
            # Get blockers for this issue
            blocker_ids = self._uow.graph.get_blockers(issue.id)

            # Check if any blockers are open
            has_open_blocker = False
            for blocker_id in blocker_ids:
                blocker = self._uow.issues.get(blocker_id)
                if blocker and blocker.status not in {IssueStatus.CLOSED, IssueStatus.RESOLVED}:
                    has_open_blocker = True
                    break

            if has_open_blocker:
                blocked_issues.append(issue)

        return blocked_issues

    def get_longest_dependency_chain(self) -> list[Issue]:
        """Find the longest dependency chain.

        Uses DFS to find the maximum depth path in the dependency graph.

        Returns:
            List of Issues forming the longest chain (root to leaf)

        Example:
            >>> chain = service.get_longest_dependency_chain()
            >>> len(chain)
            5
        """
        all_issues = self._uow.issues.list_all()

        if not all_issues:
            return []

        # Build adjacency list for all issues
        adjacency: dict[str, list[str]] = defaultdict(list)
        for issue in all_issues:
            deps = self._uow.graph.get_dependencies(issue.id)
            for dep in deps:
                adjacency[dep.from_issue_id].append(dep.to_issue_id)

        # Find longest path using DFS
        longest_path: list[str] = []

        def dfs(issue_id: str, path: list[str], visited: set[str]) -> None:
            """DFS to find longest path."""
            nonlocal longest_path

            path.append(issue_id)
            visited.add(issue_id)

            # Update longest if current path is longer
            if len(path) > len(longest_path):
                longest_path = path[:]

            # Explore neighbors
            for neighbor_id in adjacency.get(issue_id, []):
                if neighbor_id not in visited:
                    dfs(neighbor_id, path, visited)

            # Backtrack
            path.pop()
            visited.remove(issue_id)

        # Try DFS from each issue (to handle disconnected components)
        for issue in all_issues:
            dfs(issue.id, [], set())

        # Convert IDs back to Issue objects
        result: list[Issue] = []
        for issue_id in longest_path:
            maybe_issue = self._uow.issues.get(issue_id)
            if maybe_issue:
                result.append(maybe_issue)

        return result

    def get_completion_rate(self) -> dict[str, float | int]:
        """Calculate completion rate.

        Returns:
            Dictionary with:
                - total: Total number of issues
                - closed: Number of closed issues
                - resolved: Number of resolved issues
                - completion_rate: Percentage of closed issues (0-100)
                - resolution_rate: Percentage of closed or resolved issues (0-100)

        Example:
            >>> service.get_completion_rate()
            {'total': 100, 'closed': 30, 'resolved': 20, 'completion_rate': 30.0, ...}
        """
        all_issues = self._uow.issues.list_all()

        total = len(all_issues)
        if total == 0:
            return {
                "total": 0,
                "closed": 0,
                "resolved": 0,
                "completion_rate": 0.0,
                "resolution_rate": 0.0,
            }

        closed_count = sum(1 for issue in all_issues if issue.status == IssueStatus.CLOSED)
        resolved_count = sum(1 for issue in all_issues if issue.status == IssueStatus.RESOLVED)

        completion_rate = (closed_count / total) * 100
        resolution_rate = ((closed_count + resolved_count) / total) * 100

        return {
            "total": total,
            "closed": closed_count,
            "resolved": resolved_count,
            "completion_rate": round(completion_rate, 2),
            "resolution_rate": round(resolution_rate, 2),
        }

    def get_priority_breakdown(self) -> dict[str, dict[str, int]]:
        """Get detailed breakdown of issues by priority and status.

        Returns:
            Nested dictionary with priority -> status -> count mapping

        Example:
            >>> service.get_priority_breakdown()
            {'high': {'open': 5, 'closed': 3}, 'medium': {'open': 10}, ...}
        """
        all_issues = self._uow.issues.list_all()

        # Build nested breakdown
        breakdown: dict[str, dict[str, int]] = {}

        for priority in IssuePriority:
            priority_name = priority.name.lower()
            breakdown[priority_name] = {}

            for status in IssueStatus:
                status_name = status.name.lower()
                count = sum(1 for issue in all_issues if issue.priority == priority and issue.status == status)
                if count > 0:  # Only include non-zero counts
                    breakdown[priority_name][status_name] = count

        return breakdown


__all__ = ["IssueStatsService"]

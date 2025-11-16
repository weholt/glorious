"""Issue service for business logic operations.

Provides high-level operations for issue management, coordinating
between repositories and enforcing business rules.
"""

from issue_tracker.adapters.db.unit_of_work import UnitOfWork
from issue_tracker.domain.entities.comment import Comment
from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.issue import Issue, IssuePriority, IssueStatus, IssueType
from issue_tracker.domain.ports import Clock, IdentifierService


class IssueService:
    """Service for issue management operations.

    Coordinates between repositories and enforces business rules.
    All operations use UnitOfWork for transaction management.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
    ) -> None:
        """Initialize issue service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock

    def create_issue(
        self,
        title: str,
        description: str = "",
        priority: IssuePriority = IssuePriority.MEDIUM,
        issue_type: IssueType = IssueType.TASK,
        assignee: str | None = None,
        epic_id: str | None = None,
        labels: list[str] | None = None,
        project_id: str = "default",
        custom_id: str | None = None,
    ) -> Issue:
        """Create a new issue.

        Args:
            title: Issue title
            description: Issue description (default: empty)
            priority: Issue priority (default: MEDIUM)
            issue_type: Issue type (default: TASK)
            assignee: Optional assignee username
            epic_id: Optional parent epic ID
            labels: Optional list of labels
            project_id: Project identifier (default: "default")
            custom_id: Optional custom issue ID (auto-generated if not provided)

        Returns:
            Created issue entity

        Examples:
            >>> service.create_issue("Fix bug", priority=IssuePriority.HIGH)
            Issue(id='issue-abc123', title='Fix bug', ...)

            >>> service.create_issue("Custom", custom_id="PROJECT-123")
            Issue(id='PROJECT-123', title='Custom', ...)
        """
        # Use custom ID if provided, otherwise generate one
        if custom_id:
            # Validate that custom ID doesn't already exist
            existing = self.uow.issues.get(custom_id)
            if existing:
                raise ValueError(f"Issue with ID '{custom_id}' already exists")
            issue_id = custom_id
        else:
            issue_id = self.id_service.generate("issue")

        now = self.clock.now()

        issue = Issue(
            id=issue_id,
            project_id=project_id,
            title=title,
            description=description,
            status=IssueStatus.OPEN,
            priority=priority,
            type=issue_type,
            assignee=assignee,
            epic_id=epic_id,
            labels=labels or [],
            created_at=now,
            updated_at=now,
        )

        return self.uow.issues.save(issue)

    def get_issue(self, issue_id: str) -> Issue | None:
        """Get issue by ID.

        Args:
            issue_id: Issue identifier

        Returns:
            Issue if found, None otherwise
        """
        return self.uow.issues.get(issue_id)

    def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: IssuePriority | None = None,
        assignee: str | None = None,
        epic_id: str | None = None,
    ) -> Issue | None:
        """Update issue fields.

        Args:
            issue_id: Issue identifier
            title: New title (if provided)
            description: New description (if provided)
            priority: New priority (if provided)
            assignee: New assignee (if provided)
            epic_id: New epic ID (if provided)

        Returns:
            Updated issue if found, None otherwise
        """
        issue = self.uow.issues.get(issue_id)
        if not issue:
            return None

        if title is not None:
            issue.title = title
        if description is not None:
            issue.description = description
        if priority is not None:
            issue.priority = priority
        if assignee is not None:
            issue.assignee = assignee
        if epic_id is not None:
            issue.epic_id = epic_id

        issue.updated_at = self.clock.now()
        return self.uow.issues.save(issue)

    def transition_issue(self, issue_id: str, new_status: IssueStatus) -> Issue | None:
        """Transition issue to new status.

        Args:
            issue_id: Issue identifier
            new_status: Target status

        Returns:
            Updated issue if found, None otherwise

        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        issue = self.uow.issues.get(issue_id)
        if not issue:
            return None

        # transition() returns a new Issue object
        transitioned = issue.transition(new_status)
        transitioned.updated_at = self.clock.now()

        if new_status == IssueStatus.CLOSED:
            transitioned.closed_at = self.clock.now()

        return self.uow.issues.save(transitioned)

    def close_issue(self, issue_id: str) -> Issue | None:
        """Close an issue.

        If the issue is not in RESOLVED status, it will be transitioned to
        RESOLVED first, then to CLOSED.

        Args:
            issue_id: Issue identifier

        Returns:
            Closed issue if found, None otherwise
        """
        issue = self.uow.issues.get(issue_id)
        if not issue:
            return None

        # If not already resolved, transition to resolved first
        if issue.status != IssueStatus.RESOLVED:
            issue = self.transition_issue(issue_id, IssueStatus.RESOLVED)
            if not issue:
                return None

        # Then close it
        return self.transition_issue(issue_id, IssueStatus.CLOSED)

    def reopen_issue(self, issue_id: str) -> Issue | None:
        """Reopen a closed issue.

        Args:
            issue_id: Issue identifier

        Returns:
            Reopened issue if found, None otherwise
        """
        issue = self.uow.issues.get(issue_id)
        if not issue:
            return None

        issue.status = IssueStatus.OPEN
        issue.closed_at = None
        issue.updated_at = self.clock.now()
        return self.uow.issues.save(issue)

    def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue.

        Args:
            issue_id: Issue identifier

        Returns:
            True if deleted, False if not found
        """
        return self.uow.issues.delete(issue_id)

    def list_issues(
        self,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee: str | None = None,
        epic_id: str | None = None,
        issue_type: IssueType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Issue]:
        """List issues with optional filtering.

        Args:
            status: Filter by status
            priority: Filter by priority
            assignee: Filter by assignee
            epic_id: Filter by epic
            issue_type: Filter by type
            limit: Maximum results (default: 100)
            offset: Offset for pagination (default: 0)

        Returns:
            List of matching issues
        """
        if status:
            return self.uow.issues.list_by_status(status, limit, offset)
        elif priority is not None:
            return self.uow.issues.list_by_priority(priority, limit, offset)
        elif assignee:
            return self.uow.issues.list_by_assignee(assignee, limit, offset)
        elif epic_id:
            return self.uow.issues.list_by_epic(epic_id, limit, offset)
        elif issue_type:
            return self.uow.issues.list_by_type(issue_type, limit, offset)
        else:
            return self.uow.issues.list_all(limit, offset)

    def add_comment(self, issue_id: str, author: str, text: str) -> Comment | None:
        """Add comment to issue.

        Args:
            issue_id: Issue identifier
            author: Comment author username
            text: Comment text content

        Returns:
            Created comment if issue exists, None otherwise
        """
        # Verify issue exists
        issue = self.uow.issues.get(issue_id)
        if not issue:
            return None

        comment_id = self.id_service.generate("comment")
        now = self.clock.now()

        comment = Comment(
            id=comment_id,
            issue_id=issue_id,
            author=author,
            text=text,
            created_at=now,
            updated_at=now,
        )

        return self.uow.comments.save(comment)

    def list_comments(self, issue_id: str) -> list[Comment]:
        """List all comments for an issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of comments ordered by creation time
        """
        return self.uow.comments.list_by_issue(issue_id)

    def add_dependency(
        self,
        from_issue_id: str,
        to_issue_id: str,
        dependency_type: DependencyType = DependencyType.DEPENDS_ON,
    ) -> Dependency | None:
        """Add dependency between issues.

        Args:
            from_issue_id: Source issue ID
            to_issue_id: Target issue ID
            dependency_type: Type of dependency (default: DEPENDS_ON)

        Returns:
            Created dependency if no cycle detected, None otherwise
        """
        # Check for cycles
        if self.uow.graph.has_cycle(from_issue_id, to_issue_id):
            return None

        now = self.clock.now()
        dependency = Dependency(
            from_issue_id=from_issue_id,
            to_issue_id=to_issue_id,
            dependency_type=dependency_type,
            created_at=now,
        )

        return self.uow.graph.add_dependency(dependency)

    def remove_dependency(
        self,
        from_issue_id: str,
        to_issue_id: str,
        dependency_type: DependencyType = DependencyType.DEPENDS_ON,
    ) -> bool:
        """Remove dependency between issues.

        Args:
            from_issue_id: Source issue ID
            to_issue_id: Target issue ID
            dependency_type: Type of dependency (default: DEPENDS_ON)

        Returns:
            True if removed, False if not found
        """
        return self.uow.graph.remove_dependency(from_issue_id, to_issue_id, dependency_type)

    def get_blockers(self, issue_id: str) -> list[str]:
        """Get issues blocking this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs that block this issue
        """
        return self.uow.graph.get_blockers(issue_id)

    def get_blocked_issues(self, issue_id: str) -> list[str]:
        """Get issues blocked by this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs blocked by this issue
        """
        return self.uow.graph.get_blocked_by(issue_id)

    def bulk_update_status(self, issue_ids: list[str], new_status: IssueStatus) -> tuple[list[Issue], list[str]]:
        """Update status for multiple issues in a single transaction.

        Args:
            issue_ids: List of issue IDs to update
            new_status: New status to apply

        Returns:
            Tuple of (successfully updated issues, failed issue IDs)
        """
        updated: list[Issue] = []
        failed: list[str] = []

        for issue_id in issue_ids:
            try:
                issue = self.transition_issue(issue_id, new_status)
                if issue:
                    updated.append(issue)
                else:
                    failed.append(issue_id)
            except Exception:
                failed.append(issue_id)

        return updated, failed

    def bulk_update_priority(self, issue_ids: list[str], new_priority: IssuePriority) -> tuple[list[Issue], list[str]]:
        """Update priority for multiple issues in a single transaction.

        Args:
            issue_ids: List of issue IDs to update
            new_priority: New priority to apply

        Returns:
            Tuple of (successfully updated issues, failed issue IDs)
        """
        updated: list[Issue] = []
        failed: list[str] = []

        for issue_id in issue_ids:
            try:
                issue = self.update_issue(issue_id, priority=new_priority)
                if issue:
                    updated.append(issue)
                else:
                    failed.append(issue_id)
            except Exception:
                failed.append(issue_id)

        return updated, failed

    def bulk_assign(self, issue_ids: list[str], assignee: str) -> tuple[list[Issue], list[str]]:
        """Assign multiple issues to a user in a single transaction.

        Args:
            issue_ids: List of issue IDs to assign
            assignee: Username to assign issues to

        Returns:
            Tuple of (successfully updated issues, failed issue IDs)
        """
        updated: list[Issue] = []
        failed: list[str] = []

        for issue_id in issue_ids:
            try:
                issue = self.update_issue(issue_id, assignee=assignee)
                if issue:
                    updated.append(issue)
                else:
                    failed.append(issue_id)
            except Exception:
                failed.append(issue_id)

        return updated, failed

    def set_epic(self, issue_id: str, epic_id: str) -> Issue | None:
        """Set the epic for an issue.
        
        Args:
            issue_id: ID of the issue
            epic_id: ID of the epic to assign
            
        Returns:
            Updated issue or None if not found
        """
        with self.uow:
            issue = self.uow.issues.get(issue_id)
            if not issue:
                return None
            
            issue.epic_id = epic_id
            issue.updated_at = self.clock.now()
            self.uow.issues.save(issue)
            self.uow.commit()
            return issue
    
    def clear_epic(self, issue_id: str) -> Issue | None:
        """Clear the epic from an issue.
        
        Args:
            issue_id: ID of the issue
            
        Returns:
            Updated issue or None if not found
        """
        with self.uow:
            issue = self.uow.issues.get(issue_id)
            if not issue:
                return None
            
            issue.epic_id = None
            issue.updated_at = self.clock.now()
            self.uow.issues.save(issue)
            self.uow.commit()
            return issue
    
    def get_epic_issues(self, epic_id: str) -> list[Issue]:
        """Get all issues in an epic.
        
        Args:
            epic_id: ID of the epic
            
        Returns:
            List of issues in the epic
        """
        with self.uow:
            # Get all issues with this epic_id
            all_issues = self.uow.issues.list()
            return [issue for issue in all_issues if issue.epic_id == epic_id]


__all__ = ["IssueService"]

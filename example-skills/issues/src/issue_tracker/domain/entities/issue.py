"""Issue entity for issue tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from issue_tracker.domain.exceptions import InvalidTransitionError, InvariantViolationError
from issue_tracker.domain.utils import utcnow_naive
from issue_tracker.domain.value_objects import IssuePriority


class IssueStatus(str, Enum):
    """Issue lifecycle status.

    Compatible with Beads status transitions.
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ARCHIVED = "archived"


class IssueType(str, Enum):
    """Issue type classification.

    Compatible with Beads issue types.
    """

    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"


@dataclass
class Issue:
    """Issue entity for tracking work items.

    Compatible with Beads issue tracking system. Supports full lifecycle
    management, dependencies, labels, and epic relationships.

    Lifecycle:
        OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED
        OPEN -> BLOCKED -> OPEN
        Any state -> ARCHIVED
        ARCHIVED -> OPEN (restore)

    Invariants:
        - Title must be non-empty
        - Priority must be 0-4
        - Epic references only valid for non-epic issues
        - Assignee must be non-empty if set
        - Labels are unique (no duplicates)
        - Cannot transition CLOSED -> OPEN (must restore from ARCHIVED)

    Attributes:
        id: Unique issue identifier (e.g., "issue-abc123")
        project_id: Project this issue belongs to
        title: Issue title/summary
        description: Detailed description
        status: Current lifecycle status (default: OPEN)
        priority: Priority level 0-4 (default: 2/MEDIUM)
        type: Issue type (BUG, FEATURE, TASK, EPIC, CHORE)
        assignee: Optional assigned user
        epic_id: Parent epic identifier (only for non-epic issues)
        labels: List of tags/labels
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        closed_at: Closure timestamp (if applicable)
    """

    id: str
    project_id: str
    title: str
    description: str
    status: IssueStatus = IssueStatus.OPEN
    priority: IssuePriority = IssuePriority.MEDIUM
    type: IssueType = IssueType.TASK
    assignee: str | None = None
    epic_id: str | None = None
    labels: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate invariants after initialization."""
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Enforce business rules."""
        if not self.title or not self.title.strip():
            raise InvariantViolationError("Issue title cannot be empty")

        if not isinstance(self.priority, IssuePriority):
            try:
                # Try to convert if it's an int
                self.priority = IssuePriority(self.priority)
            except (ValueError, TypeError):
                raise InvariantViolationError(f"Invalid priority: {self.priority}. Must be 0-4")

        if self.type == IssueType.EPIC and self.epic_id is not None:
            raise InvariantViolationError("Epic issues cannot have parent epic", self.id)

        if self.assignee is not None and not self.assignee.strip():
            raise InvariantViolationError("Assignee cannot be empty string", self.id)

        # Deduplicate labels
        if self.labels:
            self.labels = list(dict.fromkeys(self.labels))

    def transition(self, target_status: IssueStatus) -> "Issue":
        """Transition issue to new status with validation.

        Valid transitions:
            OPEN -> IN_PROGRESS, BLOCKED, RESOLVED, ARCHIVED
            IN_PROGRESS -> OPEN, BLOCKED, RESOLVED, ARCHIVED
            BLOCKED -> OPEN, RESOLVED, ARCHIVED
            RESOLVED -> CLOSED, ARCHIVED
            CLOSED -> ARCHIVED (cannot reopen)
            ARCHIVED -> OPEN (restore)

        Args:
            target_status: Desired status

        Returns:
            New Issue instance with updated status

        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        valid_transitions = {
            IssueStatus.OPEN: {
                IssueStatus.IN_PROGRESS,
                IssueStatus.BLOCKED,
                IssueStatus.RESOLVED,
                IssueStatus.ARCHIVED,
            },
            IssueStatus.IN_PROGRESS: {
                IssueStatus.OPEN,
                IssueStatus.BLOCKED,
                IssueStatus.RESOLVED,
                IssueStatus.ARCHIVED,
            },
            IssueStatus.BLOCKED: {
                IssueStatus.OPEN,
                IssueStatus.RESOLVED,
                IssueStatus.ARCHIVED,
            },
            IssueStatus.RESOLVED: {
                IssueStatus.CLOSED,
                IssueStatus.ARCHIVED,
            },
            IssueStatus.CLOSED: {
                IssueStatus.ARCHIVED,
            },
            IssueStatus.ARCHIVED: {
                IssueStatus.OPEN,
            },
        }

        if target_status not in valid_transitions[self.status]:
            raise InvalidTransitionError(
                message=f"Cannot transition from {self.status.value} to {target_status.value}",
                entity_id=str(self.id),
                current_state=self.status.value,
                target_state=target_status.value,
            )

        new_closed_at = self.closed_at
        if target_status == IssueStatus.CLOSED:
            new_closed_at = utcnow_naive()
        elif target_status == IssueStatus.OPEN and self.status == IssueStatus.ARCHIVED:
            # Restoring from archive
            new_closed_at = None

        return Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=target_status,
            priority=self.priority,
            type=self.type,
            assignee=self.assignee,
            epic_id=self.epic_id,
            labels=self.labels.copy(),
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=new_closed_at,
        )

    def add_label(self, label: str) -> "Issue":
        """Add a label to the issue (idempotent).

        Args:
            label: Label to add

        Returns:
            New Issue instance with label added
        """
        if not label or not label.strip():
            raise InvariantViolationError("Label cannot be empty")

        label = label.strip()
        new_labels = self.labels.copy()
        if label not in new_labels:
            new_labels.append(label)

        return Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            type=self.type,
            assignee=self.assignee,
            epic_id=self.epic_id,
            labels=new_labels,
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=self.closed_at,
        )

    def remove_label(self, label: str) -> "Issue":
        """Remove a label from the issue (idempotent).

        Args:
            label: Label to remove

        Returns:
            New Issue instance with label removed
        """
        label = label.strip()
        new_labels = [lbl for lbl in self.labels if lbl != label]

        return Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            type=self.type,
            assignee=self.assignee,
            epic_id=self.epic_id,
            labels=new_labels,
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=self.closed_at,
        )

    def assign_to(self, user_id: str | None) -> "Issue":
        """Assign issue to a user.

        Args:
            user_id: Username to assign (or None to unassign)

        Returns:
            New Issue instance with assignee updated
        """
        if user_id is not None and not user_id.strip():
            raise InvariantViolationError("Assignee cannot be empty string", self.id)

        # Trim whitespace from user_id
        trimmed_user_id = user_id.strip() if user_id is not None else None

        return Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            type=self.type,
            assignee=trimmed_user_id,
            epic_id=self.epic_id,
            labels=self.labels.copy(),
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=self.closed_at,
        )

    def assign_to_epic(self, epic_id: str | None) -> "Issue":
        """Set or clear epic reference.

        Args:
            epic_id: Epic identifier (or None to clear)

        Returns:
            New Issue instance with epic_id updated

        Raises:
            InvariantViolationError: If this issue is an epic
        """
        if self.type == IssueType.EPIC:
            raise InvariantViolationError("Cannot set epic on epic issue", self.id)

        return Issue(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            type=self.type,
            assignee=self.assignee,
            epic_id=epic_id,
            labels=self.labels.copy(),
            created_at=self.created_at,
            updated_at=utcnow_naive(),
            closed_at=self.closed_at,
        )


__all__ = ["Issue", "IssueStatus", "IssueType"]

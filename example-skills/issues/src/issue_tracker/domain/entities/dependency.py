"""Dependency entity for issue tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from issue_tracker.domain.exceptions import InvariantViolationError
from issue_tracker.domain.utils import utcnow_naive


class DependencyType(str, Enum):
    """Dependency types between issues.

    Compatible with Beads dependency types.
    """

    BLOCKS = "blocks"  # Issue A blocks Issue B
    DEPENDS_ON = "depends-on"  # Issue A depends on Issue B
    RELATED_TO = "related-to"  # Issues are related
    DISCOVERED_FROM = "discovered-from"  # Issue B discovered during work on Issue A


@dataclass
class Dependency:
    """Dependency entity for issue relationships.

    Represents a directed edge between two issues.

    Attributes:
        id: Unique dependency identifier (auto-increment)
        from_issue_id: Source issue identifier
        to_issue_id: Target issue identifier
        dependency_type: Type of relationship
        description: Optional context about the dependency
        created_at: Creation timestamp
    """

    from_issue_id: str
    to_issue_id: str
    dependency_type: DependencyType
    id: int | None = None
    description: str | None = None
    created_at: datetime = field(default_factory=utcnow_naive)

    def __post_init__(self) -> None:
        """Validate invariants after initialization."""
        # Validate from != to (self-dependency)
        if self.from_issue_id == self.to_issue_id:
            raise InvariantViolationError(f"Issue cannot depend on itself: {self.from_issue_id}")

        # Trim description if provided
        if self.description is not None:
            trimmed = self.description.strip()
            self.description = trimmed if trimmed else None


__all__ = ["Dependency", "DependencyType"]

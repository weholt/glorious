"""Epic entity for issue tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from issue_tracker.domain.utils import utcnow_naive


class EpicStatus(str, Enum):
    """Epic status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


@dataclass
class Epic:
    """Epic entity for grouping related issues.

    Attributes:
        id: Unique epic identifier
        title: Epic title
        description: Optional epic description
        status: Epic status
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        closed_at: Closure timestamp (if applicable)
    """

    id: str
    title: str
    description: str | None = None
    status: EpicStatus = EpicStatus.OPEN
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)
    closed_at: datetime | None = None


__all__ = ["Epic", "EpicStatus"]

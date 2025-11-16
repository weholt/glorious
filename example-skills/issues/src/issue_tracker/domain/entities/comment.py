"""Comment entity for issue tracking."""

from dataclasses import dataclass, field
from datetime import datetime

from issue_tracker.domain.utils import utcnow_naive


@dataclass
class Comment:
    """Comment entity for issue discussions.

    Attributes:
        id: Unique comment identifier
        issue_id: Parent issue identifier
        author: Comment author username
        text: Comment text content
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    id: str
    issue_id: str
    author: str
    text: str
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)


__all__ = ["Comment"]

"""Label entity for issue tracking."""

from dataclasses import dataclass, field
from datetime import datetime

from issue_tracker.domain.utils import utcnow_naive


@dataclass
class Label:
    """Label entity for categorizing issues.

    Attributes:
        id: Unique label identifier
        name: Label name (unique)
        color: Optional hex color code
        description: Optional label description
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    id: str
    name: str
    color: str | None = None
    description: str | None = None
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)


__all__ = ["Label"]

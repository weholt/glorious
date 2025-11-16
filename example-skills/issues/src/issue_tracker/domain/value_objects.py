"""Value objects for issue tracking domain."""

from enum import IntEnum


class IssuePriority(IntEnum):
    """Issue priority levels (0=highest, 4=lowest).

    Compatible with Beads priority system.
    """

    CRITICAL = 0  # P0 - Drop everything
    HIGH = 1  # P1 - Next sprint
    MEDIUM = 2  # P2 - Normal priority (default)
    LOW = 3  # P3 - When convenient
    BACKLOG = 4  # P4 - Nice to have


__all__ = ["IssuePriority"]

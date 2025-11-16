"""Service protocols for dependency injection.

Defines interfaces for external dependencies like time providers,
ID generators, and transaction management.
"""

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Protocol for time provider services.

    Allows injection of different time sources (real time, frozen time for tests, etc.)
    """

    def now(self) -> datetime:
        """Get current UTC datetime.

        Returns:
            Current datetime in UTC timezone (naive datetime)
        """
        ...


@runtime_checkable
class IdentifierService(Protocol):
    """Protocol for generating unique identifiers.

    Used for creating IDs for issues, comments, dependencies, etc.
    """

    def generate(self, prefix: str = "issue") -> str:
        """Generate a new unique identifier.

        Args:
            prefix: Entity type prefix (e.g., "issue", "comment", "epic")

        Returns:
            New identifier with format prefix-XXXXXX (6 hex chars)

        Examples:
            >>> service.generate("issue")
            'issue-a3f8e9'
            >>> service.generate("comment")
            'comment-7b2d4c'
        """
        ...


__all__ = ["Clock", "IdentifierService"]

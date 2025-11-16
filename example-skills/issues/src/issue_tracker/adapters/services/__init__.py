"""Service implementations for dependency injection."""

import secrets
from datetime import datetime

from issue_tracker.domain.ports import Clock, IdentifierService
from issue_tracker.domain.utils import utcnow_naive


class SystemClock(Clock):
    """System clock implementation using real time."""

    def now(self) -> datetime:
        """Get current UTC datetime as naive datetime.

        Returns:
            Current UTC time with timezone info stripped
        """
        return utcnow_naive()


class HashIdentifierService(IdentifierService):
    """Identifier service using secure random hex strings."""

    def generate(self, prefix: str = "issue") -> str:
        """Generate unique identifier with hex suffix.

        Args:
            prefix: Entity type prefix (default: "issue")

        Returns:
            Identifier in format prefix-XXXXXX where X is hex digit

        Examples:
            >>> service = HashIdentifierService()
            >>> id1 = service.generate("issue")
            >>> id1.startswith("issue-")
            True
            >>> len(id1)
            12  # "issue-" (6) + 6 hex chars
        """
        # Generate 3 random bytes = 6 hex characters
        hex_suffix = secrets.token_hex(3)
        return f"{prefix}-{hex_suffix}"


__all__ = ["SystemClock", "HashIdentifierService"]

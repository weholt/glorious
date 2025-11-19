"""Business logic for temporal skill."""

import re
from datetime import datetime, timedelta

from .models import TimeFilter


class TemporalService:
    """Service layer for temporal filtering logic.

    Provides time parsing and filter generation utilities
    that can be used by other skills.
    """

    @staticmethod
    def parse_time_spec(time_spec: str) -> datetime | None:
        """Parse a time specification into a datetime.

        Supports formats like:
        - '7d' (7 days ago)
        - '3h' (3 hours ago)
        - '30m' (30 minutes ago)
        - '2025-11-14' (specific date)
        - 'last-week', 'yesterday', etc.

        Args:
            time_spec: Time specification string

        Returns:
            Parsed datetime or None if parsing fails
        """
        # Try relative time (e.g., "7d", "3h", "30m")
        if match := re.match(r"(\d+)([dhm])", time_spec.lower()):
            amount, unit = match.groups()
            amount = int(amount)

            if unit == "d":
                delta = timedelta(days=amount)
            elif unit == "h":
                delta = timedelta(hours=amount)
            elif unit == "m":
                delta = timedelta(minutes=amount)
            else:
                return None

            return datetime.utcnow() - delta

        # Try special keywords
        spec_lower = time_spec.lower()
        if spec_lower in ["yesterday", "last-day"]:
            return datetime.utcnow() - timedelta(days=1)
        elif spec_lower in ["last-week", "lastweek"]:
            return datetime.utcnow() - timedelta(weeks=1)
        elif spec_lower in ["last-month", "lastmonth"]:
            return datetime.utcnow() - timedelta(days=30)

        # Try ISO date format
        try:
            return datetime.fromisoformat(time_spec)
        except ValueError:
            pass

        return None

    @staticmethod
    def create_filter(
        since: str | None = None,
        until: str | None = None,
    ) -> TimeFilter:
        """Create a time filter from specifications.

        Args:
            since: Start time specification
            until: End time specification

        Returns:
            TimeFilter object
        """
        start_time = None
        end_time = None
        description_parts = []

        if since:
            start_time = TemporalService.parse_time_spec(since)
            if start_time:
                description_parts.append(f"since {since}")

        if until:
            end_time = TemporalService.parse_time_spec(until)
            if end_time:
                description_parts.append(f"until {until}")

        description = " ".join(description_parts) if description_parts else "no time filter"

        return TimeFilter(
            start_time=start_time,
            end_time=end_time,
            description=description,
        )

    @staticmethod
    def get_examples() -> list[str]:
        """Get list of temporal filter examples.

        Returns:
            List of example specifications with descriptions
        """
        return [
            "--since 7d          Last 7 days",
            "--since 3h          Last 3 hours",
            "--since 30m         Last 30 minutes",
            "--until 2025-11-14  Before specific date",
            "--since yesterday   Since yesterday",
            "--since last-week   Last week",
        ]

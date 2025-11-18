"""Domain models and utilities for temporal skill."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimeFilter:
    """Represents a temporal filter specification.

    Used for parsing and applying time-based filters
    across different skills.
    """

    start_time: datetime | None = None
    end_time: datetime | None = None
    description: str = ""

    def to_sql_condition(self, column_name: str = "created_at") -> tuple[str, list]:
        """Generate SQL WHERE condition.

        Args:
            column_name: Name of the timestamp column

        Returns:
            Tuple of (condition_string, parameters)
        """
        conditions = []
        params = []

        if self.start_time:
            conditions.append(f"{column_name} >= ?")
            params.append(self.start_time.isoformat())

        if self.end_time:
            conditions.append(f"{column_name} <= ?")
            params.append(self.end_time.isoformat())

        if not conditions:
            return ("1=1", [])

        return (" AND ".join(conditions), params)

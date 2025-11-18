"""Repository for telemetry event data access."""

from sqlmodel import func, select

from glorious_agents.core.repository import BaseRepository

from .models import TelemetryEvent


class TelemetryRepository(BaseRepository[TelemetryEvent]):
    """Repository for telemetry events with domain-specific queries."""

    def get_recent_events(self, limit: int = 50, category: str = "") -> list[TelemetryEvent]:
        """Get recent telemetry events.

        Args:
            limit: Maximum number of events
            category: Optional category filter

        Returns:
            List of events ordered by timestamp (most recent first)
        """
        statement = select(TelemetryEvent).order_by(TelemetryEvent.timestamp.desc())

        if category:
            statement = statement.where(TelemetryEvent.category == category)

        statement = statement.limit(limit)
        return list(self.session.exec(statement))

    def get_statistics(self, group_by: str, limit: int = 10) -> list[tuple[str, int, float]]:
        """Get telemetry statistics grouped by field.

        Args:
            group_by: Field to group by (category, skill, or status)
            limit: Maximum number of groups

        Returns:
            List of (group_value, count, avg_duration) tuples
        """
        if group_by == "category":
            field = TelemetryEvent.category
        elif group_by == "skill":
            field = TelemetryEvent.skill
        elif group_by == "status":
            field = TelemetryEvent.status
        else:
            return []

        statement = (
            select(field, func.count(), func.avg(TelemetryEvent.duration_ms))
            .where(field != "")
            .group_by(field)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def search_events(self, query: str, limit: int = 10) -> list[TelemetryEvent]:
        """Search events by category, event text, or skill.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching events ordered by timestamp
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(TelemetryEvent)
            .where(
                (TelemetryEvent.category.like(query_pattern))
                | (TelemetryEvent.event.like(query_pattern))
                | (TelemetryEvent.skill.like(query_pattern))
                | (TelemetryEvent.status.like(query_pattern))
            )
            .order_by(TelemetryEvent.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

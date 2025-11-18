"""Business logic for telemetry skill."""

import json

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import TelemetryEvent
from .repository import TelemetryRepository


class TelemetryService:
    """Service layer for telemetry event management.

    Handles business logic for event logging and analytics
    while delegating data access to the repository.
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus | None = None) -> None:
        """Initialize service with dependencies.

        Args:
            uow: Unit of Work for transaction management
            event_bus: Optional event bus for publishing events
        """
        self.uow = uow
        self.event_bus = event_bus
        self.repo = TelemetryRepository(uow.session, TelemetryEvent)

    def log_event(
        self,
        category: str,
        event: str,
        skill: str = "",
        duration_ms: int = 0,
        status: str = "success",
        project_id: str = "",
        meta: dict | None = None,
    ) -> TelemetryEvent:
        """Log a telemetry event.

        Args:
            category: Event category
            event: Event description
            skill: Skill name
            duration_ms: Duration in milliseconds
            status: Event status
            project_id: Project identifier
            meta: Optional metadata dictionary

        Returns:
            Created event record
        """
        meta_json = json.dumps(meta) if meta else ""

        telemetry_event = TelemetryEvent(
            category=category,
            event=event,
            skill=skill,
            duration_ms=duration_ms,
            status=status,
            project_id=project_id,
            meta=meta_json,
        )
        telemetry_event = self.repo.add(telemetry_event)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "telemetry_event_logged",
                {
                    "id": telemetry_event.id,
                    "category": category,
                    "skill": skill,
                    "status": status,
                },
            )

        return telemetry_event

    def get_recent_events(self, limit: int = 50, category: str = "") -> list[TelemetryEvent]:
        """Get recent telemetry events.

        Args:
            limit: Maximum number of events
            category: Optional category filter

        Returns:
            List of events ordered by timestamp
        """
        return self.repo.get_recent_events(limit, category)

    def get_statistics(self, group_by: str, limit: int = 10) -> list[tuple[str, int, float]]:
        """Get telemetry statistics.

        Args:
            group_by: Field to group by (category, skill, or status)
            limit: Maximum number of groups

        Returns:
            List of (group_value, count, avg_duration) tuples
        """
        return self.repo.get_statistics(group_by, limit)

    def search_events(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for telemetry events.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        events = self.repo.search_events(query, limit)

        results = []
        for event in events:
            # Calculate score based on relevance
            score = 0.5
            query_lower = query.lower()

            if query_lower in event.category.lower():
                score += 0.3
            if query_lower in event.event.lower():
                score += 0.3
            if event.skill and query_lower in event.skill.lower():
                score += 0.2

            score = min(1.0, max(0.0, score))

            results.append(
                SearchResult(
                    skill="telemetry",
                    id=event.id,
                    type="event",
                    content=f"{event.category}: {event.event}",
                    metadata={
                        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                        "skill": event.skill,
                        "duration_ms": event.duration_ms,
                        "status": event.status,
                    },
                    score=score,
                )
            )

        return results

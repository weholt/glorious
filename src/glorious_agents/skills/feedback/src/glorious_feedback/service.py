"""Business logic for feedback skill."""

import json

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Feedback
from .repository import FeedbackRepository


class FeedbackService:
    """Service layer for feedback management.

    Handles business logic for action feedback tracking
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
        self.repo = FeedbackRepository(uow.session, Feedback)

    def record_feedback(
        self,
        action_id: str,
        status: str,
        reason: str = "",
        action_type: str = "",
        meta: dict | None = None,
    ) -> Feedback:
        """Record action feedback.

        Args:
            action_id: Action identifier
            status: Action status
            reason: Feedback reason
            action_type: Optional action type
            meta: Optional metadata dictionary

        Returns:
            Created feedback record
        """
        meta_json = json.dumps(meta) if meta else ""

        feedback = Feedback(
            action_id=action_id,
            action_type=action_type,
            status=status,
            reason=reason,
            meta=meta_json,
        )
        feedback = self.repo.add(feedback)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "feedback_recorded",
                {
                    "id": feedback.id,
                    "action_id": action_id,
                    "status": status,
                },
            )

        return feedback

    def get_recent_feedback(self, limit: int = 50) -> list[Feedback]:
        """Get recent feedback entries.

        Args:
            limit: Maximum number of entries

        Returns:
            List of feedback ordered by creation time
        """
        return self.repo.get_recent_feedback(limit)

    def get_feedback_for_action(self, action_id: str, limit: int = 10) -> list[Feedback]:
        """Get feedback for a specific action.

        Args:
            action_id: Action identifier
            limit: Maximum number of entries

        Returns:
            List of feedback for the action
        """
        return self.repo.get_by_action_id(action_id, limit)

    def get_statistics(self, group_by: str, limit: int = 10) -> list[tuple[str, int]]:
        """Get feedback statistics.

        Args:
            group_by: Field to group by (status or action_type)
            limit: Maximum number of groups

        Returns:
            List of (group_value, count) tuples
        """
        return self.repo.get_statistics(group_by, limit)

    def search_feedback(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for feedback entries.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        feedback_list = self.repo.search_feedback(query, limit)

        results = []
        for fb in feedback_list:
            # Calculate score based on relevance
            score = 0.6
            query_lower = query.lower()

            if query_lower in fb.action_id.lower():
                score += 0.2
            if fb.reason and query_lower in fb.reason.lower():
                score += 0.2

            score = min(1.0, max(0.0, score))

            # Truncate reason for display
            reason_preview = fb.reason[:80] if fb.reason else ""

            results.append(
                SearchResult(
                    skill="feedback",
                    id=fb.id,
                    type="feedback",
                    content=f"{fb.action_id}: {reason_preview}",
                    metadata={
                        "action_id": fb.action_id,
                        "action_type": fb.action_type,
                        "status": fb.status,
                        "created_at": fb.created_at.isoformat() if fb.created_at else None,
                    },
                    score=score,
                )
            )

        return results

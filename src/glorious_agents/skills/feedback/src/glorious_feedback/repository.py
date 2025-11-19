"""Repository for feedback data access."""

from sqlmodel import func, select

from glorious_agents.core.repository import BaseRepository

from .models import Feedback


class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for feedback with domain-specific queries."""

    def get_recent_feedback(self, limit: int = 50) -> list[Feedback]:
        """Get recent feedback entries.

        Args:
            limit: Maximum number of entries

        Returns:
            List of feedback ordered by creation time (most recent first)
        """
        statement = select(Feedback).order_by(Feedback.created_at.desc()).limit(limit)
        return list(self.session.exec(statement))

    def get_by_action_id(self, action_id: str, limit: int = 10) -> list[Feedback]:
        """Get feedback for a specific action.

        Args:
            action_id: Action identifier
            limit: Maximum number of entries

        Returns:
            List of feedback for the action
        """
        statement = (
            select(Feedback)
            .where(Feedback.action_id == action_id)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_statistics(self, group_by: str, limit: int = 10) -> list[tuple[str, int]]:
        """Get feedback statistics grouped by field.

        Args:
            group_by: Field to group by (status or action_type)
            limit: Maximum number of groups

        Returns:
            List of (group_value, count) tuples
        """
        if group_by == "status":
            field = Feedback.status
        elif group_by == "action_type":
            field = Feedback.action_type
        else:
            return []

        statement = (
            select(field, func.count())
            .where(field != "")
            .group_by(field)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def search_feedback(self, query: str, limit: int = 10) -> list[Feedback]:
        """Search feedback by action_id or reason.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching feedback ordered by creation time
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(Feedback)
            .where(
                (Feedback.action_id.like(query_pattern))
                | (Feedback.reason.like(query_pattern))
                | (Feedback.action_type.like(query_pattern))
            )
            .order_by(Feedback.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

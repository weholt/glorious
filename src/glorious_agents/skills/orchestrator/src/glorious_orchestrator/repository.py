"""Repository for orchestrator workflow data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import Workflow


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for workflows with domain-specific queries."""

    def get_by_status(self, status: str, limit: int = 20) -> list[Workflow]:
        """Get workflows by status.

        Args:
            status: Workflow status filter
            limit: Maximum number of workflows to return

        Returns:
            List of workflows ordered by creation date
        """
        statement = (
            select(Workflow)
            .where(Workflow.status == status)
            .order_by(Workflow.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent(self, limit: int = 20) -> list[Workflow]:
        """Get recent workflows.

        Args:
            limit: Maximum number of workflows to return

        Returns:
            List of workflows ordered by creation date (newest first)
        """
        statement = select(Workflow).order_by(Workflow.created_at.desc()).limit(limit)
        return list(self.session.exec(statement))

    def search_workflows(self, query: str, limit: int = 10) -> list[Workflow]:
        """Search workflows by name, intent, or status.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching workflows ordered by creation date
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(Workflow)
            .where(
                (Workflow.name.like(query_pattern))
                | (Workflow.intent.like(query_pattern))
                | (Workflow.status.like(query_pattern))
            )
            .order_by(Workflow.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

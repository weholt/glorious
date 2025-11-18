"""Repository for planner task data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import PlannerTask


class PlannerRepository(BaseRepository[PlannerTask]):
    """Repository for planner tasks with domain-specific queries."""

    def get_by_status(self, status: str, limit: int = 20) -> list[PlannerTask]:
        """Get tasks by status, ordered by priority.

        Args:
            status: Task status filter
            limit: Maximum number of tasks to return

        Returns:
            List of tasks ordered by importance and priority
        """
        statement = (
            select(PlannerTask)
            .where(PlannerTask.status == status)
            .order_by(
                PlannerTask.important.desc(),
                PlannerTask.priority.desc(),
                PlannerTask.created_at.asc(),
            )
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_next_task(self, respect_important: bool = True) -> PlannerTask | None:
        """Get the highest priority queued task.

        Args:
            respect_important: Whether to prioritize important tasks

        Returns:
            Next task to work on, or None if queue is empty
        """
        statement = select(PlannerTask).where(PlannerTask.status == "queued")

        if respect_important:
            statement = statement.order_by(
                PlannerTask.important.desc(), PlannerTask.priority.desc()
            )
        else:
            statement = statement.order_by(PlannerTask.priority.desc())

        statement = statement.limit(1)
        result = self.session.exec(statement).first()
        return result

    def search_tasks(self, query: str, limit: int = 10) -> list[PlannerTask]:
        """Search tasks by issue_id or project_id.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching tasks ordered by priority
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(PlannerTask)
            .where(
                (PlannerTask.issue_id.like(query_pattern))
                | (PlannerTask.project_id.like(query_pattern))
            )
            .order_by(PlannerTask.priority.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_by_project(self, project_id: str, limit: int = 50) -> list[PlannerTask]:
        """Get all tasks for a project.

        Args:
            project_id: Project identifier
            limit: Maximum number of tasks

        Returns:
            List of tasks for the project
        """
        statement = (
            select(PlannerTask)
            .where(PlannerTask.project_id == project_id)
            .order_by(
                PlannerTask.status.asc(),
                PlannerTask.priority.desc(),
            )
            .limit(limit)
        )
        return list(self.session.exec(statement))

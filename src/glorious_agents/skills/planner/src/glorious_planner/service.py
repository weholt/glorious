"""Business logic for planner skill."""

from datetime import datetime

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import PlannerTask
from .repository import PlannerRepository


class PlannerService:
    """Service layer for planner task management.

    Handles business logic, validation, and event publishing
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
        self.repo = PlannerRepository(uow.session, PlannerTask)

    def create_task(
        self,
        issue_id: str,
        priority: int = 0,
        project_id: str = "",
        important: bool = False,
    ) -> PlannerTask:
        """Create a new task in the queue.

        Args:
            issue_id: Issue identifier
            priority: Task priority (-100 to 100)
            project_id: Project identifier
            important: Whether task is important

        Returns:
            Created task
        """
        task = PlannerTask(
            issue_id=issue_id,
            priority=priority,
            project_id=project_id,
            important=important,
            status="queued",
        )
        task = self.repo.add(task)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "planner_task_created",
                {
                    "id": task.id,
                    "issue_id": task.issue_id,
                    "priority": task.priority,
                    "important": task.important,
                },
            )

        return task

    def get_next_task(self, respect_important: bool = True) -> PlannerTask | None:
        """Get the next task to work on.

        Args:
            respect_important: Whether to prioritize important tasks

        Returns:
            Next task or None if queue is empty
        """
        return self.repo.get_next_task(respect_important)

    def update_task_status(self, task_id: int, status: str) -> PlannerTask | None:
        """Update task status.

        Args:
            task_id: Task identifier
            status: New status (queued, running, blocked, done)

        Returns:
            Updated task or None if not found
        """
        task = self.repo.get(task_id)
        if not task:
            return None

        task.status = status
        task.updated_at = datetime.utcnow()
        task = self.repo.update(task)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "planner_task_updated",
                {
                    "id": task.id,
                    "issue_id": task.issue_id,
                    "status": task.status,
                },
            )

        return task

    def list_tasks(self, status: str = "queued", limit: int = 20) -> list[PlannerTask]:
        """List tasks by status.

        Args:
            status: Status filter
            limit: Maximum number of tasks

        Returns:
            List of tasks
        """
        return self.repo.get_by_status(status, limit)

    def delete_task(self, task_id: int) -> bool:
        """Delete a task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        return self.repo.delete(task_id)

    def search_tasks(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for tasks.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        tasks = self.repo.search_tasks(query, limit)

        results = []
        for task in tasks:
            # Calculate score based on priority and importance
            score = 0.5 + (task.priority / 200.0)
            if task.important:
                score += 0.3
            score = min(1.0, max(0.0, score))

            results.append(
                SearchResult(
                    skill="planner",
                    id=task.id,
                    type="task",
                    content=f"Task #{task.id}: {task.issue_id}",
                    metadata={
                        "issue_id": task.issue_id,
                        "status": task.status,
                        "priority": task.priority,
                        "project_id": task.project_id,
                        "important": task.important,
                    },
                    score=score,
                )
            )

        return results

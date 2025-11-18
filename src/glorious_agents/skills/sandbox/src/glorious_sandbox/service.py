"""Business logic for sandbox skill."""

from datetime import datetime

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Sandbox
from .repository import SandboxRepository


class SandboxService:
    """Service layer for sandbox management.

    Handles business logic for Docker-based isolated execution
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
        self.repo = SandboxRepository(uow.session, Sandbox)

    def create_sandbox(
        self,
        container_id: str,
        image: str,
        status: str = "running",
    ) -> Sandbox:
        """Create a new sandbox record.

        Args:
            container_id: Docker container identifier
            image: Docker image name
            status: Initial status (default: running)

        Returns:
            Created sandbox
        """
        sandbox = Sandbox(
            container_id=container_id,
            image=image,
            status=status,
        )
        sandbox = self.repo.add(sandbox)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "sandbox_created",
                {
                    "id": sandbox.id,
                    "container_id": container_id,
                    "image": image,
                },
            )

        return sandbox

    def update_sandbox_status(
        self,
        sandbox_id: int,
        status: str,
        exit_code: int | None = None,
        logs: str | None = None,
    ) -> Sandbox | None:
        """Update sandbox status.

        Args:
            sandbox_id: Sandbox identifier
            status: New status (running, completed, failed)
            exit_code: Container exit code
            logs: Container logs

        Returns:
            Updated sandbox or None if not found
        """
        sandbox = self.repo.get(sandbox_id)
        if not sandbox:
            return None

        sandbox.status = status
        if exit_code is not None:
            sandbox.exit_code = exit_code
        if logs is not None:
            sandbox.logs = logs
        if status in ["completed", "failed"]:
            sandbox.finished_at = datetime.utcnow()

        sandbox = self.repo.update(sandbox)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "sandbox_updated",
                {
                    "id": sandbox.id,
                    "container_id": sandbox.container_id,
                    "status": status,
                    "exit_code": exit_code,
                },
            )

        return sandbox

    def get_recent_sandboxes(self, limit: int = 20) -> list[Sandbox]:
        """Get recent sandboxes.

        Args:
            limit: Maximum number of sandboxes

        Returns:
            List of sandboxes ordered by creation time
        """
        return self.repo.get_recent_sandboxes(limit)

    def get_sandbox_by_container_id(self, container_id: str) -> Sandbox | None:
        """Get sandbox by container ID.

        Args:
            container_id: Docker container identifier

        Returns:
            Sandbox or None if not found
        """
        return self.repo.get_by_container_id(container_id)

    def get_sandbox_logs(self, sandbox_id: int) -> str | None:
        """Get logs for a sandbox.

        Args:
            sandbox_id: Sandbox identifier

        Returns:
            Logs string or None if not found
        """
        sandbox = self.repo.get(sandbox_id)
        return sandbox.logs if sandbox else None

    def search_sandboxes(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for sandboxes.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        sandboxes = self.repo.search_sandboxes(query, limit)

        results = []
        for sb in sandboxes:
            # Calculate score based on status and relevance
            score = 0.5
            query_lower = query.lower()

            if sb.image and query_lower in sb.image.lower():
                score += 0.3
            if query_lower in sb.status.lower():
                score += 0.2
            if sb.logs and query_lower in sb.logs.lower():
                score += 0.2

            score = min(1.0, max(0.0, score))

            # Truncate logs for display
            logs_preview = sb.logs[:200] if sb.logs else ""

            results.append(
                SearchResult(
                    skill="sandbox",
                    id=sb.id,
                    type="sandbox",
                    content=f"{sb.image or 'unknown'} ({sb.status})\n{logs_preview}",
                    metadata={
                        "container_id": sb.container_id,
                        "status": sb.status,
                        "exit_code": sb.exit_code,
                        "created_at": sb.created_at.isoformat() if sb.created_at else None,
                    },
                    score=score,
                )
            )

        return results

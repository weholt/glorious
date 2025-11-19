"""Repository for sandbox data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import Sandbox


class SandboxRepository(BaseRepository[Sandbox]):
    """Repository for sandboxes with domain-specific queries."""

    def get_by_status(self, status: str, limit: int = 20) -> list[Sandbox]:
        """Get sandboxes by status.

        Args:
            status: Sandbox status filter
            limit: Maximum number of sandboxes to return

        Returns:
            List of sandboxes ordered by creation time
        """
        statement = (
            select(Sandbox)
            .where(Sandbox.status == status)
            .order_by(Sandbox.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent_sandboxes(self, limit: int = 20) -> list[Sandbox]:
        """Get recent sandboxes.

        Args:
            limit: Maximum number of sandboxes

        Returns:
            List of sandboxes ordered by creation time (most recent first)
        """
        statement = select(Sandbox).order_by(Sandbox.created_at.desc()).limit(limit)
        return list(self.session.exec(statement))

    def get_by_container_id(self, container_id: str) -> Sandbox | None:
        """Get sandbox by container ID.

        Args:
            container_id: Docker container identifier

        Returns:
            Sandbox or None if not found
        """
        statement = select(Sandbox).where(Sandbox.container_id == container_id)
        return self.session.exec(statement).first()

    def search_sandboxes(self, query: str, limit: int = 10) -> list[Sandbox]:
        """Search sandboxes by image or logs.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching sandboxes ordered by creation time
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(Sandbox)
            .where(
                (Sandbox.image.like(query_pattern))
                | (Sandbox.status.like(query_pattern))
                | (Sandbox.logs.like(query_pattern))
            )
            .order_by(Sandbox.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

"""Repository for vacuum operation data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import VacuumOperation


class VacuumRepository(BaseRepository[VacuumOperation]):
    """Repository for vacuum operations with domain-specific queries."""

    def get_by_status(self, status: str, limit: int = 20) -> list[VacuumOperation]:
        """Get operations by status.

        Args:
            status: Operation status filter
            limit: Maximum number of operations to return

        Returns:
            List of operations ordered by start time
        """
        statement = (
            select(VacuumOperation)
            .where(VacuumOperation.status == status)
            .order_by(VacuumOperation.started_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent_operations(self, limit: int = 20) -> list[VacuumOperation]:
        """Get recent operations.

        Args:
            limit: Maximum number of operations

        Returns:
            List of operations ordered by start time (most recent first)
        """
        statement = select(VacuumOperation).order_by(VacuumOperation.started_at.desc()).limit(limit)
        return list(self.session.exec(statement))

    def get_by_mode(self, mode: str, limit: int = 10) -> list[VacuumOperation]:
        """Get operations by mode.

        Args:
            mode: Operation mode filter
            limit: Maximum number of operations

        Returns:
            List of operations for the mode
        """
        statement = (
            select(VacuumOperation)
            .where(VacuumOperation.mode == mode)
            .order_by(VacuumOperation.started_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

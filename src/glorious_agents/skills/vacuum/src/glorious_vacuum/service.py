"""Business logic for vacuum skill."""

from datetime import datetime

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import VacuumOperation
from .repository import VacuumRepository


class VacuumService:
    """Service layer for vacuum operation management.

    Handles business logic for knowledge distillation and optimization
    operations while delegating data access to the repository.
    """

    VALID_MODES = ["summarize", "dedupe", "promote-rules", "sharpen"]

    def __init__(self, uow: UnitOfWork, event_bus: EventBus | None = None) -> None:
        """Initialize service with dependencies.

        Args:
            uow: Unit of Work for transaction management
            event_bus: Optional event bus for publishing events
        """
        self.uow = uow
        self.event_bus = event_bus
        self.repo = VacuumRepository(uow.session, VacuumOperation)

    def start_operation(
        self,
        mode: str,
    ) -> VacuumOperation:
        """Start a new vacuum operation.

        Args:
            mode: Operation mode (summarize, dedupe, promote-rules, sharpen)

        Returns:
            Created operation

        Raises:
            ValueError: If mode is invalid
        """
        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of: {', '.join(self.VALID_MODES)}"
            )

        operation = VacuumOperation(
            mode=mode,
            status="running",
        )
        operation = self.repo.add(operation)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "vacuum_operation_started",
                {
                    "id": operation.id,
                    "mode": operation.mode,
                },
            )

        return operation

    def complete_operation(
        self,
        operation_id: int,
        items_processed: int = 0,
        items_modified: int = 0,
    ) -> VacuumOperation | None:
        """Complete a vacuum operation.

        Args:
            operation_id: Operation identifier
            items_processed: Number of items processed
            items_modified: Number of items modified

        Returns:
            Updated operation or None if not found
        """
        operation = self.repo.get(operation_id)
        if not operation:
            return None

        operation.status = "completed"
        operation.completed_at = datetime.utcnow()
        operation.items_processed = items_processed
        operation.items_modified = items_modified
        operation = self.repo.update(operation)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "vacuum_operation_completed",
                {
                    "id": operation.id,
                    "mode": operation.mode,
                    "items_processed": items_processed,
                    "items_modified": items_modified,
                },
            )

        return operation

    def get_recent_operations(self, limit: int = 20) -> list[VacuumOperation]:
        """Get recent operations.

        Args:
            limit: Maximum number of operations

        Returns:
            List of operations ordered by start time
        """
        return self.repo.get_recent_operations(limit)

    def get_operations_by_mode(self, mode: str, limit: int = 10) -> list[VacuumOperation]:
        """Get operations by mode.

        Args:
            mode: Operation mode
            limit: Maximum number of operations

        Returns:
            List of operations for the mode
        """
        return self.repo.get_by_mode(mode, limit)

    def search_operations(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for vacuum operations.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        # Search by mode
        query_lower = query.lower()
        operations = self.repo.get_recent_operations(limit * 2)  # Get more to filter

        results = []
        for op in operations:
            if query_lower in op.mode.lower() or query_lower in op.status.lower():
                # Calculate score based on status and recency
                score = 0.5
                if op.status == "completed":
                    score += 0.2
                if op.items_modified > 0:
                    score += 0.3
                score = min(1.0, max(0.0, score))

                results.append(
                    SearchResult(
                        skill="vacuum",
                        id=op.id,
                        type="operation",
                        content=f"Vacuum {op.mode}: {op.items_processed} processed, {op.items_modified} modified",
                        metadata={
                            "mode": op.mode,
                            "status": op.status,
                            "items_processed": op.items_processed,
                            "items_modified": op.items_modified,
                            "started_at": op.started_at.isoformat() if op.started_at else None,
                        },
                        score=score,
                    )
                )

                if len(results) >= limit:
                    break

        return results

"""Business logic for orchestrator skill."""

import json
from datetime import datetime

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Workflow
from .repository import WorkflowRepository


class OrchestratorService:
    """Service layer for workflow orchestration.

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
        self.repo = WorkflowRepository(uow.session, Workflow)

    def create_workflow(
        self,
        name: str,
        intent: str | None = None,
        steps: list[str] | None = None,
        status: str = "pending",
    ) -> Workflow:
        """Create a new workflow.

        Args:
            name: Workflow name
            intent: Natural language intent
            steps: List of workflow steps
            status: Initial status

        Returns:
            Created workflow
        """
        workflow = Workflow(
            name=name,
            intent=intent,
            steps=json.dumps(steps) if steps else None,
            status=status,
        )
        workflow = self.repo.add(workflow)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "workflow_created",
                {
                    "id": workflow.id,
                    "name": workflow.name,
                    "status": workflow.status,
                },
            )

        return workflow

    def get_workflow(self, workflow_id: int) -> Workflow | None:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow or None if not found
        """
        return self.repo.get(workflow_id)

    def update_workflow_status(
        self, workflow_id: int, status: str, complete: bool = False
    ) -> Workflow | None:
        """Update workflow status.

        Args:
            workflow_id: Workflow identifier
            status: New status
            complete: Whether workflow is completed

        Returns:
            Updated workflow or None if not found
        """
        workflow = self.repo.get(workflow_id)
        if not workflow:
            return None

        workflow.status = status
        if complete:
            workflow.completed_at = datetime.utcnow()

        workflow = self.repo.update(workflow)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "workflow_updated",
                {
                    "id": workflow.id,
                    "name": workflow.name,
                    "status": workflow.status,
                    "completed": complete,
                },
            )

        return workflow

    def list_workflows(self, status: str | None = None, limit: int = 20) -> list[Workflow]:
        """List workflows.

        Args:
            status: Optional status filter
            limit: Maximum number of workflows

        Returns:
            List of workflows
        """
        if status:
            return self.repo.get_by_status(status, limit)
        return self.repo.get_recent(limit)

    def search_workflows(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for workflows.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        workflows = self.repo.search_workflows(query, limit)

        results = []
        query_lower = query.lower()

        for workflow in workflows:
            score = 0.0

            # Score based on match quality
            if workflow.name and query_lower in workflow.name.lower():
                score += 0.8

            if workflow.intent and query_lower in workflow.intent.lower():
                score += 0.6

            if workflow.status and query_lower in workflow.status.lower():
                score += 0.3

            # Ensure score is between 0 and 1
            score = min(1.0, max(0.0, score))

            content = workflow.name
            if workflow.intent:
                content += f"\n{workflow.intent}"

            results.append(
                SearchResult(
                    skill="orchestrator",
                    id=workflow.id,
                    type="workflow",
                    content=content,
                    metadata={
                        "status": workflow.status,
                        "created_at": workflow.created_at.isoformat()
                        if workflow.created_at
                        else None,
                        "completed_at": workflow.completed_at.isoformat()
                        if workflow.completed_at
                        else None,
                    },
                    score=score,
                )
            )

        return results

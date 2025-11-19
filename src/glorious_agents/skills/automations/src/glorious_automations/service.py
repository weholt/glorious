"""Business logic for automations skill."""

import json
import uuid
from datetime import datetime
from typing import Any

from rich.console import Console

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Automation, AutomationExecution
from .repository import AutomationExecutionRepository, AutomationRepository

console = Console()


class AutomationService:
    """Service layer for automation management.

    Handles business logic, validation, event registration,
    and action execution while delegating data access to repositories.
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus | None = None) -> None:
        """Initialize service with dependencies.

        Args:
            uow: Unit of Work for transaction management
            event_bus: Optional event bus for subscribing/publishing events
        """
        self.uow = uow
        self.event_bus = event_bus
        self.automation_repo = AutomationRepository(uow.session, Automation)
        self.execution_repo = AutomationExecutionRepository(uow.session, AutomationExecution)

    def create_automation(
        self,
        name: str,
        trigger_topic: str,
        actions: list[dict[str, Any]] | str,
        description: str = "",
        trigger_condition: str = "",
    ) -> Automation:
        """Create a new automation.

        Args:
            name: Automation name
            trigger_topic: Event topic to listen to
            actions: List of actions or JSON string
            description: Optional description
            trigger_condition: Optional Python expression to filter events

        Returns:
            Created automation

        Raises:
            ValueError: If actions is invalid JSON
        """
        # Validate and convert actions to JSON string
        if isinstance(actions, str):
            try:
                json.loads(actions)
                actions_json = actions
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in actions: {e}")
        else:
            actions_json = json.dumps(actions)

        # Generate unique ID
        auto_id = f"auto-{uuid.uuid4().hex[:8]}"

        automation = Automation(
            id=auto_id,
            name=name,
            description=description or None,
            trigger_topic=trigger_topic,
            trigger_condition=trigger_condition or None,
            actions=actions_json,
            enabled=True,
        )
        automation = self.automation_repo.add(automation)

        # Register with event bus if available
        if self.event_bus:
            self._register_automation_handler(automation)

        return automation

    def get_automation(self, automation_id: str) -> Automation | None:
        """Get automation by ID.

        Args:
            automation_id: Automation identifier

        Returns:
            Automation or None if not found
        """
        return self.automation_repo.get(automation_id)

    def enable_automation(self, automation_id: str) -> Automation | None:
        """Enable an automation.

        Args:
            automation_id: Automation identifier

        Returns:
            Updated automation or None if not found
        """
        automation = self.automation_repo.get(automation_id)
        if not automation:
            return None

        automation.enabled = True
        automation.updated_at = datetime.utcnow()
        automation = self.automation_repo.update(automation)

        # Re-register with event bus if available
        if self.event_bus:
            self._register_automation_handler(automation)

        return automation

    def disable_automation(self, automation_id: str) -> Automation | None:
        """Disable an automation.

        Args:
            automation_id: Automation identifier

        Returns:
            Updated automation or None if not found
        """
        automation = self.automation_repo.get(automation_id)
        if not automation:
            return None

        automation.enabled = False
        automation.updated_at = datetime.utcnow()
        automation = self.automation_repo.update(automation)

        return automation

    def delete_automation(self, automation_id: str) -> bool:
        """Delete an automation.

        Args:
            automation_id: Automation identifier

        Returns:
            True if deleted, False if not found
        """
        return self.automation_repo.delete(automation_id)

    def list_automations(self, enabled_only: bool = False, limit: int = 100) -> list[Automation]:
        """List automations.

        Args:
            enabled_only: Whether to return only enabled automations
            limit: Maximum number of automations

        Returns:
            List of automations
        """
        return self.automation_repo.get_all(enabled_only, limit)

    def execute_automation(
        self, automation_id: str, trigger_data: dict[str, Any]
    ) -> AutomationExecution:
        """Execute an automation.

        Args:
            automation_id: Automation identifier
            trigger_data: Event data that triggered the automation

        Returns:
            Execution record
        """
        automation = self.automation_repo.get(automation_id)
        if not automation:
            raise ValueError(f"Automation not found: {automation_id}")

        # Check condition if present
        if automation.trigger_condition:
            try:
                if not eval(automation.trigger_condition, {"data": trigger_data}):
                    # Condition not met, record as skipped
                    execution = AutomationExecution(
                        automation_id=automation_id,
                        trigger_data=json.dumps(trigger_data),
                        status="skipped",
                        result="Condition not met",
                    )
                    return self.execution_repo.add(execution)
            except Exception as e:
                # Condition evaluation error
                execution = AutomationExecution(
                    automation_id=automation_id,
                    trigger_data=json.dumps(trigger_data),
                    status="failed",
                    error=f"Condition eval error: {e}",
                )
                return self.execution_repo.add(execution)

        # Execute actions
        try:
            actions = json.loads(automation.actions)
            results = []

            for action in actions:
                action_type = action.get("type")
                if action_type == "log":
                    message = action.get("message", "")
                    console.print(f"[blue]Automation log:[/blue] {message}")
                    results.append({"type": "log", "success": True})
                elif action_type == "publish":
                    topic = action.get("topic")
                    data = action.get("data", {})
                    if self.event_bus:
                        self.event_bus.publish(topic, data)
                    results.append({"type": "publish", "topic": topic, "success": True})
                else:
                    results.append(
                        {"type": action_type, "success": False, "error": "Unknown action type"}
                    )

            execution = AutomationExecution(
                automation_id=automation_id,
                trigger_data=json.dumps(trigger_data),
                status="success",
                result=json.dumps(results),
            )
            return self.execution_repo.add(execution)

        except Exception as e:
            execution = AutomationExecution(
                automation_id=automation_id,
                trigger_data=json.dumps(trigger_data),
                status="failed",
                error=str(e),
            )
            return self.execution_repo.add(execution)

    def get_executions(
        self, automation_id: str | None = None, limit: int = 20
    ) -> list[AutomationExecution]:
        """Get execution history.

        Args:
            automation_id: Optional automation ID filter
            limit: Maximum number of executions

        Returns:
            List of executions
        """
        if automation_id:
            return self.execution_repo.get_by_automation(automation_id, limit)
        return self.execution_repo.get_recent(limit)

    def register_all_automations(self) -> None:
        """Register all enabled automations with the event bus."""
        if not self.event_bus:
            return

        automations = self.automation_repo.get_enabled()
        for automation in automations:
            self._register_automation_handler(automation)

    def _register_automation_handler(self, automation: Automation) -> None:
        """Register an automation handler with the event bus.

        Args:
            automation: Automation to register
        """
        if not self.event_bus or not automation.enabled:
            return

        def handler(data: dict[str, Any]) -> None:
            # Create a new service instance with a new UoW for each execution
            # to avoid session conflicts
            from .dependencies import get_automation_service

            service = get_automation_service(event_bus=self.event_bus)
            with service.uow:
                service.execute_automation(automation.id, data)

        self.event_bus.subscribe(automation.trigger_topic, handler)

    def search_automations(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for automations.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        automations = self.automation_repo.search_automations(query, limit)

        results = []
        query_lower = query.lower()

        for automation in automations:
            score = 0.0

            # Score based on match quality
            if automation.name and query_lower in automation.name.lower():
                score += 0.8

            if automation.description and query_lower in automation.description.lower():
                score += 0.5

            if automation.trigger_topic and query_lower in automation.trigger_topic.lower():
                score += 0.3

            # Ensure score is between 0 and 1
            score = min(1.0, max(0.0, score))

            content = automation.name
            if automation.description:
                content += f"\n{automation.description}"

            results.append(
                SearchResult(
                    skill="automations",
                    id=automation.id,
                    type="automation",
                    content=content,
                    metadata={
                        "trigger_topic": automation.trigger_topic,
                        "enabled": automation.enabled,
                        "created_at": automation.created_at.isoformat()
                        if automation.created_at
                        else None,
                    },
                    score=score,
                )
            )

        return results

"""Repository for automations data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import Automation, AutomationExecution


class AutomationRepository(BaseRepository[Automation]):
    """Repository for automations with domain-specific queries."""

    def get_by_trigger_topic(self, topic: str) -> list[Automation]:
        """Get all automations for a specific trigger topic.

        Args:
            topic: Event topic to filter by

        Returns:
            List of automations
        """
        statement = select(Automation).where(Automation.trigger_topic == topic)
        return list(self.session.exec(statement))

    def get_enabled(self, limit: int = 100) -> list[Automation]:
        """Get all enabled automations.

        Args:
            limit: Maximum number of automations

        Returns:
            List of enabled automations ordered by creation date
        """
        statement = (
            select(Automation)
            .where(Automation.enabled)
            .order_by(Automation.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def search_automations(self, query: str, limit: int = 10) -> list[Automation]:
        """Search automations by name, description, or trigger topic.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching automations
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(Automation)
            .where(
                (Automation.name.like(query_pattern))
                | (Automation.description.like(query_pattern))
                | (Automation.trigger_topic.like(query_pattern))
            )
            .order_by(Automation.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_all(self, enabled_only: bool = False, limit: int = 100) -> list[Automation]:
        """Get all automations.

        Args:
            enabled_only: Whether to return only enabled automations
            limit: Maximum number of automations

        Returns:
            List of automations
        """
        statement = select(Automation)
        if enabled_only:
            statement = statement.where(Automation.enabled)
        statement = statement.order_by(Automation.created_at.desc()).limit(limit)
        return list(self.session.exec(statement))


class AutomationExecutionRepository(BaseRepository[AutomationExecution]):
    """Repository for automation executions."""

    def get_by_automation(self, automation_id: str, limit: int = 20) -> list[AutomationExecution]:
        """Get execution history for an automation.

        Args:
            automation_id: Automation identifier
            limit: Maximum number of executions

        Returns:
            List of executions ordered by execution time (newest first)
        """
        statement = (
            select(AutomationExecution)
            .where(AutomationExecution.automation_id == automation_id)
            .order_by(AutomationExecution.executed_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent(self, limit: int = 20) -> list[AutomationExecution]:
        """Get recent executions across all automations.

        Args:
            limit: Maximum number of executions

        Returns:
            List of executions ordered by execution time (newest first)
        """
        statement = (
            select(AutomationExecution)
            .order_by(AutomationExecution.executed_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

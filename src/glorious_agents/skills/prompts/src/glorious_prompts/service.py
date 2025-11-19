"""Business logic for prompts skill."""

import json

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Prompt
from .repository import PromptsRepository


class PromptsService:
    """Service layer for prompt template management.

    Handles business logic for versioning, rendering, and searching
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
        self.repo = PromptsRepository(uow.session, Prompt)

    def register_prompt(
        self,
        name: str,
        template: str,
        meta: dict | None = None,
    ) -> Prompt:
        """Register a new prompt template with automatic versioning.

        Args:
            name: Prompt name
            template: Prompt template string
            meta: Optional metadata dictionary

        Returns:
            Created prompt
        """
        # Get next version number
        max_version = self.repo.get_max_version(name)
        new_version = max_version + 1

        # Convert meta to JSON string if provided
        meta_json = json.dumps(meta) if meta else None

        prompt = Prompt(
            name=name,
            version=new_version,
            template=template,
            meta=meta_json,
        )
        prompt = self.repo.add(prompt)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "prompt_registered",
                {
                    "id": prompt.id,
                    "name": prompt.name,
                    "version": prompt.version,
                },
            )

        return prompt

    def get_latest_prompt(self, name: str) -> Prompt | None:
        """Get the latest version of a prompt.

        Args:
            name: Prompt name

        Returns:
            Latest prompt version or None if not found
        """
        return self.repo.get_latest_version(name)

    def get_prompt_version(self, name: str, version: int) -> Prompt | None:
        """Get a specific version of a prompt.

        Args:
            name: Prompt name
            version: Version number

        Returns:
            Prompt or None if not found
        """
        return self.repo.get_by_name_version(name, version)

    def render_prompt(self, name: str, variables: dict, version: int | None = None) -> str | None:
        """Render a prompt template with variables.

        Args:
            name: Prompt name
            variables: Variables for template substitution
            version: Optional specific version (defaults to latest)

        Returns:
            Rendered prompt or None if prompt not found

        Raises:
            KeyError: If required variable is missing
        """
        if version is not None:
            prompt = self.get_prompt_version(name, version)
        else:
            prompt = self.get_latest_prompt(name)

        if not prompt:
            return None

        # Render template with variables
        return prompt.template.format(**variables)

    def list_prompts(self) -> list[dict[str, int]]:
        """List all prompt names with version information.

        Returns:
            List of dicts with name, latest_version, and total_versions
        """
        return self.repo.list_prompt_names()

    def delete_prompt(self, name: str) -> int:
        """Delete all versions of a prompt.

        Args:
            name: Prompt name

        Returns:
            Number of deleted versions
        """
        count = self.repo.delete_by_name(name)

        # Publish event if event bus available
        if self.event_bus and count > 0:
            self.event_bus.publish(
                "prompt_deleted",
                {
                    "name": name,
                    "versions_deleted": count,
                },
            )

        return count

    def search_prompts(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for prompts.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results with scores
        """
        prompts = self.repo.search_prompts(query, limit)

        results = []
        query_lower = query.lower()

        for prompt in prompts:
            # Score based on name match (higher) vs template match (lower)
            score = 0.9 if query_lower in prompt.name.lower() else 0.6

            # Truncate template for display
            template_preview = prompt.template[:100]
            if len(prompt.template) > 100:
                template_preview += "..."

            results.append(
                SearchResult(
                    skill="prompts",
                    id=f"{prompt.name}_v{prompt.version}",
                    type="prompt",
                    content=f"{prompt.name} (v{prompt.version}): {template_preview}",
                    metadata={
                        "name": prompt.name,
                        "version": prompt.version,
                        "created_at": str(prompt.created_at),
                    },
                    score=score,
                )
            )

        return results

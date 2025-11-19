"""Business logic for linker skill."""

from typing import Any

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Link
from .repository import LinkerRepository


class LinkerService:
    """Service layer for link management.

    Handles business logic for creating and querying relationships
    between entities while delegating data access to the repository.
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus | None = None) -> None:
        """Initialize service with dependencies.

        Args:
            uow: Unit of Work for transaction management
            event_bus: Optional event bus for publishing events
        """
        self.uow = uow
        self.event_bus = event_bus
        self.repo = LinkerRepository(uow.session, Link)

    def add_link(
        self,
        kind: str,
        a_type: str,
        a_id: str,
        b_type: str,
        b_id: str,
        weight: float = 1.0,
    ) -> Link:
        """Create a link between two entities.

        Args:
            kind: Link kind/type
            a_type: Source entity type
            a_id: Source entity ID
            b_type: Target entity type
            b_id: Target entity ID
            weight: Link weight/strength (0.0-10.0)

        Returns:
            Created link
        """
        link = Link(
            kind=kind,
            a_type=a_type,
            a_id=a_id,
            b_type=b_type,
            b_id=b_id,
            weight=weight,
        )
        link = self.repo.add(link)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "link_created",
                {
                    "id": link.id,
                    "kind": link.kind,
                    "source": f"{link.a_type}:{link.a_id}",
                    "target": f"{link.b_type}:{link.b_id}",
                    "weight": link.weight,
                },
            )

        return link

    def get_context_bundle(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        """Get all linked entities for a given entity.

        Returns context from both outgoing and incoming links.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of linked entities with metadata
        """
        links = self.repo.get_links_for_entity(entity_type, entity_id)

        results = []
        for link in links:
            # Determine which entity is the "other" one
            if link.a_type == entity_type and link.a_id == entity_id:
                # This is an outgoing link
                results.append(
                    {
                        "kind": link.kind,
                        "type": link.b_type,
                        "id": link.b_id,
                        "weight": link.weight,
                    }
                )
            else:
                # This is an incoming link
                results.append(
                    {
                        "kind": link.kind,
                        "type": link.a_type,
                        "id": link.a_id,
                        "weight": link.weight,
                    }
                )

        return results

    def get_link(self, link_id: int) -> Link | None:
        """Get a link by ID.

        Args:
            link_id: Link identifier

        Returns:
            Link or None if not found
        """
        return self.repo.get(link_id)

    def delete_link(self, link_id: int) -> bool:
        """Delete a link.

        Args:
            link_id: Link identifier

        Returns:
            True if deleted, False if not found
        """
        success = self.repo.delete(link_id)

        # Publish event if event bus available
        if self.event_bus and success:
            self.event_bus.publish(
                "link_deleted",
                {"id": link_id},
            )

        return success

    def list_links(self, limit: int = 50) -> list[Link]:
        """List recent links.

        Args:
            limit: Maximum number of links

        Returns:
            List of links ordered by creation date
        """
        return self.repo.get_recent_links(limit)

    def search_links(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for links.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results with scores
        """
        links = self.repo.search_links(query, limit * 2)  # Get more to filter

        results = []
        query_lower = query.lower()

        for link in links[:limit]:
            score = 0.0

            # Score based on what matched
            if query_lower in link.kind.lower():
                score += 0.7

            if query_lower in link.a_type.lower() or query_lower in link.a_id.lower():
                score += 0.5

            if query_lower in link.b_type.lower() or query_lower in link.b_id.lower():
                score += 0.5

            score = min(1.0, score)

            results.append(
                SearchResult(
                    skill="linker",
                    id=link.id,
                    type="link",
                    content=f"{link.kind}: {link.a_type}:{link.a_id} → {link.b_type}:{link.b_id}",
                    metadata={
                        "kind": link.kind,
                        "source": f"{link.a_type}:{link.a_id}",
                        "target": f"{link.b_type}:{link.b_id}",
                        "weight": link.weight,
                        "created_at": str(link.created_at),
                    },
                    score=score,
                )
            )

        return results

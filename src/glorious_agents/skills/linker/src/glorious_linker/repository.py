"""Repository for linker data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import Link


class LinkerRepository(BaseRepository[Link]):
    """Repository for links with domain-specific queries."""

    def get_links_for_entity(self, entity_type: str, entity_id: str) -> list[Link]:
        """Get all links where entity is either source or target.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of links involving the entity
        """
        statement = (
            select(Link)
            .where(
                ((Link.a_type == entity_type) & (Link.a_id == entity_id))
                | ((Link.b_type == entity_type) & (Link.b_id == entity_id))
            )
            .order_by(Link.weight.desc())
        )

        return list(self.session.exec(statement))

    def get_outgoing_links(self, entity_type: str, entity_id: str) -> list[Link]:
        """Get links where entity is the source.

        Args:
            entity_type: Source entity type
            entity_id: Source entity ID

        Returns:
            List of outgoing links ordered by weight
        """
        statement = (
            select(Link)
            .where((Link.a_type == entity_type) & (Link.a_id == entity_id))
            .order_by(Link.weight.desc())
        )
        return list(self.session.exec(statement))

    def get_incoming_links(self, entity_type: str, entity_id: str) -> list[Link]:
        """Get links where entity is the target.

        Args:
            entity_type: Target entity type
            entity_id: Target entity ID

        Returns:
            List of incoming links ordered by weight
        """
        statement = (
            select(Link)
            .where((Link.b_type == entity_type) & (Link.b_id == entity_id))
            .order_by(Link.weight.desc())
        )
        return list(self.session.exec(statement))

    def get_by_kind(self, kind: str, limit: int = 100) -> list[Link]:
        """Get all links of a specific kind.

        Args:
            kind: Link kind/type
            limit: Maximum number of results

        Returns:
            List of links of the specified kind
        """
        statement = (
            select(Link)
            .where(Link.kind == kind)
            .order_by(Link.weight.desc(), Link.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def search_links(self, query: str, limit: int = 50) -> list[Link]:
        """Search links by kind, entity types, or IDs.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching links
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(Link)
            .where(
                (Link.kind.like(query_pattern))
                | (Link.a_type.like(query_pattern))
                | (Link.a_id.like(query_pattern))
                | (Link.b_type.like(query_pattern))
                | (Link.b_id.like(query_pattern))
            )
            .order_by(Link.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent_links(self, limit: int = 50) -> list[Link]:
        """Get most recent links.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent links
        """
        statement = select(Link).order_by(Link.created_at.desc()).limit(limit)
        return list(self.session.exec(statement))

    def find_link(
        self,
        kind: str,
        a_type: str,
        a_id: str,
        b_type: str,
        b_id: str,
    ) -> Link | None:
        """Find a specific link by its components.

        Args:
            kind: Link kind
            a_type: Source entity type
            a_id: Source entity ID
            b_type: Target entity type
            b_id: Target entity ID

        Returns:
            Link if found, None otherwise
        """
        statement = select(Link).where(
            (Link.kind == kind)
            & (Link.a_type == a_type)
            & (Link.a_id == a_id)
            & (Link.b_type == b_type)
            & (Link.b_id == b_id)
        )
        return self.session.exec(statement).first()

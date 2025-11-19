"""Repository for notes data access with FTS support."""

from sqlalchemy import text
from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import Note


class NotesRepository(BaseRepository[Note]):
    """Repository for notes with FTS and domain-specific queries."""

    def search_fts(self, query: str, limit: int = 10) -> list[Note]:
        """Search notes using FTS5 full-text search.

        Args:
            query: FTS5 search query
            limit: Maximum number of results

        Returns:
            List of matching notes ordered by importance and relevance
        """
        # Use raw SQL for FTS5 query since SQLModel doesn't support virtual tables
        sql = text("""
            SELECT n.id, n.content, n.tags, n.created_at, n.updated_at, n.importance
            FROM notes n
            JOIN notes_fts fts ON n.id = fts.rowid
            WHERE notes_fts MATCH :query
            ORDER BY n.importance DESC, rank
            LIMIT :limit
        """)

        result = self.session.exec(sql, {"query": query, "limit": limit})

        # Convert rows to Note objects
        notes = []
        for row in result:
            note = Note(
                id=row[0],
                content=row[1],
                tags=row[2],
                created_at=row[3],
                updated_at=row[4],
                importance=row[5],
            )
            notes.append(note)

        return notes

    def get_by_importance(self, importance: int, limit: int = 20) -> list[Note]:
        """Get notes by importance level.

        Args:
            importance: Importance level (0=normal, 1=important, 2=critical)
            limit: Maximum number of results

        Returns:
            List of notes ordered by creation date (newest first)
        """
        statement = (
            select(Note)
            .where(Note.importance == importance)
            .order_by(Note.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent(
        self,
        limit: int = 10,
        min_importance: int | None = None,
    ) -> list[Note]:
        """Get recent notes, optionally filtered by minimum importance.

        Args:
            limit: Maximum number of results
            min_importance: Minimum importance level (None for all)

        Returns:
            List of notes ordered by importance and creation date
        """
        statement = select(Note)

        if min_importance is not None:
            statement = statement.where(Note.importance >= min_importance)

        statement = statement.order_by(
            Note.importance.desc(),
            Note.created_at.desc(),
        ).limit(limit)

        return list(self.session.exec(statement))

    def search_by_tags(self, tags: str, limit: int = 20) -> list[Note]:
        """Search notes by tags (partial match).

        Args:
            tags: Tags to search for
            limit: Maximum number of results

        Returns:
            List of matching notes ordered by importance
        """
        query_pattern = f"%{tags.lower()}%"
        statement = (
            select(Note)
            .where(Note.tags.like(query_pattern))
            .order_by(Note.importance.desc(), Note.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

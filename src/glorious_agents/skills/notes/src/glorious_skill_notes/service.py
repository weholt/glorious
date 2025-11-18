"""Business logic for notes skill."""

from datetime import datetime

from sqlalchemy import text

from glorious_agents.core.context import EventBus
from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Note
from .repository import NotesRepository


class NotesService:
    """Service layer for notes management.

    Handles business logic, FTS search, validation, and event publishing
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
        self.repo = NotesRepository(uow.session, Note)

    def _ensure_fts_tables(self) -> None:
        """Ensure FTS virtual tables and triggers exist.

        This is needed because SQLModel doesn't handle virtual tables.
        """
        # Create FTS5 virtual table
        self.uow.session.exec(
            text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                content,
                tags,
                content='notes',
                content_rowid='id'
            )
        """)
        )

        # Create triggers to keep FTS index in sync
        self.uow.session.exec(
            text("""
            CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
                INSERT INTO notes_fts(rowid, content, tags)
                VALUES (new.id, new.content, new.tags);
            END
        """)
        )

        self.uow.session.exec(
            text("""
            CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
                DELETE FROM notes_fts WHERE rowid = old.id;
            END
        """)
        )

        self.uow.session.exec(
            text("""
            CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
                DELETE FROM notes_fts WHERE rowid = old.id;
                INSERT INTO notes_fts(rowid, content, tags)
                VALUES (new.id, new.content, new.tags);
            END
        """)
        )

        self.uow.session.commit()

    def create_note(
        self,
        content: str,
        tags: str = "",
        importance: int = 0,
    ) -> Note:
        """Create a new note.

        Args:
            content: Note content
            tags: Comma-separated tags
            importance: Importance level (0=normal, 1=important, 2=critical)

        Returns:
            Created note
        """
        note = Note(
            content=content,
            tags=tags,
            importance=importance,
        )
        note = self.repo.add(note)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "note_created",
                {
                    "id": note.id,
                    "tags": note.tags,
                    "content": note.content[:100],  # Truncate for event
                    "importance": note.importance,
                },
            )

        return note

    def get_note(self, note_id: int) -> Note | None:
        """Get a note by ID.

        Args:
            note_id: Note identifier

        Returns:
            Note or None if not found
        """
        return self.repo.get(note_id)

    def update_importance(self, note_id: int, importance: int) -> Note | None:
        """Update note importance level.

        Args:
            note_id: Note identifier
            importance: New importance level (0-2)

        Returns:
            Updated note or None if not found
        """
        note = self.repo.get(note_id)
        if not note:
            return None

        note.importance = importance
        note.updated_at = datetime.utcnow()
        note = self.repo.update(note)

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                "note_updated",
                {
                    "id": note.id,
                    "importance": note.importance,
                },
            )

        return note

    def delete_note(self, note_id: int) -> bool:
        """Delete a note.

        Args:
            note_id: Note identifier

        Returns:
            True if deleted, False if not found
        """
        return self.repo.delete(note_id)

    def list_notes(
        self,
        limit: int = 10,
        min_importance: int | None = None,
    ) -> list[Note]:
        """List recent notes.

        Args:
            limit: Maximum number of notes
            min_importance: Minimum importance level filter

        Returns:
            List of notes ordered by importance and date
        """
        return self.repo.get_recent(limit, min_importance)

    def search_notes(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for notes using FTS.

        Args:
            query: FTS5 search query
            limit: Maximum results

        Returns:
            List of search results with scores
        """
        # Ensure FTS tables exist
        self._ensure_fts_tables()

        # Perform FTS search with rank
        sql = text("""
            SELECT n.id, n.content, n.tags, n.created_at, n.importance, rank
            FROM notes n
            JOIN notes_fts fts ON n.id = fts.rowid
            WHERE notes_fts MATCH :query
            ORDER BY n.importance DESC, rank
            LIMIT :limit
        """)

        result = self.uow.session.exec(sql, {"query": query, "limit": limit})

        results = []
        for row in result:
            # Convert FTS5 rank to 0-1 score (rank is negative, higher absolute = better)
            base_score = min(1.0, abs(row[5]) / 10.0) if row[5] else 0.5

            # Boost score based on importance (critical=+0.3, important=+0.15)
            importance = row[4]
            importance_boost = importance * 0.15
            score = min(1.0, base_score + importance_boost)

            results.append(
                SearchResult(
                    skill="notes",
                    id=row[0],
                    type="note",
                    content=row[1],
                    metadata={
                        "tags": row[2],
                        "created_at": str(row[3]),
                        "importance": importance,
                    },
                    score=score,
                )
            )

        return results

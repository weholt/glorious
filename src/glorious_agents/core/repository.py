"""Generic repository pattern for type-safe database operations.

This module provides a base repository implementation that eliminates
boilerplate CRUD code across skills while maintaining full type safety.
"""

from typing import Any, Generic, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository[T: SQLModel]:
    """Generic repository for CRUD operations.

    Provides type-safe database operations without boilerplate.
    Each skill can subclass this to add domain-specific queries.

    Example:
        ```python
        class NoteRepository(BaseRepository[Note]):
            def get_by_importance(self, min_importance: int) -> list[Note]:
                statement = select(Note).where(
                    Note.importance >= min_importance
                )
                return list(self.session.exec(statement))
        ```
    """

    def __init__(self, session: Session, model_class: type[T]) -> None:
        """Initialize repository.

        Args:
            session: SQLModel session for database operations
            model_class: The SQLModel class this repository manages
        """
        self.session = session
        self.model_class = model_class

    def add(self, entity: T) -> T:
        """Add entity to database.

        Args:
            entity: Entity instance to add

        Returns:
            The added entity with ID populated

        Note:
            Uses flush() to get ID without committing transaction.
            Caller must commit via UnitOfWork or session.
        """
        self.session.add(entity)
        self.session.flush()  # Get ID without committing
        self.session.refresh(entity)
        return entity

    def get(self, id: int | str) -> T | None:
        """Get entity by ID.

        Args:
            id: Primary key value

        Returns:
            Entity if found, None otherwise
        """
        return self.session.get(self.model_class, id)

    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Get all entities with pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        statement = select(self.model_class).limit(limit).offset(offset)
        return list(self.session.exec(statement))

    def update(self, entity: T) -> T:
        """Update entity.

        Args:
            entity: Entity with modified fields

        Returns:
            Updated entity

        Note:
            Entity must have been retrieved from this session or
            merged into it. Caller must commit changes.
        """
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def delete(self, id: int | str) -> bool:
        """Delete entity by ID.

        Args:
            id: Primary key value

        Returns:
            True if entity was deleted, False if not found

        Note:
            Caller must commit the deletion.
        """
        entity = self.get(id)
        if entity:
            self.session.delete(entity)
            self.session.flush()
            return True
        return False

    def search(self, **filters: Any) -> list[T]:
        """Search entities by exact field matches.

        Args:
            **filters: Field name to value mappings

        Returns:
            List of matching entities

        Example:
            ```python
            # Search for notes with specific importance
            notes = repo.search(importance=2)
            ```
        """
        statement = select(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)
        return list(self.session.exec(statement))

    def count(self, **filters: Any) -> int:
        """Count entities matching filters.

        Args:
            **filters: Field name to value mappings

        Returns:
            Number of matching entities
        """
        from sqlalchemy import func

        statement = select(func.count()).select_from(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)
        result = self.session.exec(statement)
        return result.one()

    def exists(self, id: int | str) -> bool:
        """Check if entity exists.

        Args:
            id: Primary key value

        Returns:
            True if entity exists
        """
        return self.get(id) is not None

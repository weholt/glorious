"""Base skill class for modernized architecture.

This module provides a base class that eliminates boilerplate code
across skills by providing standard database and event bus access
patterns with dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from glorious_agents.core.context import EventBus
from glorious_agents.core.repository import BaseRepository
from glorious_agents.core.unit_of_work import UnitOfWork

T = TypeVar("T", bound=SQLModel)


class BaseSkill[T: SQLModel](ABC):
    """Base class for all skills with DI and ORM support.

    Eliminates 90% of boilerplate code across skills by providing:
    - Automatic session management
    - Transaction support via context manager
    - Event publishing capabilities
    - Repository access pattern

    Example:
        ```python
        class NoteSkill(BaseSkill[Note]):
            def get_model_class(self) -> type[Note]:
                return Note

            def add_note(self, content: str) -> Note:
                repo = self.get_repository()
                note = Note(content=content)
                note = repo.add(note)
                self.publish_event("note_created", {"id": note.id})
                return note

        # Usage
        engine = create_engine("sqlite:///test.db")
        event_bus = EventBus()

        with NoteSkill(engine, event_bus) as skill:
            note = skill.add_note("Hello World")
            # Automatically commits on success
        ```
    """

    def __init__(self, engine: Engine, event_bus: EventBus) -> None:
        """Initialize skill with dependencies.

        Args:
            engine: SQLAlchemy engine for database access
            event_bus: Event bus for publishing events
        """
        self.engine = engine
        self.event_bus = event_bus
        self._session: Session | None = None
        self._repository: BaseRepository[T] | None = None

    @property
    def session(self) -> Session:
        """Get or create database session.

        Returns:
            Active SQLModel session

        Note:
            Session is created lazily on first access and reused.
            Automatically closed when skill is closed.
        """
        if self._session is None:
            self._session = Session(self.engine)
        return self._session

    def get_repository(self) -> BaseRepository[T]:
        """Get repository for this skill's model.

        Returns:
            Repository instance for the skill's model class

        Note:
            Repository is created lazily and reused.
        """
        if self._repository is None:
            self._repository = BaseRepository(self.session, self.get_model_class())
        return self._repository

    def create_unit_of_work(self) -> UnitOfWork:
        """Create Unit of Work for complex transactions.

        Returns:
            UnitOfWork instance using this skill's session

        Example:
            ```python
            with skill.create_unit_of_work() as uow:
                repo = uow.get_repository("notes", Note)
                note = repo.add(Note(content="test"))
            ```
        """
        return UnitOfWork(self.session)

    def commit(self) -> None:
        """Commit current transaction.

        Raises:
            Exception: If commit fails
        """
        if self._session:
            self._session.commit()

    def rollback(self) -> None:
        """Rollback current transaction.

        Called automatically if an exception occurs within
        a context manager block.
        """
        if self._session:
            self._session.rollback()

    def close(self) -> None:
        """Close session and cleanup resources.

        Called automatically when exiting context manager.
        """
        if self._session:
            self._session.close()
            self._session = None
        self._repository = None

    def publish_event(self, topic: str, data: dict[str, Any]) -> None:
        """Publish event to event bus.

        Args:
            topic: Event topic/channel name
            data: Event payload dictionary

        Example:
            ```python
            self.publish_event("note_created", {
                "id": note.id,
                "content": note.content
            })
            ```
        """
        self.event_bus.publish(topic, data)

    def __enter__(self) -> "BaseSkill[T]":
        """Enter context manager.

        Returns:
            Self for use in with statements
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager with automatic transaction handling.

        Commits if no exception, otherwise rolls back.
        Always closes resources.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception instance if raised
            exc_tb: Exception traceback if raised
        """
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

    @abstractmethod
    def get_model_class(self) -> type[T]:
        """Return the SQLModel class for this skill.

        Returns:
            SQLModel class that this skill manages

        Example:
            ```python
            def get_model_class(self) -> type[Note]:
                return Note
            ```
        """
        pass

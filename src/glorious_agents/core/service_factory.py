"""Service factory pattern for dependency injection.

This module provides factory classes for creating services with proper
dependency injection, making testing easier and reducing coupling.
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from glorious_agents.core.repository import BaseRepository
from glorious_agents.core.unit_of_work import UnitOfWork

T = TypeVar("T")


class ServiceFactory[T]:
    """Factory for creating services with proper DI.

    Centralizes dependency creation and wiring, making it easy
    to inject test doubles or change implementations.

    Example:
        ```python
        from sqlalchemy import create_engine

        engine = create_engine("sqlite:///test.db")
        factory = ServiceFactory(engine)

        # Create repositories
        note_repo = factory.create_repository(Note)

        # Create services
        session = factory.create_session()
        uow = factory.create_unit_of_work(session)
        service = NoteService(uow, event_bus)
        ```
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize factory with database engine.

        Args:
            engine: SQLAlchemy engine for database connections
        """
        self.engine = engine

    def create_session(self) -> Session:
        """Create new database session.

        Returns:
            Fresh SQLModel session

        Note:
            Caller is responsible for closing the session.
        """
        return Session(self.engine)

    def create_unit_of_work(self, session: Session | None = None) -> UnitOfWork:
        """Create Unit of Work for transaction management.

        Args:
            session: Optional existing session to use

        Returns:
            UnitOfWork instance

        Note:
            If no session provided, creates a new one.
        """
        session = session or self.create_session()
        return UnitOfWork(session)

    def create_repository(
        self, model_class: type[SQLModel], session: Session | None = None
    ) -> BaseRepository[Any]:
        """Create repository for given model.

        Args:
            model_class: SQLModel class for repository
            session: Optional existing session to use

        Returns:
            Repository instance

        Note:
            If no session provided, creates a new one.
        """
        session = session or self.create_session()
        return BaseRepository(session, model_class)

    def create_service(self, service_class: type[T], **dependencies: Any) -> T:
        """Create service with dependencies.

        Args:
            service_class: Service class to instantiate
            **dependencies: Dependencies to inject into service

        Returns:
            Service instance

        Example:
            ```python
            service = factory.create_service(
                NoteService,
                uow=uow,
                event_bus=event_bus,
                clock=clock
            )
            ```
        """
        return service_class(**dependencies)

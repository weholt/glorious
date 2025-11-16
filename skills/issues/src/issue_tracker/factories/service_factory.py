"""Service factory for creating domain services with dependencies."""

from sqlalchemy import Engine
from sqlmodel import Session

from issue_tracker.adapters.db.unit_of_work import UnitOfWork
from issue_tracker.adapters.services import HashIdentifierService, SystemClock
from issue_tracker.domain.ports import Clock, IdentifierService
from issue_tracker.services import IssueGraphService, IssueService, IssueStatsService


class ServiceFactory:
    """Factory for creating domain services with proper dependency injection.

    Centralizes service creation logic to ensure consistent wiring
    of dependencies across the application.

    Example:
        >>> from issue_tracker.adapters.db.engine import create_db_engine
        >>> engine = create_db_engine()
        >>> factory = ServiceFactory(engine)
        >>> issue_service = factory.create_issue_service()
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize service factory.

        Args:
            engine: SQLAlchemy engine for database operations
        """
        self._engine = engine

    def _create_session(self) -> Session:
        """Create a new database session.

        Returns:
            SQLModel Session bound to engine
        """
        return Session(self._engine)

    def create_clock(self) -> Clock:
        """Create clock service for timestamp generation.

        Returns:
            SystemClock instance using real UTC time
        """
        return SystemClock()

    def create_identifier_service(self) -> IdentifierService:
        """Create identifier service for ID generation.

        Returns:
            HashIdentifierService using secure random generation
        """
        return HashIdentifierService()

    def create_unit_of_work(self) -> UnitOfWork:
        """Create unit of work for transaction management.

        Returns:
            UnitOfWork instance with new session
        """
        session = self._create_session()
        return UnitOfWork(session)

    def create_issue_service(
        self,
        clock: Clock | None = None,
        id_service: IdentifierService | None = None,
        uow: UnitOfWork | None = None,
    ) -> IssueService:
        """Create issue service with dependencies.

        Args:
            clock: Optional clock service (creates new if None)
            id_service: Optional identifier service (creates new if None)
            uow: Optional unit of work (creates new if None)

        Returns:
            IssueService instance with all dependencies wired
        """
        clock = clock or self.create_clock()
        id_service = id_service or self.create_identifier_service()
        uow = uow or self.create_unit_of_work()
        return IssueService(uow, id_service, clock)

    def create_issue_graph_service(
        self,
        uow: UnitOfWork | None = None,
        max_depth: int = 10,
    ) -> IssueGraphService:
        """Create issue graph service with dependencies.

        Args:
            uow: Optional unit of work (creates new if None)
            max_depth: Maximum dependency tree depth (default: 10)

        Returns:
            IssueGraphService instance
        """
        uow = uow or self.create_unit_of_work()
        return IssueGraphService(uow, max_depth=max_depth)

    def create_issue_stats_service(
        self,
        uow: UnitOfWork | None = None,
    ) -> IssueStatsService:
        """Create issue statistics service with dependencies.

        Args:
            uow: Optional unit of work (creates new if None)

        Returns:
            IssueStatsService instance
        """
        uow = uow or self.create_unit_of_work()
        return IssueStatsService(uow)


__all__ = ["ServiceFactory"]

"""Unit of Work pattern for transaction management."""

import logging
from types import TracebackType
from typing import Any

from sqlmodel import Session

from issue_tracker.adapters.db.repositories import CommentRepository, IssueGraphRepository, IssueRepository

logger = logging.getLogger(__name__)

__all__ = ["UnitOfWork"]


class UnitOfWork:
    """Unit of Work for managing database transactions.

    Provides transaction boundaries and lazy-loaded repositories.
    Automatically commits on successful completion or rolls back on exceptions.

    Examples:
        >>> from sqlmodel import Session, create_engine
        >>> engine = create_engine("sqlite:///./issues.db")
        >>> session = Session(engine)
        >>>
        >>> # Use as context manager
        >>> with UnitOfWork(session) as uow:
        ...     issue = uow.issues.get("issue-123")
        ...     issue.status = IssueStatus.CLOSED
        ...     uow.issues.save(issue)
        ...     # Automatically commits on success

        >>> # Rollback on exception
        >>> try:
        ...     with UnitOfWork(session) as uow:
        ...         issue = uow.issues.get("issue-123")
        ...         raise ValueError("Something went wrong")
        ... except ValueError:
        ...     pass  # Transaction rolled back automatically
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session.

        Args:
            session: SQLModel database session for queries and transactions
        """
        self.session = session
        self._in_transaction = False
        self._issues: IssueRepository | None = None
        self._comments: CommentRepository | None = None
        self._graph: IssueGraphRepository | None = None

    def __enter__(self) -> "UnitOfWork":
        """Begin transaction.

        Returns:
            Self for context manager pattern
        """
        logger.debug("Entering transaction context")
        self._in_transaction = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """End transaction - commit on success, rollback on exception.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception instance if raised
            exc_tb: Exception traceback if raised
        """
        if exc_type is not None:
            logger.warning("Transaction error, rolling back: %s", exc_type.__name__)
            self.rollback()
        else:
            if self._in_transaction:
                logger.debug("Committing transaction")
                self.commit()
        self._in_transaction = False

    def commit(self) -> None:
        """Commit current transaction.

        Persists all changes made within the transaction to the database.
        """
        logger.debug("Committing database transaction")
        self.session.commit()
        logger.debug("Transaction committed successfully")

    def rollback(self) -> None:
        """Rollback current transaction.

        Discards all changes made within the transaction.
        """
        if self._in_transaction:
            logger.warning("Rolling back database transaction")
            self.session.rollback()
            logger.debug("Transaction rolled back")

    @property
    def issues(self) -> IssueRepository:
        """Lazy-load issue repository.

        Returns:
            Issue repository instance
        """
        if self._issues is None:
            self._issues = IssueRepository(self.session)
        return self._issues

    @property
    def comments(self) -> CommentRepository:
        """Lazy-load comment repository.

        Returns:
            Comment repository instance
        """
        if self._comments is None:
            self._comments = CommentRepository(self.session)
        return self._comments

    @property
    def graph(self) -> IssueGraphRepository:
        """Lazy-load issue graph repository.

        Returns:
            Issue graph repository instance for dependency management
        """
        if self._graph is None:
            self._graph = IssueGraphRepository(self.session)
        return self._graph

    def close(self) -> None:
        """Close the underlying session.

        CRITICAL: Must be called to prevent memory leaks when UnitOfWork
        is not used as a context manager.
        """
        try:
            self.session.close()
        except Exception as e:
            logger.warning("Failed to close session: %s", e)

    def __del__(self) -> None:
        """Ensure session cleanup on garbage collection."""
        self.close()

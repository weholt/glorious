"""Unit of Work pattern for transaction management.

This module provides the UnitOfWork pattern for managing database transactions
and coordinating multiple repository operations atomically.
"""

from typing import Any

from sqlmodel import Session, SQLModel

from glorious_agents.core.repository import BaseRepository


class UnitOfWork:
    """Manages transactions and repository lifecycle.

    Ensures atomic operations across multiple repositories.
    Implements context manager protocol for automatic commit/rollback.

    Example:
        ```python
        engine = create_engine("sqlite:///test.db")
        session = Session(engine)
        uow = UnitOfWork(session)

        with uow:
            note_repo = uow.get_repository("notes", Note)
            note = note_repo.add(Note(content="test"))
            # Automatically commits on success, rolls back on exception
        ```
    """

    def __init__(self, session: Session) -> None:
        """Initialize UnitOfWork.

        Args:
            session: SQLModel session to manage
        """
        self.session = session
        self._repositories: dict[str, BaseRepository[Any]] = {}

    def get_repository(self, name: str, model_class: type[SQLModel]) -> BaseRepository[Any]:
        """Get or create repository for model.

        Args:
            name: Unique name for this repository (e.g., "notes", "issues")
            model_class: SQLModel class for the repository

        Returns:
            Repository instance for the model

        Note:
            Repositories are cached by name, so multiple calls with the
            same name return the same instance.
        """
        if name not in self._repositories:
            self._repositories[name] = BaseRepository(self.session, model_class)
        return self._repositories[name]

    def commit(self) -> None:
        """Commit all changes in current transaction.

        Raises:
            Exception: If commit fails
        """
        self.session.commit()

    def rollback(self) -> None:
        """Rollback all changes in current transaction.

        This is called automatically if an exception occurs
        within a context manager block.
        """
        self.session.rollback()

    def close(self) -> None:
        """Close the session and release resources.

        This is called automatically when exiting a context
        manager block.
        """
        self.session.close()

    def flush(self) -> None:
        """Flush pending changes without committing.

        Useful for getting auto-generated IDs without
        committing the transaction.
        """
        self.session.flush()

    def refresh(self, entity: SQLModel) -> None:
        """Refresh entity from database.

        Args:
            entity: Entity to refresh

        Note:
            Useful after commit to get updated computed fields.
        """
        self.session.refresh(entity)

    def __enter__(self) -> "UnitOfWork":
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

        Commits if no exception occurred, otherwise rolls back.
        Always closes the session.

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

"""Tests for UnitOfWork."""

from unittest.mock import patch

import pytest
from sqlmodel import Session, create_engine

from issue_tracker.adapters.db.unit_of_work import UnitOfWork


@pytest.fixture
def mock_session() -> Session:
    """Create a mock session for unit tests."""
    engine = create_engine("sqlite:///:memory:")
    return Session(engine)


class TestUnitOfWorkRollback:
    """Test rollback functionality."""

    def test_rollback_in_transaction(self, mock_session: Session) -> None:
        """Test rollback when in transaction."""
        uow = UnitOfWork(mock_session)
        uow._in_transaction = True

        with patch.object(mock_session, "rollback") as mock_rollback:
            uow.rollback()
            mock_rollback.assert_called_once()

    def test_rollback_not_in_transaction(self, mock_session: Session) -> None:
        """Test rollback when not in transaction."""
        uow = UnitOfWork(mock_session)
        uow._in_transaction = False

        with patch.object(mock_session, "rollback") as mock_rollback:
            uow.rollback()
            mock_rollback.assert_not_called()


class TestUnitOfWorkClose:
    """Test close functionality."""

    def test_close_session(self, mock_session: Session) -> None:
        """Test closing the session."""
        uow = UnitOfWork(mock_session)

        with patch.object(mock_session, "close") as mock_close:
            uow.close()
            mock_close.assert_called_once()

    def test_close_with_exception(self, mock_session: Session) -> None:
        """Test close handles exceptions gracefully."""
        uow = UnitOfWork(mock_session)

        with patch.object(mock_session, "close", side_effect=Exception("Close error")):
            # Should not raise exception
            uow.close()

    def test_exit_with_exception(self, mock_session: Session) -> None:
        """Test __exit__ with exception rolls back."""
        uow = UnitOfWork(mock_session)
        uow.__enter__()

        with patch.object(mock_session, "rollback") as mock_rollback:
            uow.__exit__(Exception, Exception("error"), None)
            mock_rollback.assert_called_once()

"""Integration test fixtures for database operations."""

from collections.abc import Generator

import psutil
import pytest
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from issue_tracker.adapters.db.engine import create_db_engine


def pytest_sessionstart(session):
    """Clean up all daemon processes before test session starts."""
    killed = 0
    try:
        for proc in psutil.process_iter():
            try:
                cmdline = proc.cmdline()
                if cmdline and any("issue_tracker.daemon.service" in str(arg) for arg in cmdline):
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass

    if killed > 0:
        print(f"\n[CLEANUP] Killed {killed} orphaned daemon processes before test session")


def pytest_sessionfinish(session, exitstatus):
    """Clean up all daemon processes after test session ends."""
    killed = 0
    try:
        for proc in psutil.process_iter():
            try:
                cmdline = proc.cmdline()
                if cmdline and any("issue_tracker.daemon.service" in str(arg) for arg in cmdline):
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass

    if killed > 0:
        print(f"\n[CLEANUP] Killed {killed} orphaned daemon processes after test session")

    # CRITICAL: Dispose all cached engines to prevent memory leak
    # Without this, engines accumulate in registry causing Linux OOM
    try:
        from issue_tracker.cli.dependencies import dispose_all_engines

        dispose_all_engines()
        print("\n[CLEANUP] Disposed all database engines")
    except Exception as e:
        print(f"\n[CLEANUP] Failed to dispose engines: {e}")


@pytest.fixture(scope="function")
def test_engine() -> Generator[Engine, None, None]:
    """Create an in-memory database engine for testing.

    Uses SQLite in-memory database for fast, isolated tests.
    Properly disposes engine to prevent memory leaks on Linux.
    """
    engine = create_db_engine("sqlite:///:memory:")
    yield engine
    # CRITICAL: Dispose engine to release connection pool and file descriptors
    # Without this, Linux accumulates memory and file handles causing OOM
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Create a test database session.

    Creates all tables and provides a clean session for each test.
    Session is automatically closed after the test.
    """
    # Create all tables
    SQLModel.metadata.create_all(test_engine)

    # Create session
    session = Session(test_engine)

    yield session

    # Cleanup - close session first, then drop tables
    session.close()
    SQLModel.metadata.drop_all(test_engine)
    # Note: Engine disposal is handled by test_engine fixture

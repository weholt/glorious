"""Dependency injection for CLI commands.

Provides factory functions for creating service instances with real adapters.
Manages database connection lifecycle and adapter instantiation.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from ..factories.service_factory import ServiceFactory
from ..services.issue_graph_service import IssueGraphService
from ..services.issue_service import IssueService
from ..services.issue_stats_service import IssueStatsService

logger = logging.getLogger(__name__)

# Track all created engines for proper cleanup
# CRITICAL: Prevents memory leaks in tests where DB path changes
_engine_registry: dict[str, Engine] = {}


@lru_cache
def get_issues_folder() -> str:
    """Get issues folder from environment or default.

    Returns:
        Path to issues folder

    """
    return os.getenv("ISSUES_FOLDER", "./.issues")


@lru_cache
def get_db_url() -> str:
    """Get database URL from environment or default.

    Returns:
        SQLite database URL

    """
    # Use ISSUES_DB_PATH if set, otherwise construct from ISSUES_FOLDER
    if "ISSUES_DB_PATH" in os.environ:
        db_path = os.getenv("ISSUES_DB_PATH", "./.issues/issues.db")
        path = Path(db_path).resolve()
    else:
        issues_folder = get_issues_folder()
        path = Path(issues_folder).resolve() / "issues.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Use as_posix() for forward slashes on all platforms (SQLite URL requirement)
    return f"sqlite:///{path.as_posix()}"


def get_engine():
    """Get cached database engine.

    IMPORTANT: Engines are cached per db_url to prevent memory leaks.
    Each unique database path gets its own engine instance.
    All engines are tracked in _engine_registry for proper disposal.

    Returns:
        SQLAlchemy engine instance with SQLite optimizations

    """
    db_url = get_db_url()

    # Return existing engine if already created for this URL
    if db_url in _engine_registry:
        return _engine_registry[db_url]

    # Create new engine
    echo = os.getenv("ISSUES_DB_ECHO", "false").lower() == "true"

    # SQLite connection args for better concurrency
    connect_args = {
        "check_same_thread": False,  # Allow multi-threaded access
        "timeout": 30,  # Wait up to 30 seconds for locks
    }

    engine = create_engine(db_url, echo=echo, connect_args=connect_args)

    # Enable WAL mode for better concurrency
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas for better concurrency."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        cursor.close()

    # Register engine for cleanup
    _engine_registry[db_url] = engine

    return engine


def dispose_all_engines():
    """Dispose all cached engines and clear registry.

    CRITICAL: Must be called during test cleanup to prevent memory leaks.
    Linux accumulates file handles and memory without proper disposal.
    """
    global _engine_registry
    for engine in _engine_registry.values():
        try:
            engine.dispose()
        except Exception as e:
            logger.debug(f"Error disposing engine: {e}")
    _engine_registry.clear()


def get_session() -> Session:
    """Create new database session.

    Returns:
        SQLModel session for database operations

    """
    engine = get_engine()
    return Session(engine)


def get_issue_service() -> IssueService:
    """Create IssueService with real adapters.

    IMPORTANT: The returned service contains a UnitOfWork with an open session.
    Call service.uow.close() when done to prevent memory leaks.

    Returns:
        Configured IssueService instance

    """
    engine = get_engine()
    factory = ServiceFactory(engine)

    clock = factory.create_clock()
    id_service = factory.create_identifier_service()
    uow = factory.create_unit_of_work()

    return factory.create_issue_service(clock, id_service, uow)


def get_issue_graph_service() -> IssueGraphService:
    """Create IssueGraphService with real adapters.

    Returns:
        Configured IssueGraphService instance

    """
    engine = get_engine()
    factory = ServiceFactory(engine)

    uow = factory.create_unit_of_work()

    return factory.create_issue_graph_service(uow)


def get_issue_stats_service() -> IssueStatsService:
    """Create IssueStatsService with real adapters.

    Returns:
        Configured IssueStatsService instance

    """
    engine = get_engine()
    factory = ServiceFactory(engine)

    uow = factory.create_unit_of_work()

    return factory.create_issue_stats_service(uow)

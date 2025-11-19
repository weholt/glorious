"""SQLAlchemy engine registry for proper lifecycle management.

This module provides a global registry for SQLAlchemy engines to ensure
proper resource management and connection pooling across the application.
"""

import logging
from typing import Any

from sqlalchemy import Engine, create_engine

logger = logging.getLogger(__name__)

# Global registry of engine instances keyed by database URL
_engine_registry: dict[str, Engine] = {}


def get_engine(
    db_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_pre_ping: bool = True,
    connect_args: dict[str, Any] | None = None,
) -> Engine:
    """Get or create SQLAlchemy engine for given database URL.

    Engines are cached globally and reused to enable connection pooling.
    Use dispose_engine() or dispose_all_engines() to cleanup.

    Args:
        db_url: Database URL (e.g., "sqlite:///path/to/db.sqlite")
        echo: Whether to log SQL statements (default: False)
        pool_size: Number of connections to keep in pool (default: 5)
        max_overflow: Max overflow connections (default: 10)
        pool_pre_ping: Test connections before use (default: True)
        connect_args: Additional connection arguments

    Returns:
        Cached or newly created SQLAlchemy engine

    Example:
        ```python
        from glorious_agents.core.engine_registry import get_engine

        # Get engine for agent database
        engine = get_engine("sqlite:///~/.agent/glorious.db")

        # Use with session
        from sqlmodel import Session
        session = Session(engine)
        ```
    """
    if db_url in _engine_registry:
        return _engine_registry[db_url]

    # SQLite-specific configuration
    if db_url.startswith("sqlite"):
        connect_args = connect_args or {}
        # Allow cross-thread use for SQLite
        connect_args.setdefault("check_same_thread", False)
        # Enable WAL mode for better concurrency
        connect_args.setdefault("timeout", 5.0)

        engine = create_engine(
            db_url,
            echo=echo,
            connect_args=connect_args,
            pool_pre_ping=pool_pre_ping,
        )
    else:
        # PostgreSQL/MySQL/other databases
        engine = create_engine(
            db_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            connect_args=connect_args or {},
        )

    _engine_registry[db_url] = engine
    logger.info(f"Created engine for {db_url}")
    return engine


def get_engine_for_agent_db(echo: bool = False) -> Engine:
    """Get engine for the main agent database.

    Convenience function that uses the configured agent database path.

    Args:
        echo: Whether to log SQL statements (default: False)

    Returns:
        SQLAlchemy engine for agent database

    Example:
        ```python
        from glorious_agents.core.engine_registry import get_engine_for_agent_db

        engine = get_engine_for_agent_db()
        ```
    """
    from glorious_agents.core.db import get_agent_db_path

    db_path = get_agent_db_path()
    db_url = f"sqlite:///{db_path}"
    return get_engine(db_url, echo=echo)


def dispose_engine(db_url: str) -> bool:
    """Dispose of engine and remove from registry.

    Args:
        db_url: Database URL of engine to dispose

    Returns:
        True if engine was found and disposed, False otherwise
    """
    if db_url in _engine_registry:
        engine = _engine_registry.pop(db_url)
        engine.dispose()
        logger.info(f"Disposed engine for {db_url}")
        return True
    return False


def dispose_all_engines() -> int:
    """Dispose of all engines in the registry.

    Should be called during application shutdown to ensure
    all database connections are properly closed.

    Returns:
        Number of engines disposed

    Example:
        ```python
        import atexit
        from glorious_agents.core.engine_registry import dispose_all_engines

        # Register cleanup on exit
        atexit.register(dispose_all_engines)
        ```
    """
    count = len(_engine_registry)
    for db_url, engine in list(_engine_registry.items()):
        try:
            engine.dispose()
            logger.info(f"Disposed engine for {db_url}")
        except Exception as e:
            logger.error(f"Error disposing engine for {db_url}: {e}")
    _engine_registry.clear()
    return count


def get_active_engines() -> list[str]:
    """Get list of database URLs for active engines.

    Returns:
        List of database URLs with active engines

    Example:
        ```python
        from glorious_agents.core.engine_registry import get_active_engines

        engines = get_active_engines()
        print(f"Active engines: {engines}")
        ```
    """
    return list(_engine_registry.keys())


def has_engine(db_url: str) -> bool:
    """Check if engine exists for given database URL.

    Args:
        db_url: Database URL to check

    Returns:
        True if engine exists in registry
    """
    return db_url in _engine_registry

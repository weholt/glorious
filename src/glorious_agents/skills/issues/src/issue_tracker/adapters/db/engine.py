"""Database engine factory for issue tracker."""

import os
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool


def _get_default_db_url() -> str:
    """Get default database URL from glorious-agents config."""
    try:
        from glorious_agents.core.db import get_agent_db_path

        db_path = get_agent_db_path()
        return f"sqlite:///{db_path}"
    except ImportError:
        # Fallback for standalone usage - use unified database location
        from pathlib import Path

        db_path = Path.cwd() / ".agent" / "glorious.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"


def create_db_engine(db_url: str | None = None, echo: bool = False) -> Engine:
    """Create SQLAlchemy engine for issue tracker.

    Args:
        db_url: Database URL. If None, uses unified glorious.db from config
                or falls back to ISSUE_TRACKER_DB_URL env var
        echo: Whether to log SQL statements (default: False)

    Returns:
        Configured SQLAlchemy engine

    Examples:
        >>> # Use unified database (default)
        >>> engine = create_db_engine()

        >>> # Use custom database
        >>> engine = create_db_engine("sqlite:///./test.db")

        >>> # Use PostgreSQL
        >>> engine = create_db_engine("postgresql://user:pass@localhost/issues")
    """
    if db_url is None:
        db_url = os.environ.get("ISSUE_TRACKER_DB_URL", _get_default_db_url())

    # Use StaticPool for SQLite in-memory databases
    if db_url == "sqlite:///:memory:" or db_url == "sqlite://":
        return create_engine(
            db_url,
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    # Use default pooling for file-based SQLite and other databases
    if db_url.startswith("sqlite:///"):
        return create_engine(
            db_url,
            echo=echo,
            connect_args={
                "check_same_thread": False,
                "timeout": 30.0,  # Wait up to 30 seconds for database lock
            },
        )

    # PostgreSQL, MySQL, etc.
    return create_engine(db_url, echo=echo)


def get_database_path() -> Path:
    """Get the path to the database file.

    Returns:
        Path to database file, or Path("memory") for in-memory databases

    Raises:
        ValueError: If database URL is not SQLite-based
    """
    db_url = os.environ.get("ISSUE_TRACKER_DB_URL", _get_default_db_url())

    if db_url == "sqlite:///:memory:" or db_url == "sqlite://":
        return Path("memory")

    if db_url.startswith("sqlite:///"):
        # Extract path after sqlite:///
        path_str = db_url[len("sqlite:///") :]
        return Path(path_str)

    raise ValueError(f"Only SQLite databases supported for path extraction: {db_url}")

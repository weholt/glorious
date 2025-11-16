"""Database engine factory for issue tracker."""

import os
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool


def create_db_engine(db_url: str | None = None, echo: bool = False) -> Engine:
    """Create SQLAlchemy engine for issue tracker.

    Args:
        db_url: Database URL. If None, reads from ISSUE_TRACKER_DB_URL env var
                or defaults to sqlite:///./issues.db
        echo: Whether to log SQL statements (default: False)

    Returns:
        Configured SQLAlchemy engine

    Examples:
        >>> # Use default SQLite database
        >>> engine = create_db_engine()

        >>> # Use custom database
        >>> engine = create_db_engine("sqlite:///./test.db")

        >>> # Use PostgreSQL
        >>> engine = create_db_engine("postgresql://user:pass@localhost/issues")
    """
    if db_url is None:
        db_url = os.environ.get("ISSUE_TRACKER_DB_URL", "sqlite:///./issues.db")

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
    db_url = os.environ.get("ISSUE_TRACKER_DB_URL", "sqlite:///./issues.db")

    if db_url == "sqlite:///:memory:" or db_url == "sqlite://":
        return Path("memory")

    if db_url.startswith("sqlite:///"):
        # Extract path after sqlite:///
        path_str = db_url[len("sqlite:///") :]
        return Path(path_str)

    raise ValueError(f"Only SQLite databases supported for path extraction: {db_url}")

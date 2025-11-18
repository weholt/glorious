"""Database connection management."""

import sqlite3
from pathlib import Path

from glorious_agents.config import get_config


def get_data_folder() -> Path:
    """Get the data folder path from configuration."""
    config = get_config()
    data_folder = config.DATA_FOLDER
    data_folder.mkdir(parents=True, exist_ok=True)
    return data_folder


def get_agent_db_path(agent_code: str | None = None) -> Path:
    """
    Get the database path for the unified database.

    Args:
        agent_code: Optional agent code (deprecated, kept for compatibility).

    Returns:
        Path to the unified SQLite database.
    """
    config = get_config()
    data_folder = get_data_folder()
    return data_folder / config.DB_NAME


def get_connection(check_same_thread: bool = False) -> sqlite3.Connection:
    """
    Get a connection to the active agent's database with optimized settings.

    Args:
        check_same_thread: Whether to check if connection is used from same thread.

    Returns:
        SQLite connection with WAL mode and performance optimizations enabled.
    """
    db_path = get_agent_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=check_same_thread)

    # Performance optimizations
    conn.execute("PRAGMA journal_mode=WAL;")  # Better concurrency
    conn.execute("PRAGMA synchronous=NORMAL;")  # Balanced durability/performance
    conn.execute("PRAGMA cache_size=-64000;")  # 64MB cache (negative = KB)
    conn.execute("PRAGMA temp_store=MEMORY;")  # Store temp tables in memory
    conn.execute("PRAGMA mmap_size=268435456;")  # 256MB memory-mapped I/O
    conn.execute("PRAGMA page_size=4096;")  # Optimal page size for modern systems
    conn.execute("PRAGMA busy_timeout=5000;")  # Wait 5s on lock instead of failing

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON;")

    return conn


def get_master_db_path() -> Path:
    """Get the path to the unified database (master tables are now in main DB)."""
    return get_agent_db_path()

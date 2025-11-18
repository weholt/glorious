"""Database connection management."""

import sqlite3
from pathlib import Path

from glorious_agents.config import get_config


def get_data_folder() -> Path:
    """
    Return the configured data folder Path and ensure the directory exists.

    Ensures the directory specified by the configuration's DATA_FOLDER exists (creates it if missing).

    Returns:
        Path: Path object pointing to the data folder.
    """
    config = get_config()
    data_folder = config.DATA_FOLDER
    data_folder.mkdir(parents=True, exist_ok=True)
    return data_folder


def get_agent_db_path(agent_code: str | None = None) -> Path:
    """
    Resolve the path to the unified SQLite database file in the configured data folder.

    Parameters:
        agent_code (str | None): Deprecated and kept for compatibility; ignored when computing the path.

    Returns:
        Path: Path to the unified SQLite database file.
    """
    config = get_config()
    data_folder = get_data_folder()
    return data_folder / config.DB_NAME


def get_connection(check_same_thread: bool = False) -> sqlite3.Connection:
    """
    Open a SQLite connection to the active agent's database configured for production use.

    Parameters:
        check_same_thread (bool): If True, restricts the connection to the creating thread; otherwise allow cross-thread use.

    Returns:
        sqlite3.Connection: A connection to the agent database with WAL journal mode, foreign key enforcement enabled, and performance-oriented PRAGMA settings applied.
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
    """
    Provide the filesystem path to the unified database used for master tables.

    Returns:
        Path: Path object pointing to the unified database file.
    """
    return get_agent_db_path()

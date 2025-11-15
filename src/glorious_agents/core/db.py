"""Database management for shared agent SQLite database."""

import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from glorious_agents.config import config

load_dotenv()


def get_agent_folder() -> Path:
    """Get the agent folder path from configuration."""
    return config.AGENT_FOLDER


def get_agent_db_path(agent_code: str | None = None) -> Path:
    """
    Get the database path for the active or specified agent.

    Args:
        agent_code: Optional agent code. If None, uses active agent.

    Returns:
        Path to the agent's SQLite database.
    """
    agent_folder = get_agent_folder()

    if agent_code is None:
        # Read active agent code
        active_file = agent_folder / "active_agent"
        if active_file.exists():
            agent_code = active_file.read_text().strip()
        else:
            agent_code = "default"

    # Create agents directory if needed
    agents_dir = agent_folder / "agents" / agent_code
    agents_dir.mkdir(parents=True, exist_ok=True)

    return agents_dir / "agent.db"


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


def init_skill_schema(skill_name: str, schema_path: Path) -> None:
    """
    Initialize a skill's database schema.

    Args:
        skill_name: Name of the skill.
        schema_path: Path to the SQL schema file.
    """
    if not schema_path.exists():
        return

    conn = get_connection()
    try:
        # Read and execute schema
        schema_sql = schema_path.read_text()
        conn.executescript(schema_sql)
        conn.commit()

        # Track that schema was applied (using a metadata table)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _skill_schemas (
                skill_name TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("INSERT OR IGNORE INTO _skill_schemas (skill_name) VALUES (?)", (skill_name,))
        conn.commit()
    finally:
        conn.close()


def get_master_db_path() -> Path:
    """Get the path to the master registry database."""
    return config.get_master_db_path()


def init_master_db() -> None:
    """Initialize the master registry database."""
    db_path = get_master_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT,
                project_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def batch_execute(
    query: str,
    params_list: list[tuple[str, ...]],
    batch_size: int = 100,
) -> None:
    """
    Execute a query multiple times with different parameters in batches.

    This provides better performance than individual executes by grouping
    operations into transactions.

    Args:
        query: SQL query with placeholders.
        params_list: List of parameter tuples for the query.
        batch_size: Number of operations per transaction (default: 100).

    Example:
        >>> params = [("note1", "tag1"), ("note2", "tag2"), ("note3", "tag3")]
        >>> batch_execute(
        ...     "INSERT INTO notes (content, tags) VALUES (?, ?)",
        ...     params,
        ...     batch_size=50
        ... )
    """
    conn = get_connection()
    try:
        for i in range(0, len(params_list), batch_size):
            batch = params_list[i : i + batch_size]
            conn.executemany(query, batch)
            conn.commit()
    finally:
        conn.close()


def optimize_database() -> None:
    """
    Perform database optimization operations.

    This should be run periodically (e.g., weekly) to maintain performance.
    Operations include:
    - VACUUM to reclaim space and defragment
    - ANALYZE to update query planner statistics
    - FTS5 OPTIMIZE to compact full-text search indexes

    Example:
        >>> optimize_database()  # Run as part of maintenance task
    """
    conn = get_connection()
    try:
        # Update statistics for query optimizer
        conn.execute("ANALYZE;")

        # Optimize FTS5 indexes (use 'merge' for incremental optimization)
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '%_fts'
        """)
        for (fts_table,) in cursor.fetchall():
            try:
                conn.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES('optimize');")
            except sqlite3.Error:
                pass  # Some FTS tables might not support optimize

        # Note: VACUUM requires no active transactions and can take time
        # Only run this during off-peak times or maintenance windows
        # conn.execute("VACUUM;")  # Uncomment for deep cleanup

        conn.commit()
    finally:
        conn.close()

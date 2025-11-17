"""Database management for unified SQLite database.

This module provides database connection and initialization for the unified
glorious.db database that contains all agent data with prefixed tables.
"""

import sqlite3
from pathlib import Path

from glorious_agents.config import config


def get_agent_folder() -> Path:
    """Get the agent folder path from configuration."""
    agent_folder = config.AGENT_FOLDER
    agent_folder.mkdir(parents=True, exist_ok=True)
    return agent_folder


def get_agent_db_path(agent_code: str | None = None) -> Path:
    """
    Get the database path for the unified database.

    Args:
        agent_code: Optional agent code (deprecated, kept for compatibility).

    Returns:
        Path to the unified SQLite database.
    """
    agent_folder = get_agent_folder()
    return agent_folder / config.DB_NAME


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

    # Check if skill has migrations directory
    migrations_dir = schema_path.parent / "migrations"
    if migrations_dir.exists():
        # Use migration system
        from glorious_agents.core.migrations import run_migrations

        run_migrations(skill_name, migrations_dir)
    else:
        # Legacy: execute schema.sql directly
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
            conn.execute(
                "INSERT OR IGNORE INTO _skill_schemas (skill_name) VALUES (?)", (skill_name,)
            )
            conn.commit()
        finally:
            conn.close()


def get_master_db_path() -> Path:
    """Get the path to the unified database (master tables are now in main DB)."""
    return get_agent_db_path()


def init_master_db() -> None:
    """Initialize the master registry tables in unified database."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS core_agents (
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


def migrate_legacy_databases() -> None:
    """
    Migrate data from legacy database files to unified database.

    Looks for old database files and migrates them to the unified database.
    Legacy files: agent.db (in agents/default/), master.db, glorious_shared.db
    """
    agent_folder = get_agent_folder()
    unified_db = get_agent_db_path()

    # Check for legacy agent.db
    legacy_agent_db = agent_folder / "agents" / "default" / "agent.db"
    if legacy_agent_db.exists() and not unified_db.exists():
        import shutil

        unified_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_agent_db, unified_db)
        print(f"Migrated legacy agent.db to {unified_db}")

    # Check for legacy master.db
    legacy_master_db = agent_folder / config.DB_MASTER_NAME
    if legacy_master_db.exists():
        # Migrate agents table to core_agents
        try:
            legacy_conn = sqlite3.connect(str(legacy_master_db))
            unified_conn = get_connection()

            # Copy agents data
            cursor = legacy_conn.execute("SELECT * FROM agents")
            rows = cursor.fetchall()
            if rows:
                unified_conn.executemany(
                    "INSERT OR IGNORE INTO core_agents VALUES (?, ?, ?, ?, ?)", rows
                )
                unified_conn.commit()
                print(f"Migrated {len(rows)} agents from master.db")

            legacy_conn.close()
            unified_conn.close()
        except Exception as e:
            print(f"Warning: Could not migrate master.db: {e}")


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

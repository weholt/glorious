"""Database optimization and maintenance operations."""

import sqlite3

from glorious_agents.core.db.connection import get_connection


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

"""Batch operations for improved database performance."""

from typing import Any

from glorious_agents.core.db.connection import get_connection


def batch_execute(
    query: str,
    params_list: list[tuple[Any, ...]],
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

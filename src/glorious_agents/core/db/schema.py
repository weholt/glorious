"""Schema initialization for skills and core tables."""

import sqlite3
from pathlib import Path

from glorious_agents.core.db.connection import get_connection


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
        # Use migration system: first apply base schema, then migrations
        from glorious_agents.core.migrations import (
            get_current_version,
            init_migrations_table,
            run_migrations,
        )

        # Initialize migrations table first
        init_migrations_table()

        # Only apply base schema if no migrations have been run yet
        if get_current_version(skill_name) == 0:
            conn = get_connection()
            try:
                schema_sql = schema_path.read_text()
                conn.executescript(schema_sql)
                conn.commit()
            finally:
                conn.close()

        # Then apply any pending migrations
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

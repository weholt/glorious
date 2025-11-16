"""Database migration system for schema versioning."""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from glorious_agents.core.db import get_connection


def init_migrations_table() -> None:
    """Initialize the migrations tracking table."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                version INTEGER NOT NULL,
                migration_file TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(skill_name, version)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_migrations_skill ON _migrations(skill_name)")
        conn.commit()
    finally:
        conn.close()


def get_current_version(skill_name: str) -> int:
    """
    Get the current schema version for a skill.

    Args:
        skill_name: Name of the skill.

    Returns:
        Current version number (0 if no migrations applied).
    """
    conn = get_connection()
    try:
        result = conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM _migrations WHERE skill_name = ?", (skill_name,)
        ).fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def get_migration_checksum(content: str) -> str:
    """Calculate SHA256 checksum of migration content."""
    return hashlib.sha256(content.encode()).hexdigest()


def apply_migration(skill_name: str, version: int, migration_path: Path) -> None:
    """
    Apply a migration file.

    Args:
        skill_name: Name of the skill.
        version: Migration version number.
        migration_path: Path to the migration SQL file.

    Raises:
        ValueError: If migration already applied with different checksum.
    """
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    content = migration_path.read_text()
    checksum = get_migration_checksum(content)

    conn = get_connection()
    try:
        # Check if already applied
        existing = conn.execute(
            "SELECT checksum FROM _migrations WHERE skill_name = ? AND version = ?", (skill_name, version)
        ).fetchone()

        if existing:
            if existing[0] != checksum:
                raise ValueError(
                    f"Migration {skill_name} v{version} checksum mismatch! "
                    f"Expected {existing[0]}, got {checksum}. "
                    f"Do not modify applied migrations."
                )
            return  # Already applied

        # Apply migration
        conn.executescript(content)

        # Record migration
        conn.execute(
            "INSERT INTO _migrations (skill_name, version, migration_file, checksum) VALUES (?, ?, ?, ?)",
            (skill_name, version, migration_path.name, checksum),
        )
        conn.commit()
    finally:
        conn.close()


def run_migrations(skill_name: str, migrations_dir: Path) -> list[int]:
    """
    Run all pending migrations for a skill.

    Migration files should be named: {version}_{description}.sql
    Example: 001_initial_schema.sql, 002_add_index.sql

    Args:
        skill_name: Name of the skill.
        migrations_dir: Directory containing migration files.

    Returns:
        List of versions that were applied.
    """
    if not migrations_dir.exists():
        return []

    init_migrations_table()
    current_version = get_current_version(skill_name)

    # Find migration files
    migration_files = sorted(migrations_dir.glob("*.sql"))
    applied_versions = []

    for migration_file in migration_files:
        # Parse version from filename (e.g., "001_initial.sql" -> 1)
        try:
            version_str = migration_file.stem.split("_")[0]
            version = int(version_str)
        except (ValueError, IndexError):
            continue  # Skip files that don't match pattern

        if version > current_version:
            apply_migration(skill_name, version, migration_file)
            applied_versions.append(version)

    return applied_versions


def create_migration_file(skill_name: str, migrations_dir: Path, description: str) -> Path:
    """
    Create a new migration file with the next version number.

    Args:
        skill_name: Name of the skill.
        migrations_dir: Directory to create migration in.
        description: Description for the migration (used in filename).

    Returns:
        Path to the created migration file.
    """
    migrations_dir.mkdir(parents=True, exist_ok=True)
    init_migrations_table()

    current_version = get_current_version(skill_name)
    next_version = current_version + 1

    # Clean description for filename
    clean_desc = description.lower().replace(" ", "_")
    clean_desc = "".join(c for c in clean_desc if c.isalnum() or c == "_")

    filename = f"{next_version:03d}_{clean_desc}.sql"
    migration_path = migrations_dir / filename

    # Create template
    template = f"""-- Migration: {description}
-- Skill: {skill_name}
-- Version: {next_version}
-- Created: {datetime.now().isoformat()}

-- Add your migration SQL here
-- Example:
-- ALTER TABLE my_table ADD COLUMN new_column TEXT;
-- CREATE INDEX idx_new_column ON my_table(new_column);
"""
    migration_path.write_text(template)
    return migration_path


def get_migration_history(skill_name: str | None = None) -> list[dict[str, Any]]:
    """
    Get migration history.

    Args:
        skill_name: Optional skill name to filter by.

    Returns:
        List of migration records.
    """
    conn = get_connection()
    try:
        if skill_name:
            rows = conn.execute(
                "SELECT skill_name, version, migration_file, applied_at FROM _migrations WHERE skill_name = ? ORDER BY version",
                (skill_name,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT skill_name, version, migration_file, applied_at FROM _migrations ORDER BY skill_name, version"
            ).fetchall()

        return [{"skill_name": r[0], "version": r[1], "migration_file": r[2], "applied_at": r[3]} for r in rows]
    finally:
        conn.close()


def rollback_migration(skill_name: str, target_version: int) -> None:
    """
    Rollback migrations to a target version.

    Note: This only removes migration records, it does NOT undo SQL changes.
    You must manually create down migrations to revert schema changes.

    Args:
        skill_name: Name of the skill.
        target_version: Version to roll back to.
    """
    conn = get_connection()
    try:
        current = get_current_version(skill_name)
        if target_version >= current:
            return

        conn.execute(
            "DELETE FROM _migrations WHERE skill_name = ? AND version > ?", (skill_name, target_version)
        )
        conn.commit()
    finally:
        conn.close()

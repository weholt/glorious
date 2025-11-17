"""Unit tests for database migration module."""

import shutil
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from glorious_agents.core.db_migration import (
    migrate_from_legacy,
    show_migration_status,
)


@pytest.mark.logic
def test_migrate_from_legacy_no_legacy_databases(
    temp_data_folder: Path, tmp_path: Path, capsys
) -> None:
    """Test migration when no legacy databases exist."""
    # Mock Path.home() to return a path with no legacy databases
    with patch("glorious_agents.core.db_migration.Path.home", return_value=tmp_path / "empty"):
        migrate_from_legacy()

    captured = capsys.readouterr()
    assert "No legacy databases found" in captured.out or "Starting fresh" in captured.out


@pytest.mark.logic
def test_migrate_from_legacy_agent_db(temp_data_folder: Path, tmp_path: Path, capsys) -> None:
    """Test migration of legacy agent.db."""
    # Create a legacy agent database
    legacy_home = tmp_path / ".glorious"
    legacy_agent_db = legacy_home / "agents" / "default" / "agent.db"
    legacy_agent_db.parent.mkdir(parents=True, exist_ok=True)

    # Create a simple database with a test table
    conn = sqlite3.connect(str(legacy_agent_db))
    conn.execute("CREATE TABLE test_data (id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO test_data (value) VALUES ('test')")
    conn.commit()
    conn.close()

    # Mock Path.home() to return our tmp_path
    with patch("glorious_agents.core.db_migration.Path.home", return_value=tmp_path):
        migrate_from_legacy()

    captured = capsys.readouterr()
    assert "Migrated agent database" in captured.out

    # Verify data was migrated
    from glorious_agents.core.db import get_agent_db_path, get_connection

    db_path = get_agent_db_path()
    assert db_path.exists()

    conn = get_connection()
    cursor = conn.execute("SELECT value FROM test_data")
    assert cursor.fetchone()[0] == "test"
    conn.close()


@pytest.mark.logic
def test_migrate_from_legacy_master_db(temp_data_folder: Path, tmp_path: Path, capsys) -> None:
    """Test migration of legacy master.db."""
    from glorious_agents.core.db import get_connection

    # Ensure unified db exists first
    conn = get_connection()
    conn.close()

    # Create a legacy master database
    legacy_home = tmp_path / ".glorious"
    legacy_home.mkdir(exist_ok=True)
    legacy_master_db = legacy_home / "master.db"

    conn = sqlite3.connect(str(legacy_master_db))
    conn.execute("""
        CREATE TABLE agents (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT,
            project_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "INSERT INTO agents (code, name, role, project_id) VALUES (?, ?, ?, ?)",
        ("test1", "Test Agent 1", "tester", "proj1"),
    )
    conn.commit()
    conn.close()

    # Mock Path.home() to return our tmp_path
    with patch("glorious_agents.core.db_migration.Path.home", return_value=tmp_path):
        migrate_from_legacy()

    captured = capsys.readouterr()
    assert "agents from master.db" in captured.out

    # Verify data was migrated
    conn = get_connection()
    cursor = conn.execute("SELECT code, name FROM core_agents WHERE code='test1'")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "test1"
    assert row[1] == "Test Agent 1"
    conn.close()


@pytest.mark.logic
def test_migrate_from_legacy_with_backup(temp_data_folder: Path, tmp_path: Path, capsys) -> None:
    """Test migration creates backup when unified db already exists."""
    from glorious_agents.core.db import get_agent_db_path, get_connection

    # Create existing unified database
    unified_db_path = get_agent_db_path()
    conn = get_connection()
    conn.execute("CREATE TABLE existing_data (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    # Create a legacy agent database
    legacy_home = tmp_path / ".glorious"
    legacy_agent_db = legacy_home / "agents" / "default" / "agent.db"
    legacy_agent_db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(legacy_agent_db))
    conn.execute("CREATE TABLE test_data (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    # Mock Path.home() to return our tmp_path
    with patch("glorious_agents.core.db_migration.Path.home", return_value=tmp_path):
        migrate_from_legacy()

    captured = capsys.readouterr()
    assert "Backing up current database" in captured.out

    # Verify backup was created
    backup_path = unified_db_path.with_suffix(".db.backup")
    assert backup_path.exists()


@pytest.mark.logic
def test_migrate_from_legacy_master_db_error(
    temp_data_folder: Path, tmp_path: Path, capsys
) -> None:
    """Test migration handles errors in master.db gracefully."""
    from glorious_agents.core.db import get_agent_db_path, get_connection

    # Ensure unified db exists first
    conn = get_connection()
    conn.close()

    # Create a corrupted master database
    legacy_home = tmp_path / ".glorious"
    legacy_home.mkdir(exist_ok=True)
    legacy_master_db = legacy_home / "master.db"

    # Create a database with wrong schema (will cause SQL error when selecting)
    conn = sqlite3.connect(str(legacy_master_db))
    conn.execute("CREATE TABLE agents (wrong_column TEXT)")
    conn.commit()
    conn.close()

    # Mock Path.home() to return our tmp_path
    with patch("glorious_agents.core.db_migration.Path.home", return_value=tmp_path):
        migrate_from_legacy()

    captured = capsys.readouterr()
    # Should complete without crashing - the error is caught and logged
    # Since no agent.db exists and master.db has wrong schema, it should say no databases found
    assert (
        "legacy master database" in captured.out.lower()
        or "no legacy databases" in captured.out.lower()
    )


@pytest.mark.logic
def test_show_migration_status_no_databases(temp_data_folder: Path, capsys) -> None:
    """Test show_migration_status when no databases exist."""
    with patch("glorious_agents.core.db_migration.Path.home", return_value=Path("/nonexistent")):
        show_migration_status()

    captured = capsys.readouterr()
    assert "Database Migration Status" in captured.out
    assert "Not initialized" in captured.out or "Not found" in captured.out


@pytest.mark.logic
def test_show_migration_status_with_unified_db(temp_data_folder: Path, capsys) -> None:
    """Test show_migration_status with unified database."""
    from glorious_agents.core.db import get_connection

    # Create unified database
    conn = get_connection()
    conn.close()

    with patch("glorious_agents.core.db_migration.Path.home", return_value=Path("/nonexistent")):
        show_migration_status()

    captured = capsys.readouterr()
    assert "Database Migration Status" in captured.out
    assert "Active" in captured.out


@pytest.mark.logic
def test_show_migration_status_with_legacy_databases(
    temp_data_folder: Path, tmp_path: Path, capsys
) -> None:
    """Test show_migration_status with legacy databases."""
    from glorious_agents.core.db import get_connection

    # Create unified database
    conn = get_connection()
    conn.close()

    # Create legacy databases
    legacy_home = tmp_path / ".glorious"
    legacy_agent_db = legacy_home / "agents" / "default" / "agent.db"
    legacy_agent_db.parent.mkdir(parents=True, exist_ok=True)
    legacy_agent_db.write_text("dummy")

    legacy_master_db = legacy_home / "master.db"
    legacy_master_db.write_text("dummy")

    with patch("glorious_agents.core.db_migration.Path.home", return_value=tmp_path):
        show_migration_status()

    captured = capsys.readouterr()
    assert "Database Migration Status" in captured.out
    assert "Legacy databases found" in captured.out or "Found" in captured.out


@pytest.mark.logic
def test_migrate_from_legacy_multiple_agents(
    temp_data_folder: Path, tmp_path: Path, capsys
) -> None:
    """Test migration of multiple agents from master.db."""
    from glorious_agents.core.db import get_connection

    # Ensure unified db exists first
    conn = get_connection()
    conn.close()

    # Create a legacy master database with multiple agents
    legacy_home = tmp_path / ".glorious"
    legacy_home.mkdir(exist_ok=True)
    legacy_master_db = legacy_home / "master.db"

    conn = sqlite3.connect(str(legacy_master_db))
    conn.execute("""
        CREATE TABLE agents (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT,
            project_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    agents = [
        ("agent1", "Agent One", "role1", "proj1"),
        ("agent2", "Agent Two", "role2", "proj2"),
        ("agent3", "Agent Three", "role3", "proj3"),
    ]
    for agent in agents:
        conn.execute("INSERT INTO agents (code, name, role, project_id) VALUES (?, ?, ?, ?)", agent)
    conn.commit()
    conn.close()

    # Mock Path.home() to return our tmp_path
    with patch("glorious_agents.core.db_migration.Path.home", return_value=tmp_path):
        migrate_from_legacy()

    captured = capsys.readouterr()
    assert "Migrated 3 agents from master.db" in captured.out

    # Verify all agents were migrated
    conn = get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM core_agents")
    count = cursor.fetchone()[0]
    assert count == 3
    conn.close()

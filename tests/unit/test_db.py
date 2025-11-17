"""Unit tests for database module."""

from pathlib import Path

import pytest

from glorious_agents.core.db import (
    get_agent_db_path,
    get_connection,
    get_data_folder,
    init_skill_schema,
)


@pytest.mark.logic
def test_get_data_folder(temp_data_folder: Path) -> None:
    """Test data folder resolution from environment."""
    assert get_data_folder() == temp_data_folder


@pytest.mark.logic
def test_get_agent_db_path_default(temp_data_folder: Path) -> None:
    """Test unified DB path."""
    db_path = get_agent_db_path()
    assert db_path.parent == temp_data_folder
    assert db_path.name == "glorious.db"
    # Path created on first connection, not on path retrieval
    assert db_path.parent.exists()


@pytest.mark.logic
def test_get_agent_db_path_custom(temp_data_folder: Path) -> None:
    """Test unified DB path returns same path regardless of agent."""
    # Even with active agent file, should use unified DB
    active_file = temp_data_folder / "active_agent"
    active_file.write_text("test-agent")

    db_path = get_agent_db_path()
    assert db_path.parent == temp_data_folder
    assert db_path.name == "glorious.db"


@pytest.mark.logic
def test_get_connection_wal_mode(temp_data_folder: Path) -> None:
    """Test that connection uses WAL mode."""
    conn = get_connection()

    # Check journal mode
    cur = conn.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0]
    assert mode.upper() == "WAL"

    conn.close()


@pytest.mark.logic
def test_init_skill_schema(temp_data_folder: Path, tmp_path: Path) -> None:
    """Test skill schema initialization."""
    # Create a test schema file
    schema_file = tmp_path / "test_schema.sql"
    schema_file.write_text("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            value TEXT
        );
    """)

    init_skill_schema("test_skill", schema_file)

    # Verify table exists
    conn = get_connection()
    cur = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='test_table'
    """)
    assert cur.fetchone() is not None

    # Verify metadata table
    cur = conn.execute("""
        SELECT skill_name FROM _skill_schemas
        WHERE skill_name='test_skill'
    """)
    assert cur.fetchone() is not None

    conn.close()


@pytest.mark.logic
def test_init_skill_schema_nonexistent(temp_data_folder: Path, tmp_path: Path) -> None:
    """Test init_skill_schema with nonexistent file."""
    nonexistent_file = tmp_path / "nonexistent.sql"

    # Should not raise error
    init_skill_schema("test_skill", nonexistent_file)


@pytest.mark.logic
def test_get_connection_works(temp_data_folder: Path) -> None:
    """Test that get_connection works."""
    conn = get_connection()

    # Should be able to execute queries
    cursor = conn.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1

    conn.close()


@pytest.mark.logic
def test_get_connection_creates_db_file(temp_data_folder: Path) -> None:
    """Test that get_connection creates the database file."""
    db_path = get_agent_db_path()

    # Get connection (creates file if needed)
    conn = get_connection()

    # Verify database file exists
    assert db_path.exists()

    conn.close()


@pytest.mark.logic
def test_get_connection_thread_safe(temp_data_folder: Path) -> None:
    """Test that get_connection can be called with check_same_thread=False."""
    conn = get_connection(check_same_thread=False)

    # Should be able to execute queries
    cursor = conn.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1

    conn.close()


@pytest.mark.logic
def test_init_skill_schema_duplicate(temp_data_folder: Path, tmp_path: Path) -> None:
    """Test that init_skill_schema is idempotent."""
    schema_file = tmp_path / "test_schema.sql"
    schema_file.write_text("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            value TEXT
        );
    """)

    # Initialize twice
    init_skill_schema("test_skill", schema_file)
    init_skill_schema("test_skill", schema_file)

    # Should still work
    conn = get_connection()
    cur = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='test_table'
    """)
    assert cur.fetchone() is not None
    conn.close()


@pytest.mark.logic
def test_get_master_db_path(temp_data_folder: Path) -> None:
    """Test get_master_db_path returns unified db path."""
    from glorious_agents.core.db import get_master_db_path

    master_path = get_master_db_path()
    unified_path = get_agent_db_path()
    assert master_path == unified_path


@pytest.mark.logic
def test_init_master_db(temp_data_folder: Path) -> None:
    """Test init_master_db creates core_agents table."""
    from glorious_agents.core.db import init_master_db

    init_master_db()

    conn = get_connection()
    cur = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='core_agents'
    """)
    assert cur.fetchone() is not None
    conn.close()


@pytest.mark.logic
def test_batch_execute(temp_data_folder: Path) -> None:
    """Test batch_execute with multiple params."""
    from glorious_agents.core.db import batch_execute

    # Create a test table
    conn = get_connection()
    conn.execute("CREATE TABLE test_batch (id INTEGER PRIMARY KEY, value TEXT)")
    conn.close()

    # Batch insert
    params = [("value1",), ("value2",), ("value3",), ("value4",), ("value5",)]
    batch_execute("INSERT INTO test_batch (value) VALUES (?)", params, batch_size=2)

    # Verify all rows were inserted
    conn = get_connection()
    cur = conn.execute("SELECT COUNT(*) FROM test_batch")
    count = cur.fetchone()[0]
    assert count == 5
    conn.close()


@pytest.mark.logic
def test_batch_execute_empty_list(temp_data_folder: Path) -> None:
    """Test batch_execute with empty params list."""
    from glorious_agents.core.db import batch_execute

    conn = get_connection()
    conn.execute("CREATE TABLE test_batch (id INTEGER PRIMARY KEY, value TEXT)")
    conn.close()

    # Should not crash with empty list
    batch_execute("INSERT INTO test_batch (value) VALUES (?)", [], batch_size=10)

    conn = get_connection()
    cur = conn.execute("SELECT COUNT(*) FROM test_batch")
    count = cur.fetchone()[0]
    assert count == 0
    conn.close()


@pytest.mark.logic
def test_optimize_database(temp_data_folder: Path) -> None:
    """Test optimize_database runs without errors."""
    from glorious_agents.core.db import optimize_database

    # Create some data first
    conn = get_connection()
    conn.execute("CREATE TABLE test_data (id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO test_data (value) VALUES ('test')")
    conn.commit()
    conn.close()

    # Should run without errors
    optimize_database()


@pytest.mark.logic
def test_optimize_database_with_fts(temp_data_folder: Path) -> None:
    """Test optimize_database with FTS5 tables."""
    from glorious_agents.core.db import optimize_database

    # Create an FTS5 table
    conn = get_connection()
    conn.execute("CREATE VIRTUAL TABLE test_fts USING fts5(content)")
    conn.execute("INSERT INTO test_fts (content) VALUES ('test content')")
    conn.commit()
    conn.close()

    # Should optimize FTS5 tables
    optimize_database()


@pytest.mark.logic
def test_migrate_legacy_databases_no_legacy(temp_data_folder: Path, capsys) -> None:
    """Test migrate_legacy_databases when no legacy files exist."""
    from glorious_agents.core.db import migrate_legacy_databases

    migrate_legacy_databases()
    # Should complete without errors


@pytest.mark.logic
def test_migrate_legacy_databases_agent_db(temp_data_folder: Path, capsys) -> None:
    """Test migrate_legacy_databases with legacy agent.db."""
    from glorious_agents.core.db import migrate_legacy_databases

    # Create legacy agent.db
    legacy_dir = temp_data_folder / "agents" / "default"
    legacy_dir.mkdir(parents=True)
    legacy_db = legacy_dir / "agent.db"

    import sqlite3

    conn = sqlite3.connect(str(legacy_db))
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO test_table (id) VALUES (1)")
    conn.commit()
    conn.close()

    # Remove unified db if it exists
    unified_db = get_agent_db_path()
    unified_db.unlink(missing_ok=True)

    migrate_legacy_databases()
    captured = capsys.readouterr()

    # Verify migration happened
    assert unified_db.exists()
    assert "Migrated legacy agent.db" in captured.out


@pytest.mark.logic
def test_migrate_legacy_databases_master_db(temp_data_folder: Path, capsys) -> None:
    """Test migrate_legacy_databases with legacy master.db."""
    from glorious_agents.core.db import init_master_db, migrate_legacy_databases

    # Ensure unified db exists and core_agents table is created
    init_master_db()

    # Create legacy master.db
    legacy_master = temp_data_folder / "master.db"

    import sqlite3

    conn = sqlite3.connect(str(legacy_master))
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
        ("test1", "Test Agent", "tester", "proj1"),
    )
    conn.commit()
    conn.close()

    migrate_legacy_databases()
    captured = capsys.readouterr()

    # Verify agents were migrated
    conn = get_connection()
    cur = conn.execute("SELECT code FROM core_agents WHERE code='test1'")
    assert cur.fetchone() is not None
    conn.close()
    assert "Migrated" in captured.out
    assert "agents from master.db" in captured.out


@pytest.mark.logic
def test_migrate_legacy_databases_error_handling(temp_data_folder: Path, capsys) -> None:
    """Test migrate_legacy_databases handles errors gracefully."""
    from glorious_agents.core.db import migrate_legacy_databases

    # Ensure unified db exists
    conn = get_connection()
    conn.close()

    # Create corrupted legacy master.db
    legacy_master = temp_data_folder / "master.db"
    legacy_master.write_text("not a database")

    migrate_legacy_databases()
    captured = capsys.readouterr()

    # Should handle error gracefully
    assert "Warning" in captured.out or "Could not migrate" in captured.out


@pytest.mark.logic
def test_connection_pragmas(temp_data_folder: Path) -> None:
    """Test that connection has correct PRAGMA settings."""
    conn = get_connection()

    # Check various pragmas
    cur = conn.execute("PRAGMA foreign_keys;")
    assert cur.fetchone()[0] == 1

    cur = conn.execute("PRAGMA synchronous;")
    sync_mode = cur.fetchone()[0]
    assert sync_mode in (1, 2)  # NORMAL or FULL

    cur = conn.execute("PRAGMA busy_timeout;")
    timeout = cur.fetchone()[0]
    assert timeout == 5000

    conn.close()

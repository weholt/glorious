"""Unit tests for database module."""

from pathlib import Path

import pytest

from glorious_agents.core.db import (
    get_agent_db_path,
    get_agent_folder,
    get_connection,
    init_skill_schema,
)


@pytest.mark.logic
def test_get_agent_folder(temp_agent_folder: Path) -> None:
    """Test agent folder resolution from environment."""
    assert get_agent_folder() == temp_agent_folder


@pytest.mark.logic
def test_get_agent_db_path_default(temp_agent_folder: Path) -> None:
    """Test default agent DB path."""
    db_path = get_agent_db_path()
    assert db_path.parent.name == "default"
    assert db_path.name == "agent.db"
    # Path created on first connection, not on path retrieval
    assert db_path.parent.exists()


@pytest.mark.logic
def test_get_agent_db_path_custom(temp_agent_folder: Path) -> None:
    """Test custom agent DB path."""
    # Create active agent file
    active_file = temp_agent_folder / "active_agent"
    active_file.write_text("test-agent")
    
    db_path = get_agent_db_path()
    assert db_path.parent.name == "test-agent"
    assert db_path.name == "agent.db"


@pytest.mark.logic
def test_get_connection_wal_mode(temp_agent_folder: Path) -> None:
    """Test that connection uses WAL mode."""
    conn = get_connection()
    
    # Check journal mode
    cur = conn.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0]
    assert mode.upper() == "WAL"
    
    conn.close()


@pytest.mark.logic
def test_init_skill_schema(temp_agent_folder: Path, tmp_path: Path) -> None:
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

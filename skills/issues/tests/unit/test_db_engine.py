"""Tests for database engine factory."""

import os
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.pool import StaticPool

from issue_tracker.adapters.db.engine import create_db_engine, get_database_path


def test_create_db_engine_default():
    """Test creating engine with default settings."""
    engine = create_db_engine()
    assert engine is not None
    # Test it works
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_create_db_engine_memory():
    """Test creating in-memory SQLite engine."""
    engine = create_db_engine("sqlite:///:memory:")
    assert engine is not None
    assert engine.pool.__class__ == StaticPool
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_create_db_engine_memory_short():
    """Test creating in-memory SQLite engine with short URL."""
    engine = create_db_engine("sqlite://")
    assert engine is not None
    assert engine.pool.__class__ == StaticPool


def test_create_db_engine_file(tmp_path):
    """Test creating file-based SQLite engine."""
    db_file = tmp_path / "test.db"
    engine = create_db_engine(f"sqlite:///{db_file}")
    assert engine is not None
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_create_db_engine_echo():
    """Test creating engine with echo enabled."""
    engine = create_db_engine("sqlite:///:memory:", echo=True)
    assert engine.echo is True


def test_create_db_engine_from_env(monkeypatch):
    """Test creating engine from environment variable."""
    monkeypatch.setenv("ISSUE_TRACKER_DB_URL", "sqlite:///:memory:")
    engine = create_db_engine()
    assert engine is not None


def test_get_database_path_default():
    """Test getting database path with default URL."""
    path = get_database_path()
    assert path == Path("./issues.db")


def test_get_database_path_memory():
    """Test getting database path for in-memory database."""
    os.environ["ISSUE_TRACKER_DB_URL"] = "sqlite:///:memory:"
    path = get_database_path()
    assert path == Path("memory")
    del os.environ["ISSUE_TRACKER_DB_URL"]


def test_get_database_path_memory_short():
    """Test getting database path for in-memory database (short URL)."""
    os.environ["ISSUE_TRACKER_DB_URL"] = "sqlite://"
    path = get_database_path()
    assert path == Path("memory")
    del os.environ["ISSUE_TRACKER_DB_URL"]


def test_get_database_path_custom():
    """Test getting database path for custom file."""
    os.environ["ISSUE_TRACKER_DB_URL"] = "sqlite:///custom/path/db.db"
    path = get_database_path()
    assert path == Path("custom/path/db.db")
    del os.environ["ISSUE_TRACKER_DB_URL"]


def test_get_database_path_non_sqlite():
    """Test getting database path for non-SQLite raises error."""
    os.environ["ISSUE_TRACKER_DB_URL"] = "postgresql://localhost/test"
    with pytest.raises(ValueError, match="Only SQLite databases supported"):
        get_database_path()
    del os.environ["ISSUE_TRACKER_DB_URL"]

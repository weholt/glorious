"""Tests for cache skill."""

import pytest
from datetime import datetime, timedelta

from glorious_agents.core.context import SkillContext
from glorious_skill_cache.skill import init_context, set_cache, get_cache, prune_expired


@pytest.fixture
def cache_context(tmp_path):
    """Create a test context with cache skill initialized."""
    import sqlite3
    
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    
    # Initialize schema
    schema_sql = """
    CREATE TABLE IF NOT EXISTS cache_entries (
        key TEXT PRIMARY KEY,
        value BLOB NOT NULL,
        kind TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        ttl_seconds INTEGER,
        meta JSON
    );
    """
    conn.executescript(schema_sql)
    conn.commit()
    
    ctx = SkillContext(conn, {})
    init_context(ctx)
    
    yield ctx
    
    conn.close()


def test_set_and_get_cache(cache_context):
    """Test basic cache set and get operations."""
    set_cache("test-key", "test-value")
    
    result = get_cache("test-key")
    assert result == "test-value"


def test_get_nonexistent_key(cache_context):
    """Test getting a non-existent cache key."""
    result = get_cache("nonexistent")
    assert result is None


def test_cache_with_ttl(cache_context):
    """Test cache entry with TTL."""
    # Set with 1 second TTL
    set_cache("ttl-key", "ttl-value", ttl_seconds=1)
    
    # Should be available immediately
    result = get_cache("ttl-key")
    assert result == "ttl-value"


def test_cache_expiration(cache_context):
    """Test that expired entries are removed."""
    # Set entry with past creation time (simulated expiration)
    past_time = (datetime.utcnow() - timedelta(seconds=10)).isoformat()
    
    cache_context.conn.execute("""
        INSERT INTO cache_entries (key, value, kind, created_at, ttl_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, ("expired-key", b"expired-value", "test", past_time, 5))
    cache_context.conn.commit()
    
    # Should return None for expired entry
    result = get_cache("expired-key")
    assert result is None


def test_cache_kinds(cache_context):
    """Test cache with different kinds."""
    set_cache("ast:file1", "ast-data", kind="ast")
    set_cache("symbol:func1", "symbol-data", kind="symbols")
    
    assert get_cache("ast:file1") == "ast-data"
    assert get_cache("symbol:func1") == "symbol-data"


def test_prune_expired(cache_context):
    """Test pruning expired entries."""
    # Add expired entry
    past_time = (datetime.utcnow() - timedelta(seconds=10)).isoformat()
    cache_context.conn.execute("""
        INSERT INTO cache_entries (key, value, kind, created_at, ttl_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, ("expired1", b"value1", "test", past_time, 5))
    
    # Add valid entry
    set_cache("valid1", "value2", ttl_seconds=3600)
    
    cache_context.conn.commit()
    
    # Prune should remove only expired
    deleted = prune_expired()
    assert deleted == 1
    
    # Valid entry should still exist
    assert get_cache("valid1") == "value2"


def test_cache_replace(cache_context):
    """Test replacing existing cache entry."""
    set_cache("key1", "value1")
    set_cache("key1", "value2")
    
    result = get_cache("key1")
    assert result == "value2"


def test_large_value(cache_context):
    """Test caching large values."""
    large_value = "x" * 100000
    set_cache("large-key", large_value)
    
    result = get_cache("large-key")
    assert result == large_value

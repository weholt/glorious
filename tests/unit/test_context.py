"""Unit tests for context and event bus."""

from pathlib import Path

import pytest

from glorious_agents.core.context import EventBus, SkillContext


@pytest.mark.logic
def test_event_bus_publish_subscribe() -> None:
    """Test basic pub/sub functionality."""
    bus = EventBus()
    received = []
    
    def handler(data: dict) -> None:
        received.append(data)
    
    bus.subscribe("test_topic", handler)
    bus.publish("test_topic", {"key": "value"})
    
    assert len(received) == 1
    assert received[0]["key"] == "value"


@pytest.mark.logic
def test_event_bus_multiple_subscribers() -> None:
    """Test multiple subscribers to same topic."""
    bus = EventBus()
    received1 = []
    received2 = []
    
    bus.subscribe("topic", lambda d: received1.append(d))
    bus.subscribe("topic", lambda d: received2.append(d))
    
    bus.publish("topic", {"msg": "hello"})
    
    assert len(received1) == 1
    assert len(received2) == 1


@pytest.mark.logic
def test_event_bus_error_handling() -> None:
    """Test that errors in handlers don't break the bus."""
    bus = EventBus()
    received = []
    
    def failing_handler(data: dict) -> None:
        raise ValueError("Test error")
    
    def working_handler(data: dict) -> None:
        received.append(data)
    
    bus.subscribe("topic", failing_handler)
    bus.subscribe("topic", working_handler)
    
    bus.publish("topic", {"test": "data"})
    
    # Working handler should still receive the event
    assert len(received) == 1


@pytest.mark.logic
def test_skill_context_registration(skill_context: SkillContext) -> None:
    """Test skill registration in context."""
    def dummy_app() -> str:
        return "test"
    
    skill_context.register_skill("test_skill", dummy_app)
    
    retrieved = skill_context.get_skill("test_skill")
    assert retrieved is not None
    assert retrieved() == "test"


@pytest.mark.logic
def test_skill_context_cache(skill_context: SkillContext) -> None:
    """Test context caching functionality."""
    skill_context.cache_set("key1", "value1")
    skill_context.cache_set("key2", 42)
    
    assert skill_context.cache_get("key1") == "value1"
    assert skill_context.cache_get("key2") == 42
    assert skill_context.cache_get("nonexistent") is None
    
    skill_context.cache_clear()
    assert skill_context.cache_get("key1") is None


@pytest.mark.logic
def test_skill_context_event_integration(skill_context: SkillContext) -> None:
    """Test that context integrates with event bus."""
    received = []
    
    skill_context.subscribe("test_event", lambda d: received.append(d))
    skill_context.publish("test_event", {"data": "test"})
    
    assert len(received) == 1
    assert received[0]["data"] == "test"


@pytest.mark.logic
def test_skill_context_cache_ttl(skill_context: SkillContext) -> None:
    """Test cache with TTL expiration."""
    import time
    
    # Set with 1 second TTL
    skill_context.cache_set("expiring", "value", ttl=1)
    assert skill_context.cache_get("expiring") == "value"
    
    # Wait for expiration
    time.sleep(1.1)
    assert skill_context.cache_get("expiring") is None


@pytest.mark.logic
def test_skill_context_cache_has(skill_context: SkillContext) -> None:
    """Test cache_has method."""
    skill_context.cache_set("existing", "value")
    
    assert skill_context.cache_has("existing") is True
    assert skill_context.cache_has("nonexistent") is False


@pytest.mark.logic
def test_skill_context_cache_delete(skill_context: SkillContext) -> None:
    """Test cache_delete method."""
    skill_context.cache_set("to_delete", "value")
    
    assert skill_context.cache_delete("to_delete") is True
    assert skill_context.cache_get("to_delete") is None
    assert skill_context.cache_delete("to_delete") is False  # Already deleted


@pytest.mark.logic
def test_skill_context_cache_prune_expired(skill_context: SkillContext) -> None:
    """Test pruning expired entries."""
    import time
    
    skill_context.cache_set("permanent", "value")
    skill_context.cache_set("expires1", "value", ttl=1)
    skill_context.cache_set("expires2", "value", ttl=1)
    
    time.sleep(1.1)
    
    count = skill_context.cache_prune_expired()
    assert count == 2
    assert skill_context.cache_get("permanent") == "value"
    assert skill_context.cache_get("expires1") is None
    assert skill_context.cache_get("expires2") is None


@pytest.mark.logic
def test_skill_context_get_config_no_skill(skill_context: SkillContext) -> None:
    """Test get_config when no skill name is set."""
    # No _skill_name attribute set
    result = skill_context.get_config("some.key", default="default_value")
    assert result == "default_value"


@pytest.mark.logic
def test_skill_context_get_config_nonexistent_file(
    skill_context: SkillContext, temp_agent_folder: Path
) -> None:
    """Test get_config with nonexistent config file."""
    skill_context._skill_name = "test_skill"
    
    # Config file doesn't exist
    result = skill_context.get_config("some.key", default="default_value")
    assert result == "default_value"


@pytest.mark.logic
def test_skill_context_get_config_with_file(
    skill_context: SkillContext, temp_agent_folder: Path
) -> None:
    """Test get_config with existing config file."""
    import tomli_w
    
    skill_context._skill_name = "test_skill"
    
    # Create config directory and file
    config_dir = temp_agent_folder / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "test_skill.toml"
    
    config_data = {
        "cache": {"ttl_default": 300},
        "api": {"url": "https://example.com", "timeout": 30},
        "simple_key": "simple_value",
    }
    
    with open(config_file, "wb") as f:
        tomli_w.dump(config_data, f)
    
    # Test nested keys
    assert skill_context.get_config("cache.ttl_default") == 300
    assert skill_context.get_config("api.url") == "https://example.com"
    assert skill_context.get_config("api.timeout") == 30
    
    # Test simple key
    assert skill_context.get_config("simple_key") == "simple_value"
    
    # Test nonexistent key
    assert skill_context.get_config("nonexistent.key", "default") == "default"


@pytest.mark.logic
def test_skill_context_get_skill_nonexistent(skill_context: SkillContext) -> None:
    """Test get_skill for nonexistent skill."""
    result = skill_context.get_skill("nonexistent_skill")
    assert result is None


@pytest.mark.logic
def test_skill_context_conn_property(skill_context: SkillContext) -> None:
    """Test conn property returns connection."""
    conn = skill_context.conn
    assert conn is not None
    # Verify it's a working connection
    cursor = conn.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1


@pytest.mark.logic
def test_skill_context_cache_max_size(skill_context: SkillContext) -> None:
    """Test cache size limit with LRU eviction."""
    from glorious_agents.core.context import EventBus, SkillContext
    import sqlite3
    
    # Create context with small cache
    conn = sqlite3.connect(":memory:")
    bus = EventBus()
    ctx = SkillContext(conn, bus, cache_max_size=3)
    
    # Add 4 items
    ctx.cache_set("key1", "value1")
    ctx.cache_set("key2", "value2")
    ctx.cache_set("key3", "value3")
    ctx.cache_set("key4", "value4")
    
    # First key should be evicted (LRU)
    assert ctx.cache_get("key1") is None
    assert ctx.cache_get("key2") == "value2"
    assert ctx.cache_get("key3") == "value3"
    assert ctx.cache_get("key4") == "value4"


@pytest.mark.logic
def test_event_bus_thread_safety() -> None:
    """Test concurrent publishing and subscribing to event bus."""
    import threading
    
    bus = EventBus()
    received = []
    errors = []
    
    def handler(data: dict) -> None:
        received.append(data)
    
    def subscribe_worker() -> None:
        try:
            for i in range(10):
                bus.subscribe(f"topic_{i % 3}", handler)
        except Exception as e:
            errors.append(e)
    
    def publish_worker() -> None:
        try:
            for i in range(10):
                bus.publish(f"topic_{i % 3}", {"index": i})
        except Exception as e:
            errors.append(e)
    
    # Run concurrent operations
    threads = []
    for _ in range(3):
        threads.append(threading.Thread(target=subscribe_worker))
        threads.append(threading.Thread(target=publish_worker))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Should not have any errors
    assert len(errors) == 0
    # Should have received some events
    assert len(received) > 0


@pytest.mark.logic
def test_skill_context_cache_concurrent_access() -> None:
    """Test concurrent cache access is thread-safe."""
    from glorious_agents.core.context import EventBus, SkillContext
    import sqlite3
    import threading
    
    conn = sqlite3.connect(":memory:")
    bus = EventBus()
    ctx = SkillContext(conn, bus, cache_max_size=100)
    errors = []
    
    def writer_worker(worker_id: int) -> None:
        try:
            for i in range(20):
                ctx.cache_set(f"key_{worker_id}_{i}", f"value_{i}")
        except Exception as e:
            errors.append(e)
    
    def reader_worker(worker_id: int) -> None:
        try:
            for i in range(20):
                ctx.cache_get(f"key_{worker_id}_{i}")
        except Exception as e:
            errors.append(e)
    
    # Run concurrent operations
    threads = []
    for i in range(5):
        threads.append(threading.Thread(target=writer_worker, args=(i,)))
        threads.append(threading.Thread(target=reader_worker, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Should not have any errors
    assert len(errors) == 0

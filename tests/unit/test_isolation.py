"""Tests for skill isolation and permission system."""

import sqlite3
from unittest.mock import MagicMock

import pytest

from glorious_agents.core.isolation import (
    Permission,
    PermissionRegistry,
    RestrictedConnection,
    RestrictedSkillContext,
    SkillPermissions,
    create_restricted_context,
    get_permission_registry,
)


@pytest.mark.logic
def test_skill_permissions_defaults() -> None:
    """Test default permissions for skills."""
    perms = SkillPermissions("test_skill")
    
    # Default permissions should be read-only
    assert perms.has(Permission.DB_READ)
    assert perms.has(Permission.EVENT_SUBSCRIBE)
    assert perms.has(Permission.SKILL_CALL)
    
    # Write permissions should not be granted by default
    assert not perms.has(Permission.DB_WRITE)
    assert not perms.has(Permission.FILESYSTEM_WRITE)
    assert not perms.has(Permission.EVENT_PUBLISH)


@pytest.mark.logic
def test_skill_permissions_grant_revoke() -> None:
    """Test granting and revoking permissions."""
    perms = SkillPermissions("test_skill")
    
    # Grant a permission
    perms.grant(Permission.DB_WRITE)
    assert perms.has(Permission.DB_WRITE)
    
    # Revoke a permission
    perms.revoke(Permission.DB_WRITE)
    assert not perms.has(Permission.DB_WRITE)


@pytest.mark.logic
def test_skill_permissions_require() -> None:
    """Test requiring permissions."""
    perms = SkillPermissions("test_skill")
    
    # Should not raise for granted permission
    perms.require(Permission.DB_READ)
    
    # Should raise for missing permission
    with pytest.raises(PermissionError, match="does not have permission"):
        perms.require(Permission.DB_WRITE)


@pytest.mark.logic
def test_restricted_connection_read() -> None:
    """Test restricted connection allows reads."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER)")
    
    perms = SkillPermissions("test_skill")
    restricted = RestrictedConnection(conn, perms)
    
    # Read should work with default permissions
    cursor = restricted.execute("SELECT * FROM test")
    assert cursor is not None


@pytest.mark.logic
def test_restricted_connection_write_denied() -> None:
    """Test restricted connection blocks writes without permission."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER)")
    
    perms = SkillPermissions("test_skill")
    restricted = RestrictedConnection(conn, perms)
    
    # Write should fail without permission
    with pytest.raises(PermissionError, match="does not have permission"):
        restricted.execute("INSERT INTO test VALUES (1)")


@pytest.mark.logic
def test_restricted_connection_write_allowed() -> None:
    """Test restricted connection allows writes with permission."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER)")
    
    perms = SkillPermissions("test_skill")
    perms.grant(Permission.DB_WRITE)
    restricted = RestrictedConnection(conn, perms)
    
    # Write should work with permission
    restricted.execute("INSERT INTO test VALUES (1)")
    restricted.commit()
    
    result = conn.execute("SELECT COUNT(*) FROM test").fetchone()
    assert result[0] == 1


@pytest.mark.logic
def test_restricted_connection_close_denied() -> None:
    """Test restricted connection blocks closing shared connection."""
    conn = sqlite3.connect(":memory:")
    perms = SkillPermissions("test_skill")
    restricted = RestrictedConnection(conn, perms)
    
    # Should not be able to close shared connection
    with pytest.raises(PermissionError, match="Cannot close"):
        restricted.close()


@pytest.mark.logic
def test_restricted_event_bus_publish_denied() -> None:
    """Test restricted event bus blocks publish without permission."""
    mock_bus = MagicMock()
    perms = SkillPermissions("test_skill")
    
    from glorious_agents.core.isolation import RestrictedEventBus
    restricted = RestrictedEventBus(mock_bus, perms)
    
    # Publish should fail without permission
    with pytest.raises(PermissionError, match="does not have permission"):
        restricted.publish("test_topic", {"data": "value"})


@pytest.mark.logic
def test_restricted_event_bus_subscribe_allowed() -> None:
    """Test restricted event bus allows subscribe with default permissions."""
    mock_bus = MagicMock()
    perms = SkillPermissions("test_skill")
    
    from glorious_agents.core.isolation import RestrictedEventBus
    restricted = RestrictedEventBus(mock_bus, perms)
    
    # Subscribe should work with default permissions
    def callback(data: dict) -> None:
        pass
    
    restricted.subscribe("test_topic", callback)
    mock_bus.subscribe.assert_called_once()


@pytest.mark.logic
def test_restricted_context_access() -> None:
    """Test restricted context provides limited access."""
    mock_ctx = MagicMock()
    mock_ctx.conn = sqlite3.connect(":memory:")
    mock_ctx._event_bus = MagicMock()
    
    perms = SkillPermissions("test_skill")
    restricted = RestrictedSkillContext(mock_ctx, perms)
    
    # Should have access to cache
    restricted.cache_get("key")
    mock_ctx.cache_get.assert_called_once_with("key")
    
    # Should have access to config
    restricted.get_config("key", "default")
    mock_ctx.get_config.assert_called_once_with("key", "default")


@pytest.mark.logic
def test_restricted_context_skill_call_denied() -> None:
    """Test restricted context requires permission for skill calls."""
    mock_ctx = MagicMock()
    mock_ctx.conn = sqlite3.connect(":memory:")
    mock_ctx._event_bus = MagicMock()
    
    perms = SkillPermissions("test_skill")
    perms.revoke(Permission.SKILL_CALL)
    
    restricted = RestrictedSkillContext(mock_ctx, perms)
    
    # Should fail without skill_call permission
    with pytest.raises(PermissionError, match="does not have permission"):
        restricted.get_skill("other_skill")


@pytest.mark.logic
def test_permission_registry_defaults() -> None:
    """Test permission registry has defaults for core skills."""
    registry = PermissionRegistry()
    
    # Core skills should have write permissions
    issues_perms = registry.get("issues")
    assert issues_perms.has(Permission.DB_WRITE)
    assert issues_perms.has(Permission.EVENT_PUBLISH)
    
    # Unknown skills should get default (read-only) permissions
    unknown_perms = registry.get("unknown_skill")
    assert unknown_perms.has(Permission.DB_READ)
    assert not unknown_perms.has(Permission.DB_WRITE)


@pytest.mark.logic
def test_permission_registry_set() -> None:
    """Test setting custom permissions in registry."""
    registry = PermissionRegistry()
    
    custom_perms = SkillPermissions("custom_skill")
    custom_perms.grant(Permission.NETWORK)
    
    registry.set("custom_skill", custom_perms)
    
    retrieved = registry.get("custom_skill")
    assert retrieved.has(Permission.NETWORK)


@pytest.mark.logic
def test_create_restricted_context() -> None:
    """Test creating restricted context for a skill."""
    mock_ctx = MagicMock()
    mock_ctx.conn = sqlite3.connect(":memory:")
    mock_ctx._event_bus = MagicMock()
    
    restricted = create_restricted_context(mock_ctx, "issues")
    
    # Should be a RestrictedSkillContext
    assert isinstance(restricted, RestrictedSkillContext)
    
    # Should have permissions from registry
    assert restricted._permissions.has(Permission.DB_WRITE)


@pytest.mark.logic
def test_global_permission_registry() -> None:
    """Test global permission registry singleton."""
    registry1 = get_permission_registry()
    registry2 = get_permission_registry()
    
    # Should be the same instance
    assert registry1 is registry2

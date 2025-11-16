"""Skill isolation and security controls."""

import logging
import sqlite3
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permissions that can be granted to skills."""

    DB_READ = "db_read"
    DB_WRITE = "db_write"
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    NETWORK = "network"
    SUBPROCESS = "subprocess"
    EVENT_PUBLISH = "event_publish"
    EVENT_SUBSCRIBE = "event_subscribe"
    SKILL_CALL = "skill_call"


class SkillPermissions:
    """Permission set for a skill."""

    def __init__(self, skill_name: str, permissions: set[Permission] | None = None) -> None:
        self.skill_name = skill_name
        self._permissions = permissions or self._default_permissions()

    @staticmethod
    def _default_permissions() -> set[Permission]:
        """Default permissions for skills - read-only access."""
        return {
            Permission.DB_READ,
            Permission.EVENT_SUBSCRIBE,
            Permission.SKILL_CALL,
        }

    def has(self, permission: Permission) -> bool:
        """Check if skill has a specific permission."""
        return permission in self._permissions

    def grant(self, permission: Permission) -> None:
        """Grant a permission to the skill."""
        self._permissions.add(permission)

    def revoke(self, permission: Permission) -> None:
        """Revoke a permission from the skill."""
        self._permissions.discard(permission)

    def require(self, permission: Permission) -> None:
        """Require a permission, raise if not granted."""
        if not self.has(permission):
            raise PermissionError(
                f"Skill '{self.skill_name}' does not have permission: {permission.value}"
            )


class RestrictedConnection:
    """Database connection wrapper with permission checks."""

    def __init__(self, conn: sqlite3.Connection, permissions: SkillPermissions) -> None:
        self._conn = conn
        self._permissions = permissions

    def execute(self, sql: str, parameters: Any = None) -> sqlite3.Cursor:
        """Execute SQL with permission checks."""
        sql_upper = sql.strip().upper()

        # Check for write operations
        write_operations = ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
        is_write = any(sql_upper.startswith(op) for op in write_operations)

        if is_write:
            self._permissions.require(Permission.DB_WRITE)
        else:
            self._permissions.require(Permission.DB_READ)

        if parameters is None:
            return self._conn.execute(sql)
        return self._conn.execute(sql, parameters)

    def executemany(self, sql: str, parameters: Any) -> sqlite3.Cursor:
        """Execute many SQL statements with permission checks."""
        self._permissions.require(Permission.DB_WRITE)
        return self._conn.executemany(sql, parameters)

    def commit(self) -> None:
        """Commit transaction."""
        self._permissions.require(Permission.DB_WRITE)
        self._conn.commit()

    def rollback(self) -> None:
        """Rollback transaction."""
        self._conn.rollback()

    def close(self) -> None:
        """Close connection - not allowed for shared connection."""
        raise PermissionError("Cannot close shared database connection")

    @property
    def row_factory(self) -> Any:
        """Get row factory."""
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, factory: Any) -> None:
        """Set row factory."""
        self._conn.row_factory = factory


class RestrictedEventBus:
    """Event bus wrapper with permission checks."""

    def __init__(self, event_bus: Any, permissions: SkillPermissions) -> None:
        self._event_bus = event_bus
        self._permissions = permissions

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        """Publish event with permission check."""
        self._permissions.require(Permission.EVENT_PUBLISH)
        self._event_bus.publish(topic, data)

    def subscribe(self, topic: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """Subscribe to event with permission check."""
        self._permissions.require(Permission.EVENT_SUBSCRIBE)
        self._event_bus.subscribe(topic, callback)


class RestrictedSkillContext:
    """Restricted context provided to skills with permission enforcement."""

    def __init__(self, ctx: Any, permissions: SkillPermissions) -> None:
        self._ctx = ctx
        self._permissions = permissions
        self._restricted_conn = RestrictedConnection(ctx.conn, permissions)
        self._restricted_event_bus = RestrictedEventBus(ctx._event_bus, permissions)

    @property
    def conn(self) -> RestrictedConnection:
        """Get restricted database connection."""
        return self._restricted_conn

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        """Publish event."""
        self._restricted_event_bus.publish(topic, data)

    def subscribe(self, topic: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """Subscribe to event."""
        self._restricted_event_bus.subscribe(topic, callback)

    def get_skill(self, name: str) -> Any:
        """Get a skill app."""
        self._permissions.require(Permission.SKILL_CALL)
        return self._ctx.get_skill(name)

    def cache_get(self, key: str) -> Any:
        """Get value from cache."""
        return self._ctx.cache_get(key)

    def cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        self._ctx.cache_set(key, value, ttl)

    def cache_has(self, key: str) -> bool:
        """Check if key exists in cache."""
        result: bool = self._ctx.cache_has(key)
        return result

    def cache_delete(self, key: str) -> bool:
        """Delete key from cache."""
        result: bool = self._ctx.cache_delete(key)
        return result

    def cache_clear(self) -> None:
        """Clear cache."""
        self._ctx.cache_clear()

    def cache_prune_expired(self) -> int:
        """Prune expired cache entries."""
        result: int = self._ctx.cache_prune_expired()
        return result

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._ctx.get_config(key, default)


class PermissionRegistry:
    """Registry of skill permissions."""

    def __init__(self) -> None:
        self._permissions: dict[str, SkillPermissions] = {}
        self._setup_default_permissions()

    def _setup_default_permissions(self) -> None:
        """Setup default permissions for known skills."""
        # Core skills that need write access
        core_skills_write = [
            "issues",
            "notes",
            "planner",
            "feedback",
            "cache",
            "prompts",
            "temporal",
            "vacuum",
            "atlas",
            "automations",
            "ai",
            "sandbox",
            "telemetry",
            "linker",
            "migrate",
            "docs",
        ]

        for skill in core_skills_write:
            perms = SkillPermissions(skill)
            perms.grant(Permission.DB_WRITE)
            perms.grant(Permission.EVENT_PUBLISH)
            self._permissions[skill] = perms

    def get(self, skill_name: str) -> SkillPermissions:
        """Get permissions for a skill."""
        if skill_name not in self._permissions:
            self._permissions[skill_name] = SkillPermissions(skill_name)
        return self._permissions[skill_name]

    def set(self, skill_name: str, permissions: SkillPermissions) -> None:
        """Set permissions for a skill."""
        self._permissions[skill_name] = permissions


# Global permission registry
_permission_registry = PermissionRegistry()


def get_permission_registry() -> PermissionRegistry:
    """Get the global permission registry."""
    return _permission_registry


def create_restricted_context(ctx: Any, skill_name: str) -> RestrictedSkillContext:
    """Create a restricted context for a skill."""
    permissions = _permission_registry.get(skill_name)
    return RestrictedSkillContext(ctx, permissions)

# Proposed Code Changes

Based on the comprehensive code review, here are concrete proposals to address the high and medium priority issues. Each proposal includes specific code changes, rationale, and implementation guidance.

## High Priority Fixes

### 1. SECURE-001: Fix SQL Injection Vulnerability in RestrictedConnection

**Current Issue**: String prefix matching can be bypassed with comments, whitespace, or CTEs.

**Proposed Solution**: Use sqlparse library for robust SQL statement type detection.

#### Changes to `pyproject.toml`

Add sqlparse as a dependency:

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.7.0",
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "tomli-w>=1.0.0",
    "ruff>=0.14.5",
    "sqlparse>=0.5.0",  # NEW: For secure SQL parsing
]
```

#### Changes to `src/glorious_agents/core/isolation.py`

Replace the `RestrictedConnection.execute()` method:

```python
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML, DDL

class RestrictedConnection:
    """Database connection wrapper with permission checks."""
    
    # Class-level constants for SQL operation types
    READ_OPERATIONS = {"SELECT", "PRAGMA"}
    WRITE_OPERATIONS = {"INSERT", "UPDATE", "DELETE"}
    DDL_OPERATIONS = {"CREATE", "DROP", "ALTER", "TRUNCATE", "RENAME"}
    
    def __init__(self, conn: sqlite3.Connection, permissions: SkillPermissions) -> None:
        self._conn = conn
        self._permissions = permissions
    
    def _get_sql_operation_type(self, sql: str) -> str:
        """
        Determine the type of SQL operation using sqlparse.
        
        Returns:
            'read', 'write', 'ddl', or 'unknown'
        """
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return 'unknown'
            
            stmt: Statement = parsed[0]
            
            # Get first meaningful token
            first_token = stmt.token_first(skip_ws=True, skip_cm=True)
            if not first_token:
                return 'unknown'
            
            # Check token type and value
            token_value = first_token.value.upper()
            
            if token_value in self.READ_OPERATIONS:
                return 'read'
            elif token_value in self.WRITE_OPERATIONS:
                return 'write'
            elif token_value in self.DDL_OPERATIONS:
                return 'ddl'
            elif token_value in {"WITH"}:
                # CTE - analyze the actual operation
                # Look for INSERT/UPDATE/DELETE/SELECT after WITH
                tokens = list(stmt.flatten())
                for i, token in enumerate(tokens):
                    if token.ttype is Keyword.DML:
                        if token.value.upper() in self.WRITE_OPERATIONS:
                            return 'write'
                        elif token.value.upper() == 'SELECT':
                            return 'read'
                return 'unknown'
            else:
                return 'unknown'
        except Exception:
            # If parsing fails, be conservative and treat as write
            return 'write'
    
    def execute(self, sql: str, parameters: Any = None) -> sqlite3.Cursor:
        """Execute SQL with permission checks using robust parsing."""
        operation_type = self._get_sql_operation_type(sql)
        
        if operation_type == 'ddl':
            # DDL operations need special permission (could add Permission.DB_DDL)
            self._permissions.require(Permission.DB_WRITE)
        elif operation_type in ('write', 'unknown'):
            # Write or unknown operations require write permission
            self._permissions.require(Permission.DB_WRITE)
        else:  # read
            self._permissions.require(Permission.DB_READ)
        
        if parameters is None:
            return self._conn.execute(sql)
        return self._conn.execute(sql, parameters)
```

**Testing Requirements**:
- Test with comments: `/* comment */ INSERT INTO ...`
- Test with CTEs: `WITH cte AS (...) INSERT ...`
- Test with whitespace: `\n\t  INSERT ...`
- Test malformed SQL
- Performance test with large queries

---

### 2. SEC-002: Implement Proper Database Connection Lifecycle

**Current Issue**: Database connections are never closed, leading to resource leaks.

**Proposed Solution**: Implement context manager pattern and explicit cleanup.

#### Changes to `src/glorious_agents/core/context.py`

Add context manager methods to SkillContext:

```python
class SkillContext:
    """Shared context for all skills with TTL-aware cache."""
    
    def __init__(
        self, conn: sqlite3.Connection, event_bus: EventBus, cache_max_size: int = 1000
    ) -> None:
        self._conn = conn
        self._event_bus = event_bus
        self._skills: dict[str, SkillApp] = {}
        self._cache = TTLCache(max_size=cache_max_size)
        self._closed = False
    
    def __enter__(self) -> "SkillContext":
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup resources."""
        self.close()
    
    def close(self) -> None:
        """Close database connection and cleanup resources."""
        if not self._closed:
            try:
                self._conn.close()
            except Exception:
                pass  # Ignore errors during cleanup
            self._closed = True
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Get the shared database connection."""
        if self._closed:
            raise RuntimeError("Cannot use connection after context is closed")
        return self._conn
    
    # ... rest of methods unchanged
```

#### Changes to `src/glorious_agents/core/runtime.py`

Add cleanup function and improve lifecycle:

```python
"""Runtime singleton for skill context."""

import atexit
import threading

from glorious_agents.core.context import EventBus, SkillContext
from glorious_agents.core.db import get_connection

_context: SkillContext | None = None
_lock = threading.Lock()


def get_ctx() -> SkillContext:
    """
    Get the singleton skill context.
    
    Thread-safe singleton initialization using double-checked locking pattern.
    The context is shared across all skills and provides access to the database
    connection and event bus.
    
    Returns:
        The shared SkillContext instance.
    """
    global _context
    # Double-checked locking for performance
    if _context is None:
        with _lock:
            # Check again inside lock to prevent race condition
            if _context is None:
                conn = get_connection(check_same_thread=False)
                event_bus = EventBus()
                _context = SkillContext(conn, event_bus)
                # Register cleanup on exit
                atexit.register(_cleanup_context)
    return _context


def reset_ctx() -> None:
    """
    Reset the context (useful for testing).
    
    Thread-safe cleanup of the singleton context. Closes the database connection
    and resets the global context to None.
    """
    global _context
    with _lock:
        if _context is not None:
            _context.close()
        _context = None


def _cleanup_context() -> None:
    """Cleanup function called on program exit."""
    reset_ctx()
```

**Benefits**:
- Resources properly cleaned up on exit
- Can use with statements for scoped contexts
- Prevents SQLite "database is locked" errors
- Better testing support

---

### 3. STRUCT-001: Refactor Config Singleton to Support Dependency Injection

**Current Issue**: Module-level singleton prevents testing and configuration flexibility.

**Proposed Solution**: Remove module-level singleton, provide factory function.

#### Changes to `src/glorious_agents/config.py`

```python
"""Configuration management for glorious-agents.

This module provides centralized configuration with environment variable support.
All configuration values can be overridden via environment variables with the
GLORIOUS_ prefix or via .env file in project root.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def _find_project_root() -> Path:
    """Find the project root by looking for .git directory or .env file."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / ".env").exists():
            return parent
    return current


class Config:
    """Configuration settings for the glorious-agents framework."""

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """Initialize configuration from environment variables and .env file.
        
        Args:
            env_file: Optional path to .env file. If None, searches project root.
        """
        # Load .env file from project root if it exists
        if env_file is None:
            project_root = _find_project_root()
            env_file = project_root / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)

        # Unified database name (single database for all data)
        self.DB_NAME: str = os.getenv("GLORIOUS_DB_NAME", "glorious.db")

        # Legacy database names (for migration)
        self.DB_SHARED_NAME: str = os.getenv("GLORIOUS_DB_SHARED_NAME", "glorious_shared.db")
        self.DB_MASTER_NAME: str = os.getenv("GLORIOUS_DB_MASTER_NAME", "master.db")

        # Daemon settings
        self.DAEMON_HOST: str = os.getenv("GLORIOUS_DAEMON_HOST", "127.0.0.1")
        self.DAEMON_PORT: int = int(os.getenv("GLORIOUS_DAEMON_PORT", "8765"))
        self.DAEMON_API_KEY: str | None = os.getenv("GLORIOUS_DAEMON_API_KEY")

        # Skills directory
        self.SKILLS_DIR: Path = Path(os.getenv("GLORIOUS_SKILLS_DIR", "skills"))

        # Agent data directory - PROJECT-SPECIFIC by default
        # Uses .agent/ in project root, can be overridden via DATA_FOLDER
        data_folder = os.getenv("DATA_FOLDER")
        if data_folder:
            self.DATA_FOLDER = Path(data_folder)
        else:
            project_root = _find_project_root()
            self.DATA_FOLDER = project_root / ".agent"

    def get_db_path(self, db_name: str | None = None) -> Path:
        """Get the full path to a database file.

        Args:
            db_name: Optional database name. If None, uses the unified DB_NAME.
        """
        if db_name is None:
            db_name = self.DB_NAME
        return self.DATA_FOLDER / db_name

    def get_unified_db_path(self) -> Path:
        """Get the path to the unified database."""
        return self.get_db_path(self.DB_NAME)

    def get_shared_db_path(self) -> Path:
        """Get the path to the shared skills database (legacy)."""
        return self.get_db_path(self.DB_SHARED_NAME)

    def get_master_db_path(self) -> Path:
        """Get the path to the master registry database (legacy)."""
        return self.get_db_path(self.DB_MASTER_NAME)


# Default singleton for backward compatibility
# New code should use get_config() or create Config() instances
_default_config: Optional[Config] = None
_config_lock = threading.Lock()


def get_config() -> Config:
    """Get the default configuration instance (lazy-loaded singleton).
    
    For testing, use Config() directly to create isolated instances.
    """
    global _default_config
    if _default_config is None:
        with _config_lock:
            if _default_config is None:
                _default_config = Config()
    return _default_config


def reset_config() -> None:
    """Reset the default config (useful for testing)."""
    global _default_config
    with _config_lock:
        _default_config = None


# Backward compatibility: module-level 'config' attribute
# This allows existing code like `from glorious_agents.config import config` to work
# But encourages new code to use get_config() or dependency injection
config = get_config()
```

**Migration Path**:
1. Existing code continues to work with `from glorious_agents.config import config`
2. New code can use `get_config()` for lazy loading
3. Tests can use `Config()` directly for isolation
4. Eventually deprecate module-level `config`

---

### 4. DESIGN-001: Split db.py into Focused Modules

**Current Issue**: Single file with 258 lines handling multiple concerns.

**Proposed Solution**: Create a `db/` package with specialized modules.

#### New Structure

```
src/glorious_agents/core/db/
├── __init__.py          # Public API exports
├── connection.py        # Connection management
├── schema.py           # Schema initialization
├── optimization.py     # Performance optimization
├── batch.py            # Batch operations
└── migration.py        # Legacy migration (consolidate with existing)
```

#### `src/glorious_agents/core/db/__init__.py`

```python
"""Database management for unified SQLite database."""

from glorious_agents.core.db.batch import batch_execute
from glorious_agents.core.db.connection import (
    get_agent_db_path,
    get_connection,
    get_data_folder,
    get_master_db_path,
)
from glorious_agents.core.db.migration import migrate_legacy_databases
from glorious_agents.core.db.optimization import optimize_database
from glorious_agents.core.db.schema import init_master_db, init_skill_schema

__all__ = [
    "batch_execute",
    "get_agent_db_path",
    "get_connection",
    "get_data_folder",
    "get_master_db_path",
    "init_master_db",
    "init_skill_schema",
    "migrate_legacy_databases",
    "optimize_database",
]
```

#### `src/glorious_agents/core/db/connection.py`

```python
"""Database connection management."""

import sqlite3
from pathlib import Path

from glorious_agents.config import get_config


def get_data_folder() -> Path:
    """Get the data folder path from configuration."""
    config = get_config()
    data_folder = config.DATA_FOLDER
    data_folder.mkdir(parents=True, exist_ok=True)
    return data_folder


def get_agent_db_path(agent_code: str | None = None) -> Path:
    """
    Get the database path for the unified database.

    Args:
        agent_code: Optional agent code (deprecated, kept for compatibility).

    Returns:
        Path to the unified SQLite database.
    """
    config = get_config()
    data_folder = get_data_folder()
    return data_folder / config.DB_NAME


def get_connection(check_same_thread: bool = False) -> sqlite3.Connection:
    """
    Get a connection to the active agent's database with optimized settings.

    Args:
        check_same_thread: Whether to check if connection is used from same thread.

    Returns:
        SQLite connection with WAL mode and performance optimizations enabled.
    """
    db_path = get_agent_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=check_same_thread)

    # Performance optimizations
    conn.execute("PRAGMA journal_mode=WAL;")  # Better concurrency
    conn.execute("PRAGMA synchronous=NORMAL;")  # Balanced durability/performance
    conn.execute("PRAGMA cache_size=-64000;")  # 64MB cache (negative = KB)
    conn.execute("PRAGMA temp_store=MEMORY;")  # Store temp tables in memory
    conn.execute("PRAGMA mmap_size=268435456;")  # 256MB memory-mapped I/O
    conn.execute("PRAGMA page_size=4096;")  # Optimal page size for modern systems
    conn.execute("PRAGMA busy_timeout=5000;")  # Wait 5s on lock instead of failing

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON;")

    return conn


def get_master_db_path() -> Path:
    """Get the path to the unified database (master tables are now in main DB)."""
    return get_agent_db_path()
```

#### `src/glorious_agents/core/db/schema.py`

```python
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
```

**Other modules** (`batch.py`, `optimization.py`, `migration.py`) would follow similar patterns.

---

## Medium Priority Improvements

### 5. ENHANCE-004: Extract Duplicate Config Schema Normalization

**Current Issue**: Same logic repeated in 3 places in loader modules.

**Proposed Solution**: Create utility function.

#### New file: `src/glorious_agents/core/loader/utils.py`

```python
"""Utility functions for skill loading."""

from typing import Any


def normalize_config_schema(schema_data: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Normalize config schema by extracting properties from JSON Schema format.
    
    Args:
        schema_data: Raw schema data which may be in JSON Schema format
        
    Returns:
        Normalized schema dict with just the properties, or None if no schema
        
    Example:
        >>> schema = {"properties": {"key": {"type": "string"}}}
        >>> normalize_config_schema(schema)
        {"key": {"type": "string"}}
    """
    if not schema_data or not isinstance(schema_data, dict):
        return None
    
    # If it's a JSON Schema with "properties", extract them
    if "properties" in schema_data:
        return dict(schema_data["properties"])
    
    # Otherwise return as-is
    return dict(schema_data)
```

Then update all three locations to use this function instead of inline logic.

---

### 6. ERROR-001: Improve EventBus Error Handling

**Current Issue**: All exceptions swallowed with only logging.

**Proposed Solution**: Add configurable error handling and metrics.

#### Changes to `src/glorious_agents/core/context.py`

```python
from enum import Enum
from typing import Callable, Protocol


class ErrorHandlingMode(Enum):
    """Error handling modes for event bus."""
    SILENT = "silent"  # Log errors but continue (current behavior)
    FAIL_FAST = "fail_fast"  # Raise first error
    COLLECT = "collect"  # Collect all errors and provide them


class EventBus:
    """In-process publish-subscribe event bus with configurable error handling."""

    def __init__(self, error_mode: ErrorHandlingMode = ErrorHandlingMode.SILENT) -> None:
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._error_mode = error_mode
        self._last_errors: list[tuple[str, Exception]] = []

    def subscribe(self, topic: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Event topic name.
            callback: Function to call when event is published.
        """
        with self._lock:
            self._subscribers[topic].append(callback)

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        """
        Publish an event to a topic.

        Args:
            topic: Event topic name.
            data: Event data payload.
            
        Raises:
            Exception: If error_mode is FAIL_FAST and a handler raises
        """
        with self._lock:
            callbacks = self._subscribers.get(topic, [])
            self._last_errors.clear()

        # Execute callbacks outside lock to avoid deadlocks
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                # Log error
                logger.error(f"Error in event handler for {topic}: {e}", exc_info=True)
                
                # Handle based on mode
                if self._error_mode == ErrorHandlingMode.FAIL_FAST:
                    raise
                elif self._error_mode == ErrorHandlingMode.COLLECT:
                    self._last_errors.append((topic, e))
                # SILENT mode: just log (default behavior)
    
    def get_last_errors(self) -> list[tuple[str, Exception]]:
        """Get errors from last publish operation (if error_mode is COLLECT)."""
        return self._last_errors.copy()
    
    def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic."""
        with self._lock:
            return len(self._subscribers.get(topic, []))
    
    def get_all_topics(self) -> list[str]:
        """Get list of all topics with subscribers."""
        with self._lock:
            return list(self._subscribers.keys())
```

---

## Testing Recommendations

For each change:

1. **Unit tests**: Test individual functions in isolation
2. **Integration tests**: Test interaction between components
3. **Security tests**: Specifically test bypass attempts for SQL parsing
4. **Performance tests**: Ensure changes don't degrade performance
5. **Backward compatibility**: Verify existing code still works

## Implementation Priority

1. **Week 1**: SECURE-001 (SQL injection) - CRITICAL
2. **Week 2**: SEC-002 (Connection lifecycle) - HIGH
3. **Week 3**: STRUCT-001 (Config refactoring) - HIGH  
4. **Week 4**: DESIGN-001 (db.py split) - HIGH
5. **Week 5**: Medium priority items

## Conclusion

These changes address the most critical security and architectural issues while maintaining backward compatibility where possible. Each change improves testability, maintainability, and security of the codebase.

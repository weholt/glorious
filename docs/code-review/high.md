# High Priority Issues

---
id: "SEC-001"
title: "Singleton pattern with mutable global state in runtime.py"
description: "Global mutable _context variable with threading lock creates potential race conditions"
created: 2025-11-18
section: core/runtime
tags: [security, concurrency, singleton, design-pattern]
type: structural-violation
priority: high
status: proposed
---

The `runtime.py` module uses a global mutable singleton pattern with `_context` and `_lock`. While it implements double-checked locking, this pattern can be problematic:
- Makes testing difficult (requires explicit reset)
- Creates implicit dependencies between modules
- Can lead to subtle concurrency issues if context is modified after initialization

**Recommended fix**: Consider using dependency injection or a context manager pattern instead of a global singleton. If singleton is necessary, consider making it immutable after initialization.

---
id: "SEC-002"
title: "Database connection remains open indefinitely in singleton context"
description: "The shared SQLite connection in SkillContext is never properly closed except in reset_ctx()"
created: 2025-11-18
section: core/runtime, core/context
tags: [resource-leak, database, lifecycle]
type: bug
priority: high
status: proposed
---

The database connection created in `get_ctx()` is stored in the singleton context and remains open for the entire application lifetime. This can cause:
- Resource leaks if the application doesn't properly shut down
- Lock issues in SQLite if multiple processes try to access
- WAL file growth without proper cleanup

**Recommended fix**: Implement a proper context manager for the SkillContext that ensures connection cleanup. Add lifecycle management with explicit startup/shutdown hooks.

**File path**: `src/glorious_agents/core/runtime.py:29`, `src/glorious_agents/core/context.py:66`

---
id: "PERF-001"
title: "O(n) list append in EventBus can cause performance degradation"
description: "Event subscribers are stored in a list, making subscribe operations O(n) for duplicate checks"
created: 2025-11-18
section: core/context
tags: [performance, data-structure]
type: performance
priority: high
status: proposed
---

The EventBus stores subscribers in a `list` which is fine for small numbers, but could become a bottleneck with many subscribers:
- `subscribe()` appends to list (currently O(1) but no duplicate check)
- If duplicate checking was needed, it would be O(n)
- Memory overhead increases linearly

**Recommended fix**: Consider whether duplicate subscriptions should be prevented. If needed, track subscriptions per callback in a dict/set structure.

**File path**: `src/glorious_agents/core/context.py:19-31`

---
id: "STRUCT-001"
title: "Config singleton pattern violates dependency injection principle"
description: "Global config object in config.py makes testing and configuration management difficult"
created: 2025-11-18
section: config
tags: [architecture, testability, dependency-injection]
type: structural-violation
priority: high
status: proposed
---

The module exports a singleton `config = Config()` at module level. This pattern:
- Makes unit testing difficult (requires environment variable manipulation)
- Creates hidden dependencies across modules
- Prevents using different configurations in the same process
- Makes it impossible to test configuration loading logic in isolation

**Recommended fix**: 
1. Remove the module-level singleton
2. Provide a factory function `get_config()` or `create_config()`
3. Pass config as a parameter where needed (dependency injection)
4. For convenience, can still provide a lazy-loaded default via function

**File path**: `src/glorious_agents/config.py:81`

---
id: "ERROR-001"
title: "Broad exception catching without re-raise in EventBus"
description: "EventBus catches all exceptions in callbacks but only logs them"
created: 2025-11-18
section: core/context
tags: [error-handling, debugging]
type: code-smell
priority: high
status: proposed
---

The `EventBus.publish()` method catches all exceptions from callbacks but only logs them:
```python
except Exception as e:
    logger.error(f"Error in event handler for {topic}: {e}", exc_info=True)
```

While this prevents one bad handler from breaking others, it can hide serious bugs and make debugging difficult.

**Recommended fix**: 
- Add a configuration option to control error handling behavior (fail-fast vs. continue)
- Consider accumulating errors and providing a way to query them
- Add metrics/telemetry for failed event handlers
- Document the error handling behavior clearly

**File path**: `src/glorious_agents/core/context.py:45-50`

---
id: "SECURE-001"
title: "SQL injection vulnerability in RestrictedConnection.execute"
description: "SQL command detection uses string prefix matching which can be bypassed"
created: 2025-11-18
section: core/isolation
tags: [security, sql-injection, vulnerability]
type: security
priority: high
status: proposed
---

The `RestrictedConnection.execute()` method checks for write operations using:
```python
sql_upper = sql.strip().upper()
is_write = any(sql_upper.startswith(op) for op in write_operations)
```

This can be bypassed with:
- Comments: `/* comment */ INSERT ...`
- Whitespace: `\n\t INSERT ...`
- Common Table Expressions: `WITH ... INSERT ...`
- Nested queries

**Recommended fix**: 
1. Use a proper SQL parser (e.g., sqlparse) to detect operation types
2. Add comprehensive tests for bypass attempts
3. Consider using SQLite's read-only connection flag instead
4. Document security implications clearly

**File path**: `src/glorious_agents/core/isolation.py:69-84`

---
id: "DESIGN-001"
title: "Mixed concerns in db.py module"
description: "Database connection, schema management, optimization, and migration all in one module"
created: 2025-11-18
section: core/db
tags: [separation-of-concerns, modularity]
type: structural-violation
priority: high
status: proposed
---

The `db.py` module has 258 lines and handles multiple unrelated concerns:
- Connection management
- Schema initialization
- Legacy database migration
- Batch operations
- Database optimization

This violates Single Responsibility Principle and makes the module hard to test and maintain.

**Recommended fix**: Split into separate modules:
- `db/connection.py` - Connection management
- `db/schema.py` - Schema initialization
- `db/optimization.py` - Performance optimization
- `db/migration.py` - Legacy migration (note: db_migration.py already exists, consider consolidation)
- `db/batch.py` - Batch operations

**File path**: `src/glorious_agents/core/db.py`

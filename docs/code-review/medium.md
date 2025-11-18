# Medium Priority Issues

---
id: "ENHANCE-001"
title: "Missing type hints for Protocol implementations"
description: "SkillApp Protocol uses Any for parameters and return types"
created: 2025-11-18
section: core/context
tags: [type-safety, protocol, typing]
type: enhancement
priority: medium
status: proposed
---

The `SkillApp` Protocol is defined with `Any` for all parameters and return:
```python
class SkillApp(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
```

This provides no type safety benefits and defeats the purpose of using Protocol.

**Recommended fix**: If possible, define more specific signatures or use TypeVar to maintain type information. Document why Any is used if it's intentional.

**File path**: `src/glorious_agents/core/context.py:53-58`

---
id: "ENHANCE-002"
title: "Inconsistent error handling across loader modules"
description: "Some modules catch and log errors, others let them propagate"
created: 2025-11-18
section: core/loader
tags: [error-handling, consistency]
type: enhancement
priority: medium
status: proposed
---

Error handling is inconsistent across loader modules:
- `discovery.py`: Catches specific exceptions and logs them
- `initialization.py`: Some functions catch and suppress, others propagate
- `__init__.py`: Accumulates failed skills in a list

This makes it hard to understand what happens when a skill fails to load.

**Recommended fix**: Establish a consistent error handling policy:
1. Define which errors are recoverable vs. fatal
2. Use a custom exception hierarchy for skill loading
3. Document error handling behavior in module docstrings
4. Consider returning Result types instead of raising exceptions

**File path**: `src/glorious_agents/core/loader/`

---
id: "ENHANCE-003"
title: "Magic strings for permission types"
description: "Permission enum values are strings, but used inconsistently"
created: 2025-11-18
section: core/isolation
tags: [enum, type-safety]
type: enhancement
priority: medium
status: proposed
---

The Permission enum uses string values but these are never actually used. The enum members themselves are used for comparison. This is redundant.

**Recommended fix**: Either remove the string values (use auto()) or actually use them for serialization/deserialization if needed.

**File path**: `src/glorious_agents/core/isolation.py:12-23`

---
id: "DOC-001"
title: "Incomplete docstrings for public functions"
description: "Many public functions lack comprehensive docstrings"
created: 2025-11-18
section: multiple
tags: [documentation, maintainability]
type: documentation
priority: medium
status: proposed
---

Several public functions have incomplete or missing docstrings:
- `_find_project_root()` in config.py has no docstring for the return type
- `get_connection()` doesn't document the check_same_thread parameter's implications
- `batch_execute()` has a good example but could document transaction behavior better

**Recommended fix**: Add complete Google-style docstrings for all public functions including:
- Full parameter descriptions
- Return type descriptions
- Exception documentation
- Usage examples for complex functions

**File path**: Multiple files

---
id: "TEST-001"
title: "Low test coverage for loader initialization module"
description: "initialization.py has only 61% coverage according to test results"
created: 2025-11-18
section: core/loader/initialization
tags: [testing, coverage]
type: testing
priority: medium
status: proposed
---

The test results show only 61% coverage for `initialization.py`:
- Lines 44-70, 80-88, 96 are not covered
- This includes error handling paths and edge cases

**Recommended fix**: Add tests for:
1. Skills without schema files
2. Local vs. entrypoint skill loading
3. Skills with init() functions that fail
4. Edge cases in path manipulation

**File path**: `src/glorious_agents/core/loader/initialization.py`

---
id: "PERF-002"
title: "Repeated path.exists() checks in discovery"
description: "Schema file existence checked multiple times unnecessarily"
created: 2025-11-18
section: core/loader/discovery
tags: [performance, optimization]
type: performance
priority: medium
status: proposed
---

The discovery module checks `manifest_file.exists()` and then reads it, but doesn't cache the result. Similarly for schema files.

**Recommended fix**: Use try/except pattern instead of check-then-use:
```python
try:
    manifest_data = json.loads(manifest_file.read_text())
except FileNotFoundError:
    continue
except json.JSONDecodeError:
    logger.error(...)
```

This is more Pythonic (EAFP) and avoids TOCTOU race conditions.

**File path**: `src/glorious_agents/core/loader/discovery.py:32-34`

---
id: "ENHANCE-004"
title: "Duplicate code for config_schema normalization"
description: "Same config schema extraction logic repeated in multiple places"
created: 2025-11-18
section: core/loader
tags: [duplication, dry]
type: duplication
priority: medium
status: proposed
---

The config schema normalization logic (extracting 'properties' from JSON Schema) is duplicated in at least 3 places:
1. `discovery.py:57-66` (discover_local_skills)
2. `discovery.py:154-162` (discover_entrypoint_skills)
3. `__init__.py:71-78` (load_all_skills)

**Recommended fix**: Extract to a shared utility function:
```python
def normalize_config_schema(schema_data: dict | None) -> dict | None:
    if not schema_data or not isinstance(schema_data, dict):
        return None
    if "properties" in schema_data:
        return dict(schema_data["properties"])
    return dict(schema_data)
```

**File path**: `src/glorious_agents/core/loader/`

---
id: "STRUCT-002"
title: "SkillContext has too many responsibilities"
description: "SkillContext manages DB, events, skills, cache, and config"
created: 2025-11-18
section: core/context
tags: [srp, refactoring]
type: structural-violation
priority: medium
status: proposed
---

The SkillContext class violates Single Responsibility Principle by handling:
- Database connection
- Event bus management
- Skill registration
- Cache operations
- Configuration loading

This makes it hard to test and maintain.

**Recommended fix**: Consider breaking into smaller, focused components:
- DatabaseContext
- EventBusContext
- SkillRegistry (already exists separately)
- CacheContext
- ConfigContext

Then compose them into a facade if needed.

**File path**: `src/glorious_agents/core/context.py:61-173`

---
id: "ERROR-002"
title: "Silent failures in config loading"
description: "_load_skill_config catches all exceptions and sets empty dict"
created: 2025-11-18
section: core/context
tags: [error-handling, silent-failure]
type: code-smell
priority: medium
status: proposed
---

The `_load_skill_config` method catches all exceptions and silently sets an empty dict:
```python
except Exception as e:
    logger.error(f"Error loading config for {skill_name}: {e}")
    setattr(self, config_key, {})
```

This means a malformed TOML file is indistinguishable from a missing file.

**Recommended fix**: 
- Distinguish between missing file (not an error) and parsing errors (should fail fast)
- Raise a custom ConfigurationError for parsing issues
- Let the caller decide how to handle missing config

**File path**: `src/glorious_agents/core/context.py:117-137`

---
id: "DESIGN-002"
title: "RestrictedConnection doesn't restrict close() but should restrict other operations"
description: "Permission model is incomplete - missing restrictions for DDL operations"
created: 2025-11-18
section: core/isolation
tags: [security, permissions, completeness]
type: enhancement
priority: medium
status: proposed
---

The RestrictedConnection blocks close() but doesn't differentiate between:
- DDL operations (CREATE, DROP, ALTER) 
- DML operations (INSERT, UPDATE, DELETE)
- DQL operations (SELECT)

Currently it only checks DB_WRITE for all modifications, but DDL should perhaps require a separate permission.

**Recommended fix**: Add Permission.DB_DDL and check for it on schema-modifying operations.

**File path**: `src/glorious_agents/core/isolation.py:62-103`

---
id: "ENHANCE-005"
title: "No metrics or observability in event system"
description: "EventBus has no way to monitor subscriber count, event frequency, or failures"
created: 2025-11-18
section: core/context
tags: [observability, metrics]
type: enhancement
priority: medium
status: proposed
---

The EventBus doesn't provide any observability:
- Can't query how many subscribers exist for a topic
- No metrics on publish frequency or payload sizes
- Failed handler exceptions are only logged, not counted
- No way to monitor event system health

**Recommended fix**: Add methods like:
- `get_subscriber_count(topic)` 
- `get_all_topics()`
- Track metrics (if telemetry skill is available)
- Emit health check events

**File path**: `src/glorious_agents/core/context.py:15-51`

---
id: "PERF-003"
title: "TTLCache prune_expired() requires O(n) scan"
description: "No automatic cleanup of expired entries"
created: 2025-11-18
section: core/cache
tags: [performance, memory-leak]
type: performance
priority: medium
status: proposed
---

The TTLCache only removes expired entries when:
1. They are accessed via get()
2. prune_expired() is called manually

If keys are set but never accessed again, they remain in memory until manual pruning or eviction by LRU.

**Recommended fix**: 
- Add background thread for periodic automatic pruning
- Or use a more sophisticated expiration strategy (e.g., time-based eviction queue)
- Document that users should call prune_expired() periodically

**File path**: `src/glorious_agents/core/cache.py:82-98`

---
id: "ENHANCE-006"
title: "ValidationException error formatting loses type information"
description: "Error dict format discards original Pydantic error structure"
created: 2025-11-18
section: core/validation
tags: [error-handling, type-safety]
type: enhancement
priority: medium
status: proposed
---

The ValidationException converts all errors to dicts with just 'loc' and 'msg', losing:
- Error type information (missing, type_error, value_error, etc.)
- Contextual information (input data, constraints)
- Error codes that could be used programmatically

**Recommended fix**: Preserve the full error structure or at minimum add an 'error_type' field.

**File path**: `src/glorious_agents/core/validation.py:29-40`

---
id: "DESIGN-003"
title: "CLI initialization logic split between cli.py and main()"
description: "init_app() and main() both handle skill loading with different logic"
created: 2025-11-18
section: cli
tags: [code-organization, duplication]
type: structural-violation
priority: medium
status: proposed
---

Skill initialization happens in two places:
1. `init_app()` - loads skills and mounts them
2. `main()` - checks if initialization should be skipped

This split logic makes it hard to understand the initialization flow.

**Recommended fix**: Consolidate initialization logic in one place, perhaps a proper application class with lifecycle methods.

**File path**: `src/glorious_agents/cli.py:25-52, 410-448`

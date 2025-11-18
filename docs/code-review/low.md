# Low Priority Issues

---
id: "STYLE-001"
title: "Inconsistent quote style in string literals"
description: "Mix of single and double quotes throughout codebase"
created: 2025-11-18
section: multiple
tags: [style, consistency]
type: style
priority: low
status: proposed
---

While not a functional issue, mixing quote styles reduces code consistency. Python style guides typically recommend picking one style and sticking with it.

**Recommended fix**: Configure ruff/black to enforce consistent quote style (either single or double).

**File path**: Multiple files

---
id: "DOC-002"
title: "Generic 'TODO' and 'FIXME' comments should be tracked"
description: "Check if there are any TODO/FIXME comments that should be converted to issues"
created: 2025-11-18
section: multiple
tags: [documentation, technical-debt]
type: documentation
priority: low
status: proposed
---

TODO and FIXME comments are easy to forget. Better to track them in the issue tracker.

**Recommended fix**: Search for TODO/FIXME comments and either fix them or create tracked issues.

**File path**: Multiple files

---
id: "ENHANCE-007"
title: "Verbose logging could use structured logging"
description: "Logger calls use string formatting instead of structured data"
created: 2025-11-18
section: multiple
tags: [logging, observability]
type: enhancement
priority: low
status: proposed
---

Current logging uses string formatting:
```python
logger.error(f"Error loading skill '{skill_name}': {error_msg}", exc_info=True)
```

Structured logging with extra fields would be more useful for log aggregation:
```python
logger.error("Error loading skill", extra={"skill_name": skill_name, "error": error_msg}, exc_info=True)
```

**Recommended fix**: Consider using structlog or adding extra fields to standard logging calls.

**File path**: Multiple files

---
id: "PERF-004"
title: "Repeated Path object creation"
description: "Some functions create Path objects multiple times for the same path"
created: 2025-11-18
section: config, multiple
tags: [performance, optimization]
type: performance
priority: low
status: proposed
---

Minor optimization: Cache Path objects instead of recreating them:
```python
# Current
env_file = project_root / ".env"
if env_file.exists():

# Could be:
env_file_path = project_root / ".env"
if env_file_path.exists():
    load_dotenv(env_file_path)
```

Not a major issue but shows attention to detail.

**File path**: Various

---
id: "ENHANCE-008"
title: "RestrictedConnection could support context manager protocol"
description: "Would enable with-statement usage for cleaner code"
created: 2025-11-18
section: core/isolation
tags: [pythonic, usability]
type: enhancement
priority: low
status: proposed
---

While RestrictedConnection blocks close(), it could still implement `__enter__` and `__exit__` for consistency with normal connections (even if exit is a no-op).

**Recommended fix**: Add context manager methods for better API consistency.

**File path**: `src/glorious_agents/core/isolation.py:62-112`

---
id: "DESIGN-004"
title: "Global permission registry could be configurable"
description: "Hardcoded skill permissions make customization difficult"
created: 2025-11-18
section: core/isolation
tags: [configuration, extensibility]
type: enhancement
priority: low
status: proposed
---

The permission registry hardcodes which skills get write access in `_setup_default_permissions()`. This makes it hard to:
- Add new skills without modifying code
- Customize permissions for different deployments
- Test with different permission configurations

**Recommended fix**: Load permissions from a configuration file (e.g., `permissions.toml`).

**File path**: `src/glorious_agents/core/isolation.py:199-225`

---
id: "ENHANCE-009"
title: "CLI info command could show more statistics"
description: "Additional metrics would be helpful for debugging"
created: 2025-11-18
section: cli
tags: [usability, observability]
type: enhancement
priority: low
status: proposed
---

The `agent info` command could show:
- Cache statistics (if applicable)
- Active event subscriptions
- Loaded skills count
- Recent errors or warnings
- Database WAL size

**Recommended fix**: Expand the info command with additional diagnostics.

**File path**: `src/glorious_agents/cli.py:238-332`

---
id: "STYLE-002"
title: "Some functions are longer than recommended 15 lines"
description: "Functions exceeding recommended length should be considered for refactoring"
created: 2025-11-18
section: multiple
tags: [readability, refactoring]
type: style
priority: low
status: proposed
---

According to the code analysis guidelines, functions longer than 15 lines should be considered for refactoring. Several functions exceed this:
- `cli.py:_generate_skill_documentation()` - 59 lines
- `cli.py:init()` - 13 lines (close but ok)
- `cli.py:search()` - 72 lines
- `db.py:init_skill_schema()` - 58 lines
- `db.py:migrate_legacy_databases()` - 41 lines

While not always necessary to split, consider if these could be more readable when broken into smaller functions.

**Recommended fix**: Review long functions and extract logical sub-operations.

**File path**: Multiple files

---
id: "TEST-002"
title: "Missing tests for Permission system edge cases"
description: "Permission enforcement should have comprehensive tests"
created: 2025-11-18
section: tests
tags: [testing, security]
type: testing
priority: low
status: proposed
---

The permission/isolation system should have tests for:
- Attempting operations without required permissions
- Permission grant/revoke operations
- RestrictedConnection behavior
- Edge cases in SQL operation detection

**Recommended fix**: Add comprehensive security-focused tests for the isolation module.

**File path**: `tests/` (new tests needed)

---
id: "DOC-003"
title: "README could include architecture diagram"
description: "Visual representation of component relationships would aid understanding"
created: 2025-11-18
section: documentation
tags: [documentation, onboarding]
type: documentation
priority: low
status: proposed
---

The README mentions architecture but doesn't include a diagram. A visual showing:
- Core components (Context, EventBus, Registry, DB)
- Skill loading flow
- Runtime structure

Would help new contributors understand the system faster.

**Recommended fix**: Add mermaid diagrams to README or docs.

**File path**: `README.md`, `docs/`

---
id: "ENHANCE-010"
title: "Database optimization function doesn't run VACUUM"
description: "VACUUM is commented out but should be available as an option"
created: 2025-11-18
section: core/db
tags: [maintenance, configuration]
type: enhancement
priority: low
status: proposed
---

The `optimize_database()` function has VACUUM commented out with a note about it being expensive. This should be available as an explicit operation.

**Recommended fix**: 
- Add a separate `vacuum_database()` function
- Or add a `full_optimize=False` parameter
- Document when users should run full optimization

**File path**: `src/glorious_agents/core/db.py:222-257`

---
id: "STYLE-003"
title: "Type alias F could be more descriptive"
description: "Single letter type variables reduce code readability"
created: 2025-11-18
section: core/validation
tags: [naming, readability]
type: style
priority: low
status: proposed
---

Using `F` as a TypeVar name is not as clear as it could be:
```python
F = TypeVar("F", bound=Callable[..., Any])
```

**Recommended fix**: Use more descriptive names like `FuncType` or `CallableT`.

**File path**: `src/glorious_agents/core/validation.py:20`

---
id: "PERF-005"
title: "Validation decorator uses get_type_hints on every call"
description: "Type hints could be cached after first invocation"
created: 2025-11-18
section: core/validation
tags: [performance, caching]
type: performance
priority: low
status: proposed
---

The `validate_input` decorator calls `get_type_hints(func)` on every function invocation. This could be cached.

**Recommended fix**: 
```python
@functools.wraps(func)
def wrapper(*args: Any, **kwargs: Any) -> Any:
    if not hasattr(wrapper, '_type_hints'):
        wrapper._type_hints = get_type_hints(func)
    type_hints = wrapper._type_hints
    # ... rest of logic
```

**File path**: `src/glorious_agents/core/validation.py:130-140`

---
id: "DESIGN-005"
title: "Search function in CLI duplicates skill module import logic"
description: "Module loading for search could be centralized"
created: 2025-11-18
section: cli
tags: [duplication, maintainability]
type: duplication
priority: low
status: proposed
---

The search command manually imports modules to check for search functions. This logic could be abstracted.

**Recommended fix**: Add a method to the registry or loader that returns callable skill methods by name.

**File path**: `src/glorious_agents/cli.py:335-407`

---
id: "ENHANCE-011"
title: "CLI could support plugins for custom commands"
description: "Allow extending the CLI without modifying core code"
created: 2025-11-18
section: cli
tags: [extensibility, plugin-system]
type: enhancement
priority: low
status: proposed
---

Currently, adding management commands requires modifying `cli.py`. A plugin system would allow:
- Custom commands in separate packages
- Third-party extensions
- Easier testing of custom commands

**Recommended fix**: Design a plugin entry point system similar to skills.

**File path**: `src/glorious_agents/cli.py`

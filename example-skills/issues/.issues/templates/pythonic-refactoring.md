# Template: Pythonic Code Refactoring

**Description**: Refactor codebase to follow Pythonic idioms, modern Python features, and community best practices for clean, expressive code

## Overview

Transform existing Python code into idiomatic, clean, expressive Pythonic code following PEP 8, PEP 20 (Zen of Python), and modern Python features. This analysis focuses on making code more readable, maintainable, and aligned with Python community standards.

## Tasks

### 1. Idiom and Expression Analysis

**Priority**: high
**Estimated Effort**: large

**Description**: Identify non-Pythonic patterns and replace with idiomatic constructs

**Subtasks**:

- [ ] Find verbose loops that should be comprehensions
- [ ] Identify manual iteration instead of built-in functions
- [ ] Detect LBYL (Look Before You Leap) instead of EAFP
- [ ] Find verbose conditionals that can use truthiness
- [ ] Identify manual string building vs. f-strings
- [ ] Detect missing context managers for resources
- [ ] Find manual implementations of standard library features
- [ ] Identify opportunities for itertools/functools usage
- [ ] Document all non-Pythonic patterns

**Acceptance Criteria**:

- Complete inventory of non-idiomatic code
- Comprehension opportunities identified
- EAFP refactoring candidates documented
- Standard library usage improvements listed
- Pythonic alternatives provided for each finding

**Issue Template**:

```markdown
---
id: "PYTH-XXX"
title: "Non-Pythonic pattern: [description]"
description: "Code can be more idiomatic"
created: YYYY-MM-DD
section: code-style
tags: [pythonic, idiom, refactor]
type: enhancement
priority: medium
status: proposed
---

**Location**: `path/to/file.py:line_range`

**Current Pattern**:
```python
# Non-Pythonic code
```

**Pythonic Alternative**:
```python
# Idiomatic Python
```

**Benefits**: Improved readability, shorter code, better performance.

**References**: [PEP or documentation link]
```

---

### 2. Type Annotations Audit

**Priority**: high
**Estimated Effort**: medium

**Description**: Add or improve type hints throughout codebase

**Subtasks**:

- [ ] Identify functions without type annotations
- [ ] Check for incomplete type hints (missing return types)
- [ ] Find overly broad types (Any usage)
- [ ] Identify missing generic type parameters
- [ ] Check for proper Optional usage
- [ ] Detect missing Protocol definitions
- [ ] Review TypeVar usage
- [ ] Add type hints to public APIs first
- [ ] Document all type annotation gaps

**Acceptance Criteria**:

- Type coverage percentage calculated
- All public functions have type hints
- Generic types properly parameterized
- Protocol definitions created where needed
- MyPy runs without errors

**Issue Template**:

```markdown
---
id: "TYPE-XXX"
title: "Missing type annotations: [module/function]"
description: "Add type hints for better clarity"
created: YYYY-MM-DD
section: type-hints
tags: [typing, annotations, mypy]
type: enhancement
priority: high
status: proposed
---

**Location**: `path/to/file.py:function_name`

**Current Signature**:
```python
def function(param1, param2):
    ...
```

**With Type Hints**:
```python
def function(param1: Type1, param2: Type2) -> ReturnType:
    ...
```

**Benefits**: Better IDE support, catches bugs early, self-documenting.
```

---

### 3. Data Structure Modernization

**Priority**: high
**Estimated Effort**: medium

**Description**: Replace manual data structures with modern Python alternatives

**Subtasks**:

- [ ] Find classes that should be dataclasses
- [ ] Identify tuples that should be NamedTuple
- [ ] Detect dicts that should be typed TypedDict
- [ ] Find manual property implementations
- [ ] Identify classes with only `__init__` that should be dataclass
- [ ] Check for frozen/immutable data needs
- [ ] Find field validation that should use Pydantic
- [ ] Document all data structure improvements

**Acceptance Criteria**:

- Dataclass candidates identified
- NamedTuple opportunities documented
- TypedDict usage verified
- Pydantic integration assessed
- Immutability patterns applied

**Issue Template**:

```markdown
---
id: "DATA-XXX"
title: "Convert to dataclass: [ClassName]"
description: "Use modern data structure"
created: YYYY-MM-DD
section: data-structures
tags: [dataclass, modernization, clean-code]
type: enhancement
priority: medium
status: proposed
---

**Location**: `path/to/file.py:ClassName`

**Current Implementation**:
```python
class OldStyle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

**Dataclass Version**:
```python
from dataclasses import dataclass

@dataclass
class ModernStyle:
    x: int
    y: str
```

**Benefits**: Less boilerplate, auto-generated methods, type hints enforced.
```

---

### 4. Resource Management and Context Managers

**Priority**: high
**Estimated Effort**: medium

**Description**: Ensure proper resource handling with context managers

**Subtasks**:

- [ ] Find file operations without context managers
- [ ] Identify manual resource cleanup (try/finally)
- [ ] Detect database connections not using context managers
- [ ] Find lock usage without `with` statements
- [ ] Identify custom classes that should support context protocol
- [ ] Check for missing `__enter__` and `__exit__` implementations
- [ ] Find nested context managers that can use contextlib
- [ ] Document all resource management issues

**Acceptance Criteria**:

- All file operations use `with` statements
- Manual try/finally blocks replaced
- Custom context managers identified
- contextlib utilities applied where appropriate
- Resource leaks eliminated

**Issue Template**:

```markdown
---
id: "CTX-XXX"
title: "Add context manager: [description]"
description: "Improve resource management"
created: YYYY-MM-DD
section: resource-management
tags: [context-manager, resources, with-statement]
type: enhancement
priority: high
status: proposed
---

**Location**: `path/to/file.py:function_name`

**Current Pattern**:
```python
f = open("file.txt")
try:
    data = f.read()
finally:
    f.close()
```

**With Context Manager**:
```python
with open("file.txt") as f:
    data = f.read()
```

**Benefits**: Automatic cleanup, exception-safe, cleaner code.
```

---

### 5. Standard Library Utilization

**Priority**: medium
**Estimated Effort**: medium

**Description**: Replace custom implementations with standard library features

**Subtasks**:

- [ ] Find manual implementations of itertools functions
- [ ] Identify custom sorting/filtering vs. built-ins
- [ ] Detect custom date/time handling vs. datetime/dateutil
- [ ] Find manual path operations vs. pathlib
- [ ] Identify custom collection types vs. collections module
- [ ] Check for manual functional programming vs. functools
- [ ] Find custom parsing vs. standard library parsers
- [ ] Document all standard library opportunities

**Acceptance Criteria**:

- Custom implementations documented
- Standard library alternatives identified
- Performance comparison for critical paths
- Migration plan for each replacement
- Dependencies reduced where possible

**Issue Template**:

```markdown
---
id: "STDLIB-XXX"
title: "Use stdlib: [feature]"
description: "Replace custom code with standard library"
created: YYYY-MM-DD
section: standard-library
tags: [stdlib, simplification, best-practice]
type: enhancement
priority: medium
status: proposed
---

**Location**: `path/to/file.py:function_name`

**Custom Implementation**: [Brief description]

**Standard Library Alternative**: `module.function`

**Benefits**: Maintained by core Python, well-tested, performance-optimized.

**Migration Notes**: [Any compatibility considerations]
```

---

### 6. Function and Class Organization

**Priority**: medium
**Estimated Effort**: medium

**Description**: Improve function/class structure following Python best practices

**Subtasks**:

- [ ] Identify classes that should be simple functions
- [ ] Find static methods that should be module functions
- [ ] Detect unnecessary class inheritance
- [ ] Find missing `@property` decorators
- [ ] Identify missing `@classmethod` or `@staticmethod`
- [ ] Check for proper method organization (dunder, public, private)
- [ ] Find long parameter lists that need refactoring
- [ ] Document all organizational improvements

**Acceptance Criteria**:

- Function-vs-class decisions documented
- Decorator usage optimized
- Method organization standardized
- Parameter lists simplified
- Code organization improved

**Issue Template**:

```markdown
---
id: "ORG-XXX"
title: "Organizational improvement: [description]"
description: "Better structure for [component]"
created: YYYY-MM-DD
section: organization
tags: [structure, functions, classes]
type: enhancement
priority: medium
status: proposed
---

**Location**: `path/to/file.py:name`

**Issue**: [Class should be function | Static method misuse | etc.]

**Current Structure**: [Brief description]

**Recommended Structure**: [Better approach]

**Rationale**: Python prefers simplicity; classes when needed for state, functions otherwise.
```

---

### 7. Error Handling Pythonic Patterns

**Priority**: high
**Estimated Effort**: small

**Description**: Refactor error handling to use EAFP and Pythonic patterns

**Subtasks**:

- [ ] Replace LBYL with EAFP where appropriate
- [ ] Find bare except clauses
- [ ] Identify missing exception context (`from`)
- [ ] Check for proper exception inheritance
- [ ] Find exception swallowing (pass in except)
- [ ] Detect missing logging in exception handlers
- [ ] Review custom exception design
- [ ] Document all error handling improvements

**Acceptance Criteria**:

- EAFP pattern applied consistently
- Exception handling improved
- Custom exceptions properly designed
- Logging added to exception paths
- No silent failures remain

**Issue Template**:

```markdown
---
id: "ERR-XXX"
title: "Error handling improvement: [description]"
description: "Make exception handling more Pythonic"
created: YYYY-MM-DD
section: error-handling
tags: [exceptions, eafp, error-handling]
type: enhancement
priority: high
status: proposed
---

**Location**: `path/to/file.py:line_range`

**Current Pattern** (LBYL):
```python
if os.path.exists(file):
    with open(file) as f:
        ...
```

**Pythonic Pattern** (EAFP):
```python
try:
    with open(file) as f:
        ...
except FileNotFoundError:
    # Handle missing file
```

**Benefits**: Cleaner code, better performance, handles race conditions.
```

---

### 8. Import and Module Organization

**Priority**: medium
**Estimated Effort**: small

**Description**: Organize imports and modules following Pythonic conventions

**Subtasks**:

- [ ] Sort imports using isort or Ruff
- [ ] Group imports (stdlib, third-party, local)
- [ ] Find relative imports that should be absolute
- [ ] Identify circular import issues
- [ ] Check for star imports (`from x import *`)
- [ ] Find imports inside functions (should be at top)
- [ ] Review `__init__.py` exports
- [ ] Document import organization improvements

**Acceptance Criteria**:

- All imports sorted and grouped
- Relative imports minimized
- Circular imports resolved
- Star imports eliminated
- Function-level imports moved to top

**Issue Template**:

```markdown
---
id: "IMP-XXX"
title: "Import organization: [file/module]"
description: "Improve import structure"
created: YYYY-MM-DD
section: imports
tags: [imports, organization, pep8]
type: enhancement
priority: low
status: proposed
---

**Location**: `path/to/file.py`

**Issues**: [Unsorted | Star imports | Inline imports | etc.]

**Current State**: [Brief description]

**Corrected Imports**:
```python
# Standard library
import os
from pathlib import Path

# Third-party
import requests

# Local
from myapp import utils
```

**Tool**: Run `ruff check --select I` or `isort` to fix.
```

---

## Issue Management for Refactoring

### Progressive Refactoring Strategy

1. **Create Refactoring Epic**:
   ```bash
   uv run issues create "Pythonic Code Refactoring 2025" --type epic --priority high
   ```

2. **Phase 1 - High Impact**: Type hints and resource management
   ```bash
   uv run issues create "Add type hints to public API" --deps subtask-of:EPIC-ID
   uv run issues create "Fix resource management" --deps subtask-of:EPIC-ID
   ```

3. **Phase 2 - Modernization**: Dataclasses and standard library
   ```bash
   uv run issues create "Convert to dataclasses" --deps subtask-of:EPIC-ID
   uv run issues create "Use stdlib alternatives" --deps subtask-of:EPIC-ID
   ```

4. **Phase 3 - Polish**: Imports and organization
   ```bash
   uv run issues create "Organize imports" --deps subtask-of:EPIC-ID
   ```

### Refactoring Workflow

1. **Analysis Phase**: Run through all tasks, document findings
2. **Prioritization**: Group by impact and risk
3. **Batch Similar Changes**: Group related refactorings
4. **Test Coverage**: Ensure tests exist before refactoring
5. **Incremental Changes**: Small PRs, one pattern at a time
6. **Validation**: Run tests after each change
7. **Documentation**: Update docs to reflect new patterns

### Testing During Refactoring

```bash
# Before each refactoring
uv run pytest tests/ -v

# After refactoring
uv run pytest tests/ -v
uv run mypy src/
uv run ruff check src/

# Ensure no regressions
```

---

## Pythonic Principles Reference

### PEP 20 - Zen of Python

```
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
```

Apply these when evaluating code quality.

### Common Pythonic Patterns

**Comprehensions**:
```python
# Instead of
result = []
for item in items:
    if condition(item):
        result.append(transform(item))

# Use
result = [transform(item) for item in items if condition(item)]
```

**EAFP**:
```python
# Instead of (LBYL)
if key in dictionary:
    value = dictionary[key]

# Use (EAFP)
try:
    value = dictionary[key]
except KeyError:
    # Handle missing key
```

**Context Managers**:
```python
# Instead of
resource = acquire_resource()
try:
    use_resource(resource)
finally:
    release_resource(resource)

# Use
with acquire_resource() as resource:
    use_resource(resource)
```

---

## Automated Refactoring Tools

```bash
# Auto-format
uv run black src/

# Auto-fix linting
uv run ruff check --fix src/

# Sort imports
uv run ruff check --select I --fix src/

# Type checking
uv run mypy src/

# Complexity check
uv run radon cc src/ -s -a
```

---

## Final Deliverables

1. **Refactoring Report**: All findings in `.work/agent/issues/`
2. **Phased Plan**: Prioritized refactoring roadmap
3. **Pattern Guide**: Document Pythonic patterns adopted
4. **Before/After Examples**: Code comparisons
5. **Metrics**: Improvement in code quality scores
6. **Updated Style Guide**: Project-specific Python conventions

---

## Notes

- Prefer simplicity over cleverness
- Maintain backward compatibility in public APIs
- Add tests before refactoring if missing
- Run full test suite after each change
- Update documentation to reflect new patterns
- Use type checkers to validate changes
- Consider performance impact of changes
- Balance perfection with pragmatism
- Focus on readability and maintainability

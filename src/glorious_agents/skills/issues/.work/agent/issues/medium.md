# Issues - medium

## Missing CLI Commands

### Issue: Implement `epic-set` command
**Priority**: MEDIUM  
**Status**: TODO  
**Created**: 2025-11-12
**Description**: Add `issues epic-set <issue_id> <epic_id>` command to assign an issue to an epic.

**Notes**:
- May overlap with existing `epic-add` command - verify functionality first
- Spec location: `.work/agent/cli-specification.md` Phase 5, command 18
- Implementation estimate: ~40 lines

**Acceptance Criteria**:
- [ ] Command accepts `<issue_id>` and `<epic_id>` arguments
- [ ] Updates issue's epic_id field using IssueService
- [ ] Supports `--json` output flag
- [ ] Validates epic exists and is of type EPIC
- [ ] Returns error for non-existent issues
- [ ] Has unit and integration tests
- [ ] 70%+ test coverage maintained

---

### Issue: Implement `epic-clear` command
**Priority**: MEDIUM  
**Status**: TODO  
**Created**: 2025-11-12
**Description**: Add `issues epic-clear <issue_id>` command to remove an issue from its epic.

**Notes**:
- May overlap with existing `epic-remove` command - verify functionality first
- Spec location: `.work/agent/cli-specification.md` Phase 5, command 19
- Implementation estimate: ~40 lines

**Acceptance Criteria**:
- [ ] Command accepts `<issue_id>` argument
- [ ] Clears issue's epic_id field (sets to None)
- [ ] Supports `--json` output flag
- [ ] Returns error for non-existent issues
- [ ] Handles issues without epic gracefully
- [ ] Has unit and integration tests
- [ ] 70%+ test coverage maintained

---


id: "ENHANCE-001"
title: "Add comprehensive type hints to all modules"
description: "Add Python type annotations for better static analysis and IDE support"
created: 2025-11-11
section: code-quality
tags: [type-hints, static-analysis, mypy]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Python type hints improve code maintainability, enable better static analysis with mypy, and provide IDE autocomplete support. The codebase should have type annotations on all function signatures and return values.

**Files**:
- All Python files in `src/issue_tracker/`
- Focus on public APIs first, then internal functions

**Implementation**:
1. Add type hints to function parameters and return types
2. Use `from __future__ import annotations` for forward references
3. Use `typing` module for complex types (Dict, List, Optional, etc.)
4. Run mypy to validate type correctness
5. Fix any type errors discovered

**Acceptance Criteria**:
- All public functions have type hints
- mypy runs without errors
- Type coverage >= 90%
- No use of `Any` type unless absolutely necessary

**Dependencies**: None

**References**:
- PEP 484 (Type Hints)
- PEP 526 (Variable Annotations)
- mypy documentation

---

---
id: "ENHANCE-002"
title: "Add Google-style docstrings to all public APIs"
description: "Comprehensive documentation for all public functions, classes, and methods"
created: 2025-11-11
section: documentation
tags: [docstrings, documentation, api-reference]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Well-documented code is crucial for maintainability. Google-style docstrings provide clear documentation that can be automatically parsed for API reference generation with mkdocstrings.

**Files**:
- All public modules in `src/issue_tracker/`
- Domain entities, services, repositories
- CLI commands

**Implementation**:
1. Add docstrings to all public functions and classes
2. Follow Google docstring format:
   - Brief description
   - Args section for parameters
   - Returns section for return values
   - Raises section for exceptions
   - Examples section where helpful
3. Use mkdocstrings to generate API reference docs

**Example**:
```python
def create_issue(title: str, priority: int = 2) -> Issue:
    """Create a new issue with the given title and priority.

    Args:
        title: The issue title. Must not be empty.
        priority: Priority level from 0 (critical) to 4 (backlog). Defaults to 2 (medium).

    Returns:
        The newly created Issue entity with generated ID and timestamps.

    Raises:
        ValueError: If title is empty or priority is out of range.

    Examples:
        >>> issue = create_issue("Fix bug", priority=1)
        >>> print(issue.id)
        issue-a3f8e9
    """
```

**Acceptance Criteria**:
- All public functions have docstrings
- Docstrings follow Google style format
- mkdocstrings can generate API reference
- No missing parameter or return value documentation

**Dependencies**: None

**References**:
- Google Style Guide (Python Docstrings)
- mkdocstrings documentation

---

---
id: "ENHANCE-003"
title: "Configure pre-commit hooks for automated quality checks"
description: "Set up pre-commit to run formatting, linting, and type checking before commits"
created: 2025-11-11
section: tooling
tags: [pre-commit, automation, quality-gates]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Pre-commit hooks prevent poorly formatted or linted code from being committed to the repository. This ensures consistency and catches issues early.

**Files**:
- Create `.pre-commit-config.yaml`
- Update `README.md` with setup instructions

**Implementation**:
1. Create `.pre-commit-config.yaml` with hooks:
   - Ruff (linting and formatting)
   - mypy (type checking)
   - trailing whitespace removal
   - EOF newline fixer
2. Document installation: `pre-commit install`
3. Add to CI workflow

**Pre-commit Config**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
```

**Acceptance Criteria**:
- Pre-commit config file created
- Hooks run automatically on git commit
- Documentation updated with installation steps
- CI validates pre-commit checks

**Dependencies**: None

**References**:
- pre-commit.com documentation

---

---
id: "ENHANCE-004"
title: "Use pathlib.Path for all file operations"
description: "Replace string-based path manipulation with pathlib for OS-agnostic code"
created: 2025-11-11
section: code-quality
tags: [pathlib, cross-platform, refactor]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Using pathlib.Path improves code readability and ensures cross-platform compatibility. String-based path manipulation is error-prone and not OS-agnostic.

**Files**:
- All files using file/directory paths
- Database configuration
- Log file paths
- Socket/pipe paths

**Anti-Pattern**:
```python
# Bad - string concatenation
db_path = base_dir + "/.issues/issues.db"
log_path = workspace + "/daemon.log"
```

**Pattern**:
```python
# Good - pathlib
from pathlib import Path

db_path = Path(base_dir) / ".issues" / "issues.db"
log_path = Path(workspace) / "daemon.log"

# Benefits
if db_path.exists():
    size = db_path.stat().st_size
```

**Acceptance Criteria**:
- All file paths use pathlib.Path
- No string concatenation for paths
- No hardcoded directory separators (/ or \\)
- Cross-platform tests pass (Linux, Mac, Windows)

**Dependencies**: None

**References**:
- Python pathlib documentation
- PEP 428 (pathlib)

---

---
id: "ENHANCE-005"
title: "Extract configuration to environment variables and config files"
description: "Remove hardcoded constants and use configuration management"
created: 2025-11-11
section: configuration
tags: [config, env-vars, twelve-factor]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Hardcoded configuration values reduce flexibility and violate the Twelve-Factor App principle of storing config in the environment. Configuration should be externalized.

**Files**:
- Create `src/issue_tracker/config.py`
- Create `.env.example`
- Update all modules with hardcoded values

**Anti-Pattern**:
```python
# Bad - hardcoded values
DATABASE_PATH = ".issues/issues.db"
SYNC_INTERVAL = 5
DAEMON_MODE = "poll"
```

**Pattern**:
```python
# Good - configuration management
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_path: Path = Path(".issues/issues.db")
    sync_interval_seconds: int = 5
    daemon_mode: str = "poll"
    auto_start_daemon: bool = True
    
    class Config:
        env_prefix = "ISSUES_"
        env_file = ".env"

settings = Settings()
```

**Environment Variables**:
- `ISSUES_DATABASE_PATH`
- `ISSUES_SYNC_INTERVAL_SECONDS`
- `ISSUES_DAEMON_MODE`
- `ISSUES_AUTO_START_DAEMON`
- `ISSUES_NO_DAEMON`
- `ISSUES_WATCHER_FALLBACK`

**Acceptance Criteria**:
- No hardcoded configuration in code
- All config via Settings class
- Environment variables documented in `.env.example`
- Settings validation with Pydantic
- Configuration tests

**Dependencies**: None

**References**:
- Twelve-Factor App (Config)
- Pydantic Settings documentation

---

---
id: "ENHANCE-006"
title: "Implement structured logging with context"
description: "Replace print statements with proper logging framework"
created: 2025-11-11
section: observability
tags: [logging, monitoring, debugging]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Using print() for debugging is not production-ready. Structured logging with context provides better observability and debugging capabilities.

**Files**:
- Create `src/issue_tracker/logging_config.py`
- Update all modules using print()
- Daemon logging to file

**Anti-Pattern**:
```python
# Bad - print statements
print(f"Creating issue: {title}")
print(f"Error: {e}")
```

**Pattern**:
```python
# Good - structured logging
import logging
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# With context
logger.info("Creating issue", extra={
    "title": title,
    "priority": priority,
    "user_id": user_id
})

logger.error("Failed to create issue", extra={
    "title": title,
    "error": str(e)
}, exc_info=True)
```

**Log Levels**:
- DEBUG: Detailed information for debugging
- INFO: General informational messages
- WARNING: Warning messages (non-critical)
- ERROR: Error messages (failures)
- CRITICAL: Critical errors (system failures)

**Acceptance Criteria**:
- No print() statements in production code
- All logging via logging module
- Structured log format (JSON for daemon)
- Log context includes operation metadata
- Daemon logs to `.issues/daemon.log`
- Log rotation configured

**Dependencies**: None

**References**:
- Python logging documentation
- structlog (optional enhancement)

---

---
id: "ENHANCE-007"
title: "Add security audit with Bandit and fix issues"
description: "Run static security analysis and fix vulnerabilities"
created: 2025-11-11
section: security
tags: [security, bandit, vulnerabilities]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Security vulnerabilities can be caught early with static analysis tools like Bandit. Running security audits should be part of the CI pipeline.

**Files**:
- All Python files in `src/issue_tracker/`
- Add Bandit to CI workflow

**Common Issues to Check**:
- No hardcoded passwords/secrets
- No use of eval() or exec()
- No weak cryptography
- No SQL injection vulnerabilities
- No insecure file permissions
- No use of assert in production code

**Implementation**:
1. Install Bandit: `uv add --dev bandit`
2. Run audit: `bandit -r src/issue_tracker/`
3. Fix high/medium severity issues
4. Add to build.py script
5. Add to CI workflow

**Acceptance Criteria**:
- Bandit runs without high/medium severity issues
- Security checks in CI pipeline
- No hardcoded secrets
- Secure file permissions for database/socket
- Input validation on all external inputs

**Dependencies**: None

**References**:
- Bandit documentation
- OWASP Top 10

---

---
id: "ENHANCE-008"
title: "Refactor large functions into smaller, focused units"
description: "Break down functions >15 lines into smaller, single-responsibility functions"
created: 2025-11-11
section: code-quality
tags: [refactoring, clean-code, maintainability]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md, .github/prompts/code-analysis.prompt.md
status: proposed
---

**Context**:
Large functions (>15-20 lines) are harder to test, understand, and maintain. Functions should follow the Single Responsibility Principle and do one thing well.

**Files**:
- Identify with: `grep -r "def " src/ | wc -l` then analyze
- Focus on CLI commands and service layer

**Anti-Pattern**:
```python
# Bad - 40-line function doing multiple things
def create_issue_with_setup(title, priority, assignee):
    # Validate inputs (5 lines)
    # Check database connection (10 lines)
    # Create issue entity (5 lines)
    # Save to database (10 lines)
    # Send notification (10 lines)
    # Return result
```

**Pattern**:
```python
# Good - small, focused functions
def validate_issue_inputs(title: str, priority: int) -> None:
    """Validate issue creation inputs."""
    if not title:
        raise ValueError("Title required")
    if not 0 <= priority <= 4:
        raise ValueError("Invalid priority")

def create_issue_entity(title: str, priority: int) -> Issue:
    """Create issue domain entity."""
    return Issue(
        id=generate_id(),
        title=title,
        priority=priority,
        created_at=utcnow()
    )

def create_issue(title: str, priority: int = 2) -> Issue:
    """Create and persist a new issue."""
    validate_issue_inputs(title, priority)
    issue = create_issue_entity(title, priority)
    repository.save(issue)
    return issue
```

**Acceptance Criteria**:
- No functions >20 lines (excluding docstrings)
- Each function has single responsibility
- Functions are testable in isolation
- Complex logic extracted to helper functions

**Dependencies**: None

**References**:
- Clean Code (Robert C. Martin)
- SOLID Principles

---

---
id: "ENHANCE-009"
title: "Add error recovery and retry logic for network operations"
description: "Implement exponential backoff for git push/pull operations"
created: 2025-11-11
section: reliability
tags: [error-handling, retry-logic, resilience]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Network operations (git push, git pull) can fail transiently. Implementing retry logic with exponential backoff improves reliability.

**Files**:
- `src/issue_tracker/daemon/git_client.py`
- `src/issue_tracker/daemon/sync_engine.py`

**Pattern**:
```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> T:
    """Retry function with exponential backoff."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)
            delay *= backoff_factor
```

**Usage**:
```python
# Git push with retries
result = retry_with_backoff(
    lambda: git_push(remote, branch),
    max_retries=5,
    initial_delay=2.0
)
```

**Acceptance Criteria**:
- Retry logic for git push/pull
- Exponential backoff implemented
- Configurable max retries
- Logs retry attempts
- Tests for retry scenarios

**Dependencies**: None

**References**:
- Exponential Backoff and Jitter (AWS Architecture Blog)

---

---
id: "ENHANCE-010"
title: "Add performance profiling and optimization for hot paths"
description: "Profile critical operations and optimize bottlenecks"
created: 2025-11-11
section: performance
tags: [performance, profiling, optimization]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Performance matters for responsiveness. Profiling helps identify bottlenecks and guide optimization efforts.

**Files**:
- All service layer files
- Database repository queries
- Sync engine operations

**Hot Paths to Profile**:
1. Issue list query with filters (most common operation)
2. Dependency graph traversal
3. Cycle detection algorithm
4. JSONL export/import
5. Database query patterns

**Tools**:
- cProfile for function-level profiling
- py-spy for sampling profiler
- pytest-benchmark for benchmarking

**Implementation**:
1. Add profiling decorator:
```python
import cProfile
import pstats
from functools import wraps

def profile(func):
    """Profile function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)
        return result
    return wrapper
```

2. Add benchmark tests:
```python
def test_list_issues_performance(benchmark):
    """Benchmark list_issues with 1000 issues."""
    result = benchmark(service.list_issues, limit=100)
    assert len(result) <= 100
    # Should complete in <100ms
    assert benchmark.stats['mean'] < 0.1
```

**Acceptance Criteria**:
- Hot paths identified and profiled
- Benchmark tests for critical operations
- No N+1 query problems
- Database indexes optimized
- Performance regression tests in CI

**Dependencies**: None

**References**:
- Python profiling documentation
- pytest-benchmark documentation

---

---
id: "ENHANCE-011"
title: "Implement dependency injection for testability"
description: "Use dependency injection pattern throughout the codebase"
created: 2025-11-11
section: architecture
tags: [dependency-injection, testing, solid-principles]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Dependency Injection (DI) improves testability by allowing mock/fake dependencies to be injected during tests. It also follows the Dependency Inversion Principle (SOLID).

**Files**:
- Service layer classes
- Repository implementations
- CLI command handlers

**Anti-Pattern**:
```python
# Bad - hardcoded dependencies
class IssueService:
    def __init__(self):
        self.repository = IssueRepository()  # Hardcoded
        self.clock = SystemClock()  # Hardcoded
```

**Pattern**:
```python
# Good - dependency injection
from typing import Protocol

class IssueRepository(Protocol):
    """Repository protocol."""
    def save(self, issue: Issue) -> None: ...

class Clock(Protocol):
    """Time provider protocol."""
    def now(self) -> datetime: ...

class IssueService:
    def __init__(
        self,
        repository: IssueRepository,
        clock: Clock
    ):
        self.repository = repository
        self.clock = clock
```

**Benefits**:
- Easy to test with mocks
- Flexible (swap implementations)
- Follows Dependency Inversion Principle
- No global state

**Testing**:
```python
def test_create_issue():
    mock_repo = MockIssueRepository()
    mock_clock = MockClock()
    service = IssueService(mock_repo, mock_clock)
    
    issue = service.create_issue("Test", priority=1)
    
    assert mock_repo.saved_issues == [issue]
```

**Acceptance Criteria**:
- All services use dependency injection
- Protocols defined for dependencies
- No hardcoded dependencies
- Tests use mock dependencies
- Factory pattern for production wiring

**Dependencies**: None

**References**:
- Dependency Inversion Principle (SOLID)
- Python typing.Protocol documentation

---

---
id: "ENHANCE-012"
title: "Add comprehensive error handling with custom exceptions"
description: "Define domain-specific exception hierarchy and handle errors consistently"
created: 2025-11-11
section: error-handling
tags: [exceptions, error-handling, robustness]
type: enhancement
priority: medium
references: .github/prompts/best-practices-check.prompt.md
status: proposed
---

**Context**:
Custom exceptions provide better error semantics and enable specific error handling. Generic exceptions (ValueError, RuntimeError) don't convey domain meaning.

**Files**:
- Already exists: `src/issue_tracker/domain/exceptions.py`
- Update all modules to use custom exceptions

**Exception Hierarchy**:
```python
class IssueTrackerError(Exception):
    """Base exception for all issue tracker errors."""
    pass

class EntityNotFoundError(IssueTrackerError):
    """Raised when an entity is not found."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} not found: {entity_id}")

class InvariantViolationError(IssueTrackerError):
    """Raised when a domain invariant is violated."""
    pass

class InvalidTransitionError(IssueTrackerError):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, from_status: str, to_status: str):
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"Invalid transition: {from_status} → {to_status}"
        )

class CycleDetectedError(IssueTrackerError):
    """Raised when a dependency cycle is detected."""
    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        super().__init__(f"Cycle detected: {' → '.join(cycle)}")
```

**Usage**:
```python
# Raise specific exceptions
def get_issue(issue_id: str) -> Issue:
    issue = repository.get(issue_id)
    if not issue:
        raise EntityNotFoundError("Issue", issue_id)
    return issue

# Catch specific exceptions
try:
    service.transition_issue(issue_id, "closed")
except InvalidTransitionError as e:
    logger.warning(f"Cannot transition: {e}")
    return {"error": str(e)}
```

**Acceptance Criteria**:
- All domain errors use custom exceptions
- Exception hierarchy documented
- No bare except: clauses
- Error context preserved
- CLI shows user-friendly error messages

**Dependencies**: Already partially implemented

**References**:
- Python exception handling best practices

---

# Issue Tracker CLI Feature Extraction Plan

## Overview
Extract all issue-tracker features from `reference-code/` folder to achieve feature parity with the Beads repository (https://github.com/steveyegge/beads). Focus: **CLI features only** (no API or MCP).

## Objectives
1. Extract complete domain model (entities, value objects, exceptions)
2. Extract repository protocols and implementations
3. Extract business logic services
4. Extract CLI commands with full functionality
5. Extract all supporting utilities and factories
6. Migrate or create comprehensive test suites
7. Ensure 70%+ test coverage
8. Follow best practices from `.github/prompts/best-practices-check.prompt.md`

---

## Phase 1: Domain Layer Extraction

### 1.1 Core Entities
**Source:** `reference-code/backend/domain/entities/`  
**Target:** `src/issue_tracker/domain/entities/`

Files to extract:
- `issue.py` - Issue entity with full lifecycle, status transitions, labels, assignee, epic support
- `epic.py` - Epic entity for hierarchical issue grouping
- `label.py` - Label entity with color support and validation
- `comment.py` - Comment entity for issue discussions

**Key Features:**
- Immutable entities with functional updates
- Full invariant validation in `__post_init__`
- Status state machine enforcement (Issue.transition())
- Label management (add/remove with deduplication)
- Epic assignment validation
- Comment CRUD operations

**Tests Required:**
- Entity creation with valid/invalid data
- State transition validation
- Invariant violation handling
- Label operations
- Epic assignment rules
- Comment text validation

---

### 1.2 Value Objects
**Source:** `reference-code/backend/domain/value_objects.py`  
**Target:** `src/issue_tracker/domain/value_objects.py`

Extract:
- `Identifier` class with parsing and validation
- `IssuePriority` enum (0-4: CRITICAL, HIGH, MEDIUM, LOW, BACKLOG)
- `IssueStatus` enum (OPEN, IN_PROGRESS, BLOCKED, RESOLVED, CLOSED, ARCHIVED)
- `IssueType` enum (BUG, FEATURE, TASK, EPIC, CHORE)
- `DependencyType` enum (BLOCKS, RELATED, PARENT_CHILD, DISCOVERED_FROM)
- `IssueDependency` dataclass

**Tests Required:**
- Identifier parsing with valid/invalid formats
- Enum value validation
- Dependency object creation

---

### 1.3 Domain Exceptions
**Source:** `reference-code/backend/domain/exceptions.py`  
**Target:** `src/issue_tracker/domain/exceptions.py`

Extract:
- `EntityNotFoundError`
- `InvariantViolationError`
- `InvalidTransitionError`
- Base exception hierarchy

**Tests Required:**
- Exception creation with proper messages
- Exception inheritance
- Error context preservation

---

### 1.4 Repository Protocols
**Source:** `reference-code/backend/domain/ports/issues.py`  
**Target:** `src/issue_tracker/domain/ports/issues.py`

Extract:
- `IssueRepository` protocol with all query methods
- `LabelRepository` protocol
- `EpicRepository` protocol
- `IssueGraphRepository` protocol for dependency graph

**Key Methods:**
- `get()`, `save()`, `delete()`
- `list_all()`, `list_by_status()`, `list_by_priority()`
- `list_by_labels()`, `list_by_assignee()`, `list_by_epic()`
- Graph: `add_dependency()`, `remove_dependency()`, `get_blockers()`, `has_cycle()`

---

### 1.5 Service Protocols
**Source:** `reference-code/backend/domain/ports/services.py`  
**Target:** `src/issue_tracker/domain/ports/services.py`

Extract:
- `Clock` protocol for time management
- `IdentifierService` protocol for ID generation
- `UnitOfWork` protocol for transaction management

---

## Phase 2: Infrastructure Layer Extraction

### 2.1 Database Repositories
**Source:** `reference-code/backend/adapters/db/repositories/`  
**Target:** `src/issue_tracker/adapters/db/repositories/`

Extract:
- `issue_repository.py` - SQLModel implementation
- `comment_repository.py` - Comment persistence
- Database models in `adapters/db/models/`
- Junction table for issue-label relationships

**Features:**
- SQLModel/SQLAlchemy ORM integration
- Query optimization with joins
- Label filtering with AND/OR logic
- Advanced filtering (text search, date ranges, empty checks)
- Pagination support

**Tests Required:**
- CRUD operations for all entities
- Query filtering combinations
- Transaction rollback handling
- Constraint violation handling

---

### 2.2 Graph Repository
**Source:** `reference-code/backend/adapters/db/repositories/issue_graph_repository.py`  
**Target:** `src/issue_tracker/adapters/db/repositories/issue_graph_repository.py`

Extract:
- Dependency edge storage
- Cycle detection algorithm
- Transitive dependency queries
- Blocker/blocked traversal

**Tests Required:**
- Dependency add/remove
- Cycle detection
- Path finding
- Blocker queries

---

### 2.3 Database Engine & UnitOfWork
**Source:** `reference-code/backend/adapters/db/`  
**Target:** `src/issue_tracker/adapters/db/`

Extract:
- `engine.py` - Database connection management
- `unit_of_work.py` - Transaction context manager
- Migration setup (Alembic)

---

## Phase 3: Service Layer Extraction

### 3.1 IssueService
**Source:** `reference-code/backend/services/issue_service.py`  
**Target:** `src/issue_tracker/services/issue_service.py`

**Methods:**
- `create_issue()` - Standard issue creation
- `create_issue_with_dependencies()` - Create with custom ID and dependencies
- `get_issue()` - Retrieve by ID
- `update_issue()` - Update fields (not status)
- `delete_issue()` - Remove issue
- `transition_issue()` - State machine transitions
- `add_label_to_issue()` / `remove_label_from_issue()`
- `set_epic()` / `clear_epic()`
- `close_issue()` / `reopen_issue()`
- `add_comment()` / `list_comments()` / `update_comment()` / `delete_comment()`
- `list_issues()` - Advanced filtering with 20+ parameters

**Tests Required:**
- Complete CRUD lifecycle
- Status transition validation
- Label operations
- Epic assignment validation
- Comment management
- Filter combinations
- Transaction rollback on errors

---

### 3.2 IssueGraphService
**Source:** `reference-code/backend/services/issue_graph_service.py`  
**Target:** `src/issue_tracker/services/issue_graph_service.py`

**Methods:**
- `add_dependency()` - With cycle prevention
- `remove_dependency()`
- `get_dependencies()` / `get_dependents()`
- `get_blockers()` / `get_blocked_issues()`
- `get_ready_queue()` - Issues with no open blockers
- `has_path()` - Path existence check
- `get_dependency_chain()` - Shortest path (BFS)
- `detect_cycles()` - DFS-based cycle finder
- `build_dependency_tree()` - Recursive tree builder

**Tests Required:**
- Dependency CRUD
- Cycle prevention
- Ready queue calculation
- Path finding
- Tree building with max depth

---

### 3.3 IssueStatsService
**Source:** `reference-code/backend/services/issue_stats_service.py`  
**Target:** `src/issue_tracker/services/issue_stats_service.py`

**Methods:**
- `count_by_status()`
- `count_by_priority()`
- `get_completion_rate()`
- `get_priority_breakdown()`
- `get_blocked_issues()`
- `get_recently_updated()`

**Tests Required:**
- Aggregation calculations
- Empty project handling
- Date filtering

---

## Phase 4: CLI Layer Extraction

### 4.1 CLI Commands
**Source:** `reference-code/backend/cli/commands/issues.py` (2763 lines)  
**Target:** `src/issue_tracker/cli/commands/issues.py`

**Commands to Extract:**

1. **create** - Create issue with template support, dependencies, custom ID
2. **list** - List with 20+ filters (status, priority, labels, text search, date ranges)
3. **show** - Display detailed info for one or multiple issues
4. **update** - Update fields (title, desc, priority, assignee)
5. **delete** - Delete single or batch from file
6. **restore** - Restore archived issues
7. **label-add** / **label-remove** - Batch label operations
8. **label-list** - Show issue labels
9. **label-list-all** - Global label usage stats
10. **epic-set** / **epic-clear** - Epic management
11. **dep-add** / **dep-remove** - Dependency management
12. **dep-tree** - Show dependency tree (text, mermaid, json)
13. **cycles** - Detect dependency cycles
14. **ready** - Show ready work queue with sorting policies
15. **blocked** - Show blocked issues with blocker details
16. **close** / **reopen** - Close/reopen with reason
17. **comment-add** / **comment-list** - Comment management
18. **stats** - Comprehensive project statistics
19. **stale** - Find stale issues
20. **bulk-create** - Create from markdown file

**Features:**
- Rich terminal output with tables and colors
- JSON output mode for scripting
- Batch operations (multiple issue IDs)
- Error handling with best-effort execution
- Template-based issue creation
- Dependency parsing from CLI args

**Tests Required:**
- Integration tests for each command
- Valid/invalid input handling
- JSON output validation
- Batch operation edge cases
- Error message verification

---

### 4.2 CLI Dependencies
**Source:** `reference-code/backend/cli/dependencies.py`  
**Target:** `src/issue_tracker/cli/dependencies.py`

Extract:
- `get_session()` - Database session factory
- Dependency injection helpers

---

### 4.3 CLI App Registration
**Source:** `reference-code/backend/cli/app.py`  
**Target:** `src/issue_tracker/cli/app.py`

Update:
- Register `issues` subcommand in main Typer app
- Add help text and documentation

---

## Phase 5: Factory & Utilities

### 5.1 Service Factory
**Source:** `reference-code/backend/factories/service_factory.py`  
**Target:** `src/issue_tracker/factories/service_factory.py`

Extract methods:
- `create_issue_service()`
- `create_issue_graph_service()`
- `create_issue_stats_service()`
- `create_identifier_service()`
- `create_clock()`
- `create_unit_of_work()`

---

### 5.2 Utilities
**Source:** `reference-code/backend/utils/`  
**Target:** `src/issue_tracker/utils/`

Extract:
- `time.py` - `utcnow_naive()` helper
- Any other utilities used by issue tracking

---

## Phase 6: Testing Strategy

### 6.1 Unit Tests
**Target:** `tests/unit/`

Required test files:
- `test_issue_entity.py` - Entity validation, transitions, label ops
- `test_epic_entity.py` - Epic validation, status rules
- `test_label_entity.py` - Label validation, color format
- `test_comment_entity.py` - Comment validation
- `test_value_objects.py` - Identifier parsing, enum validation
- `test_issue_service.py` - Service methods with mocked repos
- `test_issue_graph_service.py` - Graph algorithms (cycle detection, BFS)
- `test_issue_stats_service.py` - Aggregation logic

**Coverage Target:** 70%+ for domain and service layers

---

### 6.2 Integration Tests
**Target:** `tests/integration/`

Required test files:
- `test_issue_repository.py` - Database CRUD and queries
- `test_issue_graph_repository.py` - Graph storage and traversal
- `test_issue_cli.py` - CLI commands end-to-end
- `test_issue_lifecycle.py` - Full workflow scenarios

**Scenarios:**
- Create issue → add labels → set epic → close → reopen
- Create issues with dependencies → detect cycles → get ready queue
- Bulk operations from file
- Complex filtering combinations
- Comment thread management

---

## Phase 7: Documentation

### 7.1 Code Documentation
- Add/verify Google-style docstrings for all public functions
- Document state machine transitions
- Document dependency graph constraints
- Add usage examples to CLI help text

---

### 7.2 User Documentation
**Target:** `docs/`

Create:
- `issue-tracker-guide.md` - Complete CLI reference
- `dependency-management.md` - Graph features and cycle prevention
- `bulk-operations.md` - Batch issue creation and deletion
- `filtering-guide.md` - Advanced filtering examples

---

## Phase 8: Migration & Integration

### 8.1 Database Migrations
**Target:** `migrations/versions/`

Create Alembic migrations:
- Issue table with all fields
- Epic table
- Label table
- Comment table
- Issue-Label junction table
- Dependency edge table
- Indexes for common queries

---

### 8.2 Configuration
**Target:** `.env.example`, `pyproject.toml`

Add:
- Database connection string
- Max dependency depth setting
- Default priority/status values

---

### 8.3 Dependencies
**Target:** `pyproject.toml`

Ensure present:
- `typer[all]` - CLI framework
- `rich` - Terminal output
- `sqlmodel` - ORM
- `alembic` - Migrations
- `pytest` - Testing
- `pytest-cov` - Coverage

---

## Execution Order

### Group 1: Foundation (Domain Model)
1. Extract value objects and exceptions
2. Extract core entities (Issue, Epic, Label, Comment)
3. Extract repository protocols
4. Write unit tests for entities
5. Run `uv run scripts/build.py --verbose`

### Group 2: Infrastructure (Repositories)
1. Extract database models
2. Extract repository implementations
3. Extract graph repository
4. Write integration tests for repositories
5. Create database migrations
6. Run `uv run scripts/build.py --verbose`

### Group 3: Business Logic (Services)
1. Extract IssueService
2. Extract IssueGraphService
3. Extract IssueStatsService
4. Extract service factory
5. Write unit tests for services
6. Write integration tests for service workflows
7. Run `uv run scripts/build.py --verbose`

### Group 4: CLI Interface
1. Extract CLI dependencies
2. Extract CLI commands (issues.py)
3. Register in main CLI app
4. Write integration tests for CLI commands
5. Test JSON output mode
6. Run `uv run scripts/build.py --verbose`

### Group 5: Advanced Features
1. Implement template support
2. Implement bulk operations
3. Implement dependency tree visualization (mermaid, json)
4. Test cycle detection
5. Test ready queue sorting policies
6. Run `uv run scripts/build.py --verbose`

### Group 6: Documentation & Polish
1. Add docstrings to all public APIs
2. Create user documentation
3. Add CLI help examples
4. Create migration guide
5. Final coverage check
6. Run `uv run scripts/build.py --verbose`

---

## Validation Checklist

### Feature Parity with Beads
- [ ] Issue CRUD with all status values
- [ ] Priority levels (0-4)
- [ ] Issue types (BUG, FEATURE, TASK, EPIC, CHORE)
- [ ] Label management with colors
- [ ] Epic hierarchies
- [ ] Dependency graph with cycle prevention
- [ ] Blocker tracking
- [ ] Ready queue calculation
- [ ] Comment threads
- [ ] Status transitions with validation
- [ ] Batch operations
- [ ] Template-based creation
- [ ] Custom issue IDs
- [ ] Advanced filtering (text, dates, priority ranges, empty checks)
- [ ] Statistics and metrics
- [ ] Dependency tree visualization
- [ ] Stale issue detection

### Code Quality
- [ ] 70%+ test coverage
- [ ] All tests pass
- [ ] No linting errors (Ruff)
- [ ] Type checking passes (MyPy)
- [ ] Docstrings on all public functions
- [ ] No hardcoded configuration values
- [ ] Proper error handling
- [ ] Transaction management with UoW

### Architecture
- [ ] Clean separation: Domain → Services → CLI
- [ ] Dependency injection throughout
- [ ] Protocol-based abstractions
- [ ] Immutable entities
- [ ] Repository pattern implemented
- [ ] Factory pattern for service creation

---

## File Manifest

### Files to Extract (41 files)

#### Domain Layer (9 files)
- `domain/entities/issue.py`
- `domain/entities/epic.py`
- `domain/entities/label.py`
- `domain/entities/comment.py`
- `domain/value_objects.py` (partial - issue-related types)
- `domain/exceptions.py`
- `domain/ports/issues.py`
- `domain/ports/services.py` (partial - Clock, IdentifierService, UoW)
- `domain/ports/__init__.py`

#### Service Layer (4 files)
- `services/issue_service.py`
- `services/issue_graph_service.py`
- `services/issue_stats_service.py`
- `services/__init__.py`

#### Infrastructure Layer (8 files)
- `adapters/db/repositories/issue_repository.py`
- `adapters/db/repositories/comment_repository.py`
- `adapters/db/repositories/issue_graph_repository.py`
- `adapters/db/models/issue_models.py` (to be created if separate)
- `adapters/db/engine.py`
- `adapters/db/unit_of_work.py`
- `adapters/db/__init__.py`
- `adapters/db/repositories/__init__.py`

#### CLI Layer (3 files)
- `cli/commands/issues.py` (2763 lines - largest file)
- `cli/dependencies.py`
- `cli/app.py` (update to register issues command)

#### Factory Layer (2 files)
- `factories/service_factory.py` (partial - issue-related factories)
- `factories/__init__.py`

#### Utilities (2 files)
- `utils/time.py`
- `utils/__init__.py`

#### Tests (13 files)
- `tests/unit/test_issue_entity.py`
- `tests/unit/test_epic_entity.py`
- `tests/unit/test_label_entity.py`
- `tests/unit/test_comment_entity.py`
- `tests/unit/test_value_objects.py`
- `tests/unit/test_issue_service.py`
- `tests/unit/test_issue_graph_service.py`
- `tests/unit/test_issue_stats_service.py`
- `tests/integration/test_issue_repository.py`
- `tests/integration/test_issue_graph_repository.py`
- `tests/integration/test_issue_cli.py`
- `tests/integration/test_issue_lifecycle.py`
- `tests/conftest.py` (update with fixtures)

---

## Risk Assessment

### High Risk
- **Dependency graph cycle detection** - Complex algorithm, needs thorough testing
- **CLI batch operations** - Error handling for partial failures
- **Database migrations** - Must not break existing data

### Medium Risk
- **State machine transitions** - Must enforce all rules correctly
- **Test coverage** - Large codebase, need comprehensive tests
- **Advanced filtering** - Many parameter combinations

### Low Risk
- **Entity validation** - Straightforward invariants
- **Basic CRUD operations** - Standard patterns
- **Rich terminal output** - Library-provided features

---

## Success Criteria

1. ✅ All 20 CLI commands functional
2. ✅ 70%+ test coverage achieved
3. ✅ All tests passing
4. ✅ No linting/type errors
5. ✅ Build script passes with --verbose
6. ✅ Feature parity with Beads repository
7. ✅ Documentation complete
8. ✅ Migration guide created
9. ✅ Example workflows documented
10. ✅ JSON output mode working for all commands

---

## Timeline Estimate

- **Group 1 (Foundation):** 8-10 tasks
- **Group 2 (Infrastructure):** 8-10 tasks
- **Group 3 (Business Logic):** 10-12 tasks
- **Group 4 (CLI Interface):** 10-12 tasks
- **Group 5 (Advanced Features):** 8-10 tasks
- **Group 6 (Documentation):** 6-8 tasks

**Total:** ~50-62 tasks across 6 groups

---

## Notes

- This plan focuses **exclusively on CLI features** - no API or MCP extraction
- Follow best practices from `.github/prompts/best-practices-check.prompt.md`
- Use Sequential Thinking MCP tool to break each group into atomic tasks
- Reference focused-testing-architecture.md for test organization
- Each group ends with running `uv run scripts/build.py --verbose`
- Fix all bugs/issues before proceeding to next group
- Maintain 70%+ test coverage throughout

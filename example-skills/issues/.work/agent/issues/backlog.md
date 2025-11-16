# Backlog - Future Work

## Infrastructure Layer (Group 2)
- Database models with SQLModel
- Alembic migrations
- Repository implementations (Issue, Comment, Graph)
- Database engine & UnitOfWork
- Integration tests for repositories

## Business Logic Layer (Group 3)
- Service protocols (Clock, IdentifierService, UnitOfWork)
- IssueService with business logic
- IssueGraphService with dependency algorithms
- IssueStatsService with aggregations
- Service factory for DI
- Unit tests for services with mocks
- Integration tests for service workflows

## Initialization & Daemon (Group 5)
- Init command with workspace setup
- Daemon service with background process
- Sync engine (JSONL export/import + git)
- Polling mode (5-second intervals)
- Socket/RPC communication (JSON-RPC over Unix socket)
- Daemon management commands (list, health, stop, restart, killall, logs)
- Auto-start daemon on first CLI command
- Manual sync command
- Integration tests for daemon functionality

## Enhancements (from medium.md)
- ENHANCE-001: Type hints
- ENHANCE-002: Google-style docstrings
- ENHANCE-003: Pre-commit hooks
- ENHANCE-004: Pathlib migration
- ENHANCE-005: Configuration management
- ENHANCE-006: Structured logging
- ENHANCE-007: Security audit with Bandit
- ENHANCE-008: Refactor large functions
- ENHANCE-009: Error recovery with retry logic
- ENHANCE-010: Performance profiling
- ENHANCE-011: Dependency injection
- ENHANCE-012: Custom exception hierarchy

## Advanced Features
- Agent workflow commands (claim, discover-and-link)
- Hierarchical issue tree view
- Team collaboration features
- Advanced filtering (date ranges, text search)
- Bulk operations from markdown
- Performance optimization
- Multi-workspace daemon management
- Git hooks integration

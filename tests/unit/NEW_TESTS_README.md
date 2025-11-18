# New Unit Tests for Branch Changes

This directory contains comprehensive unit tests for the refactored database module, enhanced lifecycle management, and improved configuration handling.

## Test Files Overview

### Database Module Tests (tests/unit/core/db/)

#### test_connection.py (17 tests)
Tests for database connection management and configuration.

**Classes:**
- `TestGetDataFolder` - Data folder creation and path management
- `TestGetAgentDbPath` - Database path resolution
- `TestGetMasterDbPath` - Master DB path (backward compatibility)
- `TestGetConnection` - Connection creation with optimizations
- `TestConnectionEdgeCases` - Error conditions and edge cases

**Key Features Tested:**
- WAL mode enabled
- Foreign key constraints
- Performance optimizations (cache size, mmap, temp store)
- Thread-safe connection creation
- Path handling with special characters

#### test_schema.py (14 tests)
Tests for schema initialization.

**Classes:**
- `TestInitSkillSchema` - Skill schema initialization
- `TestInitMasterDb` - Core tables initialization
- `TestSchemaEdgeCases` - Edge cases

**Key Features Tested:**
- Schema file execution
- Migration system integration
- Metadata tracking
- Error handling
- Unicode support

#### test_batch.py (6 tests)
Tests for batch database operations.

**Key Features Tested:**
- Transaction batching
- Error rollback
- Large batch handling (1000+ operations)

#### test_optimization.py (6 tests)
Tests for database optimization operations.

**Key Features Tested:**
- ANALYZE execution
- Index optimization
- FTS5 optimization
- Idempotent operations

#### test_migration.py (6 tests)
Tests for legacy database migration.

**Key Features Tested:**
- Legacy DB detection
- Data migration
- Error handling
- Multi-source migration

### Core Module Tests (tests/unit/core/)

#### test_context_lifecycle.py (13 tests)
Tests for SkillContext lifecycle management.

**Class:**
- `TestSkillContextLifecycle`

**Key Features Tested:**
- Context manager protocol (`__enter__`, `__exit__`)
- Connection cleanup
- Resource lifecycle
- Error handling during cleanup
- Cache and event bus operations after close

#### test_runtime_cleanup.py (11 tests)
Tests for runtime cleanup functionality.

**Class:**
- `TestRuntimeCleanup`

**Key Features Tested:**
- `reset_ctx()` functionality
- Atexit handler registration
- Thread safety
- Idempotent cleanup
- Error handling

### Configuration Tests (tests/unit/)

#### test_config_enhanced.py (29 tests)
Tests for enhanced configuration module.

**Classes:**
- `TestFindProjectRoot` - Project root detection
- `TestConfigInitialization` - Config initialization
- `TestConfigPathMethods` - Path resolution
- `TestGetConfigFunction` - Singleton pattern
- `TestResetConfigFunction` - Reset functionality
- `TestConfigEdgeCases` - Edge cases

**Key Features Tested:**
- Lazy-loaded singleton
- Environment variable parsing
- Project root detection (.git, .env)
- Path resolution
- Thread safety
- Type conversion

## Running the Tests

### All New Tests
```bash
pytest tests/unit/core/db/ tests/unit/core/test_*.py tests/unit/test_config_enhanced.py -v
```

### By Category
```bash
# Database tests
pytest tests/unit/core/db/ -v

# Lifecycle tests
pytest tests/unit/core/test_context_lifecycle.py tests/unit/core/test_runtime_cleanup.py -v

# Config tests
pytest tests/unit/test_config_enhanced.py -v
```

### With Coverage
```bash
pytest tests/unit/core/db/ tests/unit/core/test_*.py tests/unit/test_config_enhanced.py \
  --cov=src/glorious_agents/core/db \
  --cov=src/glorious_agents/core/context \
  --cov=src/glorious_agents/core/runtime \
  --cov=src/glorious_agents/config \
  --cov-report=html \
  --cov-report=term-missing
```

### Run Specific Test
```bash
pytest tests/unit/core/db/test_connection.py::TestGetConnection::test_creates_connection_with_default_settings -v
```

## Test Statistics

- **Total Test Files**: 8
- **Total Test Cases**: 102
- **Lines of Code**: ~1,500+
- **Coverage Target**: >80%

## Testing Strategy

### Coverage Areas
1. **Happy Paths** - Normal operation scenarios
2. **Edge Cases** - Boundary conditions
3. **Error Handling** - Exception scenarios
4. **Resource Management** - Cleanup and lifecycle
5. **Thread Safety** - Concurrent access
6. **Backward Compatibility** - Legacy API support

### Best Practices
- ✓ Descriptive test names
- ✓ Comprehensive docstrings
- ✓ Proper mocking
- ✓ Resource cleanup
- ✓ Setup/teardown
- ✓ Fixtures from conftest.py

## Dependencies

Tests use:
- `pytest` - Test framework
- `unittest.mock` - Mocking
- Fixtures from `tests/conftest.py`

## Integration

These tests integrate with existing:
- Test infrastructure (conftest.py)
- Pytest configuration (pyproject.toml)
- CI/CD pipelines
- Coverage requirements (70%+)

## Notes

1. Tests are isolated and use mocking to avoid side effects
2. All resources are properly cleaned up
3. Thread safety is verified for singleton patterns
4. Backward compatibility is maintained
5. Security tests exist in `test_isolation_security.py`
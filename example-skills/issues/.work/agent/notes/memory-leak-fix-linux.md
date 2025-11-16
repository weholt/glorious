# Memory Leak Fix: Linux Integration Tests

## Problem

Integration tests on Linux consumed all memory and crashed the system when running:
```bash
uv run scripts/build.py --verbose --integration all
```

Works fine on Windows, but Linux OOM kills the process.

## Root Cause

The `integration_cli_runner` fixture in `tests/conftest.py` creates 29 test instances, each with:
- Unique temporary workspace
- Unique SQLite database path
- Changed working directory

The `get_engine()` function in `src/issue_tracker/cli/dependencies.py` was decorated with `@lru_cache` but:
1. Cache key had NO arguments
2. Each test changed the DB path dynamically (via `os.chdir()`)
3. `get_db_url()` also had `@lru_cache`, creating stale cache entries
4. Result: 29 SQLAlchemy engines created but NEVER disposed
5. Each engine holds:
   - Connection pool
   - File handles
   - SQLite WAL files
   - ~5MB memory per engine = 145MB leaked

On Linux:
- File descriptors accumulate faster
- SQLite file locking more strict
- Memory pressure leads to OOM

On Windows:
- More forgiving file handle management
- Different SQLite implementation
- Better memory swapping

## Solution

### Changed Files

1. **src/issue_tracker/cli/dependencies.py**
   - Removed `@lru_cache` from `get_engine()`
   - Added manual `_engine_registry: dict[str, Engine]` to track engines by URL
   - Engines cached per unique `db_url` (not globally)
   - Added `dispose_all_engines()` function to cleanup

2. **tests/conftest.py** (integration_cli_runner fixture)
   - Simplified cleanup to call `dispose_all_engines()`
   - Disposes ALL engines, not just current one
   - Clears path caches (`get_db_url`, `get_issues_folder`)

### Technical Details

**Before:**
```python
@lru_cache
def get_engine():
    db_url = get_db_url()  # Also @lru_cache
    engine = create_engine(db_url, ...)
    return engine
```

Problem: Cache key is empty `()`, but `db_url` changes. Multiple engines cached under same key.

**After:**
```python
_engine_registry: dict[str, Engine] = {}

def get_engine():
    db_url = get_db_url()
    if db_url in _engine_registry:
        return _engine_registry[db_url]
    
    engine = create_engine(db_url, ...)
    _engine_registry[db_url] = engine
    return engine

def dispose_all_engines():
    for engine in _engine_registry.values():
        engine.dispose()
    _engine_registry.clear()
```

Now: Each unique URL gets ONE engine, all tracked for cleanup.

## Verification

To verify the fix works, check:

1. **Memory usage stays stable** during integration tests
2. **No file descriptor leaks**: `lsof | grep issues.db | wc -l` stays low
3. **All tests pass** on Linux

Run:
```bash
uv run scripts/build.py --verbose --integration all
```

Expected:
- Memory usage < 500MB (was: OOM kill)
- All 90 integration tests pass
- No file handle warnings

## Related Issues

- Integration tests using `integration_cli_runner` fixture: 29 tests
- Total integration tests: 90 tests
- Tests using in-memory DB (conftest.py test_engine fixture): No leak (StaticPool)
- Tests using file DB (daemon tests): Fixed with manual dispose

## Prevention

For future test fixtures that create database engines:
1. Always call `engine.dispose()` in cleanup
2. Clear any `@lru_cache` decorated functions that affect DB path
3. Consider using `_engine_registry` pattern for multi-workspace tests
4. Test on Linux to catch file descriptor leaks early

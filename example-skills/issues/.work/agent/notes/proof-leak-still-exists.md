# PROOF: Why The Memory Leak Still Exists

## The Claim vs Reality

### What Was "Fixed":
✅ `integration_cli_runner` fixture calls `dispose_all_engines()` (tests/conftest.py:821)
✅ DaemonService._shutdown() disposes its engine (service.py:232)
✅ daemon_workspace fixture disposes its engine (test_daemon_integration.py:78)

### What Was NOT Fixed:
❌ `pytest_sessionfinish` in `tests/integration/conftest.py` does NOT call `dispose_all_engines()`
❌ DaemonService creates engines OUTSIDE the registry system (direct create_engine call)
❌ Tests create engines with direct `create_engine()` calls (5 locations in test_daemon_integration.py)

## The Two Conftest Files Problem

### File 1: tests/conftest.py (main test config)
- Line 821: ✅ Calls `dispose_all_engines()`
- Used by: CLI integration tests via `integration_cli_runner` fixture
- Scope: Only tests that use this specific fixture

### File 2: tests/integration/conftest.py (integration test config)
- Line 32-48: ❌ Does NOT call `dispose_all_engines()`
- Only kills daemon processes
- Used by: ALL integration tests including daemon tests
- Scope: Session-level hook for entire integration test suite

## The Registry Bypass Problem

### Engines Tracked in Registry:
```python
# src/issue_tracker/cli/dependencies.py:98
def get_engine():
    engine = create_engine(db_url, ...)
    _engine_registry[db_url] = engine  # ✅ TRACKED
    return engine
```

### Engines NOT Tracked:
```python
# src/issue_tracker/daemon/service.py:127
self._engine = create_engine(f"sqlite:///{self.config.database_path}")
# ❌ NOT TRACKED - direct create_engine call

# tests/integration/test_daemon_integration.py:40, 334, 363, 512
engine = create_engine(f"sqlite:///{db_path}")
# ❌ NOT TRACKED - direct create_engine call
```

## Execution Flow During Daemon Tests

```
1. pytest starts
2. tests/integration/conftest.py loaded
3. pytest_sessionstart() runs → kills orphan processes ✅
4. Test: test_daemon_starts_and_writes_pid()
   a. Fixture: daemon_workspace
      - create_engine() → engine NOT in registry
      - finally: engine.dispose() ✅ (but not in registry anyway)
   b. Fixture: daemon_config (no resources)
   c. Fixture: running_daemon
      - DaemonService.__init__
      - service._get_engine() → creates engine NOT in registry
      - service._shutdown() → engine.dispose() ✅ (but not in registry anyway)
5. Test finishes
6. More tests run... (same pattern)
7. All tests complete
8. pytest_sessionfinish() runs
   - Kill daemon processes ✅
   - Call dispose_all_engines()? ❌ NO!
9. _engine_registry still contains entries from:
   - Any CLI dependency usage during tests
   - Any get_engine() calls (if any were made)
10. Memory leak remains
```

## The Count

### Engines Created Per Daemon Test:
- daemon_workspace fixture: 1 engine (disposed but never tracked)
- DaemonService._get_engine(): 1 engine (disposed but never tracked)
- Test inline creates: 0-2 engines (disposed but never tracked)
- **Total: 2-4 engines per test, ALL bypassing registry**

### But Here's The Real Problem:
Even though these engines are disposed, they're created with `create_engine()` instead of through the registry system. The registry might still accumulate engines from:
1. Any import of `issue_tracker.cli.dependencies`
2. Any test that calls CLI commands (which use get_engine())
3. Module-level engine creation during imports

## How To Verify This Is The Issue

Run this test to see if engines accumulate:

```python
import pytest
from issue_tracker.cli.dependencies import _engine_registry, dispose_all_engines

def test_check_registry():
    print(f"\n\n🔍 Registry before dispose: {len(_engine_registry)} engines")
    for url in _engine_registry.keys():
        print(f"  - {url}")
    
    dispose_all_engines()
    
    print(f"🔍 Registry after dispose: {len(_engine_registry)} engines")
    assert len(_engine_registry) == 0
```

## The Real Fix

Add to `tests/integration/conftest.py` line 48:

```python
def pytest_sessionfinish(session, exitstatus):
    """Clean up all daemon processes after test session ends."""
    killed = 0
    try:
        for proc in psutil.process_iter():
            try:
                cmdline = proc.cmdline()
                if cmdline and any("issue_tracker.daemon.service" in str(arg) for arg in cmdline):
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass

    if killed > 0:
        print(f"\n[CLEANUP] Killed {killed} orphaned daemon processes after test session")
    
    # 🔧 ADD THESE LINES:
    try:
        from issue_tracker.cli.dependencies import dispose_all_engines
        dispose_all_engines()
        print("\n[CLEANUP] Disposed all database engines")
    except Exception as e:
        print(f"\n[CLEANUP] Failed to dispose engines: {e}")
```

## Why This Wasn't Caught Before

1. **Windows masks the issue** - higher resource limits, aggressive cleanup
2. **dispose() calls work** - individual engines ARE disposed, so it looks fixed
3. **Registry is separate concern** - even "properly" disposed engines can leave registry entries
4. **Two conftest files** - fix applied to wrong file (main tests, not integration tests)
5. **No verification** - no test actually checks if registry is empty after test run

## How To Be Sure This Time

After applying the fix, run:

```bash
# Add print statement to dispose_all_engines()
# Then run daemon tests and watch for output
uv run pytest tests/integration/test_daemon_integration.py -v -s

# Should see at session end:
# [CLEANUP] Killed X orphaned daemon processes after test session
# [CLEANUP] Disposed all database engines  <-- THIS LINE MUST APPEAR

# Also check memory:
uv run python test_memory_leak_cli.py
# Should report < 100MB increase
```

The fix is simple, but the previous attempts missed it because they fixed:
- Individual engine disposal ✅ (service._shutdown, fixture finally blocks)
- CLI test cleanup ✅ (integration_cli_runner fixture)
- But NOT session-level cleanup for integration tests ❌

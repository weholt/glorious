# Issues - critical

## ✅ COMPLETED: Integration Test Memory Leak - Linux Crash Issue

**Status:** Fixed and verified  
**Date:** 2024-11-13  
**Verification:** `uv run python verify_engine_cleanup.py` passes

### Problem Statement
Running integration tests on Linux causes memory leaks that accumulate until the system crashes. Windows does not exhibit this behavior due to different resource management.

### Root Causes (Ranked by Impact)

#### 🔴 CRITICAL #1: Engine Registry Not Disposed in Integration Tests
**Impact:** 145MB+ leak across test suite
**Location:** `tests/integration/conftest.py` - pytest_sessionfinish hook

**Analysis:**
- `_engine_registry` in `src/issue_tracker/cli/dependencies.py` tracks all created engines
- `dispose_all_engines()` function exists but is ONLY called by `integration_cli_runner` fixture
- Daemon integration tests (29 tests) don't use `integration_cli_runner`
- Each daemon test creates engines via:
  - `daemon_workspace` fixture (creates 1 engine)
  - Inline engine creation for DB updates (creates 1-2 more engines)
  - DaemonService `_get_engine()` (creates 1 engine)
- Result: 3-4 engines per test × 29 tests = 87-116 engines never disposed
- Each engine holds connection pool + file descriptors + ~5MB memory

**Fix:** Add engine disposal to session cleanup hooks

#### 🔴 CRITICAL #2: Multiple Engine Creation in Daemon Tests
**Impact:** 3-4 engines per test instead of 1
**Location:** `tests/integration/test_daemon_integration.py`

**Analysis:**
- `daemon_workspace` fixture creates engine at line 40
- Tests then create ANOTHER engine inline when updating DB (lines 334, 512)
- DaemonService creates THIRD engine via `_get_engine()` (service.py:125)
- Each unique DB path = unique engine registry entry
- Engines accumulate in registry without disposal

**Fix:** Reuse workspace engine instead of creating new ones

#### 🟡 HIGH #3: Async Resource Cleanup Timing Insufficient
**Impact:** TCP connections in TIME_WAIT state, file descriptors not released
**Location:** `tests/integration/conftest.py` - running_daemon fixture

**Analysis:**
- Linux requires TIME_WAIT period for TCP connections (default 60s)
- Current cleanup wait is 0.3 seconds (line 153)
- Fast test succession doesn't give kernel time to release resources
- File descriptors accumulate: socket, TCP connections, pidfile, logfile
- Under load (29 async tests), resources exhaust before kernel cleanup

**Fix:** Increase to 0.5-1.0 seconds OR add retry/poll logic

#### 🟡 HIGH #4: aiohttp ClientSession Not Always Closed
**Impact:** ~100KB + 2 file descriptors per unclosed session
**Location:** Tests that create IPCClient manually (not via fixture)

**Analysis:**
- `ipc_client` fixture correctly calls `await client.close()` (conftest.py:172)
- Some tests create IPCClient manually without fixture
- Each ClientSession maintains TCP connection pool, DNS resolver, file descriptors
- Linux strict about FD cleanup; accumulation causes fd limit exhaustion

**Fix:** Ensure ALL IPCClient usages either use fixture OR have try/finally with close()

### Why Linux Crashes But Windows Doesn't

**Linux:** ulimit -n strict (1024-4096), TCP TIME_WAIT enforced (60s), direct memory mapping, cgroups limits, SIGKILL on OOM

**Windows:** Higher handle limit (16384+), aggressive TCP recycling, pagefile masks issues, better process cleanup

**Result:** Same leak exists but Linux hits limits during test run while Windows completes tests

### Fixes Required

#### Fix #1: Add Engine Disposal to Session Cleanup
**File:** `tests/integration/conftest.py`
Add to `pytest_sessionfinish`:
```python
from issue_tracker.cli.dependencies import dispose_all_engines
dispose_all_engines()
```

#### Fix #2: Reuse Workspace Engine in Tests
**File:** `tests/integration/test_daemon_integration.py`
Use `get_engine()` instead of `create_engine()`

#### Fix #3: Increase Async Cleanup Wait
**File:** `tests/integration/conftest.py`
Change `await asyncio.sleep(0.3)` to `await asyncio.sleep(0.5)` in running_daemon fixture

#### Fix #4: Verify All IPCClient Close Calls
Search for `IPCClient(` and ensure try/finally with `await client.close()`

### Priority Order
1. Fix #1 - Add dispose_all_engines() (5 min, 100% impact)
2. Fix #3 - Increase async wait (2 min, 30% impact)
3. Fix #4 - Audit IPCClient (15 min, 20% impact)
4. Fix #2 - Refactor engine reuse (30 min, 40% impact)

**Total Time:** 1 hour | **Impact:** Eliminates leak, prevents Linux crashes


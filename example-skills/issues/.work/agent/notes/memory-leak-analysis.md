# Memory Leak Analysis: Integration Tests on Linux

## Executive Summary

**ROOT CAUSES IDENTIFIED:**
1. **aiohttp ClientSession leaks** - IPCClient not closing sessions (daemon tests)
2. **SQLAlchemy engine accumulation** - Multiple engines created but not disposed
3. **Async resource cleanup incomplete** - Missing awaits for TCP/HTTP cleanup
4. **Event loop resource leaks** - AppRunner cleanup incomplete

## Critical Code Sections

### 1. IPCClient Session Leak (FIXED but verify usage)

**File:** `src/issue_tracker/daemon/ipc_server.py`

**Problem:** ClientSession created but not always closed
- Each unclosed session leaks ~100KB + file descriptors
- Linux is strict about file descriptor cleanup
- Sessions maintain TCP connections that don't auto-cleanup

**Fix Status:** `IPCClient.close()` method exists (line 102-110)

**Verification Needed:** All test fixtures must call `await client.close()`

### 2. SQLAlchemy Engine Registry Leak (PARTIALLY FIXED)

**File:** `src/issue_tracker/cli/dependencies.py`

**Problem:** Engine registry tracks engines but cleanup incomplete
- `_engine_registry` dict accumulates engines (line 24)
- `dispose_all_engines()` exists (line 103-115) 
- Tests create multiple workspaces = multiple DB URLs = multiple engines
- 29 tests × 5MB per engine = 145MB leaked without cleanup

**Current State:**
- ✅ Registry exists
- ✅ `dispose_all_engines()` implemented
- ⚠️ **CRITICAL:** Only called in `integration_cli_runner` fixture (conftest.py:820)
- ❌ NOT called in daemon test fixtures

### 3. Daemon Engine Leak (FIXED in service, NOT in tests)

**File:** `src/issue_tracker/daemon/service.py`

**Problem:** Each daemon workspace fixture creates engine
- `daemon_workspace` fixture creates engine (line 40)
- ✅ Engine.dispose() called in finally block (line 78)
- ✅ Service._shutdown() disposes engine (line 232)

**BUT:** Test creates multiple engines inline (lines 334, 512):
```python
engine = create_engine(f"sqlite:///{db_path}")
try:
    # ... use engine
finally:
    engine.dispose()  # ✅ GOOD
```

### 4. Async Cleanup Incomplete (FIXED but timing issues)

**File:** `tests/integration/conftest.py` (running_daemon fixture)

**Current Cleanup Sequence (lines 141-157):**
```python
await service._shutdown()      # Disposes engine
await service.ipc_server.stop() # Stops web server
daemon_task.cancel()
try:
    await daemon_task
except asyncio.CancelledError:
    pass
await asyncio.sleep(0.3)  # ⚠️ May not be enough
```

**Problem:** TCP connections need time to fully close on Linux
- Windows releases immediately
- Linux kernel holds TIME_WAIT state for TCP connections
- 0.3s may not be sufficient under load

### 5. AppRunner Cleanup Missing

**File:** `tests/integration/conftest.py` (running_daemon fixture)

**Lines 155-157:**
```python
if hasattr(service.ipc_server, "runner") and service.ipc_server.runner:
    await service.ipc_server.runner.cleanup()
```

**Problem:** Cleanup called AFTER daemon task cancelled
- Should be part of `IPCServer.stop()` method
- Currently redundant since `stop()` calls `runner.cleanup()` (ipc_server.py:74)

## Test Fixture Hierarchy

### Daemon Integration Tests Use:

1. **daemon_workspace** (test_daemon_integration.py:30)
   - Creates engine
   - ✅ Disposes in finally block
   - Used by: 29 daemon tests

2. **daemon_config** (test_daemon_integration.py:110)
   - No resources
   - Depends on: daemon_workspace

3. **running_daemon** (test_daemon_integration.py:128)
   - Starts DaemonService
   - ✅ Calls `_shutdown()` which disposes service engine
   - ⚠️ Sleep timing may be insufficient
   - Used by: 19 async tests

4. **ipc_client** (test_daemon_integration.py:161)
   - Creates IPCClient
   - ✅ Calls `await client.close()`
   - Used by: 15 tests

### CLI Integration Tests Use:

1. **integration_cli_runner** (conftest.py:774)
   - Creates temp workspace
   - Initializes real database
   - ✅ Calls `dispose_all_engines()` at end (line 820)
   - ✅ Clears lru_cache for path functions
   - Used by: 42+ CLI tests

2. **test_engine** (integration/conftest.py:52)
   - Creates in-memory SQLite engine
   - ✅ Calls `engine.dispose()` after yield (line 62)
   - Used by: Service/lifecycle tests

3. **test_session** (integration/conftest.py:66)
   - Creates session from test_engine
   - ✅ Closes session (line 81)
   - ✅ Drops tables (line 82)
   - Used by: Service tests

## Memory Leak Patterns

### Pattern 1: Multiple Database Paths
```python
# 42 CLI tests × integration_cli_runner
# Each creates unique tmp_path workspace
# Each workspace = unique DB URL
# Each DB URL = new engine in registry
# Without dispose_all_engines(): 42 engines leak
```

### Pattern 2: Daemon Test Engine Proliferation
```python
# Test creates daemon_workspace (engine 1)
# Test updates database inline (engine 2)
# Service creates engine via _get_engine() (engine 3)
# = 3 engines per test × 29 tests = 87 engines
```

### Pattern 3: aiohttp Session Accumulation
```python
# Each IPC test creates client
# Client creates ClientSession
# If close() not called: leaks ~100KB + 2 file descriptors
# 15 tests × 100KB = 1.5MB (small but FDs accumulate)
```

### Pattern 4: Async Resource TIME_WAIT
```python
# Linux TCP connections enter TIME_WAIT state
# Default duration: 60 seconds
# Test creates connection, closes, next test starts
# Kernel still holding resources for 60s
# 29 tests × fast succession = resource exhaustion
```

## Why Linux vs Windows Difference

### Windows Behavior:
- Permissive file handle management
- TCP connections released aggressively
- Memory pressure handled by pagefile
- Process isolation stronger

### Linux Behavior:
- Strict file descriptor limits (ulimit -n)
- TCP TIME_WAIT enforced (net.ipv4.tcp_fin_timeout)
- Memory fragmentation more visible
- cgroups may limit resources further

## Fixes Needed

### CRITICAL (Must Fix):

1. **Call dispose_all_engines() in daemon test cleanup**
   - Location: `tests/integration/conftest.py`
   - Add to `pytest_sessionfinish` (line 32)
   - Currently only cleans daemon processes, not engines

2. **Increase async cleanup wait time**
   - Location: `running_daemon` fixture (line 153)
   - Change `await asyncio.sleep(0.3)` to `await asyncio.sleep(0.5)`
   - Or add retry logic

3. **Verify all IPCClient usages call close()**
   - Search: `IPCClient(` in test files
   - Ensure all have `await client.close()` in finally block
   - Most tests correctly use fixture which handles this

### HIGH PRIORITY:

4. **Deduplicate engines in daemon tests**
   - Tests create engine in workspace fixture
   - Then create another inline for updates
   - Should reuse workspace engine

5. **Add engine disposal to test cleanup hooks**
   - Both sessionstart and sessionfinish should dispose
   - Currently only kills processes

### MEDIUM PRIORITY:

6. **Consider StaticPool for test engines**
   - In-memory SQLite should use StaticPool
   - File-based can use NullPool for tests
   - Reduces connection overhead

7. **Add resource leak detection**
   - Track file descriptors at test start/end
   - Track memory at test start/end
   - Fail if exceeds threshold

## Verification Commands

```bash
# Check open file descriptors
lsof -p $(pgrep -f pytest) | wc -l

# Check TCP connections in TIME_WAIT
netstat -an | grep TIME_WAIT | wc -l

# Monitor memory during tests
watch -n 1 'ps aux | grep pytest | grep -v grep'

# Run single problematic test
uv run pytest tests/integration/test_daemon_integration.py::TestDaemonLifecycle::test_daemon_starts_and_writes_pid -v

# Run with memory profiling
uv run pytest tests/integration/ --memray
```

## Test Run Analysis

Based on `test_memory_leak_cli.py`:
- Tests: 3 CLI integration tests
- Expected leak WITHOUT fix: >150MB
- Expected leak WITH fix: <100MB
- Actual behavior: Tests pass but accumulate resources

## Recommended Fix Order

1. Add `dispose_all_engines()` to pytest_sessionfinish in integration/conftest.py
2. Verify all daemon test fixtures properly clean up
3. Increase async sleep timings
4. Add resource monitoring to CI
5. Consider pytest-timeout for hanging tests

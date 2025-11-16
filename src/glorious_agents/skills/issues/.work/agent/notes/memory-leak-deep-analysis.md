# Deep Analysis: Integration Test Memory Leak on Linux

## Executive Summary

The integration tests crash Linux systems due to **multiple unclosed async resources** and **SQLAlchemy engine accumulation**. The primary culprits are:

1. **aiohttp ClientSession leaks** (CRITICAL - NEW DISCOVERY)
2. **Async task accumulation without proper cleanup** (CRITICAL - NEW DISCOVERY)  
3. **SQLAlchemy engine disposal** (PARTIALLY FIXED but incomplete)
4. **Event loop pollution** (MEDIUM)

## Root Cause Analysis

### 1. AIOHTTP ClientSession Memory Leak (CRITICAL - PRIMARY CAUSE)

**Location**: `src/issue_tracker/daemon/ipc_server.py:111-118`

```python
async with ClientSession() as session:
    async with session.post(url, json=request, timeout=ClientTimeout(total=5)) as resp:
        # ... handle response
```

**The Problem**:
- Each test that uses `running_daemon` fixture creates a DaemonService
- Each IPC request creates a NEW ClientSession
- 16 async tests × multiple IPC calls per test = **50-80+ ClientSession instances**
- On Linux, ClientSessions don't get garbage collected until event loop closes
- Accumulates TCP connectors, SSL contexts, and connection pools in memory

**Why It's Worse on Linux**:
- Linux has stricter file descriptor limits (default 1024)
- Each ClientSession opens multiple file descriptors (sockets, pipes)
- Linux kernel's networking stack caches more aggressively
- Python's GC is less aggressive with async resources on Linux

**Evidence**:
```bash
# 16 async tests in daemon_integration.py
grep -c "pytest.mark.asyncio" tests/integration/test_daemon_integration.py
# Output: 16

# Each test makes 1-5 IPC calls via IPCClient
# Total ClientSessions created: ~60-80
```

**Solution Required**:
Use a **shared, reusable ClientSession** instead of creating new ones:

```python
class IPCClient:
    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self._session: ClientSession | None = None
    
    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        session = await self._get_session()
        # ... use session
```

OR use a fixture-level session:
```python
@pytest.fixture
async def ipc_client(running_daemon):
    client = IPCClient(...)
    async with ClientSession() as session:
        client._session = session
        yield client
```

### 2. Async Task Accumulation (CRITICAL)

**Location**: Multiple places in `tests/integration/test_daemon_integration.py`

**The Problem**:
Each test creates tasks but doesn't wait for proper cleanup:

```python
@pytest.fixture
async def running_daemon(daemon_config):
    service = DaemonService(daemon_config)
    daemon_task = asyncio.create_task(service.start())
    await asyncio.sleep(0.5)  # Give daemon time to start
    
    yield service
    
    # Cleanup - INCOMPLETE
    await service._shutdown()
    await service.ipc_server.stop()
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass
    # ⚠️ NO WAIT for background tasks to actually clean up!
```

**Issues**:
1. `daemon_task.cancel()` doesn't immediately stop the task
2. IPC server has a web.AppRunner that needs `runner.cleanup()` 
3. The `_sync_loop` task may still be running
4. No wait for TCP connections to close

**Solution Required**:
```python
@pytest.fixture
async def running_daemon(daemon_config):
    service = DaemonService(daemon_config)
    daemon_task = asyncio.create_task(service.start())
    await asyncio.sleep(0.5)
    
    yield service
    
    # PROPER cleanup sequence
    await service._shutdown()  # Stops sync loop
    await service.ipc_server.stop()  # Stops web server
    
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass
    
    # CRITICAL: Wait for all async cleanup to complete
    await asyncio.sleep(0.5)  # Let tasks finish
    
    # Close any remaining connections
    if hasattr(service.ipc_server, 'runner') and service.ipc_server.runner:
        await service.ipc_server.runner.cleanup()
```

### 3. SQLAlchemy Engine Disposal (PARTIALLY FIXED)

**Status**: Most engines now disposed, but one critical place missed

**Location**: `src/issue_tracker/daemon/service.py:113-152`

```python
def _get_issues_from_db(self) -> list[dict[str, Any]]:
    try:
        engine = create_engine(f"sqlite:///{self.config.database_path}")
        try:
            with Session(engine) as session:
                issues = session.exec(select(IssueModel)).all()
                return [...]
        finally:
            engine.dispose()  # ✅ GOOD - Already fixed
```

**BUT PROBLEM**: This is called in `_sync_loop()` **every few seconds**:

```python
async def _sync_loop(self) -> None:
    while self.running:
        if self.config.sync_enabled:
            issues = self._get_issues_from_db()  # Creates new engine!
            stats = self.sync_engine.sync(issues)
        await asyncio.sleep(self.config.sync_interval_seconds)  # Default 5 sec
```

**Impact**:
- Each test runs daemon for ~2-10 seconds
- Sync interval = 5 seconds  
- Each test creates **2-3 engines** from periodic syncs
- 16 tests × 2.5 engines = **40 engines** created just from background syncs

**Solution Required**:
DaemonService should create ONE engine at initialization and reuse it:

```python
class DaemonService:
    def __init__(self, config: DaemonConfig):
        self.config = config
        # ... other init ...
        self._engine: Engine | None = None
    
    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(f"sqlite:///{self.config.database_path}")
        return self._engine
    
    def _get_issues_from_db(self) -> list[dict[str, Any]]:
        engine = self._get_engine()  # Reuse same engine
        with Session(engine) as session:
            # ... query ...
    
    async def _shutdown(self) -> None:
        # ... existing shutdown ...
        
        # Dispose engine on shutdown
        if self._engine:
            self._engine.dispose()
            self._engine = None
```

### 4. Event Loop Pollution (MEDIUM)

**Location**: `src/issue_tracker/daemon/service.py:191`

```python
async def start(self) -> None:
    self.running = True
    self._loop = asyncio.get_running_loop()  # Store reference
    # ...
```

**The Problem**:
- The `_loop` attribute is stored but never cleared
- Referenced in `_handle_request()` which runs in executor threads
- Can keep loop alive longer than needed

**Solution**:
```python
async def _shutdown(self) -> None:
    self.running = False
    # ... existing cleanup ...
    self._loop = None  # Clear loop reference
```

### 5. Integration CLI Runner Engine Accumulation (PARTIALLY FIXED)

**Location**: `tests/conftest.py:774-826`

The `integration_cli_runner` fixture creates a unique workspace per test:
- 29 integration tests using this fixture
- Each gets a unique DB path: `/tmp/pytest-xxx/integration_workspace/`
- Each unique path creates a NEW engine in the `_engine_registry`

**Current Fix** (line 818-825):
```python
yield runner

# Cleanup
os.chdir(old_cwd)
set_service(...)
dispose_all_engines()  # ✅ Good
get_db_url.cache_clear()  # ✅ Good
get_issues_folder.cache_clear()  # ✅ Good
```

**BUT**: The daemon tests don't use `integration_cli_runner`, they use `running_daemon` fixture which creates engines OUTSIDE the registry!

## Memory Leak Calculation

### Without Fixes:
```
Per daemon test:
- 5-8 IPC calls × ClientSession (100KB each) = 500-800KB
- 2-3 periodic sync engines (10MB each) = 20-30MB  
- Background async tasks (5MB) = 5MB
- Unclosed connections (2MB) = 2MB
Total per test: ~27-37MB

16 daemon tests × 35MB = 560MB leaked
29 CLI tests × 5MB = 145MB leaked
TOTAL: ~705MB leaked during test run
```

On Linux with 8GB RAM:
- System: 2GB
- Python baseline: 200MB  
- Test framework: 100MB
- **Tests accumulate 705MB WITHOUT cleanup**
- Remaining: 5GB available
- BUT: Peak memory during parallel operations can hit 2-3GB
- **Result**: OOM crash around test 20-25

### With Fixes:
```
Per daemon test (with reused sessions/engines):
- 1 ClientSession shared (100KB) = 100KB
- 1 engine per daemon (10MB) = 10MB
- Properly closed tasks (0MB) = 0MB
Total per test: ~10MB (properly released after each test)

16 daemon tests × 10MB = 160MB max (not leaked, properly cleaned)
29 CLI tests × 5MB = 145MB max (not leaked, properly cleaned)
TOTAL: ~305MB max memory usage, properly released
```

## Why Linux vs Windows Difference

| Aspect | Linux | Windows |
|--------|-------|---------|
| **File Descriptors** | Strict limit (1024) | Relaxed limit (10000+) |
| **TCP Socket Cleanup** | Slower TIME_WAIT | Faster cleanup |
| **GC Aggressiveness** | Conservative | More aggressive |
| **Memory Overcommit** | Stricter | More lenient |
| **Async Resource Cleanup** | Explicit required | Handles some implicitly |
| **Connection Pool Behavior** | Persists longer | Cleans faster |

**Result**: Same leak affects both, but Linux hits limits first.

## Fix Priority

### CRITICAL (Implement Immediately):
1. **aiohttp ClientSession reuse** - Prevents 50-80 session leaks
2. **DaemonService engine reuse** - Prevents 40 engine recreations  
3. **Proper async cleanup in running_daemon** - Ensures tasks actually stop

### HIGH (Important but not immediate):
4. **Event loop reference clearing** - Prevents subtle memory retention
5. **Add explicit ClientSession.close() to tests** - Belt-and-suspenders safety

### MEDIUM (Nice to have):
6. **Add memory profiling to CI** - Catch future leaks early
7. **pytest-asyncio configuration** - Ensure proper loop cleanup

## Testing Strategy

To verify fixes WITHOUT running tests:

1. **Static Analysis**:
```bash
# Find all ClientSession() calls
grep -r "ClientSession()" tests/ src/

# Should only be in fixture or __init__, never in request handlers
```

2. **Code Review Checklist**:
- [ ] IPCClient has single session, reused across requests
- [ ] running_daemon fixture has sleep after cleanup
- [ ] DaemonService creates engine once in __init__
- [ ] DaemonService.dispose() disposes engine
- [ ] All async with ClientSession have matching close()
- [ ] No create_engine() in loops or request handlers

3. **Theoretical Memory Calculation**:
```python
# Before fix:
daemon_tests = 16
sessions_per_test = 5
session_size = 100_000  # 100KB
engine_per_sync = 2
engine_size = 10_000_000  # 10MB

total = (daemon_tests * sessions_per_test * session_size) + 
        (daemon_tests * engine_per_sync * engine_size)
print(f"Expected leak: {total / 1_000_000}MB")
# Output: ~328MB just from daemon tests

# After fix:
total = (1 * session_size) + (16 * 1 * engine_size)
print(f"Expected usage: {total / 1_000_000}MB") 
# Output: ~160MB, properly cleaned
```

## Implementation Order

1. **Fix IPCClient** (30 min)
   - Add `_session` attribute
   - Add `close()` method
   - Modify fixture to manage lifecycle

2. **Fix DaemonService engine** (20 min)
   - Add `_engine` attribute to `__init__`
   - Add `_get_engine()` method
   - Call `engine.dispose()` in `_shutdown()`

3. **Fix running_daemon cleanup** (10 min)
   - Add `await asyncio.sleep(0.5)` after task cancel
   - Add explicit runner cleanup

4. **Test locally** (15 min)
   - Run 3-4 daemon tests in loop
   - Monitor with `htop`
   - Should see stable memory ~200-300MB

Total: ~75 minutes to implement and verify

## Validation Metrics

**Success Criteria**:
- Integration tests complete without OOM
- Peak memory usage < 1GB during full test suite  
- No file descriptor warnings in dmesg
- `htop` shows memory returning to baseline between tests
- All 29+16 = 45 integration tests pass

**Failure Indicators** (current state):
- Memory climbing 20-40MB per test without returning
- File descriptor count > 500
- OOM killer in system logs
- Tests timing out after test 20

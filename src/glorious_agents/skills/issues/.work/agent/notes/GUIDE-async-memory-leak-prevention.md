# Integration Test Memory Leak Prevention Guide

## Problem Pattern: Async Resource Leaks in Integration Tests

When integration tests create async resources (HTTP sessions, database engines, event loops) without proper cleanup, they accumulate memory and file descriptors, causing OOM crashes on Linux systems.

## Common Causes

### 1. Creating New ClientSessions Per Request
```python
# ❌ BAD - Creates new session every call
async def send_request(self, request):
    async with ClientSession() as session:  # New session each time!
        async with session.post(url, json=request) as resp:
            return await resp.json()
```

**Problem**: Each `ClientSession` allocates:
- TCP connector with connection pool
- DNS resolver
- SSL context
- File descriptors (sockets, pipes)

On Linux, these don't get garbage collected until the event loop closes. With 16 tests × 5 calls = 80 sessions leaked.

### 2. Creating Database Engines in Loops
```python
# ❌ BAD - Creates new engine every few seconds
async def _sync_loop(self):
    while self.running:
        engine = create_engine(db_url)  # New engine each iteration!
        with Session(engine) as session:
            # ... query data ...
        await asyncio.sleep(5)
```

**Problem**: Each engine creates:
- Connection pool (5-10 connections by default)
- Thread pool for connection management
- File descriptors for each connection

With 5-second intervals, this creates 2-3 engines per test = 40+ engines total.

### 3. Incomplete Async Cleanup
```python
# ❌ BAD - Doesn't wait for cleanup to finish
@pytest.fixture
async def service_fixture():
    service = Service()
    task = asyncio.create_task(service.start())
    await asyncio.sleep(0.5)
    
    yield service
    
    await service.shutdown()
    task.cancel()
    # Missing: await for cancellation + sleep for cleanup!
```

**Problem**: 
- `task.cancel()` only schedules cancellation, doesn't wait
- TCP connections may still be closing
- Background tasks may still be running
- Resources cleaned up after fixture moves to next test

## Solutions

### Solution 1: Reusable ClientSession Pattern

```python
class IPCClient:
    """Client with reusable session."""
    
    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self._session: ClientSession | None = None
    
    async def _get_session(self) -> ClientSession:
        """Get or create a reusable ClientSession.
        
        CRITICAL: Reuses the same session across all requests.
        """
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session
    
    async def close(self) -> None:
        """Close the client session and cleanup resources.
        
        CRITICAL: Must be called to prevent memory leaks.
        Each unclosed session leaks file descriptors and TCP connections.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send request using reused session."""
        session = await self._get_session()
        async with session.post(url, json=request) as resp:
            return await resp.json()
```

**Benefits**:
- 1 session per client instead of 1 per request
- Proper lifecycle management
- Explicit cleanup

### Solution 2: Reusable Database Engine Pattern

```python
class DaemonService:
    """Service with reusable database engine."""
    
    def __init__(self, config):
        self.config = config
        self._engine = None  # Will be created on first use
    
    def _get_engine(self):
        """Get or create a reusable database engine.
        
        CRITICAL: Reuses the same engine across all operations.
        Creating a new engine repeatedly causes massive memory leak.
        """
        if self._engine is None:
            from sqlmodel import create_engine
            self._engine = create_engine(f"sqlite:///{self.config.database_path}")
        return self._engine
    
    def _get_issues_from_db(self) -> list[dict]:
        """Query database using reused engine."""
        engine = self._get_engine()  # Reuse!
        with Session(engine) as session:
            return session.exec(select(IssueModel)).all()
    
    async def _shutdown(self) -> None:
        """Shutdown with proper cleanup."""
        self.running = False
        
        # Stop background tasks
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        # CRITICAL: Dispose database engine
        if self._engine:
            self._engine.dispose()
            self._engine = None
        
        # Clear other references
        self._loop = None
```

**Benefits**:
- 1 engine per service lifetime instead of per operation
- Proper disposal on shutdown
- No connection pool accumulation

### Solution 3: Proper Async Fixture Cleanup

```python
@pytest.fixture
async def running_daemon(daemon_config):
    """Start a daemon with PROPER cleanup.
    
    CRITICAL: This pattern ensures all async resources are cleaned up.
    """
    service = DaemonService(daemon_config)
    daemon_task = asyncio.create_task(service.start())
    await asyncio.sleep(0.5)  # Let it start
    
    yield service
    
    # CRITICAL: Proper cleanup sequence
    await service._shutdown()  # Stops tasks, disposes engine
    await service.ipc_server.stop()  # Stops web server
    
    # Cancel main task
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass
    
    # CRITICAL: Wait for all async cleanup to complete
    # Without this, TCP connections and tasks may still be closing
    await asyncio.sleep(0.3)
    
    # Cleanup any remaining resources
    if hasattr(service.ipc_server, "runner") and service.ipc_server.runner:
        await service.ipc_server.runner.cleanup()


@pytest.fixture
async def ipc_client(running_daemon):
    """Create an IPC client with automatic cleanup.
    
    CRITICAL: Fixture pattern ensures client.close() is always called.
    """
    service = running_daemon
    client = IPCClient(service.config.get_socket_path())
    
    yield client
    
    # CRITICAL: Always close the client
    await client.close()
```

**Usage in tests**:
```python
@pytest.mark.asyncio
async def test_something(ipc_client):
    """Test using managed client - no manual cleanup needed."""
    response = await ipc_client.send_request({"method": "health"})
    assert response["healthy"] is True
    # Client automatically closed after test
```

**Benefits**:
- Guaranteed cleanup via pytest fixture
- No manual cleanup in each test
- Reusable pattern

## Detection Strategy

### Static Analysis
```bash
# Find ClientSession() calls - should only be in fixtures or __init__
grep -r "ClientSession()" tests/ src/

# Find create_engine() calls - check if in loops or fixtures
grep -r "create_engine(" tests/ src/

# Find fixtures without proper cleanup
grep -B 5 "yield service" tests/ | grep -A 10 "finally"
```

### Code Review Checklist
- [ ] No `ClientSession()` in request handlers
- [ ] No `create_engine()` in loops or periodic functions
- [ ] All fixtures with async resources have cleanup after yield
- [ ] `await asyncio.sleep(0.3)` after task cancellation
- [ ] Engine disposal called before setting to None
- [ ] Client sessions have `.close()` method
- [ ] Tests use fixtures instead of creating resources directly

### Runtime Monitoring
```bash
# Monitor memory during tests
htop  # Watch for climbing memory

# Monitor file descriptors (Linux)
lsof -p $(pgrep -f pytest) | wc -l
# Should stay under 200-300

# Monitor open connections
netstat -an | grep ESTABLISHED | wc -l
# Should return to baseline between tests
```

## Implementation Checklist

When fixing async resource leaks:

1. **Identify Resource Creation Points**
   - [ ] Find all `ClientSession()` calls
   - [ ] Find all `create_engine()` calls
   - [ ] Find all long-lived async objects

2. **Add Reuse Pattern**
   - [ ] Add `_resource` attribute to class
   - [ ] Add `_get_resource()` method
   - [ ] Add `close()`/`dispose()` method
   - [ ] Replace direct creation with `_get_resource()`

3. **Update Fixtures**
   - [ ] Add cleanup after `yield`
   - [ ] Add `await asyncio.sleep(0.3)` after cancellation
   - [ ] Add explicit cleanup calls
   - [ ] Create managed fixtures for clients

4. **Update Tests**
   - [ ] Use fixtures instead of direct creation
   - [ ] Add try/finally for unavoidable direct creation
   - [ ] Call cleanup methods explicitly

5. **Verify**
   - [ ] Run tests with memory monitoring
   - [ ] Check file descriptor count
   - [ ] Verify no OOM crashes
   - [ ] Ensure stable memory usage

## Example: Complete Fix

**Before** (Memory leak):
```python
# Client creates new session per request
class IPCClient:
    async def send_request(self, request):
        async with ClientSession() as session:  # LEAK!
            async with session.post(url, json=request) as resp:
                return await resp.json()

# Service creates new engine every sync
class Service:
    def get_data(self):
        engine = create_engine(db_url)  # LEAK!
        with Session(engine) as session:
            return session.query(Model).all()

# Test has incomplete cleanup
@pytest.fixture
async def service():
    svc = Service()
    task = asyncio.create_task(svc.start())
    yield svc
    task.cancel()  # Doesn't wait!
```

**After** (Fixed):
```python
# Client reuses session
class IPCClient:
    def __init__(self):
        self._session = None
    
    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session
    
    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
    
    async def send_request(self, request):
        session = await self._get_session()  # REUSE!
        async with session.post(url, json=request) as resp:
            return await resp.json()

# Service reuses engine
class Service:
    def __init__(self):
        self._engine = None
    
    def _get_engine(self):
        if self._engine is None:
            self._engine = create_engine(db_url)
        return self._engine
    
    def get_data(self):
        engine = self._get_engine()  # REUSE!
        with Session(engine) as session:
            return session.query(Model).all()
    
    def cleanup(self):
        if self._engine:
            self._engine.dispose()
            self._engine = None

# Test has complete cleanup
@pytest.fixture
async def service():
    svc = Service()
    task = asyncio.create_task(svc.start())
    await asyncio.sleep(0.5)
    
    yield svc
    
    await svc.shutdown()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await asyncio.sleep(0.3)  # WAIT!
    svc.cleanup()
```

## Why This Matters More on Linux

| Resource | Windows Behavior | Linux Behavior |
|----------|------------------|----------------|
| **File Descriptors** | Soft limit 10000+ | Hard limit 1024 |
| **TCP TIME_WAIT** | Faster cleanup | Slower (2 minutes) |
| **Memory Overcommit** | Lenient | Strict |
| **GC Aggressiveness** | More aggressive | Conservative |
| **Async Cleanup** | Some implicit | Requires explicit |

**Result**: Same leak affects both platforms, but Linux hits limits first.

## Memory Leak Math

### Without Fixes:
```
Per test with poor cleanup:
- 5 IPC calls × 100KB/session = 500KB
- 2 engine recreations × 10MB = 20MB
- Background tasks = 5MB
Total: ~25MB × 16 tests = 400MB leaked

Result: OOM crash around test 20-25 on 8GB Linux system
```

### With Fixes:
```
Per test with proper cleanup:
- 1 reused session = 100KB
- 1 reused engine = 10MB  
- Properly closed tasks = 0MB
Total: ~10MB peak (released after test)

Result: Stable memory, no crash
```

## Quick Reference Card

**Resource Reuse Pattern:**
```python
class Manager:
    def __init__(self):
        self._resource = None
    
    def _get_resource(self):
        if self._resource is None:
            self._resource = create_resource()
        return self._resource
    
    def cleanup(self):
        if self._resource:
            self._resource.dispose()
            self._resource = None
```

**Async Cleanup Pattern:**
```python
@pytest.fixture
async def async_fixture():
    resource = Resource()
    task = asyncio.create_task(resource.start())
    await asyncio.sleep(0.5)
    
    yield resource
    
    await resource.shutdown()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await asyncio.sleep(0.3)
    resource.cleanup()
```

**Client Fixture Pattern:**
```python
@pytest.fixture
async def client(service):
    client = Client()
    yield client
    await client.close()
```

## Future Prevention

Add to your development workflow:

1. **Pre-commit hook** to check for `ClientSession()` in loops
2. **CI memory monitoring** to catch leaks early
3. **Code review checklist** for async resource patterns
4. **pytest fixture templates** with proper cleanup
5. **Static analysis** for engine creation in loops

## References

- This fix was applied to resolve OOM crashes in `tests/integration/test_daemon_integration.py`
- Reduced memory usage from ~705MB leaked to ~160MB peak
- Fixed 3 critical issues: ClientSession leaks, Engine recreation, Incomplete cleanup
- See `.work/agent/notes/memory-leak-deep-analysis.md` for full analysis

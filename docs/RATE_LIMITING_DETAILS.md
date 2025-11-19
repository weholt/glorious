# Detailed Rate Limiting Search - Line-by-Line References

## 1. DATABASE CONNECTION TIMEOUT (PRIMARY FINDING)

### Core Implementation
**File:** `src/glorious_agents/core/db/connection.py:45-47`
```
45 | conn.execute("PRAGMA mmap_size=268435456;")
46 | conn.execute("PRAGMA page_size=4096;")
47 | conn.execute("PRAGMA busy_timeout=5000;")  # Wait 5s on lock
```

**Purpose:** SQLite lock timeout (5 seconds)
**Scope:** Global database connection
**Mechanism:** PRAGMA directive to SQLite engine
**Backpressure:** Waits instead of failing, but doesn't queue/limit requests

---

### Issues Skill Extension
**File:** `src/glorious_agents/skills/issues/src/issue_tracker/cli/dependencies.py`
```
Lines: SQLAlchemy engine creation with:
- check_same_thread=False  (multi-threaded access)
- timeout=30               (30 second lock timeout)
- PRAGMA busy_timeout=30000 (30 second pragm timeout)
```

**Difference:** Extended 30-second timeout for issues skill
**Why:** Issues skill needs longer database lock hold times
**Still not rate limiting:** Just tolerates longer waits

---

### Engine Registry Configuration
**File:** `src/glorious_agents/core/engine_registry.py:20-30`
```
20 | connect_args = connect_args or {}
21 | connect_args.setdefault("check_same_thread", False)
22 | connect_args.setdefault("timeout", 5.0)
```

**Default timeout:** 5.0 seconds per SQLAlchemy specification

---

## 2. CONNECTION POOLING

### SQLAlchemy Default Pool
**File:** `src/glorious_agents/skills/issues/src/issue_tracker/adapters/db/engine.py:50-71`

**For in-memory SQLite (Lines 51-57):**
```
51 | if db_url == "sqlite:///:memory:" or db_url == "sqlite://":
52 |     return create_engine(
53 |         db_url,
54 |         echo=echo,
55 |         connect_args={"check_same_thread": False},
56 |         poolclass=StaticPool,
57 |     )
```
**Pool Type:** StaticPool (no pooling, single connection)

**For file-based SQLite (Lines 60-68):**
```
60 | if db_url.startswith("sqlite:///"):
61 |     return create_engine(
62 |         db_url,
63 |         echo=echo,
64 |         connect_args={
65 |             "check_same_thread": False,
66 |             "timeout": 30.0,
67 |         },
68 |     )
```
**Pool Type:** SQLAlchemy default QueuePool
**Default pool size:** 5 connections (SQLAlchemy default)
**No explicit rate limiting:** Just connection management

---

## 3. THREAD SAFETY PATTERNS

### Singleton with Double-Checked Locking
**File:** `src/glorious_agents/core/runtime.py:10-33`

```
10 | _lock = threading.Lock()
11 |
13 | def get_ctx() -> SkillContext:
14 |     global _context
15 |     # Double-checked locking for performance
16 |     if _context is None:
17 |         with _lock:
18 |             if _context is None:
19 |                 conn = get_connection(check_same_thread=False)
20 |                 event_bus = EventBus()
21 |                 _context = SkillContext(conn, event_bus)
```

**Purpose:** Prevent race conditions on first access
**Not rate limiting:** Just prevents multiple initializations

---

### EventBus with Thread-Safe Subscribers
**File:** `src/glorious_agents/core/context.py:17-52`

```
21 |     def __init__(self) -> None:
22 |         self._subscribers: dict[str, list[Callable]] = defaultdict(list)
23 |         self._lock = threading.Lock()
24 |
25 |     def subscribe(self, topic: str, callback: Callable) -> None:
26 |         with self._lock:
27 |             self._subscribers[topic].append(callback)
28 |
29 |     def publish(self, topic: str, data: dict) -> None:
30 |         with self._lock:
31 |             callbacks = self._subscribers.get(topic, [])
32 |
33 |         # Execute callbacks outside lock
34 |         for callback in callbacks:
35 |             try:
36 |                 callback(data)
37 |             except Exception as e:
38 |                 logger.error(f"Error: {e}")
```

**Features:**
- Thread-safe list mutations with lock
- Callbacks executed outside lock to prevent deadlocks
- Synchronous execution (no buffering/queuing)
- No rate limiting on callbacks

---

## 4. ASYNC TIMEOUT MANAGEMENT

### Periodic Task Execution
**File:** `src/glorious_agents/core/daemon/tasks.py`

```
Pattern: Periodic execution with asyncio.wait_for()
- timeout parameter set to self.interval
- On TimeoutError: normal operation (interval elapsed)
- On stop: graceful shutdown with 5.0 second timeout
```

**Not rate limiting:** Just scheduling periodic execution

---

### HTTP IPC Communication
**File:** `src/glorious_agents/core/daemon/ipc.py` (aiohttp usage)

```
from aiohttp import ClientSession, ClientTimeout, web

async with session.post(
    url, json=request, 
    timeout=ClientTimeout(total=5)
) as resp:
```

**Fixed 5-second timeout:** All daemon IPC requests
**No retry logic:** Single attempt with timeout

---

## 5. SUBPROCESS EXECUTION TIMEOUTS

### Test Suite Timeouts
**File:** `scripts/test_all_skills.py`

```
- sync: timeout=120        (2 minutes)
- install: timeout=120     (2 minutes)
- per-skill: timeout=300   (5 minutes)
```

**Mechanism:** subprocess.run() timeout parameter
**Behavior:** Kills process if exceeds limit
**No graceful degradation**

---

### Git Analysis Timeouts
**File:** `src/glorious_agents/skills/code-atlas/src/code_atlas/git_analyzer.py`

```
- check_git: timeout=2     (2 seconds)
- git operations: timeout=5 (5 seconds)
```

**Purpose:** Prevent hanging git operations
**No retry logic**

---

## 6. TASK QUEUE (Planner Skill)

### Database Schema
**File:** `src/glorious_agents/skills/planner/src/glorious_planner/models.py`

```
class PlannerTask(SQLModel, table=True):
    __tablename__ = "planner_queue"
    
    priority: int = Field(default=0, index=True)
    status: str = Field(default="queued", index=True)
    # status values: "queued", "running", "blocked", "done"
```

### Service Implementation
**File:** `src/glorious_agents/skills/planner/src/glorious_planner/service.py`

```
Key methods:
- add_to_queue(): Create new task
- get_next_task(): FIFO with priority
- update_task_status(): State machine
- list_tasks(status, limit=20): Pagination
```

**What it does:**
- Queues tasks for processing
- Prioritizes work
- Allows status tracking

**What it doesn't do:**
- Rate limit task intake
- Throttle processing
- Implement backpressure
- Queue size limits

---

## 7. SEARCH RESULT LIMITING

### CLI Search Command
**File:** `src/glorious_agents/cli.py:83`

```
def search(
    query: str = typer.Argument(...),
    limit: int = typer.Option(20, "--limit", "-l"),
):
```

**Default limit:** 20 results
**Mechanism:** Array slicing `all_results[:limit]`
**Purpose:** Result pagination, not rate limiting

---

### Core Search Module
**File:** `src/glorious_agents/core/search.py`

Functions support:
- `limit_per_skill`: Max results per skill
- `total_limit`: Max total results

**Purpose:** Memory efficiency, not rate limiting

---

## 8. DATABASE CONFIGURATION

### Issues Skill Settings
**File:** `src/glorious_agents/skills/issues/src/issue_tracker/config/settings.py`

```
db_pool_size: int = Field(
    default=5,           # Default connections
    ge=1, le=20,        # Range: 1-20
    description="Connection pool size"
)

db_timeout: int = Field(
    default=30,         # 30 second timeout
    ge=5, le=300,      # Range: 5-300 seconds
    description="Database lock timeout"
)
```

**Configurable but not rate limiting:**
- Pool size only controls connection count
- Timeout only affects lock wait duration

---

## 9. KEY ABSENCE FINDINGS

### No Rate Limiter Classes
**Search:** `rg "class.*RateLimiter|class.*Throttle|class.*Quota"`
**Result:** No matches

### No Retry Decorators with Backoff
**Search:** `rg "@retry|@backoff|exponential|jitter"`
**Result:** No matches

### No Semaphore-Based Limits
**Search:** `rg "asyncio.Semaphore|threading.Semaphore"`
**Result:** No matches

### No Token Bucket Implementation
**Search:** `rg "token.*bucket|sliding.*window|leaky.*bucket"`
**Result:** No matches

### No Circuit Breaker
**Search:** `rg "circuit.*breaker|CircuitBreaker"`
**Result:** No matches

### No Request Queuing with Buffer
**Search:** `rg "asyncio.Queue|queue.Queue|collections.deque.*limit"`
**Result:** Only standard queue for task scheduling (Planner), no size limits

---

## SUMMARY TABLE

| Pattern | Location | Type | Purpose | Rate Limiting? |
|---------|----------|------|---------|---|
| PRAGMA busy_timeout | connection.py:47 | DB | Wait on lock | No |
| SQLAlchemy Pool | engine_registry.py:22 | DB | Connection mgmt | No |
| Thread Lock (Singleton) | runtime.py:10 | Thread | Race prevention | No |
| EventBus Lock | context.py:23 | Thread | Subscriber safety | No |
| Asyncio wait_for | tasks.py | Async | Task timeout | No |
| aiohttp timeout | ipc.py | Network | Request timeout | No |
| subprocess timeout | build.py | Process | Execution limit | No |
| Task Queue (DB) | planner/models.py | Work | Task scheduling | No |
| Search limit | cli.py:83 | Result | Pagination | No |

---

## CONCLUSION

The codebase implements **robust timeout and resource management** at the **infrastructure level** but **no application-level rate limiting**. All mechanisms are **defensive** (prevent hangs/crashes) not **proactive** (limit throughput).

To implement rate limiting, you would need to add:
1. Rate limiter decorator or middleware
2. Per-skill quotas (requests/second)
3. Queue with backpressure
4. Token bucket or sliding window algorithm
5. Circuit breaker for fault tolerance

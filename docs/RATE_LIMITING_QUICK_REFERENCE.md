# Rate Limiting Search - Quick Reference

## Search Results Summary

### ✅ What Exists (Infrastructure-Level)

| Component | Location | Config | Timeout |
|-----------|----------|--------|---------|
| DB Connection Lock | `core/db/connection.py:47` | PRAGMA busy_timeout | 5 seconds |
| DB Issues Skill | `issues/cli/dependencies.py` | PRAGMA busy_timeout | 30 seconds |
| SQLAlchemy Pool | `core/engine_registry.py:22` | Default QueuePool | 5 connections |
| HTTP IPC | `core/daemon/ipc.py` | aiohttp ClientTimeout | 5 seconds |
| Async Tasks | `core/daemon/tasks.py` | asyncio.wait_for | Variable |
| Process Exec | `scripts/test_all_skills.py` | subprocess.timeout | 120-300s |
| Task Queue | `skills/planner/models.py` | Database table | No limit |

### ❌ What Does NOT Exist (Application-Level)

| Pattern | Status | Notes |
|---------|--------|-------|
| Rate Limiter Class | ❌ None | No RateLimiter implementation |
| Throttling Decorator | ❌ None | No @throttle or similar |
| Quota Management | ❌ None | No per-user/skill quotas |
| Token Bucket | ❌ None | No token bucket algorithm |
| Sliding Window | ❌ None | No sliding window counter |
| Circuit Breaker | ❌ None | No circuit breaker pattern |
| Request Queue | ❌ None | Only task queue, no backpressure |
| Semaphore Limit | ❌ None | No concurrency limiting |
| Retry Logic | ❌ None | Hard timeouts only |

---

## Key Files & Line Numbers

### Database Configuration
```python
# src/glorious_agents/core/db/connection.py:47
conn.execute("PRAGMA busy_timeout=5000;")  # 5 seconds

# src/glorious_agents/core/engine_registry.py:22
connect_args.setdefault("timeout", 5.0)  # SQLAlchemy timeout
```

### HTTP Timeouts
```python
# src/glorious_agents/core/daemon/ipc.py
timeout=ClientTimeout(total=5)  # 5 second HTTP timeout
```

### Process Timeouts
```python
# scripts/test_all_skills.py
timeout=120  # 2 minutes sync
timeout=300  # 5 minutes per skill
```

### Task Queue
```python
# src/glorious_agents/skills/planner/src/glorious_planner/models.py
class PlannerTask(SQLModel, table=True):
    priority: int = Field(default=0, index=True)
    status: str = Field(default="queued", index=True)
```

### Event Bus
```python
# src/glorious_agents/core/context.py:17-52
class EventBus:
    def __init__(self) -> None:
        self._lock = threading.Lock()
    
    def publish(self, topic: str, data: dict[str, Any]) -> None:
        # Synchronous, no queuing
```

---

## Implementation Strategy

If you need to add rate limiting:

### Level 1: Decorator (Easiest)
```python
# Add to core/rate_limiter.py
from functools import wraps
from time import time

def rate_limit(calls_per_second: float):
    """Decorator to rate limit function calls."""
    def decorator(func):
        last_called = [0.0]
        min_interval = 1.0 / calls_per_second
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Level 2: Service Wrapper
```python
# Add to core/service_factory.py
class RateLimitedService:
    def __init__(self, service, calls_per_second: float):
        self.service = service
        self.limiter = TokenBucket(calls_per_second)
    
    def __getattr__(self, name):
        attr = getattr(self.service, name)
        if callable(attr):
            @wraps(attr)
            def wrapper(*args, **kwargs):
                self.limiter.acquire()
                return attr(*args, **kwargs)
            return wrapper
        return attr
```

### Level 3: Skill-Level Integration
```python
# Modify core/skill_base.py
class SkillBase:
    rate_limit: float = None  # requests/second
    
    def __init__(self):
        if self.rate_limit:
            self.limiter = TokenBucket(self.rate_limit)
```

### Level 4: Queue-Based (Most Complex)
```python
# Enhance planner task queue
class RateLimitedQueue:
    def __init__(self, max_rate: float):
        self.max_rate = max_rate
        self.token_bucket = TokenBucket(max_rate)
    
    def enqueue(self, task):
        self.token_bucket.acquire()
        return self.add_to_queue(task)
```

---

## Where to Implement

### Priority 1: CLI Entry Points
- `src/glorious_agents/cli.py` - Main command handler
- `src/glorious_agents/skills_cli/` - Skill CLI commands

### Priority 2: Skill Execution
- `src/glorious_agents/core/skill_base.py` - Base skill class
- `src/glorious_agents/core/runtime.py` - Skill context/runtime

### Priority 3: Service Layer
- Individual skill services (planner, issues, etc.)
- `src/glorious_agents/core/service_factory.py`

### Priority 4: Data Layer
- Database repositories
- API clients (if added)

### Priority 5: Enhanced Queue
- `src/glorious_agents/skills/planner/` - Task queue with limits

---

## Testing Considerations

Create rate limiting tests:
```python
# tests/unit/test_rate_limiting.py
def test_rate_limiter_respects_rate():
    limiter = TokenBucket(2.0)  # 2 requests/second
    start = time.time()
    for _ in range(4):
        limiter.acquire()
    elapsed = time.time() - start
    assert elapsed >= 1.5  # Should take ~2 seconds

def test_rate_limited_skill():
    skill = RateLimitedSkill(rate_limit=1.0)
    # Run skill 3 times
    # Should take ~3 seconds
```

---

## Configuration Options

Add to settings:
```python
# src/glorious_agents/config.py
class RateLimitConfig:
    enabled: bool = False
    cli_requests_per_second: float = 10.0
    skill_requests_per_second: float = 5.0
    db_requests_per_second: float = 100.0
    http_requests_per_second: float = 10.0
```

---

## References

- SQLAlchemy Connection Pooling: [SQLAlchemy Pool Docs](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- asyncio Timeouts: [Python asyncio wait_for](https://docs.python.org/3/library/asyncio-task.html#asyncio.wait_for)
- Rate Limiting Algorithms: Token Bucket, Sliding Window, Leaky Bucket
- Libraries to Consider: ratelimit, slowapi, aiometer

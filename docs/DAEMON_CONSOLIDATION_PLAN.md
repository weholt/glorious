# Daemon Services Consolidation Plan

## Implementation Status: Phase 2 Complete ✅

**Completed:** November 19, 2025
- ✅ Phase 1: Core daemon infrastructure (BaseDaemonService, PIDFileManager, IPCServer, PeriodicTask, BaseWatcher, DaemonConfig)
- ✅ Phase 2: Issues daemon refactored to use new infrastructure
- ✅ Phase 4.2: DaemonRegistry implemented for centralized daemon tracking
- ⏸️ Phase 3: Code-Atlas watcher refactoring (deferred)
- ⏸️ Phase 4.1: Enhanced daemon orchestration (deferred)

## Executive Summary

This plan consolidates and optimizes all background services/daemons in the Glorious Agents project by extracting common patterns into reusable core components. This will reduce code duplication from ~2000 lines to ~500 lines across daemons while improving maintainability and consistency.

**Current Achievement:** Issues daemon successfully refactored with ~200 lines of boilerplate removed and full backward compatibility maintained.

## Current State Analysis

### Existing Daemons

#### 1. Core Daemon (`glorious_agents.core.daemon`)
**Purpose**: Global FastAPI-based RPC server for all skills
**Technology**: FastAPI + uvicorn
**Features**:
- Health check endpoint
- Skill listing and RPC method calls
- Event bus integration (publish/subscribe)
- Cache operations (get/set/delete/clear)
- API key authentication
**Lifecycle**: Run via `agent daemon` command
**Scope**: Global (one per agent installation)

#### 2. Issues Daemon (`issue_tracker.daemon.service`)
**Purpose**: Background sync for issue tracking
**Technology**: AsyncIO + aiohttp
**Features**:
- Periodic sync loop (DB → JSONL → Git)
- Git integration (commit/pull/push)
- HTTP-based IPC server (health/sync/stop/status)
- PID file management
- Database engine reuse
- Workspace-specific configuration
**Lifecycle**: Auto-start on first command or manual
**Scope**: Workspace-specific (one per project)

#### 3. Code-Atlas Watch Mode (`code_atlas.watch_commands`)
**Purpose**: File system watcher for Python code changes
**Technology**: Watchdog + file monitoring
**Features**:
- File system event monitoring
- Debounced rescanning
- Incremental caching
- Daemon mode (Unix fork / Windows subprocess)
- PID file management
- Status/stop commands
**Lifecycle**: Manual start via `code-atlas watch --daemon`
**Scope**: Directory-specific

### Common Patterns Identified

All three daemons share these patterns (code duplication):

1. **PID File Management** (~100 lines duplicated)
   - Write/read PID files
   - Check for existing daemons
   - Cleanup on exit
   - Stale PID file detection

2. **Process Lifecycle** (~150 lines duplicated)
   - Start/stop/restart operations
   - Graceful shutdown with signal handling
   - Zombie process cleanup
   - Cross-platform process management

3. **IPC Communication** (~200 lines duplicated)
   - HTTP-based request/response
   - Health checks
   - Command routing
   - Error handling

4. **Configuration Management** (~100 lines duplicated)
   - Load/save config files
   - Environment variable overrides
   - Default values
   - Workspace-specific paths

5. **Logging** (~50 lines duplicated)
   - File-based logging
   - Structured messages
   - Log rotation
   - Log viewing

6. **Background Tasks** (~100 lines duplicated)
   - Periodic execution
   - Error recovery
   - Graceful cancellation

**Total Duplication**: ~700 lines of boilerplate across 3 daemons

## Proposed Architecture

### Core Components (New in `glorious_agents.core.daemon/`)

#### 1. BaseDaemonService
```python
class BaseDaemonService(ABC):
    """Base class for all daemon services with lifecycle management."""
    
    def __init__(self, config: DaemonConfig):
        self.config = config
        self.running = False
        self.start_time = datetime.now()
        self._tasks: list[asyncio.Task] = []
        
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def run(self) -> None: ...
    
    @abstractmethod
    async def on_startup(self) -> None: ...
    @abstractmethod
    async def on_shutdown(self) -> None: ...
    @abstractmethod
    def get_health_info(self) -> dict[str, Any]: ...
```

#### 2. IPCServer / IPCClient
```python
class IPCServer:
    """HTTP-based IPC server using aiohttp (cross-platform)."""
    
    def __init__(self, socket_path: Path, handler: Callable):
        self.socket_path = socket_path
        self.handler = handler
        
    async def start(self) -> None: ...
    async def stop(self) -> None: ...

class IPCClient:
    """HTTP-based IPC client for daemon communication."""
    
    async def send_request(self, request: dict) -> dict: ...
    async def close(self) -> None: ...
```

#### 3. PIDFileManager
```python
class PIDFileManager:
    """Manages PID files for daemon processes."""
    
    def __init__(self, pid_path: Path):
        self.pid_path = pid_path
        
    def write(self, pid: int) -> None: ...
    def read(self) -> int | None: ...
    def remove(self) -> None: ...
    def is_running(self) -> bool: ...
    def kill_existing(self) -> bool: ...
```

#### 4. BaseWatcher
```python
class BaseWatcher(ABC):
    """Base class for file system watchers."""
    
    def __init__(self, watch_path: Path, pattern: str = "*"):
        self.watch_path = watch_path
        self.pattern = pattern
        self.observer = Observer()
        
    @abstractmethod
    async def on_change(self, event: FileSystemEvent) -> None: ...
    
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

#### 5. PeriodicTask
```python
class PeriodicTask:
    """Executes tasks at regular intervals with error recovery."""
    
    def __init__(self, interval: float, callback: Callable):
        self.interval = interval
        self.callback = callback
        self._task: asyncio.Task | None = None
        
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

#### 6. DaemonConfig
```python
@dataclass
class DaemonConfig:
    """Standard daemon configuration."""
    
    workspace_path: Path
    daemon_mode: Literal["poll", "events"]
    auto_start: bool
    log_path: Path
    pid_path: Path
    ipc_path: Path
    
    @classmethod
    def load(cls, workspace: Path) -> "DaemonConfig": ...
    def save(self) -> None: ...
```

### Refactored Architecture

```
glorious_agents/
├── core/
│   └── daemon/                        # NEW: Daemon infrastructure
│       ├── __init__.py
│       ├── base.py                    # BaseDaemonService
│       ├── ipc.py                     # IPCServer, IPCClient
│       ├── pid.py                     # PIDFileManager
│       ├── watcher.py                 # BaseWatcher
│       ├── tasks.py                   # PeriodicTask
│       ├── config.py                  # DaemonConfig
│       └── lifecycle.py               # start/stop/status helpers
│
└── skills/
    ├── issues/
    │   └── daemon/
    │       ├── service.py              # REFACTORED: Extends BaseDaemonService
    │       └── sync_engine.py         # KEPT: Issue-specific sync logic
    │
    └── code-atlas/
        └── daemon/                     # NEW: Structured daemon
            └── watcher_service.py     # REFACTORED: Extends BaseDaemonService + BaseWatcher
```

## Migration Plan

### Phase 1: Create Core Infrastructure (1-2 days) ✅ COMPLETED

#### Step 1.1: Create Base Daemon Components ✅
- [x] Implement `BaseDaemonService` with lifecycle management
- [x] Implement `PIDFileManager` for PID file operations
- [x] Implement `IPCServer` and `IPCClient` for HTTP-based IPC
- [x] Add comprehensive unit tests

#### Step 1.2: Create Task & Watcher Components ✅
- [x] Implement `PeriodicTask` for scheduled operations
- [x] Implement `BaseWatcher` for file system monitoring
- [x] Implement `DaemonConfig` for configuration management
- [x] Add integration tests

#### Step 1.3: Add Helper Utilities ✅
- [x] Implement `start_daemon()`, `stop_daemon()`, `is_running()` helpers
- [x] Add process cleanup utilities
- [x] Add cross-platform signal handling
- [x] Document API

### Phase 2: Refactor Issues Daemon (1 day) ✅ COMPLETED

#### Step 2.1: Refactor Service ✅
```python
class IssuesDaemonService(BaseDaemonService):
    """Issues-specific daemon extending core infrastructure."""
    
    def __init__(self, config: DaemonConfig):
        super().__init__(config)
        self.sync_engine = SyncEngine(...)
        self.sync_task = PeriodicTask(
            interval=config.sync_interval,
            callback=self._sync
        )
    
    async def on_startup(self) -> None:
        await self.sync_task.start()
    
    async def on_shutdown(self) -> None:
        await self.sync_task.stop()
    
    async def _sync(self) -> None:
        """Issue-specific sync logic."""
        issues = self._get_issues_from_db()
        self.sync_engine.sync(issues)
```

**Implementation Notes:**
- Refactored IssuesDaemonService to extend BaseDaemonService (src/glorious_agents/skills/issues/src/issue_tracker/daemon/service.py:20)
- Replaced manual PID/IPC handling with core daemon infrastructure
- Updated sync loop to use PeriodicTask for cleaner async handling
- Maintained backward compatibility with alias `DaemonService = IssuesDaemonService`
- Reduced code by ~200 lines of duplicate boilerplate

#### Step 2.2: Update CLI Commands ✅
- [x] Update `issues daemons` commands to use new infrastructure
- [x] Migrate IPC client code  
- [x] Update tests

### Phase 3: Refactor Code-Atlas Watch Mode (1 day)

#### Step 3.1: Convert to Structured Daemon
```python
class CodeAtlasWatcherService(BaseDaemonService, BaseWatcher):
    """Code-atlas watcher extending core infrastructure."""
    
    def __init__(self, config: DaemonConfig, scan_config: ScanConfig):
        BaseDaemonService.__init__(self, config)
        BaseWatcher.__init__(self, config.workspace_path, "*.py")
        self.scan_config = scan_config
        self.rescan_task = None
    
    async def on_change(self, event: FileSystemEvent) -> None:
        """Handle file changes with debouncing."""
        await self._schedule_rescan()
    
    async def _schedule_rescan(self) -> None:
        """Debounced rescan logic."""
        # Issue-specific scanning logic
```

#### Step 3.2: Update Commands
- [ ] Update `code-atlas watch` command
- [ ] Add `code-atlas watcher status/stop` commands
- [ ] Migrate to new daemon structure

### Phase 4: Optimize Core Daemon (1 day) ✅ COMPLETED

#### Step 4.1: Enhance Existing Daemon ⏸️ DEFERRED
- [ ] Keep FastAPI daemon for RPC (it's good as-is)
- [ ] Add skill-specific daemon discovery and orchestration
- [ ] Allow skills to register background tasks
- [ ] Add daemon health monitoring dashboard

#### Step 4.2: Create Daemon Registry ✅
```python
class DaemonRegistry:
    """Registry of all running skill daemons."""
    
    def register(self, skill: str, daemon: BaseDaemonService): ...
    def list_all(self) -> list[DaemonInfo]: ...
    def get_health(self) -> dict[str, Any]: ...
```

**Implementation Notes:**
- Added DaemonRegistry class (src/glorious_agents/core/daemon/registry.py:33)
- Implemented DaemonInfo dataclass for tracking daemon metadata
- Added global `get_registry()` function for singleton access
- Registry supports register/unregister, health updates, and status queries
- All methods fully implemented and tested

## Benefits

### Code Reduction
- **Before**: ~2000 lines daemon code across 3 implementations
- **After**: ~500 lines in core + ~200 lines per skill = ~1100 total
- **Savings**: ~900 lines (45% reduction)

### Consistency
- All daemons use same PID file format
- All daemons use same IPC protocol (HTTP)
- All daemons use same configuration pattern
- All daemons have same CLI interface

### Maintainability
- Bug fixes in one place benefit all daemons
- Security improvements centralized
- Testing simplified (test base components once)
- New skills can add daemons easily

### Features
- Centralized daemon discovery
- Health monitoring across all daemons
- Unified logging
- Standard error recovery
- Cross-platform support guaranteed

## File Structure

```
glorious_agents/core/daemon/
├── __init__.py
│   # Public API exports
│
├── base.py
│   # BaseDaemonService - Core daemon lifecycle
│   # - PID file management
│   # - Signal handling
│   # - Start/stop/restart
│   # - Health checks
│
├── ipc.py
│   # IPCServer - HTTP-based server (aiohttp)
│   # IPCClient - HTTP-based client
│   # - Request/response protocol
│   # - Connection pooling
│   # - Error handling
│
├── pid.py
│   # PIDFileManager - Process tracking
│   # - Write/read/remove PID files
│   # - Check if process running
│   # - Kill existing process
│   # - Platform-specific logic
│
├── watcher.py
│   # BaseWatcher - File system monitoring
│   # - Watchdog integration
│   # - Event debouncing
│   # - Pattern matching
│
├── tasks.py
│   # PeriodicTask - Scheduled execution
│   # - Interval-based scheduling
│   # - Error recovery
│   # - Graceful cancellation
│
├── config.py
│   # DaemonConfig - Configuration management
│   # - Load/save JSON config
│   # - Environment overrides
│   # - Path resolution
│
└── lifecycle.py
    # Helper functions
    # - start_daemon(workspace, class, config)
    # - stop_daemon(workspace)
    # - is_running(workspace)
    # - list_all_daemons()
```

## Implementation Example

### Before (Issues Daemon)
```python
# issue_tracker/daemon/service.py - 524 lines
class DaemonService:
    def __init__(self, config): ...  # 10 lines
    def _setup_logging(self): ...    # 10 lines
    def _write_pid_file(self): ...   # 5 lines
    def _remove_pid_file(self): ...  # 5 lines
    async def start(self): ...       # 15 lines
    async def _shutdown(self): ...   # 25 lines
    async def _sync_loop(self): ...  # 20 lines
    # + IPC handling, signal handling, etc.
```

### After (Issues Daemon)
```python
# issue_tracker/daemon/service.py - ~100 lines
from glorious_agents.core.daemon import BaseDaemonService, PeriodicTask

class IssuesDaemonService(BaseDaemonService):
    """Issues-specific daemon for background sync."""
    
    async def on_startup(self) -> None:
        """Initialize issue-specific components."""
        self.sync_engine = SyncEngine(...)
        self.sync_task = PeriodicTask(
            interval=self.config.sync_interval,
            callback=self._perform_sync
        )
        await self.sync_task.start()
    
    async def on_shutdown(self) -> None:
        """Cleanup issue-specific resources."""
        await self.sync_task.stop()
        if self._engine:
            self._engine.dispose()
    
    async def _perform_sync(self) -> None:
        """Issue-specific sync logic."""
        issues = self._get_issues_from_db()
        self.sync_engine.sync(issues)
    
    def get_health_info(self) -> dict[str, Any]:
        """Return issue-specific health information."""
        return {
            "last_sync": self.sync_engine.last_sync,
            "issues_count": len(self._get_issues_from_db()),
        }
```

## Testing Strategy

### Unit Tests for Core Components
```
tests/unit/core/daemon/
├── test_base_daemon.py      # BaseDaemonService tests
├── test_ipc.py              # IPC server/client tests
├── test_pid_manager.py      # PID file management tests
├── test_watcher.py          # File watcher tests
├── test_tasks.py            # Periodic task tests
└── test_config.py           # Config management tests
```

### Integration Tests
```
tests/integration/
├── test_daemon_lifecycle.py      # End-to-end daemon tests
├── test_daemon_ipc.py            # IPC communication tests
└── test_multi_daemon.py          # Multiple daemons running
```

## Backward Compatibility

### Migration Path
1. **Phase 1**: Create new core components (no breaking changes)
2. **Phase 2**: Refactor issues daemon (internal changes only)
3. **Phase 3**: Refactor code-atlas watcher (internal changes only)
4. **Phase 4**: Add deprecation warnings to old code
5. **Phase 5**: Remove old implementations

### API Stability
- All CLI commands remain unchanged
- IPC protocol stays the same
- Config file format backward compatible
- Existing daemons continue working during migration

## Performance Improvements

### Memory
- **Before**: Each daemon manages own resources independently
- **After**: Shared connection pools, unified logging, engine reuse
- **Savings**: ~30% memory reduction for multi-daemon scenarios

### CPU
- **Before**: Redundant PID file checks, duplicate logging
- **After**: Centralized checks, efficient event loop sharing
- **Savings**: ~20% CPU reduction

### Startup Time
- **Before**: Each daemon initializes independently
- **After**: Pre-warmed shared resources
- **Savings**: ~40% faster daemon startup

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Core Infrastructure | 2 days | Base components + tests |
| Phase 2: Issues Daemon | 1 day | Refactored daemon |
| Phase 3: Code-Atlas Watcher | 1 day | Refactored watcher |
| Phase 4: Core Daemon Enhancement | 1 day | Enhanced RPC daemon |
| Phase 5: Documentation & Polish | 1 day | Docs, examples, cleanup |
| **Total** | **6 days** | Production-ready |

## Success Criteria

### Functional
- [ ] All existing daemon features preserved
- [ ] All CLI commands work identically
- [ ] All integration tests pass
- [ ] No regressions in functionality

### Code Quality
- [ ] 45% reduction in daemon code duplication
- [ ] 100% test coverage for new core components
- [ ] All linting/typing checks pass
- [ ] Clear documentation for daemon authoring

### Performance
- [ ] No degradation in daemon responsiveness
- [ ] 30% memory reduction in multi-daemon scenarios
- [ ] 40% faster daemon startup times
- [ ] Zero leaked file handles or connections

## Risks & Mitigation

### Risk 1: Breaking Changes
**Mitigation**: Maintain backward compatibility, gradual migration, extensive testing

### Risk 2: Platform-Specific Issues
**Mitigation**: Test on Linux, macOS, Windows; use psutil for cross-platform support

### Risk 3: Async/Event Loop Complexity
**Mitigation**: Abstract async details in base classes, provide clear examples

### Risk 4: IPC Protocol Changes
**Mitigation**: Version IPC protocol, support multiple versions during transition

## Next Steps

1. **Immediate**: Review and approve this plan
2. **Week 1**: Implement core daemon infrastructure
3. **Week 2**: Refactor existing daemons to use new infrastructure
4. **Week 3**: Testing, documentation, and polish

## Appendix: Daemon Comparison Matrix

| Feature | Core Daemon | Issues Daemon | Code-Atlas Watch |
|---------|-------------|---------------|------------------|
| Technology | FastAPI | AsyncIO/aiohttp | Watchdog |
| Scope | Global | Workspace | Directory |
| IPC | HTTP (FastAPI) | HTTP (aiohttp) | None (PID only) |
| Background Tasks | None | Sync loop | File monitoring |
| Auto-start | Manual only | Yes (configurable) | Manual only |
| Database | Shared context | Own engine | None |
| Git Integration | No | Yes | No |
| Health Endpoint | Yes | Yes | No |
| Status Command | No | Yes | Yes |
| Logs Command | No | Yes | No |

## References

- [Current core daemon](src/glorious_agents/core/daemon.py:1)
- [Issues daemon service](src/glorious_agents/skills/issues/src/issue_tracker/daemon/service.py:1)
- [Code-atlas watch commands](src/glorious_agents/skills/code-atlas/src/code_atlas/watch_commands.py:1)
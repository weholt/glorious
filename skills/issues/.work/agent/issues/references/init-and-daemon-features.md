# Initialization and Daemon Features Reference

Based on Beads QUICKSTART.md and DAEMON.md documentation.

## Initialization Features

### `issues init` Command

Initializes a new issue tracking workspace with configuration wizard.

**Modes:**

1. **Basic Mode** - `issues init`
   - Creates `.issues/` directory
   - Initializes SQLite database
   - Sets up default configuration
   - Auto-starts daemon

2. **Team Mode** - `issues init --team`
   - Branch workflow for collaboration
   - Shared repository with team members
   - Git hooks for sync
   - NOTE! This is not part of the initial implementation.

3. **Contributor Mode** - `issues init --contributor` (SKIP - GitHub integration)
   - Fork workflow with separate planning repo
   - OSS contributor setup
   - Not needed for current scope
   - NOTE! This is not part of the initial implementation.

**Setup Tasks:**

- Create `.issues/` directory structure
- Initialize SQLite database (`issues.db`)
- Import existing issues from git (if any)
- Prompt to install git hooks (recommended)
- Prompt to configure git merge driver (recommended)
- Auto-start daemon for continuous sync
- Create configuration file (`.issues/config.json`)

**Configuration Structure:**

```json
{
  "database_path": ".issues/issues.db",
  "issue_prefix": "issue",
  "daemon_mode": "poll",
  "auto_start_daemon": true,
  "sync_enabled": true,
  "sync_interval_seconds": 5,
  "export_path": ".issues/issues.jsonl",
  "git_integration": true
}
```

---

## Daemon Features

### Architecture

**Per-Workspace Model (LSP-style):**

```
MCP Server (one instance)
    ↓
Per-Project Daemons (one per workspace)
    ↓
SQLite Databases (complete isolation)
```

**Each workspace gets:**

- Socket at `.issues/issues.sock` (`.issues/issues.pipe` on Windows)
- Auto-starts on first command (unless disabled)
- Handles auto-sync, batching, background operations
- Complete database isolation (no cross-project pollution)

### Daemon Commands

#### 1. `issues daemons list` - List all running daemons

**Output (JSON):**

```json
[
  {
    "workspace": "/path/to/project",
    "pid": 12345,
    "socket": "/path/to/project/.issues/issues.sock",
    "version": "1.0.0",
    "uptime_seconds": 3600
  }
]
```

#### 2. `issues daemons health` - Check daemon health

**Checks:**

- Version mismatches between CLI and daemon
- Stale sockets
- Resource usage

**Output (JSON):**

```json
{
  "healthy": true,
  "issues": []
}
```

#### 3. `issues daemons stop` - Stop daemon

**Syntax:**

```bash
issues daemons stop /path/to/workspace
issues daemons stop <pid>
```

#### 4. `issues daemons restart` - Restart daemon

**Syntax:**

```bash
issues daemons restart /path/to/workspace
issues daemons restart <pid>
```

#### 5. `issues daemons killall` - Stop all daemons

**Syntax:**

```bash
issues daemons killall
issues daemons killall --force  # Force kill if graceful fails
```

#### 6. `issues daemons logs` - View daemon logs

**Syntax:**

```bash
issues daemons logs /path/to/workspace -n 100
issues daemons logs <pid> -f  # Follow mode (tail -f style)
```

**Log Patterns:**

- `[INFO] Auto-sync: export complete` - Successful JSONL export
- `[WARN] Git push failed: ...` - Push error (auto-retry)
- `[ERROR] Version mismatch` - Daemon/CLI version out of sync

### Daemon Operation Modes

#### 1. Polling Mode (Default)

- Traditional 5-second polling
- Stable and battle-tested
- ~2-3% CPU usage (continuous)
- ~30MB memory
- ~5000ms sync latency

**Enable:**

```bash
export ISSUES_DAEMON_MODE=poll
```

#### 2. Event-Driven Mode (Experimental)

- File watcher for instant reactivity
- <500ms sync latency
- ~0.5% CPU usage (idle)
- ~35MB memory (+5MB for watcher)

**Architecture:**

```
FileWatcher (platform-native)
    ├─ .issues/issues.jsonl (file changes)
    ├─ .git/refs/heads (git updates)
    └─ RPC mutations (create, update, close)
         ↓
    Debouncer (500ms batch window)
         ↓
    Export → Git Commit/Push
```

**Platform-native APIs:**

- Linux: `inotify`
- macOS: `FSEvents` (via kqueue)
- Windows: `ReadDirectoryChangesW`

**Enable:**

```bash
export ISSUES_DAEMON_MODE=events
export ISSUES_WATCHER_FALLBACK=true  # Fall back to polling if fsnotify fails
```

### Daemon Configuration

**Environment Variables:**

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| ISSUES_AUTO_START_DAEMON | true, false | true | Auto-start daemon on commands |
| ISSUES_DAEMON_MODE | poll, events | poll | Sync mode (polling vs events) |
| ISSUES_WATCHER_FALLBACK | true, false | true | Fall back to poll if events fail |
| ISSUES_NO_DAEMON | true, false | false | Disable daemon entirely (direct DB) |

### Auto-Start Behavior

**Default:** Daemon auto-starts on first `issues` command

```bash
issues ready  # Daemon starts automatically if not running
```

**Disable auto-start:**

```bash
export ISSUES_AUTO_START_DAEMON=false
issues daemon start  # Manual start required
```

**Auto-start with exponential backoff:**

- 1st attempt: immediate
- 2nd attempt: 100ms delay
- 3rd attempt: 200ms delay
- Max retries: 5

### Sync Operations

The daemon handles:

1. **Export to JSONL** - Exports pending changes to `.issues/issues.jsonl`
2. **Git commit** - Commits JSONL changes
3. **Git pull** - Pulls remote changes
4. **Import from JSONL** - Imports updates from remote
5. **Git push** - Pushes local changes

**Manual Sync:**

```bash
issues sync  # Force immediate sync, bypass debounce
```

**When to use:**

- End of agent sessions (ensure changes are committed/pushed immediately)
- Before critical operations
- After batch operations

### Common Issues & Solutions

#### Stale Sockets

**Symptoms:** `issues ready` shows "daemon not responding"

**Solutions:**

```bash
issues daemons list  # Auto-cleanup on next command
rm .issues/issues.sock  # Manual cleanup
issues ready  # Auto-starts fresh daemon
```

#### Version Mismatch

**Symptoms:** `issues ready` shows "version mismatch" error

**Solutions:**

```bash
issues version  # Check CLI version
issues daemons health --json  # Check daemon versions
issues daemons killall  # Restart all daemons
issues ready  # Auto-starts with CLI version
```

#### Daemon Won't Stop

**Solutions:**

```bash
issues daemons killall --force  # Force kill
pkill -9 issues  # Nuclear option (all processes)
rm .issues/issues.sock  # Clean up socket
```

#### Memory Leaks

**Expected memory usage:**

- Baseline: ~30MB
- With watcher: ~35MB
- Per issue: ~500 bytes (10K issues = ~5MB)

**Solutions:**

```bash
ps aux | grep "issues daemon"  # Check current memory usage
issues daemons restart .  # Restart daemon
issues daemons logs . -n 200 | grep -i "memory\|leak\|oom"  # Check logs
```

### Multi-Workspace Best Practices

**When managing multiple projects:**

```bash
issues daemons list --json  # Check all daemons
issues daemons stop /path/to/old-project  # Stop unused workspaces
issues daemons health --json  # Health check before critical work
issues daemons killall  # Clean restart after major upgrades
```

**Resource limits:**

- Each daemon: ~30-35MB memory
- 10 workspaces: ~300-350MB total
- CPU: <1% per daemon (idle), 2-3% (active sync)
- File descriptors: ~10 per daemon

**When to disable daemons:**

- ✅ Git worktrees (use `--no-daemon`)
- ✅ Embedded/resource-constrained environments
- ✅ Testing/CI (deterministic execution)
- ✅ Offline work (no git push available)

### Exclusive Lock Protocol (Advanced)

For external tools that need full database control (e.g., CI/CD, deterministic execution).

**When `.issues/.exclusive-lock` file exists:**

- Daemon skips all operations for the locked database
- External tool has complete control over git sync and database
- Stale locks (dead process) auto-cleaned

**Lock file format (JSON):**

```json
{
  "holder": "my-tool",
  "pid": 12345,
  "hostname": "build-server",
  "started_at": "2025-11-08T08:00:00Z",
  "version": "1.0.0"
}
```

**Example usage:**

```bash
# Create lock
echo '{"holder":"my-tool","pid":'$$',"hostname":"'$(hostname)'","started_at":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","version":"1.0.0"}' > .issues/.exclusive-lock

# Do work (daemon won't interfere)
issues create "My issue" -p 1

# Release lock
rm .issues/.exclusive-lock
```

**Use cases:**

- VibeCoder (deterministic execution)
- CI/CD pipelines (controlled sync timing)
- Testing frameworks (isolated test runs)

---

## Implementation Notes

### Key Differences from Beads

1. **CLI Name:** `issues` instead of `bd`
2. **Directory:** `.issues/` instead of `.beads/`
3. **Socket:** `.issues/issues.sock` instead of `.beads/bd.sock`
4. **Database:** `issues.db` instead of `beads.db`
5. **Skip GitHub Integration:** No `--contributor` mode for now
6. **Skip Agent Mail:** Not in scope for MVP

### Architecture Components

**Daemon Service:**

- Background process running per workspace
- Unix socket or Windows named pipe for IPC
- Event loop for handling sync operations
- File watcher integration (optional, event-driven mode)
- Logging to `.issues/daemon.log`

**Sync Engine:**

- Export database changes to JSONL
- Git operations (commit, pull, push)
- Import JSONL changes to database
- Conflict resolution
- Debouncing for batch operations

**Configuration Management:**

- Read from `.issues/config.json`
- Environment variable overrides
- Default values for missing config
- Validation on load

**Socket Communication:**

- JSON-RPC protocol for CLI ↔ daemon communication
- Request/response pattern
- Health check endpoint
- Shutdown/restart endpoints

### Testing Strategy

**Unit Tests:**

- Configuration loading/validation
- Sync engine logic (export, import, conflict resolution)
- Daemon lifecycle management
- File watcher event handling

**Integration Tests:**

- Daemon start/stop/restart
- Socket communication
- Multi-workspace scenarios
- Git integration
- File watcher reactivity

**End-to-End Tests:**

- Full initialization flow
- Continuous sync scenarios
- Daemon health monitoring
- Error recovery (stale sockets, crashes)
- Version mismatch handling

---

## Priority Classification

### Critical (Group 5 - Must Have for MVP)

1. **Init command** - Basic mode only
2. **Daemon start/stop** - Manual control
3. **Polling mode sync** - 5-second interval
4. **Socket communication** - JSON-RPC protocol
5. **Auto-start daemon** - On first command
6. **Sync command** - Manual sync trigger

### High (Group 6 - Important for Usability)

1. **Daemons list** - Show all running daemons
2. **Daemons health** - Check status
3. **Daemons killall** - Stop all daemons
4. **Daemon logs** - View logs with follow mode
5. **Configuration file** - `.issues/config.json`
6. **Git integration** - Export/import JSONL

### Medium (Future Enhancement)

1. **Event-driven mode** - File watcher reactivity
2. **Team mode init** - Branch workflow
3. **Exclusive lock** - External tool integration
4. **Version management** - Automatic mismatch handling
5. **Multi-workspace management** - Advanced daemon control

### Low (Nice to Have)

1. **Agent Mail integration** - Multi-agent coordination
2. **Contributor mode** - Fork workflow with GitHub
3. **Custom merge drivers** - Git conflict resolution
4. **Advanced logging** - Structured logging with filters

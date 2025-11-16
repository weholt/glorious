# Issue Tracker CLI Specification

**CLI Name:** `issues`  
**Based on:** Beads CLI Reference + Reference Implementation  
**Version:** 1.0.0  
**Target Coverage:** 70%+ test coverage

---

## Core Principles

1. **CLI Name:** All commands use `issues` as the base command
2. **JSON Output:** All commands support `--json` flag for programmatic use
3. **Batch Operations:** Multi-ID support where applicable
4. **Error Handling:** Best-effort execution with detailed error messages
5. **Rich Terminal:** Human-readable output with colors and tables (default)

---

## Command Inventory

### Phase 1: Core Issue Management (MVP)

#### 1. `issues create` - Create new issue

**Syntax:**
```bash
issues create <title> [OPTIONS]
```

**Required:**

- `<title>` - Issue title (string, quoted if spaces/special chars)

**Options:**

- `-t, --type <TYPE>` - Issue type: bug|feature|task|epic|chore (default: task)
- `-p, --priority <0-4>` - Priority level: 0=critical, 1=high, 2=medium, 3=low, 4=backlog (default: 2)
- `-d, --description <TEXT>` - Description text
- `-a, --assignee <NAME>` - Assignee username
- `-l, --label <LABELS>` - Comma-separated labels (e.g., bug,critical)
- `--labels <LABELS>` - Alias for --label
- `--id <ID>` - Custom issue ID (for parallel workers)
- `--deps <TYPE>:<ID>` - Create with dependency (e.g., discovered-from:bd-100)
- `-f, --file <PATH>` - Create from markdown file (bulk mode)
- `--json` - JSON output

**Examples:**
```bash
issues create "Fix auth bug" -t bug -p 1
issues create "Add OAuth" -d "Implement RFC 6749" --json
issues create "Epic task" -t epic -p 1 --label milestone,v2
issues create "Found bug" --deps discovered-from:issue-123 --json
issues create -f issues.md --json
```

**Output (JSON):**
```json
{
  "id": "issue-a3f8e9",
  "title": "Fix auth bug",
  "type": "bug",
  "priority": 1,
  "status": "open",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Tests:**

- Create with minimal args
- Create with all fields
- Create with custom ID
- Create with dependencies
- Bulk create from file
- Invalid type/priority validation
- Special characters in title

---

#### 2. `issues list` - List issues with filters

**Syntax:**
```bash
issues list [OPTIONS]
```

**Filters:**

- `--status <STATUS>` - Filter by status (open|in_progress|blocked|resolved|closed|archived)
- `--priority <0-4>` - Filter by priority
- `--priority-min <0-4>` - Minimum priority
- `--priority-max <0-4>` - Maximum priority
- `--type <TYPE>` - Filter by type
- `--assignee <NAME>` - Filter by assignee
- `--no-assignee` - Unassigned issues only
- `--label <LABELS>` - Labels (AND logic - must have ALL)
- `--label-any <LABELS>` - Labels (OR logic - has ANY)
- `--no-labels` - Issues with no labels
- `--epic <ID>` - Filter by epic
- `--parent <ID>` - Filter by parent issue
- `--title <TEXT>` - Substring search in title
- `--title-contains <TEXT>` - Alias for --title
- `--desc-contains <TEXT>` - Search in description
- `--notes-contains <TEXT>` - Search in notes
- `--empty-description` - Issues with no description
- `--created-after <DATE>` - Created after date (YYYY-MM-DD)
- `--created-before <DATE>` - Created before date
- `--updated-after <DATE>` - Updated after date
- `--updated-before <DATE>` - Updated before date
- `--closed-after <DATE>` - Closed after date
- `--closed-before <DATE>` - Closed before date
- `--has-blockers` - Issues with blockers
- `--no-blockers` - Issues without blockers
- `--id <IDS>` - Filter by specific IDs (comma-separated)
- `--limit <N>` - Limit results (default: no limit)
- `--json` - JSON output

**Examples:**
```bash
issues list --status open --priority 1
issues list --label bug,critical --json
issues list --label-any frontend,backend
issues list --title "auth" --no-assignee
issues list --created-after 2024-01-01 --priority-max 1
```

**Output (JSON):**
```json
[
  {
    "id": "issue-123",
    "title": "Fix auth bug",
    "type": "bug",
    "priority": 1,
    "status": "open",
    "assignee": null,
    "labels": ["bug", "critical"],
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

**Tests:**

- Each filter individually
- Multiple filter combinations
- Date range filters
- Empty/null checks
- Priority ranges
- Label AND/OR logic
- Text search
- Pagination

---

#### 3. `issues show` - Show issue details

**Syntax:**
```bash
issues show <id> [<id>...] [OPTIONS]
```

**Arguments:**

- `<id>` - One or more issue IDs

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues show issue-123
issues show issue-123 issue-456 --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "title": "Fix auth bug",
  "description": "Authentication tokens not validated",
  "type": "bug",
  "priority": 1,
  "status": "open",
  "assignee": "alice",
  "labels": ["bug", "critical"],
  "epic_id": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "closed_at": null,
  "dependencies": [],
  "dependents": []
}
```

**Tests:**

- Show single issue
- Show multiple issues
- Non-existent issue handling
- JSON output validation

---

#### 4. `issues update` - Update issue fields

**Syntax:**
```bash
issues update <id> [<id>...] [OPTIONS]
```

**Arguments:**

- `<id>` - One or more issue IDs

**Options:**

- `--title <TEXT>` - Update title
- `--description <TEXT>` - Update description
- `--priority <0-4>` - Update priority
- `--assignee <NAME>` - Update assignee
- `--status <STATUS>` - Update status (use with caution - prefer close/reopen)
- `--json` - JSON output

**Examples:**
```bash
issues update issue-123 --priority 0
issues update issue-123 issue-456 --assignee alice --json
issues update issue-123 --title "Fix critical auth bug"
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "updated_fields": ["priority"],
  "priority": 0
}
```

**Tests:**

- Update single field
- Update multiple fields
- Batch update multiple issues
- Invalid priority validation
- Non-existent issue handling

---

#### 5. `issues close` - Close issues

**Syntax:**
```bash
issues close <id> [<id>...] [OPTIONS]
```

**Arguments:**

- `<id>` - One or more issue IDs

**Options:**

- `--reason <TEXT>` - Closure reason (optional)
- `--json` - JSON output

**Examples:**
```bash
issues close issue-123 --reason "Fixed in PR #42"
issues close issue-123 issue-456 --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "status": "closed",
  "closed_at": "2024-01-15T14:30:00Z",
  "reason": "Fixed in PR #42"
}
```

**Tests:**

- Close single issue
- Batch close multiple issues
- Close with reason
- Already closed issue handling

---

#### 6. `issues reopen` - Reopen closed issues

**Syntax:**
```bash
issues reopen <id> [<id>...] [OPTIONS]
```

**Arguments:**

- `<id>` - One or more issue IDs

**Options:**

- `--reason <TEXT>` - Reopen reason (optional)
- `--json` - JSON output

**Examples:**
```bash
issues reopen issue-123 --reason "Bug still present"
issues reopen issue-123 issue-456 --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "status": "open",
  "reopened_at": "2024-01-16T09:00:00Z",
  "reason": "Bug still present"
}
```

**Tests:**

- Reopen single issue
- Batch reopen multiple issues
- Reopen with reason
- Already open issue handling

---

### Phase 2: Label Management

#### 7. `issues label add` - Add labels to issues

**Syntax:**
```bash
issues label add <id> [<id>...] <label> [OPTIONS]
```

**Arguments:**

- `<id>` - One or more issue IDs
- `<label>` - Label name (single label per command)

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues label add issue-123 urgent
issues label add issue-123 issue-456 critical --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "labels": ["bug", "urgent"]
}
```

**Tests:**

- Add single label
- Batch add to multiple issues
- Duplicate label handling
- Non-existent issue handling

---

#### 8. `issues label remove` - Remove labels from issues

**Syntax:**
```bash
issues label remove <id> [<id>...] <label> [OPTIONS]
```

**Arguments:**

- `<id>` - One or more issue IDs
- `<label>` - Label name

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues label remove issue-123 urgent
issues label remove issue-123 issue-456 critical --json
```

**Tests:**

- Remove single label
- Batch remove from multiple issues
- Non-existent label handling

---

#### 9. `issues label list` - List labels for issue

**Syntax:**
```bash
issues label list <id> [OPTIONS]
```

**Arguments:**

- `<id>` - Issue ID

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues label list issue-123
issues label list issue-123 --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "labels": ["bug", "urgent", "critical"]
}
```

---

#### 10. `issues label list-all` - Show global label usage

**Syntax:**
```bash
issues label list-all [OPTIONS]
```

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues label list-all
issues label list-all --json
```

**Output (JSON):**
```json
[
  {"label": "bug", "count": 42},
  {"label": "feature", "count": 28},
  {"label": "critical", "count": 5}
]
```

**Tests:**

- Empty project
- Project with labels
- Count accuracy

---

### Phase 3: Dependency Management

#### 11. `issues dep add` - Add dependency

**Syntax:**
```bash
issues dep add <from_id> <to_id> [OPTIONS]
```

**Arguments:**

- `<from_id>` - Dependent issue ID (this issue depends on to_id)
- `<to_id>` - Dependency issue ID (to_id blocks from_id)

**Options:**

- `--type <TYPE>` - Dependency type: blocks|related|parent-child|discovered-from (default: blocks)
- `--json` - JSON output

**Examples:**
```bash
issues dep add issue-123 issue-456
issues dep add issue-123 issue-456 --type discovered-from --json
```

**Output (JSON):**
```json
{
  "from": "issue-123",
  "to": "issue-456",
  "type": "blocks",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Tests:**

- Add blocking dependency
- Add each dependency type
- Cycle detection (should fail)
- Non-existent issue handling
- Self-dependency prevention

---

#### 12. `issues dep remove` - Remove dependency

**Syntax:**
```bash
issues dep remove <from_id> <to_id> [OPTIONS]
```

**Arguments:**

- `<from_id>` - Dependent issue ID
- `<to_id>` - Dependency issue ID

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues dep remove issue-123 issue-456
issues dep remove issue-123 issue-456 --json
```

**Output (JSON):**
```json
{
  "from": "issue-123",
  "to": "issue-456",
  "removed": true
}
```

**Tests:**

- Remove existing dependency
- Non-existent dependency handling
- Non-existent issue handling

---

#### 13. `issues dep tree` - Show dependency tree

**Syntax:**
```bash
issues dep tree <id> [OPTIONS]
```

**Arguments:**

- `<id>` - Root issue ID

**Options:**

- `--format <FORMAT>` - Output format: text|mermaid|json (default: text)
- `--max-depth <N>` - Maximum depth to traverse (default: unlimited)
- `--json` - JSON output (implies --format json)

**Examples:**
```bash
issues dep tree issue-123
issues dep tree issue-123 --format mermaid
issues dep tree issue-123 --format json --max-depth 3
```

**Output (text):**
```
issue-123: Fix auth bug
├── issue-456: Update JWT library
│   └── issue-789: Research JWT vulnerabilities
└── issue-101: Write tests
```

**Output (mermaid):**
```
graph TD
  issue-123[Fix auth bug]
  issue-456[Update JWT library]
  issue-789[Research JWT vulnerabilities]
  issue-123 --> issue-456
  issue-456 --> issue-789
```

**Output (json):**
```json
{
  "root": "issue-123",
  "tree": {
    "id": "issue-123",
    "title": "Fix auth bug",
    "children": [
      {
        "id": "issue-456",
        "title": "Update JWT library",
        "children": [
          {"id": "issue-789", "title": "Research JWT vulnerabilities", "children": []}
        ]
      }
    ]
  }
}
```

**Tests:**

- Single issue (no dependencies)
- Simple tree (2-3 levels)
- Deep tree with max-depth
- All output formats
- Cyclic graph handling

---

#### 14. `issues cycles` - Detect dependency cycles

**Syntax:**
```bash
issues cycles [OPTIONS]
```

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues cycles
issues cycles --json
```

**Output (JSON):**
```json
{
  "cycles_found": 1,
  "cycles": [
    ["issue-123", "issue-456", "issue-789", "issue-123"]
  ]
}
```

**Tests:**

- No cycles
- Single cycle
- Multiple cycles
- Self-referencing issue

---

### Phase 4: Work Management

#### 15. `issues ready` - Show ready work queue

**Syntax:**
```bash
issues ready [OPTIONS]
```

**Options:**

- `--sort <POLICY>` - Sort by: priority|created|updated (default: priority)
- `--json` - JSON output

**Examples:**
```bash
issues ready
issues ready --sort created --json
```

**Output (JSON):**
```json
[
  {
    "id": "issue-123",
    "title": "Fix auth bug",
    "priority": 1,
    "status": "open",
    "blockers": []
  }
]
```

**Tests:**

- Empty queue
- Queue with issues
- Blocked issues excluded
- Sort policies

---

#### 16. `issues blocked` - Show blocked issues

**Syntax:**
```bash
issues blocked [OPTIONS]
```

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues blocked
issues blocked --json
```

**Output (JSON):**
```json
[
  {
    "id": "issue-123",
    "title": "Deploy to production",
    "priority": 0,
    "blockers": [
      {"id": "issue-456", "title": "Fix security bug", "status": "in_progress"}
    ]
  }
]
```

**Tests:**

- No blocked issues
- Issues with single blocker
- Issues with multiple blockers
- Blocker details accuracy

---

#### 17. `issues stale` - Find stale issues

**Syntax:**
```bash
issues stale [OPTIONS]
```

**Options:**

- `--days <N>` - Days without update (default: 30)
- `--status <STATUS>` - Filter by status
- `--limit <N>` - Limit results
- `--json` - JSON output

**Examples:**
```bash
issues stale --days 90
issues stale --days 30 --status in_progress --json
issues stale --limit 10
```

**Output (JSON):**
```json
[
  {
    "id": "issue-123",
    "title": "Old feature request",
    "status": "open",
    "updated_at": "2023-06-01T10:00:00Z",
    "days_stale": 195
  }
]
```

**Tests:**

- No stale issues
- Stale issues with various ages
- Status filter
- Days threshold
- Limit parameter

---

### Phase 5: Epic Management

#### 18. `issues epic set` - Assign issue to epic

**Syntax:**
```bash
issues epic set <issue_id> <epic_id> [OPTIONS]
```

**Arguments:**

- `<issue_id>` - Issue to assign
- `<epic_id>` - Epic to assign to

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues epic set issue-123 epic-456
issues epic set issue-123 epic-456 --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "epic_id": "epic-456"
}
```

**Tests:**

- Assign to valid epic
- Non-existent epic handling
- Non-existent issue handling
- Epic type validation

---

#### 19. `issues epic clear` - Remove issue from epic

**Syntax:**
```bash
issues epic clear <issue_id> [OPTIONS]
```

**Arguments:**

- `<issue_id>` - Issue to clear epic from

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues epic clear issue-123
issues epic clear issue-123 --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "epic_id": null
}
```

**Tests:**

- Clear existing epic
- Already unassigned issue

---

### Phase 6: Comments

#### 20. `issues comment add` - Add comment to issue

**Syntax:**
```bash
issues comment add <id> <text> [OPTIONS]
```

**Arguments:**

- `<id>` - Issue ID
- `<text>` - Comment text

**Options:**

- `--author <NAME>` - Comment author (optional)
- `--json` - JSON output

**Examples:**
```bash
issues comment add issue-123 "Working on fix"
issues comment add issue-123 "PR ready for review" --author alice --json
```

**Output (JSON):**
```json
{
  "comment_id": "comment-abc123",
  "issue_id": "issue-123",
  "text": "Working on fix",
  "author": "alice",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Tests:**

- Add comment with/without author
- Empty comment validation
- Non-existent issue handling

---

#### 21. `issues comment list` - List comments for issue

**Syntax:**
```bash
issues comment list <id> [OPTIONS]
```

**Arguments:**

- `<id>` - Issue ID

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues comment list issue-123
issues comment list issue-123 --json
```

**Output (JSON):**
```json
[
  {
    "comment_id": "comment-abc123",
    "text": "Working on fix",
    "author": "alice",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

**Tests:**

- No comments
- Multiple comments
- Comment ordering (chronological)

---

### Phase 7: Statistics & Utilities

#### 22. `issues stats` - Show project statistics

**Syntax:**
```bash
issues stats [OPTIONS]
```

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues stats
issues stats --json
```

**Output (JSON):**
```json
{
  "total": 150,
  "by_status": {
    "open": 45,
    "in_progress": 20,
    "blocked": 5,
    "resolved": 10,
    "closed": 70,
    "archived": 0
  },
  "by_priority": {
    "0": 2,
    "1": 15,
    "2": 50,
    "3": 60,
    "4": 23
  },
  "completion_rate": 0.467
}
```

**Tests:**

- Empty project
- Project with issues
- Calculation accuracy

---

#### 23. `issues restore` - Restore archived issues

**Syntax:**
```bash
issues restore <id> [<id>...] [OPTIONS]
```

**Arguments:**

- `<id>` - One or more issue IDs

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues restore issue-123
issues restore issue-123 issue-456 --json
```

**Output (JSON):**
```json
{
  "id": "issue-123",
  "status": "open",
  "restored_at": "2024-01-15T10:30:00Z"
}
```

**Tests:**

- Restore single archived issue
- Batch restore
- Non-archived issue handling

---

#### 24. `issues bulk-create` - Create issues from markdown file

**Syntax:**
```bash
issues bulk-create -f <file> [OPTIONS]
```

**Options:**

- `-f, --file <PATH>` - Markdown file with issues
- `--json` - JSON output

**File Format:**
```markdown
# Issue Title 1
Type: bug
Priority: 1
Description: Fix authentication

# Issue Title 2
Type: feature
Priority: 2
Description: Add OAuth support
```

**Examples:**
```bash
issues bulk-create -f issues.md
issues bulk-create -f backlog.md --json
```

**Output (JSON):**
```json
{
  "created": 2,
  "issues": [
    {"id": "issue-123", "title": "Issue Title 1"},
    {"id": "issue-456", "title": "Issue Title 2"}
  ]
}
```

**Tests:**

- Valid markdown file
- Empty file
- Invalid format
- Partial success handling

---

### Phase 8: Advanced Features (FUTURE - Not MVP)

#### 25. `issues info` - Database introspection

**Syntax:**
```bash
issues info [OPTIONS]
```

**Options:**

- `--json` - JSON output

**Examples:**
```bash
issues info
issues info --json
```

**Output (JSON):**
```json
{
  "database_path": "/path/to/issue_tracker.db",
  "total_issues": 150,
  "last_updated": "2024-01-15T14:30:00Z"
}
```

**Tests:**

- Database exists
- Database doesn't exist

---

#### 26. `issues cleanup` - Bulk delete closed issues

**Syntax:**
```bash
issues cleanup [OPTIONS]
```

**Options:**

- `--older-than <DAYS>` - Delete issues closed more than N days ago
- `--force` - Confirm deletion without prompt
- `--dry-run` - Preview what would be deleted
- `--cascade` - Delete dependents too
- `--json` - JSON output

**Examples:**
```bash
issues cleanup --older-than 90 --dry-run
issues cleanup --older-than 90 --force --json
```

**Output (JSON):**
```json
{
  "deleted": 42,
  "issues": ["issue-123", "issue-456"]
}
```

**Tests:**

- Dry-run mode
- Force deletion
- Older-than filter
- Cascade deletion

---

## Data Model

### Issue Entity

```python
@dataclass(frozen=True)
class Issue:
    id: Identifier
    title: str
    description: str | None
    issue_type: IssueType
    priority: IssuePriority
    status: IssueStatus
    assignee: str | None
    labels: list[str]
    epic_id: Identifier | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
```

### Enums

```python
class IssueType(StrEnum):
    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"

class IssuePriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKLOG = 4

class IssueStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ARCHIVED = "archived"

class DependencyType(StrEnum):
    BLOCKS = "blocks"
    RELATED = "related"
    PARENT_CHILD = "parent-child"
    DISCOVERED_FROM = "discovered-from"
```

---

## Test Coverage Requirements

### Unit Tests (70%+ coverage)

**Domain Layer:**

- Entity validation
- State transitions
- Label operations
- Value object parsing

**Service Layer:**

- Issue CRUD operations
- Graph algorithms (cycle detection, BFS)
- Statistics calculations
- Filtering logic

### Integration Tests

**CLI Commands:**

- All 24 commands end-to-end
- JSON output validation
- Batch operations
- Error scenarios

**Repository Layer:**

- Database CRUD
- Query filtering
- Transaction handling
- Constraint violations

### Test Utilities

- Test fixtures for entities
- Mock repositories
- Database setup/teardown
- CLI command runners

---

## Error Handling

### Error Types

1. **EntityNotFoundError** - Issue/label/epic not found
2. **InvariantViolationError** - Validation failure
3. **InvalidTransitionError** - Invalid status transition
4. **CycleDetectedError** - Dependency cycle
5. **DatabaseError** - Connection/query failures

### Error Output (JSON)

```json
{
  "error": "EntityNotFoundError",
  "message": "Issue not found: issue-123",
  "code": 404
}
```

---

## Implementation Priority

### Phase 1: MVP (20 commands)

Extract from reference implementation:

1. create, list, show, update, close, reopen
2. label add/remove/list/list-all
3. dep add/tree, cycles
4. ready, blocked, stale
5. epic set/clear
6. comment add/list
7. stats, restore, bulk-create

### Phase 2: Critical Gaps (2 commands)

Implement new:

1. dep remove (CRUD completion)
2. info (introspection)

### Phase 3: Initialization & Daemon (11 commands)

Core infrastructure:

1. init (workspace initialization)
2. sync (manual sync trigger)
3. daemons list (show all daemons)
4. daemons health (check status)
5. daemons stop (stop daemon)
6. daemons restart (restart daemon)
7. daemons killall (stop all)
8. daemons logs (view logs)

### Phase 4: Nice-to-Have (FUTURE)

1. cleanup (bulk operations)
2. import (data migration)
3. Event-driven mode (file watcher)
4. Agent Mail integration

---

## Command Reference

### Initialization Commands

#### 27. `issues init` - Initialize workspace

**Syntax:**
```bash
issues init [OPTIONS]
```

**Options:**
- `--team` - Branch workflow for team collaboration
- `--json` - JSON output

**Examples:**
```bash
issues init  # Basic initialization
issues init --team  # Team workflow
```

**Output (JSON):**
```json
{
  "workspace": "/path/to/project",
  "database": ".issues/issues.db",
  "config": ".issues/config.json",
  "daemon_started": true
}
```

**Wizard Steps:**
1. Create `.issues/` directory
2. Initialize database
3. Create configuration file
4. Prompt for git hooks (optional)
5. Auto-start daemon

**Tests:**
- Initialize new workspace
- Reinitialize existing workspace (error)
- Team mode initialization
- Configuration validation

---

#### 28. `issues sync` - Manual sync trigger

**Syntax:**
```bash
issues sync [OPTIONS]
```

**Options:**
- `--json` - JSON output

**Examples:**
```bash
issues sync
issues sync --json
```

**Output (JSON):**
```json
{
  "exported": 5,
  "imported": 2,
  "committed": true,
  "pushed": true,
  "duration_ms": 450
}
```

**Use Cases:**
- End of agent sessions
- Before critical operations
- After batch operations

**Tests:**
- Manual sync with changes
- Sync with no changes
- Sync with conflicts
- Offline mode handling

---

### Daemon Management Commands

#### 29. `issues daemons list` - List all daemons

**Syntax:**
```bash
issues daemons list [OPTIONS]
```

**Options:**
- `--json` - JSON output

**Examples:**
```bash
issues daemons list
issues daemons list --json
```

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

**Tests:**
- List with no daemons
- List with multiple daemons
- JSON output validation

---

#### 30. `issues daemons health` - Check daemon health

**Syntax:**
```bash
issues daemons health [OPTIONS]
```

**Options:**
- `--json` - JSON output

**Examples:**
```bash
issues daemons health
issues daemons health --json
```

**Output (JSON):**
```json
{
  "healthy": false,
  "issues": [
    {
      "workspace": "/path/to/project",
      "issue": "version_mismatch",
      "daemon_version": "0.9.0",
      "cli_version": "1.0.0"
    }
  ]
}
```

**Checks:**
- Version mismatches
- Stale sockets
- Resource usage
- Memory leaks

**Tests:**
- Health check with no issues
- Version mismatch detection
- Stale socket detection
- Resource usage reporting

---

#### 31. `issues daemons stop` - Stop daemon

**Syntax:**
```bash
issues daemons stop <workspace|pid> [OPTIONS]
```

**Arguments:**
- `<workspace|pid>` - Workspace path or process ID

**Options:**
- `--json` - JSON output

**Examples:**
```bash
issues daemons stop /path/to/workspace
issues daemons stop 12345
issues daemons stop . --json
```

**Output (JSON):**
```json
{
  "workspace": "/path/to/project",
  "pid": 12345,
  "stopped": true
}
```

**Tests:**
- Stop by workspace path
- Stop by PID
- Stop non-existent daemon
- Graceful shutdown

---

#### 32. `issues daemons restart` - Restart daemon

**Syntax:**
```bash
issues daemons restart <workspace|pid> [OPTIONS]
```

**Arguments:**
- `<workspace|pid>` - Workspace path or process ID

**Options:**
- `--json` - JSON output

**Examples:**
```bash
issues daemons restart /path/to/workspace
issues daemons restart 12345
issues daemons restart . --json
```

**Output (JSON):**
```json
{
  "workspace": "/path/to/project",
  "old_pid": 12345,
  "new_pid": 12346,
  "restarted": true
}
```

**Tests:**
- Restart by workspace
- Restart by PID
- Restart non-existent daemon
- Auto-start after restart

---

#### 33. `issues daemons killall` - Stop all daemons

**Syntax:**
```bash
issues daemons killall [OPTIONS]
```

**Options:**
- `--force` - Force kill if graceful fails
- `--json` - JSON output

**Examples:**
```bash
issues daemons killall
issues daemons killall --force
issues daemons killall --json
```

**Output (JSON):**
```json
{
  "stopped": 3,
  "failed": 0
}
```

**Tests:**
- Kill all daemons
- Force kill
- No daemons running
- Partial failures

---

#### 34. `issues daemons logs` - View daemon logs

**Syntax:**
```bash
issues daemons logs <workspace|pid> [OPTIONS]
```

**Arguments:**
- `<workspace|pid>` - Workspace path or process ID

**Options:**
- `-n <lines>` - Number of lines to show (default: 50)
- `-f` - Follow mode (tail -f style)
- `--json` - JSON output

**Examples:**
```bash
issues daemons logs /path/to/workspace -n 100
issues daemons logs 12345 -f
issues daemons logs . --json
```

**Output (JSON):**
```json
{
  "workspace": "/path/to/project",
  "lines": [
    "[INFO] 2025-11-11T10:00:00Z Auto-sync: export complete",
    "[WARN] 2025-11-11T10:00:05Z Git push failed: retry in 5s"
  ]
}
```

**Log Patterns:**
- `[INFO] Auto-sync: export complete` - Successful export
- `[WARN] Git push failed: ...` - Push error
- `[ERROR] Version mismatch` - Version issue

**Tests:**
- View logs (last N lines)
- Follow mode
- Non-existent daemon
- Log parsing

---

## Success Criteria

- ✅ All 34 commands implemented (20 MVP + 2 critical + 11 init/daemon + 1 sync)
- ✅ 70%+ test coverage
- ✅ All tests passing
- ✅ No linting/type errors
- ✅ JSON output for all commands
- ✅ Rich terminal output (human-readable)
- ✅ Documentation complete
- ✅ Feature parity with Beads core features
- ✅ Daemon auto-start working
- ✅ Continuous sync operational

---

## Notes

- CLI name: **`issues`** (not `bd`)
- Based on reference implementation + Beads CLI spec
- Focus on core issue tracking (defer advanced features)
- Maintain clean architecture (domain → services → CLI)
- Follow best practices from AGENTS.md
- Use `uv run scripts/build.py` for validation

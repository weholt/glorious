# Issue Tracker CLI Test Scenarios

Generated from reference.md - comprehensive integration test suite for validating all CLI functionality.

## Setup & Initialization

### Scenario 1: Basic Initialization
```bash
uv run issues init
```
**Expected:**
- Creates `./issues` directory
- Creates database at `./issues/issues.db`
- Creates config at `./issues/config.json`
- Starts daemon (no visible console window)
- Prints success message with next steps

### Scenario 2: Initialization with .env Configuration
```bash
# Create .env file first
echo "ISSUES_FOLDER=./issues" > .env
echo "ISSUES_DB_PATH=./issues/issues.db" >> .env
echo "ISSUES_GIT_ENABLED=false" >> .env

uv run issues init
```
**Expected:**
- Respects ISSUES_FOLDER from .env
- Creates database at path from .env
- Git integration disabled per .env setting

### Scenario 3: Check System Info
```bash
uv run issues info --json
```
**Expected JSON fields:**
- `database_path`: Absolute path to database
- `issue_prefix`: Current prefix (e.g., "issue")
- `daemon_running`: true/false
- `agent_mail_enabled`: true/false

## Issue Creation

### Scenario 4: Basic Issue Creation
```bash
uv run issues create "Fix login bug" --json
```
**Expected:**
- Returns JSON with issue ID (e.g., `issue-abc123`)
- Issue saved to database
- Default type: task
- Default priority: 2 (medium)
- Status: open

### Scenario 5: Create Issue with All Parameters
```bash
uv run issues create "Add OAuth support" -t feature -p 1 -d "Implement OAuth 2.0" --json
```
**Expected:**
- Type: feature
- Priority: 1 (high)
- Description populated
- Returns complete issue JSON

### Scenario 6: Create Issue with Labels
```bash
uv run issues create "Security audit" -t task -p 0 -l security,backend,urgent --json
```
**Expected:**
- Issue created with 3 labels: security, backend, urgent
- Labels array in returned JSON

### Scenario 7: Create Bug with Assignee
```bash
uv run issues create "Crash on startup" -t bug -p 0 --assignee alice --json
```
**Expected:**
- Type: bug
- Priority: 0 (critical)
- Assignee: alice

### Scenario 8: Create Epic
```bash
uv run issues create "Auth System Rewrite" -t epic -p 1 --json
```
**Expected:**
- Type: epic
- Can have child issues with hierarchical IDs

### Scenario 9: Create Child Task (Hierarchical)
```bash
# First create epic
EPIC_ID=$(uv run issues create "Auth System" -t epic -p 1 --json | jq -r '.id')

# Create child tasks
uv run issues create "Design login UI" -p 1 --json
uv run issues create "Backend validation" -p 1 --json
```
**Expected:**
- Child issues get hierarchical IDs (e.g., `issue-abc.1`, `issue-abc.2`)
- Auto-numbered sequentially
- Up to 3 levels of nesting supported

### Scenario 10: Create with Dependencies
```bash
uv run issues create "Found bug during work" -t bug -p 1 --deps discovered-from:issue-abc123 --json
```
**Expected:**
- Dependency created in one command
- Type: discovered-from
- Inherits parent's source_repo field

### Scenario 11: Create with Custom ID
```bash
uv run issues create "Worker task" --id worker1-100 -p 1 --json
```
**Expected:**
- Uses provided ID instead of generating hash
- Useful for parallel workers

### Scenario 12: Create from File
```bash
# Create markdown file
cat > feature.md << 'EOF'
# Add User Settings

### Type
feature

### Priority
2

### Labels
frontend, ui

### Description
Users need ability to customize preferences.
EOF

uv run issues create -f feature.md --json
```
**Expected:**
- Parses markdown structure
- Extracts type, priority, labels, description
- Creates issue with all fields

### Scenario 13: Create with Special Characters in Title
```bash
uv run issues create "Fix: auth doesn't validate tokens" -t bug -p 1 --json
```
**Expected:**
- Title preserved exactly with special characters
- No escaping issues

### Scenario 14: Verbose Creation Logging
```bash
uv run issues --verbose create "Test verbose mode" -t task -p 2
```
**Expected:**
- Timestamped log entries showing:
  - Database URL (absolute path with forward slashes)
  - Service initialization
  - Validation steps
  - Database creation
  - Transaction commit
  - Success message

## Issue Listing & Viewing

### Scenario 15: List All Issues
```bash
uv run issues list
```
**Expected:**
- Human-readable output
- Format: `issue-id: Title`

### Scenario 16: List with JSON Output
```bash
uv run issues list --json
```
**Expected:**
- JSON array of issue objects
- Each with id, title, status, priority, type, labels, etc.

### Scenario 17: Filter by Status
```bash
uv run issues list --status open --json
uv run issues list --status in_progress --json
uv run issues list --status closed --json
```
**Expected:**
- Only issues matching status filter
- Status values: open, in_progress, blocked, closed

### Scenario 18: Filter by Priority
```bash
uv run issues list --priority 0 --json  # Critical
uv run issues list --priority 1 --json  # High
```
**Expected:**
- Only issues with specified priority
- Priorities: 0-4 (critical to backlog)

### Scenario 19: Filter by Type
```bash
uv run issues list --type bug --json
uv run issues list --type feature --json
uv run issues list --type task --json
```
**Expected:**
- Only issues of specified type
- Types: bug, feature, task, epic, chore

### Scenario 20: Filter by Assignee
```bash
uv run issues list --assignee alice --json
```
**Expected:**
- Only issues assigned to alice

### Scenario 21: Filter by Labels (AND)
```bash
uv run issues list --label backend,urgent --json
```
**Expected:**
- Issues that have BOTH backend AND urgent labels

### Scenario 22: Filter by Labels (OR)
```bash
uv run issues list --label-any frontend,backend --json
```
**Expected:**
- Issues that have EITHER frontend OR backend label

### Scenario 23: Combine Multiple Filters
```bash
uv run issues list --status open --priority 1 --label-any urgent,critical --no-assignee --json
```
**Expected:**
- Open issues
- Priority 1
- Has urgent OR critical label
- Not assigned to anyone

### Scenario 24: Filter by Specific IDs
```bash
uv run issues list --id issue-abc,issue-def --json
```
**Expected:**
- Only the two specified issues

### Scenario 25: Title Search
```bash
uv run issues list --title "auth" --json
```
**Expected:**
- Issues with "auth" in title (case-insensitive substring)

### Scenario 26: Title Pattern Matching
```bash
uv run issues list --title-contains "login" --json
```
**Expected:**
- Issues with "login" anywhere in title

### Scenario 27: Description Search
```bash
uv run issues list --desc-contains "implement" --json
```
**Expected:**
- Issues with "implement" in description

### Scenario 28: Notes Search
```bash
uv run issues list --notes-contains "TODO" --json
```
**Expected:**
- Issues with "TODO" in notes field

### Scenario 29: Date Range Filters
```bash
uv run issues list --created-after 2024-01-01 --json
uv run issues list --updated-before 2024-12-31 --json
uv run issues list --closed-after 2024-06-01 --json
```
**Expected:**
- Issues matching date criteria
- Date format: YYYY-MM-DD or RFC3339

### Scenario 30: Empty Field Checks
```bash
uv run issues list --empty-description --json
uv run issues list --no-assignee --json
uv run issues list --no-labels --json
```
**Expected:**
- Issues with no description / no assignee / no labels

### Scenario 31: Priority Range
```bash
uv run issues list --priority-min 0 --priority-max 1 --json
```
**Expected:**
- Issues with priority 0 or 1 only

### Scenario 32: Show Issue Details
```bash
uv run issues show issue-abc123 --json
```
**Expected:**
- Complete issue details in JSON
- All fields populated

### Scenario 33: Show Multiple Issues
```bash
uv run issues show issue-abc issue-def issue-ghi --json
```
**Expected:**
- JSON array with all three issues

### Scenario 34: View Dependency Tree
```bash
uv run issues dep tree issue-abc123
```
**Expected:**
- ASCII tree showing dependencies
- Format:
  ```
  → issue-abc: Title [P1] (status)
    → child-1: Child title [P2] (status)
      → grandchild: Grandchild [P3] (status)
  ```

## Issue Updates

### Scenario 35: Update Status
```bash
uv run issues update issue-abc123 --status in_progress --json
```
**Expected:**
- Status changed to in_progress
- updated_at timestamp changed

### Scenario 36: Update Priority
```bash
uv run issues update issue-abc123 --priority 0 --json
```
**Expected:**
- Priority changed to 0 (critical)
- updated_at timestamp changed

### Scenario 37: Update Multiple Issues
```bash
uv run issues update issue-abc issue-def issue-ghi --status in_progress --json
```
**Expected:**
- All three issues updated
- Returns array of updated issues

### Scenario 38: Batch Priority Update
```bash
uv run issues update issue-abc issue-def --priority 1 --json
```
**Expected:**
- Both issues now priority 1

### Scenario 39: Close Single Issue
```bash
uv run issues close issue-abc123 --reason "Implemented and tested" --json
```
**Expected:**
- Status: closed
- closed_at timestamp set
- Reason stored

### Scenario 40: Close Multiple Issues
```bash
uv run issues close issue-abc issue-def issue-ghi --reason "Batch completion" --json
```
**Expected:**
- All three closed
- Same reason for all

### Scenario 41: Reopen Issue
```bash
uv run issues reopen issue-abc123 --reason "Reopening due to regression" --json
```
**Expected:**
- Status: open
- closed_at cleared
- Reason stored

### Scenario 42: Reopen Multiple Issues
```bash
uv run issues reopen issue-abc issue-def --reason "Batch reopen" --json
```
**Expected:**
- Both issues reopened

## Label Management

### Scenario 43: Add Label to Issue
```bash
uv run issues label add issue-abc123 urgent --json
```
**Expected:**
- Label "urgent" added to issue
- Labels array updated

### Scenario 44: Add Label to Multiple Issues
```bash
uv run issues label add issue-abc issue-def issue-ghi needs-review --json
```
**Expected:**
- All three issues get "needs-review" label

### Scenario 45: Remove Label
```bash
uv run issues label remove issue-abc123 urgent --json
```
**Expected:**
- "urgent" label removed from issue

### Scenario 46: Remove Label from Multiple Issues
```bash
uv run issues label remove issue-abc issue-def urgent --json
```
**Expected:**
- Both issues have "urgent" removed

### Scenario 47: List Issue Labels
```bash
uv run issues label list issue-abc123 --json
```
**Expected:**
- JSON array of labels for that issue

### Scenario 48: List All Labels with Counts
```bash
uv run issues label list-all --json
```
**Expected:**
- JSON array like: `[{"label": "auth", "count": 5}, ...]`
- Shows usage count for each label

## Dependencies

### Scenario 49: Add Dependency
```bash
uv run issues dep add issue-child issue-parent --type blocks
```
**Expected:**
- Dependency created: child blocks parent
- Type: blocks (hard dependency)

### Scenario 50: Add Related Dependency
```bash
uv run issues dep add issue-a issue-b --type related
```
**Expected:**
- Soft relationship created
- Doesn't affect ready work queue

### Scenario 51: Add Parent-Child Dependency
```bash
uv run issues dep add issue-child issue-parent --type parent-child
```
**Expected:**
- Epic/subtask relationship
- Shows in hierarchy

### Scenario 52: Add Discovered-From Dependency
```bash
uv run issues dep add issue-new issue-original --type discovered-from
```
**Expected:**
- Tracks issues discovered during work
- New issue inherits source_repo

### Scenario 53: View Dependency Tree
```bash
uv run issues dep tree issue-abc123
```
**Expected:**
- ASCII tree with all dependencies
- Shows issue titles, priorities, statuses

### Scenario 54: Detect Dependency Cycles
```bash
uv run issues dep cycles
```
**Expected:**
- Lists any circular dependencies
- Empty if no cycles

## Work Queue Operations

### Scenario 55: Find Ready Work
```bash
uv run issues ready --json
```
**Expected:**
- Issues with no blockers
- Status: open
- JSON array of ready issues

### Scenario 56: Find Ready Work by Priority
```bash
uv run issues ready --priority 1 --json
```
**Expected:**
- Only ready P1 issues

### Scenario 57: Find Blocked Issues
```bash
uv run issues blocked --json
```
**Expected:**
- Issues blocked by dependencies
- Shows what's blocking each

### Scenario 58: Find Stale Issues (Default 30 Days)
```bash
uv run issues stale --json
```
**Expected:**
- Issues not updated in 30+ days
- Sorted by staleness

### Scenario 59: Find Stale Issues with Custom Days
```bash
uv run issues stale --days 90 --json
```
**Expected:**
- Issues not updated in 90+ days

### Scenario 60: Find Stale In-Progress Issues
```bash
uv run issues stale --days 30 --status in_progress --json
```
**Expected:**
- In-progress issues stale for 30+ days

### Scenario 61: Limit Stale Results
```bash
uv run issues stale --limit 10 --json
```
**Expected:**
- Maximum 10 stale issues returned

## Statistics

### Scenario 62: View Issue Statistics
```bash
uv run issues stats --json
```
**Expected JSON fields:**
- Total issues
- By status (open, in_progress, blocked, closed)
- By priority (P0-P4 counts)
- By type (bug, feature, task, epic, chore)

## Advanced Operations

### Scenario 63: Cleanup Closed Issues (Dry Run)
```bash
uv run issues cleanup --dry-run --json
```
**Expected:**
- Shows what would be deleted
- No actual deletion

### Scenario 64: Cleanup All Closed Issues
```bash
uv run issues cleanup --force --json
```
**Expected:**
- All closed issues deleted permanently
- Returns count of deleted issues

### Scenario 65: Cleanup Old Closed Issues
```bash
uv run issues cleanup --older-than 30 --force --json
```
**Expected:**
- Only closed issues >30 days old deleted

### Scenario 66: Cleanup with Cascade
```bash
uv run issues cleanup --older-than 90 --cascade --force --json
```
**Expected:**
- Deletes old issues AND their dependents

### Scenario 67: Find Duplicates
```bash
uv run issues duplicates --json
```
**Expected:**
- Groups of issues with identical content
- Suggests merge commands

### Scenario 68: Duplicates Dry Run
```bash
uv run issues duplicates --dry-run --json
```
**Expected:**
- Shows what would be merged
- No actual merging

### Scenario 69: Auto-Merge Duplicates
```bash
uv run issues duplicates --auto-merge --json
```
**Expected:**
- Automatically merges all duplicate groups
- Returns merge results

### Scenario 70: Merge Specific Issues
```bash
uv run issues merge issue-dup1 issue-dup2 --into issue-original --json
```
**Expected:**
- dup1 and dup2 closed
- Dependencies migrated to original
- Text references updated

### Scenario 71: Merge Dry Run
```bash
uv run issues merge issue-dup1 --into issue-original --dry-run --json
```
**Expected:**
- Shows what would happen
- No actual changes

### Scenario 72: Rename Prefix (Dry Run)
```bash
uv run issues rename-prefix kw- --dry-run --json
```
**Expected:**
- Shows all ID changes
- Updates to dependencies and text references
- No actual changes

### Scenario 73: Rename Prefix (Apply)
```bash
uv run issues rename-prefix kw- --json
```
**Expected:**
- All issue IDs updated
- Dependencies updated
- Text references rewritten
- Counter table updated

### Scenario 74: Compact Issues (Analyze)
```bash
uv run issues compact --analyze --json
```
**Expected:**
- List of candidates for compaction
- Tier assignments

### Scenario 75: Compact Specific Tier
```bash
uv run issues compact --analyze --tier 1 --limit 10 --json
```
**Expected:**
- Maximum 10 tier-1 candidates

### Scenario 76: Apply Compaction
```bash
# Create summary file first
echo "Compacted summary of work done" > summary.txt

uv run issues compact --apply --id issue-abc123 --summary summary.txt --json
```
**Expected:**
- Issue compacted with summary
- Original preserved in git history

### Scenario 77: Compact from Stdin
```bash
echo "Summary text" | uv run issues compact --apply --id issue-abc123 --summary - --json
```
**Expected:**
- Reads summary from stdin
- Applies compaction

### Scenario 78: Compact Statistics
```bash
uv run issues compact --stats --json
```
**Expected:**
- Compaction statistics
- Counts by tier

### Scenario 79: Restore Compacted Issue
```bash
uv run issues restore issue-abc123
```
**Expected:**
- Shows full history at time of compaction
- Retrieves from git history

## Import/Export

### Scenario 80: Export to JSONL
```bash
uv run issues export -o issues.jsonl
```
**Expected:**
- Creates issues.jsonl with all issues
- One JSON object per line
- Includes all fields and labels

### Scenario 81: Import from JSONL (Dry Run)
```bash
uv run issues import -i issues.jsonl --dry-run
```
**Expected:**
- Shows what would be imported
- Counts: exact matches, new issues, updates
- No actual changes

### Scenario 82: Import from JSONL
```bash
uv run issues import -i issues.jsonl --json
```
**Expected:**
- Issues imported/updated
- Returns import statistics

### Scenario 83: Import with Duplicate Detection
```bash
uv run issues import -i issues.jsonl --dedupe-after --json
```
**Expected:**
- Import completes
- Then runs duplicate detection
- Suggests merges

### Scenario 84: Import with Missing Parents
```bash
# Create JSONL with child but no parent
cat > test.jsonl << 'EOF'
{"id": "issue-abc.1", "title": "Child", "parent_id": "issue-abc"}
EOF

uv run issues import -i test.jsonl
```
**Expected:**
- Creates tombstone for missing parent
- Parent status: closed, priority: 4
- Child imports successfully

## Daemon Management

### Scenario 85: List All Daemons
```bash
uv run issues daemons list --json
```
**Expected:**
- JSON array of running daemons
- Each with PID, workspace, status

### Scenario 86: Check Daemon Health
```bash
uv run issues daemons health --json
```
**Expected:**
- Health check results
- Version mismatches
- Stale sockets

### Scenario 87: Stop Specific Daemon by Workspace
```bash
uv run issues daemons stop /path/to/workspace --json
```
**Expected:**
- Daemon stopped gracefully
- Returns stop status

### Scenario 88: Stop Daemon by PID
```bash
uv run issues daemons stop 12345 --json
```
**Expected:**
- Daemon with PID 12345 stopped

### Scenario 89: Restart Daemon
```bash
uv run issues daemons restart 12345 --json
```
**Expected:**
- Daemon stopped and restarted
- New PID assigned

### Scenario 90: View Daemon Logs
```bash
uv run issues daemons logs /path/to/workspace -n 100
```
**Expected:**
- Last 100 log lines
- Timestamped entries

### Scenario 91: Follow Daemon Logs
```bash
uv run issues daemons logs 12345 -f
```
**Expected:**
- Live log streaming
- Updates as new logs appear
- Ctrl+C to stop

### Scenario 92: Stop All Daemons
```bash
uv run issues daemons killall --json
```
**Expected:**
- All daemons stopped gracefully
- Returns count of stopped daemons

### Scenario 93: Force Stop All Daemons
```bash
uv run issues daemons killall --force --json
```
**Expected:**
- Forcefully terminates all daemons
- Used when graceful shutdown fails

## Sync Operations

### Scenario 94: Manual Sync
```bash
uv run issues sync
```
**Expected:**
- Immediate export to JSONL
- Git commit (if enabled)
- Git pull
- Import any updates
- Git push (if enabled)

### Scenario 95: No-Daemon Mode
```bash
uv run issues --no-daemon ready --json
```
**Expected:**
- Direct database access
- No daemon interaction
- Safe for git worktrees

### Scenario 96: No-Daemon via Environment
```bash
export ISSUES_NO_DAEMON=1
uv run issues ready --json
```
**Expected:**
- All commands use direct mode
- Daemon not started

## Error Handling & Edge Cases

### Scenario 97: Create Issue with Empty Title
```bash
uv run issues create "" --json
```
**Expected:**
- Error: Title is required
- Exit code 1

### Scenario 98: Invalid Issue Type
```bash
uv run issues create "Test" -t invalid --json
```
**Expected:**
- Error: Invalid type 'invalid'
- Exit code 1

### Scenario 99: Invalid Priority
```bash
uv run issues create "Test" -p 5 --json
```
**Expected:**
- Error: Invalid priority '5'
- Exit code 1
- Valid range: 0-4

### Scenario 100: Update Non-Existent Issue
```bash
uv run issues update issue-nonexistent --status closed --json
```
**Expected:**
- Error: Issue not found
- Exit code 1

### Scenario 101: Show Non-Existent Issue
```bash
uv run issues show issue-nonexistent --json
```
**Expected:**
- Error or empty result
- Graceful handling

### Scenario 102: Circular Dependency Prevention
```bash
# Create two issues
ID1=$(uv run issues create "Issue A" --json | jq -r '.id')
ID2=$(uv run issues create "Issue B" --json | jq -r '.id')

# Create circular dependency
uv run issues dep add $ID1 $ID2
uv run issues dep add $ID2 $ID1

# Check for cycles
uv run issues dep cycles
```
**Expected:**
- Cycle detected
- Reports circular dependency

### Scenario 103: Merge Issue into Itself
```bash
uv run issues merge issue-abc --into issue-abc --json
```
**Expected:**
- Error: Cannot merge issue into itself
- Exit code 1

### Scenario 104: Invalid Prefix Validation
```bash
uv run issues rename-prefix "invalid prefix with spaces" --json
```
**Expected:**
- Error: Invalid prefix format
- Rules: max 8 chars, lowercase/numbers/hyphens, starts with letter

### Scenario 105: Database Path Validation
```bash
# Test with absolute path
export ISSUES_DB_PATH="/absolute/path/to/issues.db"
uv run issues --verbose create "Test absolute path" --json
```
**Expected:**
- Verbose output shows correct absolute path
- Database URL uses forward slashes: `sqlite:///C:/path/to/issues.db`

## Performance & Scale

### Scenario 106: Create Many Issues
```bash
for i in {1..100}; do
  uv run issues create "Issue $i" -p 2 --json
done
```
**Expected:**
- All 100 issues created
- Reasonable performance
- Database remains stable

### Scenario 107: List Large Dataset
```bash
uv run issues list --json | jq 'length'
```
**Expected:**
- Returns all issues
- JSON parsing succeeds
- Performance acceptable

### Scenario 108: Complex Filter Performance
```bash
uv run issues list --status open --priority 1 --label-any urgent,critical --no-assignee --title-contains "auth" --json
```
**Expected:**
- Filter applies correctly
- Results in reasonable time
- Correct issue subset returned

## Configuration & Environment

### Scenario 109: Custom Database Path
```bash
export ISSUES_DB_PATH=./custom/location/issues.db
uv run issues init
```
**Expected:**
- Database created at custom location
- All operations use custom path

### Scenario 110: Disable Git Integration
```bash
export ISSUES_GIT_ENABLED=false
uv run issues init
```
**Expected:**
- No git operations
- No auto-commit/push

### Scenario 111: Database Echo Mode
```bash
export ISSUES_DB_ECHO=true
uv run issues create "Test echo" --json
```
**Expected:**
- SQL statements printed to stderr
- Useful for debugging

### Scenario 112: Custom Sync Interval
```bash
export ISSUES_SYNC_INTERVAL=10
uv run issues init
```
**Expected:**
- Daemon syncs every 10 seconds
- Configurable debounce

## Workflow Integration

### Scenario 113: Agent Workflow - Claim and Complete
```bash
# Find work
ISSUE_ID=$(uv run issues ready --json | jq -r '.[0].id')

# Claim it
uv run issues update $ISSUE_ID --status in_progress --json

# Work on it...

# Complete it
uv run issues close $ISSUE_ID --reason "Implemented and tested" --json
```
**Expected:**
- Complete workflow executes
- Issue transitions: open → in_progress → closed

### Scenario 114: Discover and Link Work (One Command)
```bash
PARENT_ID=$(uv run issues create "Refactor auth" --json | jq -r '.id')

# Discover bug while working
uv run issues create "Found validation bug" -t bug -p 1 --deps discovered-from:$PARENT_ID --json
```
**Expected:**
- Bug created with dependency
- Inherits parent's source_repo

### Scenario 115: Batch Label Update
```bash
# Get all open bugs
uv run issues list --status open --type bug --json | jq -r '.[].id' | while read id; do
  uv run issues label add "$id" needs-triage
done
```
**Expected:**
- All open bugs get "needs-triage" label

### Scenario 116: Sprint Planning
```bash
# Tag issues for sprint
for id in issue-abc issue-def issue-ghi; do
  uv run issues label add "$id" sprint-12
done

# Track progress
uv run issues list --label sprint-12 --status closed --json
uv run issues list --label sprint-12 --status open --json
```
**Expected:**
- Sprint tracking via labels
- Progress monitoring

### Scenario 117: End-of-Session Sync
```bash
# Agent finishes work session
uv run issues sync
```
**Expected:**
- Immediate export/commit/push
- Bypasses debounce
- Ensures changes persisted

## Git Integration

### Scenario 118: Verify Git Sync
```bash
# Enable git
export ISSUES_GIT_ENABLED=true

# Create issue
uv run issues create "Test git sync" --json

# Wait for daemon sync (5 seconds) or run manual sync
sleep 6

# Check git log
git log -1 --oneline
```
**Expected:**
- Issue exported to issues.jsonl
- Git commit created
- Commit message relevant

### Scenario 119: Import After Pull
```bash
# Simulate remote change
echo '{"id": "issue-remote", "title": "Remote issue"}' >> issues.jsonl
git add issues.jsonl
git commit -m "Add remote issue"

# Import
uv run issues import -i issues.jsonl --json
```
**Expected:**
- Remote issue imported to database
- Available via `issues list`

### Scenario 120: Handle Git Merge Conflicts
```bash
# After git merge conflict in issues.jsonl
git checkout --theirs issues.jsonl
uv run issues import -i issues.jsonl

git add issues.jsonl
git commit
```
**Expected:**
- Conflict resolved
- Database updated with merged data

## Summary

Total Scenarios: 120

**Coverage by Category:**
- Setup & Initialization: 3
- Issue Creation: 11
- Listing & Viewing: 20
- Issue Updates: 8
- Label Management: 6
- Dependencies: 6
- Work Queue: 7
- Statistics: 1
- Advanced Operations: 13
- Import/Export: 5
- Daemon Management: 9
- Sync Operations: 3
- Error Handling: 9
- Performance: 3
- Configuration: 4
- Workflow Integration: 5
- Git Integration: 3

**Test Execution Notes:**
1. Run tests in isolated environment (temp directory)
2. Clean database between tests
3. Verify JSON output structure
4. Check exit codes
5. Validate database state after operations
6. Test error conditions thoroughly
7. Verify no console windows on Windows daemon start
8. Check database path uses forward slashes on all platforms
9. Ensure transactions commit properly
10. Validate verbose logging output

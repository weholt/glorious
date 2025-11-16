# Issues Skill Usage Guide

Complete guide for using the issues skill in Glorious Agents framework.

## Overview

The issues skill provides git-backed issue tracking with hierarchical relationships, hash-based IDs, and dependency management. It's designed for agents and humans to collaborate on project management.

## Quick Start

### Installation

```bash
# Via glorious-agents (includes issues skill)
pip install glorious-agents[issues]

# Standalone
pip install issue-tracker
```

### Initialize

```bash
# Initialize in current directory
agent issues init

# Or standalone
issues init
```

This creates:
- `./.issues/` directory with SQLite database
- Git integration for version control
- Daemon for auto-sync (5-second debounce)

## Core Concepts

### Issue Types

- **`bug`** - Something broken that needs fixing
- **`feature`** - New functionality to be added
- **`task`** - Work item (tests, docs, refactoring)
- **`epic`** - Large feature composed of multiple issues (supports parent-child hierarchy)
- **`chore`** - Maintenance work (dependencies, tooling)

### Priorities

- **`0`** - Critical (security, data loss, broken builds)
- **`1`** - High (major features, important bugs)
- **`2`** - Medium (nice-to-have features, minor bugs)
- **`3`** - Low (polish, optimization)
- **`4`** - Backlog (future ideas)

### Issue Status

- **`open`** - Not started yet
- **`in_progress`** - Currently being worked on
- **`blocked`** - Cannot proceed due to blocker
- **`resolved`** - Work complete, pending review/verification
- **`closed`** - Finished and verified
- **`archived`** - Old, no longer relevant

### Hash-Based IDs

Issues use content-based hash IDs (e.g., `bd-a1b2`, `bd-f14c`) to prevent collisions when multiple agents/branches work concurrently. IDs are deterministic based on issue content.

## Basic Commands

### Creating Issues

```bash
# Basic creation
agent issues create "Fix login bug" -t bug -p 1

# With description
agent issues create "Add OAuth" -d "Implement OAuth 2.0 authentication" -t feature -p 2

# With labels
agent issues create "API issue" -t bug -p 1 -l backend,api,urgent

# With assignee
agent issues create "Refactor parser" -t task -p 2 --assignee alice

# Create from markdown file
agent issues create -f feature-plan.md
```

**Important:** Always quote titles and descriptions with special characters.

### Listing Issues

```bash
# List all open issues
agent issues list

# Filter by status
agent issues list --status in_progress

# Filter by priority
agent issues list --priority 1

# Filter by type
agent issues list --type bug

# Filter by labels (AND - must have ALL)
agent issues list --label backend,urgent

# Filter by labels (OR - must have AT LEAST ONE)
agent issues list --label-any frontend,backend

# Combine filters
agent issues list --status open --priority 1 --label security --json

# Get JSON output (recommended for agents)
agent issues list --json
```

### Viewing Issues

```bash
# Show single issue
agent issues show bd-a1b2

# Show multiple issues
agent issues show bd-a1b2 bd-f14c bd-xyz9

# JSON output
agent issues show bd-a1b2 --json
```

### Updating Issues

```bash
# Update status
agent issues update bd-a1b2 --status in_progress

# Update priority
agent issues update bd-a1b2 --priority 0

# Update multiple fields
agent issues update bd-a1b2 --status in_progress --assignee alice --priority 1

# Update multiple issues at once
agent issues update bd-a1b2 bd-f14c bd-xyz9 --priority 0

# JSON output
agent issues update bd-a1b2 --status in_progress --json
```

### Closing Issues

```bash
# Close single issue
agent issues close bd-a1b2 --reason "Bug fixed and tested"

# Close multiple issues
agent issues close bd-a1b2 bd-f14c --reason "Batch completion"

# Reopen closed issue
agent issues reopen bd-a1b2 --reason "Found regression"

# JSON output
agent issues close bd-a1b2 --reason "Done" --json
```

## Epic Management

Epics are large features that contain multiple issues. They support **hierarchical parent-child relationships** for complex project organization.

### Creating Epics

```bash
# Create top-level epic
agent issues create "Auth System Rewrite" -t epic -p 1
# Returns: bd-a3f8e9

# Create child epic (epic within an epic)
agent issues create "OAuth Implementation" -t epic -p 1 --epic bd-a3f8e9
# Returns: bd-b7e2c4 (child of bd-a3f8e9)

# Create grandchild epic (3-level hierarchy)
agent issues create "Google OAuth" -t epic -p 2 --epic bd-b7e2c4
# Returns: bd-c8f3d5 (child of bd-b7e2c4, grandchild of bd-a3f8e9)
```

### Adding Issues to Epics

```bash
# Create issue and assign to epic
agent issues create "Design login UI" -t task -p 1 --epic bd-a3f8e9

# Assign existing issue to epic
agent issues epics set bd-42 bd-a3f8e9

# Add multiple issues to epic
agent issues epics add bd-a3f8e9 bd-42 bd-43 bd-44

# JSON output
agent issues epics set bd-42 bd-a3f8e9 --json
```

### Removing from Epics

```bash
# Remove issue from its epic
agent issues epics clear bd-42

# Remove multiple issues from epic
agent issues epics remove bd-a3f8e9 bd-42 bd-43

# JSON output
agent issues epics clear bd-42 --json
```

### Viewing Epic Hierarchy

```bash
# List all issues in an epic (flat view)
agent issues list --epic bd-a3f8e9

# List issues in specific epic (CLI command)
agent issues epics list bd-a3f8e9

# View hierarchical tree structure
agent issues epics tree

# JSON output (includes parent-child relationships)
agent issues list --epic bd-a3f8e9 --json
```

**Example hierarchy output:**

```
🌲 Epic Hierarchy:

→ bd-a3f8e9: Auth System Rewrite [epic] [P1] (in_progress)
  ├─ bd-b7e2c4: OAuth Implementation [epic] [P1] (open)
  │  ├─ bd-c8f3d5: Google OAuth [epic] [P2] (open)
  │  │  └─ bd-d9g4e6: Google token validation [task] [P2] (open)
  │  └─ bd-e1h5f7: GitHub OAuth [task] [P2] (open)
  └─ bd-f2i6g8: JWT tokens [task] [P1] (in_progress)
```

### Parent-Epic Feature

The **parent_epic_id** field (stored in `epic_id` for backward compatibility) enables:

1. **Hierarchical epics** - Create epics within epics (up to 3 levels deep)
2. **Tree visualization** - View nested epic structure
3. **Recursive queries** - Get all issues under an epic including sub-epics
4. **Progress tracking** - Calculate completion across epic hierarchy

**When to use hierarchical epics:**
- Large projects with multiple phases (e.g., "v2.0 Release" → "Auth Rewrite" → "OAuth Implementation")
- Organizing by team or component (e.g., "Backend" → "API" → "Authentication")
- Breaking down complex features (e.g., "E-commerce" → "Checkout" → "Payment Gateway")

## Labels

Labels provide flexible categorization for cross-cutting concerns.

### Managing Labels

```bash
# Add labels when creating
agent issues create "API bug" -t bug -p 1 -l backend,api,urgent

# Add labels to existing issue
agent issues label add bd-a1b2 security
agent issues label add bd-a1b2 breaking-change

# Add label to multiple issues
agent issues label add bd-a1b2 bd-f14c bd-xyz9 urgent

# Remove label
agent issues label remove bd-a1b2 urgent

# List issue labels
agent issues label list bd-a1b2

# List all labels with usage counts
agent issues label list-all

# JSON output
agent issues label list-all --json
```

### Label Patterns

**Technical Components:**
```
backend, frontend, api, database, infrastructure, cli, ui, mobile
```

**Domain/Feature Areas:**
```
auth, payments, search, analytics, billing, notifications, reporting
```

**Size/Effort:**
```
small, medium, large
```

**Quality Gates:**
```
needs-review, needs-tests, needs-docs, breaking-change
```

**Release Management:**
```
v1.0, v2.0, backport-candidate, release-blocker
```

### Filtering by Labels

```bash
# Issues with ALL specified labels (AND)
agent issues list --label backend,urgent

# Issues with ANY specified label (OR)
agent issues list --label-any frontend,backend

# Combine AND/OR
agent issues list --label needs-review,needs-tests --label-any frontend,backend

# Combined with other filters
agent issues list --status open --priority 1 --label security
```

## Dependencies

Track relationships between issues with four dependency types.

### Dependency Types

- **`blocks`** - Hard dependency (issue X blocks issue Y from starting)
- **`related`** - Soft relationship (issues are connected)
- **`parent-child`** - Epic/subtask relationship (automatically managed)
- **`discovered-from`** - Track issues discovered during work

### Adding Dependencies

```bash
# Add blocking dependency (bd-2 blocks bd-1)
agent issues dep add bd-1 bd-2 --type blocks

# Add related dependency
agent issues dep add bd-1 bd-2 --type related

# Create issue with discovered-from dependency (one command)
agent issues create "Found auth bug" -t bug -p 1 --deps discovered-from:bd-100

# Old way (two commands)
agent issues create "Found bug" -t bug -p 1  # Returns bd-101
agent issues dep add bd-101 bd-100 --type discovered-from
```

### Viewing Dependencies

```bash
# Show dependency tree for an issue
agent issues dep tree bd-a1b2

# List blockers for an issue
agent issues dep list bd-a1b2

# JSON output
agent issues dep list bd-a1b2 --json
```

**Example tree output:**

```
🌲 Dependency tree for bd-3:

→ bd-3: Add authentication [P2] (open)
  → bd-2: Create API [P2] (open)
    → bd-1: Set up database [P1] (open)
```

### Finding Ready Work

```bash
# Find issues with no blockers (ready to work on)
agent issues ready

# Filter ready work by priority
agent issues ready --priority 1

# Filter ready work by labels
agent issues ready --label backend

# JSON output (recommended for agents)
agent issues ready --json
```

### Detecting Cycles

```bash
# Detect circular dependencies
agent issues dep cycles

# This prevents deadlocks like: A blocks B, B blocks A
```

## Comments

Add discussions and updates to issues.

```bash
# Add comment
agent issues comments add bd-a1b2 "Started working on this, ETA 2 hours"

# List comments
agent issues comments list bd-a1b2

# Update comment
agent issues comments update COMMENT-ID "Updated ETA: 4 hours"

# Delete comment
agent issues comments delete COMMENT-ID

# JSON output
agent issues comments list bd-a1b2 --json
```

## Advanced Features

### Finding Stale Issues

```bash
# Find issues not updated in 30+ days (default)
agent issues stale

# Custom timeframe
agent issues stale --days 90

# Filter by status
agent issues stale --days 30 --status in_progress

# Limit results
agent issues stale --limit 10

# JSON output
agent issues stale --json
```

### Statistics

```bash
# View issue statistics
agent issues stats

# JSON output
agent issues stats --json
```

**Example output:**
```
Issue Statistics:
  Total: 42
  Open: 15
  In Progress: 8
  Blocked: 2
  Resolved: 3
  Closed: 14

By Priority:
  Critical (P0): 2
  High (P1): 10
  Medium (P2): 18
  Low (P3): 8
  Backlog (P4): 4
```

### Import/Export

```bash
# Export to JSONL
agent issues export -o issues.jsonl

# Import from JSONL
agent issues import -i issues.jsonl

# Preview import (dry-run)
agent issues import -i issues.jsonl --dry-run

# Import and detect duplicates
agent issues import -i issues.jsonl --dedupe-after
```

### Duplicate Detection

```bash
# Find duplicate issues (by content hash)
agent issues duplicates

# Automatically merge all duplicates
agent issues duplicates --auto-merge

# Preview merges
agent issues duplicates --dry-run

# JSON output
agent issues duplicates --json
```

### Merging Issues

```bash
# Merge bd-42 and bd-43 into bd-41
agent issues merge bd-42 bd-43 --into bd-41

# Preview merge
agent issues merge bd-42 bd-43 --into bd-41 --dry-run

# JSON output
agent issues merge bd-42 bd-43 --into bd-41 --json
```

**What merging does:**
1. Closes source issues with reason "Merged into bd-X"
2. Migrates all dependencies to target issue
3. Updates text references (e.g., "see bd-42" → "see bd-41")
4. Preserves git history

### Cleanup

```bash
# Delete ALL closed issues (careful!)
agent issues cleanup --force

# Delete closed issues older than 30 days
agent issues cleanup --older-than 30 --force

# Preview cleanup
agent issues cleanup --dry-run

# Delete with dependents (cascade)
agent issues cleanup --older-than 90 --cascade --force

# JSON output
agent issues cleanup --dry-run --json
```

## Git Integration

The issues skill integrates with git for version control and collaboration.

### Auto-Sync

The daemon automatically syncs changes every 5 seconds (debounced):
1. Exports pending changes to `./.issues.jsonl`
2. Commits to git
3. Pulls from remote
4. Imports any updates
5. Pushes to remote

### Manual Sync

```bash
# Force immediate sync (bypass 5-second debounce)
agent issues sync
```

**Always run `agent issues sync` at end of agent sessions** to ensure changes are committed/pushed immediately.

### Git Worktrees Warning

⚠️ **Daemon mode doesn't work correctly with `git worktree`!**

**Solution:** Use `--no-daemon` flag:

```bash
# For single command
agent issues --no-daemon ready

# For entire session (set environment variable)
export ISSUES_NO_DAEMON=1
agent issues ready  # All commands use direct mode
```

### Handling Merge Conflicts

With hash-based IDs, ID collisions are eliminated. Conflicts occur when the same issue is modified on both branches.

**Resolution:**

```bash
# After git merge creates conflict in ./.issues.jsonl
git checkout --theirs ./.issues.jsonl  # Accept remote
# OR
git checkout --ours ./.issues.jsonl    # Keep local
# OR manually resolve (keep line with newer updated_at)

# Import resolved JSONL
agent issues import -i ./.issues.jsonl

# Commit the merge
git add ./.issues.jsonl
git commit
```

## Agent Workflows

### Typical Agent Workflow

```bash
# 1. Start of session - Find work
agent issues ready --json

# 2. Claim an issue
agent issues update bd-42 --status in_progress --json

# 3. Work on it...
# ... agent does work ...

# 4. Discover related work
agent issues create "Found TODO in auth.go" -t task -p 2 \
  --deps discovered-from:bd-42 --json

# 5. Complete work
agent issues close bd-42 --reason "Implemented and tested" --json

# 6. End of session - Force sync
agent issues sync
```

### Claiming Work Pattern

```bash
# Find highest priority ready work
agent issues ready --priority 1 --json | jq '.[0]'

# Claim it
ISSUE_ID=$(agent issues ready --priority 1 --json | jq -r '.[0].id')
agent issues update $ISSUE_ID --status in_progress --assignee agent-001
```

### Batch Operations

```bash
# Update multiple issues
agent issues update bd-41 bd-42 bd-43 --priority 0 --json

# Close multiple issues
agent issues close bd-41 bd-42 bd-43 --reason "Batch completion" --json

# Add label to multiple issues
agent issues label add bd-41 bd-42 bd-43 urgent --json
```

### Discovered Work Pattern

When an agent discovers work during a task:

```bash
# Create and link in one command (preferred)
agent issues create "Refactor validateToken" -t chore -p 2 \
  --deps discovered-from:bd-42 \
  --label technical-debt,backend \
  --json

# Automatically inherits parent's source_repo field
```

### Quality Gate Pattern

```bash
# Start work
agent issues update bd-42 --status in_progress

# Mark requirements
agent issues label add bd-42 needs-tests
agent issues label add bd-42 needs-docs

# Before closing, verify
agent issues label remove bd-42 needs-tests  # After writing tests
agent issues label remove bd-42 needs-docs   # After updating docs

# Close when gates satisfied
agent issues close bd-42 --json
```

## Daemon Management

The daemon provides background sync and RPC coordination.

### Daemon Commands

```bash
# List all running daemons
agent issues daemons list

# Check daemon health
agent issues daemons health

# View daemon logs
agent issues daemons logs /path/to/workspace -n 100
agent issues daemons logs /path/to/workspace -f  # Follow mode

# Stop specific daemon
agent issues daemons stop /path/to/workspace

# Restart daemon
agent issues daemons restart /path/to/workspace

# Stop all daemons
agent issues daemons killall

# Force kill if needed
agent issues daemons killall --force

# JSON output
agent issues daemons list --json
agent issues daemons health --json
```

### Daemon Architecture

- **One daemon per project** - Each project gets its own daemon at `./.sock`
- **LSP model** - Similar to language servers
- **Process isolation** - Prevents cross-project pollution
- **Auto-start** - Daemon starts automatically when needed
- **5-second debounce** - Batches changes before syncing

### Disabling Daemon

```bash
# For single command
agent issues --no-daemon create "Task"

# For entire session
export ISSUES_NO_DAEMON=1
agent issues ready  # All commands use direct mode

# Disable auto-start
export ISSUES_AUTO_START_DAEMON=false
```

## Configuration

### Database Location

By default: `~/./.default.db`

Use project-specific databases:

```bash
# Set via environment
export ISSUES_DB_PATH=./my-project.db
agent issues list

# Set via flag
agent issues --db ./my-project.db list
```

### Issue Prefix

Change the prefix for all issues:

```bash
# Preview changes
agent issues rename-prefix kw- --dry-run

# Apply rename (e.g., bd-123 → kw-123)
agent issues rename-prefix kw-

# Prefix rules:
# - Max 8 characters
# - lowercase, numbers, hyphens
# - Must start with letter
# - Must end with hyphen
```

### Project Configuration

```bash
# View current config
agent issues info --json

# Example output:
# {
#   "database_path": "/path/to/./.db",
#   "issue_prefix": "bd",
#   "daemon_running": true,
#   "agent_mail_enabled": false
# }
```

## JSON Output

**Always use `--json` flag for programmatic access.**

All commands support JSON output for reliable parsing:

```bash
# Single issue
agent issues show bd-42 --json

# List of issues
agent issues list --json

# Operation result
agent issues create "Title" -p 1 --json
agent issues update bd-42 --status in_progress --json
```

**Example JSON output:**

```json
{
  "id": "bd-a1b2",
  "title": "Fix authentication bug",
  "description": "Users cannot log in",
  "status": "open",
  "priority": 1,
  "type": "bug",
  "assignee": "alice",
  "epic_id": "bd-xyz9",
  "labels": ["auth", "urgent"],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:20:00",
  "closed_at": null
}
```

## Troubleshooting

### Daemon Issues

```bash
# Check daemon status
agent issues daemons health

# View logs
agent issues daemons logs /path/to/workspace

# Restart daemon
agent issues daemons restart /path/to/workspace

# Use direct mode if daemon is problematic
agent issues --no-daemon list
```

### Sync Issues

```bash
# Force manual sync
agent issues sync

# Check git status
cd ./.issues && git status && git log -5

# Export pending changes
agent issues export -o ./.issues.jsonl
```

### Import Failures

```bash
# Preview import
agent issues import -i issues.jsonl --dry-run

# Check for missing parents (auto-handled)
# Issues automatically creates tombstone placeholders for missing parents
```

### Labels Not Showing

```bash
# Labels only show in JSON output
agent issues list --json | jq '.[] | {id, labels}'

# See labels for specific issue
agent issues label list bd-42
```

## Best Practices

### For Agents

1. **Always use `--json` flag** - Reliable parsing
2. **Claim work before starting** - Update status to `in_progress`
3. **Use discovered-from dependencies** - Track work discovery
4. **Add labels for context** - `ai-generated`, `needs-review`
5. **Force sync at session end** - `agent issues sync`
6. **Use batch operations** - Update multiple issues efficiently
7. **Check ready work first** - Respect dependencies

### For Teams

1. **Establish label conventions** - Document in project README
2. **Use epic hierarchies** - Organize complex features
3. **Track dependencies** - Prevent deadlocks
4. **Regular cleanup** - Archive old closed issues
5. **Monitor stale issues** - Follow up on abandoned work
6. **Use priority consistently** - Clear prioritization
7. **Force sync before switching branches** - Prevent conflicts

### For Complex Projects

1. **3-level epic hierarchy** - Project → Feature → Implementation
2. **Component labels** - Organize by architecture
3. **Size estimation labels** - `small`, `medium`, `large`
4. **Quality gate labels** - Track pre-close requirements
5. **Release labels** - Manage version targeting
6. **Dependency trees** - Visualize blocked work
7. **Regular duplicate detection** - Keep database clean

## See Also

- [Reference Documentation](./reference.md) - Complete CLI reference
- [README.md](../../README.md) - Overview and installation
- [Instructions](../instructions.md) - Skill-specific instructions
- [Glorious Agents Documentation](../../../../../../docs/) - Framework docs

## Examples

### Example 1: Feature Development

```bash
# Create epic for large feature
agent issues create "User Dashboard" -t epic -p 1
# Returns: bd-abc123

# Create subtasks
agent issues create "Design dashboard layout" -t task -p 1 --epic bd-abc123
agent issues create "Implement data fetching" -t task -p 1 --epic bd-abc123
agent issues create "Add charts" -t feature -p 2 --epic bd-abc123

# View progress
agent issues epics list bd-abc123
agent issues stats
```

### Example 2: Bug Investigation

```bash
# Create bug
agent issues create "Login fails on Safari" -t bug -p 0 -l browser,auth,critical

# Claim and investigate
agent issues update bd-456 --status in_progress --assignee agent-007

# Discover root cause
agent issues create "Auth cookies not set correctly" -t bug -p 0 \
  --deps discovered-from:bd-456 \
  --label backend,auth

# Add investigation notes
agent issues comments add bd-456 "Root cause: SameSite cookie attribute"

# Fix and close
agent issues close bd-456 --reason "Fixed cookie settings, tested on Safari 17"
```

### Example 3: Release Planning

```bash
# Create release epic
agent issues create "v2.0 Release" -t epic -p 1 -l release,v2.0

# Add feature epics
agent issues create "New Auth System" -t epic -p 1 --epic bd-release --label v2.0
agent issues create "API v2" -t epic -p 1 --epic bd-release --label v2.0

# Track progress
agent issues list --label v2.0 --status open
agent issues list --label v2.0 --status closed

# Mark blockers
agent issues label add bd-789 release-blocker
agent issues list --label release-blocker
```

---

**Version:** 0.20.1  
**Last Updated:** 2025-11-16

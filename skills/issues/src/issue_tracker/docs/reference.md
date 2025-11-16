# CLI Command Reference
#  Quickstart

Get up and running with  in 2 minutes.

## Installation

```bash
uvx issues --help
```

## Initialize

First time in a repository:

```bash
# Basic setup
issues init
```

The wizard will:
- Create `./issues` directory and database
- Auto-start daemon for sync

## Your First Issues

```bash
# Create a few issues
./issues create "Set up database" -p 1 -t task
./issues create "Create API" -p 2 -t feature
./issues create "Add authentication" -p 2 -t feature

# List them
./issues list
```

**Note:** Issue IDs are hash-based (e.g., `bd-a1b2`, `bd-f14c`) to prevent collisions when multiple agents/branches work concurrently.

## Hierarchical Issues (Epics)

For large features, use hierarchical IDs to organize work:

```bash
# Create epic (generates parent hash ID)
./issues create "Auth System" -t epic -p 1
# Returns: bd-a3f8e9

# Create child tasks (automatically get .1, .2, .3 suffixes)
./issues create "Design login UI" -p 1       # bd-a3f8e9.1
./issues create "Backend validation" -p 1    # bd-a3f8e9.2
./issues create "Integration tests" -p 1     # bd-a3f8e9.3

# View hierarchy
./issues dep tree bd-a3f8e9
```

Output:
```
🌲 Dependency tree for bd-a3f8e9:

→ bd-a3f8e9: Auth System [epic] [P1] (open)
  → bd-a3f8e9.1: Design login UI [P1] (open)
  → bd-a3f8e9.2: Backend validation [P1] (open)
  → bd-a3f8e9.3: Integration tests [P1] (open)
```

## Add Dependencies

```bash
# API depends on database
./issues dep add bd-2 bd-1

# Auth depends on API
./issues dep add bd-3 bd-2

# View the tree
./issues dep tree bd-3
```

Output:
```
🌲 Dependency tree for bd-3:

→ bd-3: Add authentication [P2] (open)
  → bd-2: Create API [P2] (open)
    → bd-1: Set up database [P1] (open)
```

## Find Ready Work

```bash
./issues ready
```

Output:
```
📋 Ready work (1 issues with no blockers):

1. [P1] bd-1: Set up database
```

Only bd-1 is ready because bd-2 and bd-3 are blocked!

## Work the Queue

```bash
# Start working on bd-1
./issues update bd-1 --status in_progress

# Complete it
./issues close bd-1 --reason "Database setup complete"

# Check ready work again
./issues ready
```

Now bd-2 is ready! 🎉

## Track Progress

```bash
# See blocked issues
./issues blocked

# View statistics
./issues stats
```

## Database Location

By default: `~/./default.db`

You can use project-specific databases:

```bash
./issues --db ./my-project.db create "Task"
```

## Next Steps

- Add labels: `./issues create "Task" -l "backend,urgent"`
- Filter ready work: `./issues ready --priority 1`
- Search issues: `./issues list --status open`
- Detect cycles: `./issues dep cycles`

See [README.md](README.md) for full documentation.

## Basic Operations

### Check Status

```bash
# Check database path and daemon status
issues info --json

# Example output:
# {
#   "database_path": "/path/to/./.db",
#   "issue_prefix": "bd",
#   "daemon_running": true,
#   "agent_mail_enabled": false
# }
```

### Find Work

```bash
# Find ready work (no blockers)
issues ready --json

# Find stale issues (not updated recently)
issues stale --days 30 --json                    # Default: 30 days
issues stale --days 90 --status in_progress --json  # Filter by status
issues stale --limit 20 --json                   # Limit results
```

## Issue Management

### Create Issues

```bash
# Basic creation
# IMPORTANT: Always quote titles and descriptions with double quotes
issues create "Issue title" -t bug|feature|task -p 0-4 -d "Description" --json

# Create with explicit ID (for parallel workers)
issues create "Issue title" --id worker1-100 -p 1 --json

# Create with labels (--labels or --label work)
issues create "Issue title" -t bug -p 1 -l bug,critical --json
issues create "Issue title" -t bug -p 1 --label bug,critical --json

# Examples with special characters (all require quoting):
issues create "Fix: auth doesn't validate tokens" -t bug -p 1 --json
issues create "Add support for OAuth 2.0" -d "Implement RFC 6749 (OAuth 2.0 spec)" --json

# Create multiple issues from markdown file
issues create -f feature-plan.md --json

# Create epic with hierarchical child tasks
issues create "Auth System" -t epic -p 1 --json         # Returns: bd-a3f8e9
issues create "Login UI" -p 1 --json                     # Auto-assigned: bd-a3f8e9.1
issues create "Backend validation" -p 1 --json           # Auto-assigned: bd-a3f8e9.2
issues create "Tests" -p 1 --json                        # Auto-assigned: bd-a3f8e9.3

# Create and link discovered work (one command)
issues create "Found bug" -t bug -p 1 --deps discovered-from:<parent-id> --json
```

### Update Issues

```bash
# Update one or more issues
issues update <id> [<id>...] --status in_progress --json
issues update <id> [<id>...] --priority 1 --json

# Edit issue fields in $EDITOR (HUMANS ONLY - not for agents)
# NOTE: This command is intentionally NOT exposed via the MCP server
# Agents should use 'issues update' with field-specific parameters instead
issues edit <id>                    # Edit description
issues edit <id> --title            # Edit title
issues edit <id> --design           # Edit design notes
issues edit <id> --notes            # Edit notes
issues edit <id> --acceptance       # Edit acceptance criteria
```

### Close/Reopen Issues

```bash
# Complete work (supports multiple IDs)
issues close <id> [<id>...] --reason "Done" --json

# Reopen closed issues (supports multiple IDs)
issues reopen <id> [<id>...] --reason "Reopening" --json
```

### View Issues

```bash
# Show dependency tree
issues dep tree <id>

# Get issue details (supports multiple IDs)
issues show <id> [<id>...] --json
```

## Dependencies & Labels

### Dependencies

```bash
# Link discovered work (old way - two commands)
issues dep add <discovered-id> <parent-id> --type discovered-from

# Create and link in one command (new way - preferred)
issues create "Issue title" -t bug -p 1 --deps discovered-from:<parent-id> --json
```

### Labels

```bash
# Label management (supports multiple IDs)
issues label add <id> [<id>...] <label> --json
issues label remove <id> [<id>...] <label> --json
issues label list <id> --json
issues label list-all --json
```

## Filtering & Search

### Basic Filters

```bash
# Filter by status, priority, type
issues list --status open --priority 1 --json               # Status and priority
issues list --assignee alice --json                         # By assignee
issues list --type bug --json                               # By issue type
issues list --id bd-123,bd-456 --json                       # Specific IDs
```

### Label Filters

```bash
# Labels (AND: must have ALL)
issues list --label bug,critical --json

# Labels (OR: has ANY)
issues list --label-any frontend,backend --json
```

### Text Search

```bash
# Title search (substring)
issues list --title "auth" --json

# Pattern matching (case-insensitive substring)
issues list --title-contains "auth" --json                  # Search in title
issues list --desc-contains "implement" --json              # Search in description
issues list --notes-contains "TODO" --json                  # Search in notes
```

### Date Range Filters

```bash
# Date range filters (YYYY-MM-DD or RFC3339)
issues list --created-after 2024-01-01 --json               # Created after date
issues list --created-before 2024-12-31 --json              # Created before date
issues list --updated-after 2024-06-01 --json               # Updated after date
issues list --updated-before 2024-12-31 --json              # Updated before date
issues list --closed-after 2024-01-01 --json                # Closed after date
issues list --closed-before 2024-12-31 --json               # Closed before date
```

### Empty/Null Checks

```bash
# Empty/null checks
issues list --empty-description --json                      # Issues with no description
issues list --no-assignee --json                            # Unassigned issues
issues list --no-labels --json                              # Issues with no labels
```

### Priority Ranges

```bash
# Priority ranges
issues list --priority-min 0 --priority-max 1 --json        # P0 and P1 only
issues list --priority-min 2 --json                         # P2 and below
```

### Combine Filters

```bash
# Combine multiple filters
issues list --status open --priority 1 --label-any urgent,critical --no-assignee --json
```

## Advanced Operations

### Cleanup

```bash
# Clean up closed issues (bulk deletion)
issues cleanup --force --json                                   # Delete ALL closed issues
issues cleanup --older-than 30 --force --json                   # Delete closed >30 days ago
issues cleanup --dry-run --json                                 # Preview what would be deleted
issues cleanup --older-than 90 --cascade --force --json         # Delete old + dependents
```

### Duplicate Detection & Merging

```bash
# Find and merge duplicate issues
issues duplicates                                          # Show all duplicates
issues duplicates --auto-merge                             # Automatically merge all
issues duplicates --dry-run                                # Preview merge operations

# Merge specific duplicate issues
issues merge <source-id...> --into <target-id> --json      # Consolidate duplicates
issues merge bd-42 bd-43 --into bd-41 --dry-run            # Preview merge
```

### Compaction (Memory Decay)

```bash
# Agent-driven compaction
issues compact --analyze --json                           # Get candidates for review
issues compact --analyze --tier 1 --limit 10 --json       # Limited batch
issues compact --apply --id bd-42 --summary summary.txt   # Apply compaction
issues compact --apply --id bd-42 --summary - < summary.txt  # From stdin
issues compact --stats --json                             # Show statistics

# Legacy AI-powered compaction (requires ANTHROPIC_API_KEY)
issues compact --auto --dry-run --all                     # Preview
issues compact --auto --all --tier 1                      # Auto-compact tier 1

# Restore compacted issue from git history
issues restore <id>  # View full history at time of compaction
```

### Rename Prefix

```bash
# Rename issue prefix (e.g., from 'knowledge-work-' to 'kw-')
issues rename-prefix kw- --dry-run  # Preview changes
issues rename-prefix kw- --json     # Apply rename
```

## Database Management

### Import/Export

```bash
# Export issues to JSONL
issues export -o ./issues.jsonl                 # Export all issues
issues export -o ./issues.jsonl --json          # JSON output

# Import issues from JSONL
issues import -i ./issues.jsonl --dry-run      # Preview changes
issues import -i ./issues.jsonl                # Import and update issues
issues import -i ./issues.jsonl --dedupe-after # Import + detect duplicates

# Note: Import automatically handles missing parents!
# - If a hierarchical child's parent is missing (e.g., bd-abc.1 but no bd-abc)
# - issues will search the JSONL history for the parent
# - If found, creates a tombstone placeholder (Status=Closed, Priority=4)
# - Dependencies are also resurrected on best-effort basis
# - This prevents import failures after parent deletion
```

#### JSONL Schema

The import/export format is line-delimited JSON (JSONL) where each line is a complete issue object.

**Exported fields:**
```json
{
  "id": "bd-a1b2",
  "title": "Fix authentication bug",
  "description": "Users cannot log in",
  "status": "open",
  "priority": 1,
  "type": "bug",
  "assignee": "john",
  "epic_id": "bd-xyz9",
  "labels": ["auth", "urgent"],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:20:00",
  "closed_at": null,
  "project_id": "my-project"
}
```

**Import behavior:**

- **Required fields**: `id`, `title`
- **Optional fields**: All other fields are optional with sensible defaults
- **Timestamps**: `created_at`, `updated_at`, `closed_at` are currently exported but not imported (generated automatically)
- **Project ID**: `project_id` is exported but not imported (managed by workspace)

**For new issues (create):**
- Uses all provided fields except timestamps and project_id
- Generates new timestamps automatically
- Assigns to current project

**For existing issues (update):**
- Updates: `title`, `description`, `priority`, `assignee`, `epic_id`, `status`, `labels`
- Preserves: Original `created_at`, current `project_id`
- Regenerates: `updated_at` timestamp
- Status changes use proper state transitions (cannot violate state machine rules)

**Field value formats:**
- `status`: String - "open", "in_progress", "blocked", "resolved", "closed", "archived"
- `priority`: Integer - 0 (critical), 1 (high), 2 (medium), 3 (low), 4 (backlog)
- `type`: String - "bug", "feature", "task", "epic", "chore"
- `labels`: Array of strings
- Timestamps: ISO 8601 format (YYYY-MM-DDTHH:MM:SS)


### Daemon Management

See [docs/DAEMON.md](DAEMON.md) for complete daemon management reference.

```bash
# List all running daemons
issues daemons list --json

# Check health (version mismatches, stale sockets)
issues daemons health --json

# Stop/restart specific daemon
issues daemons stop /path/to/workspace --json
issues daemons restart 12345 --json  # By PID

# View daemon logs
issues daemons logs /path/to/workspace -n 100
issues daemons logs 12345 -f  # Follow mode

# Stop all daemons
issues daemons killall --json
issues daemons killall --force --json  # Force kill if graceful fails
```

### Sync Operations

```bash
# Manual sync (force immediate export/import/commit/push)
issues sync

# What it does:
# 1. Export pending changes to JSONL
# 2. Commit to git
# 3. Pull from remote
# 4. Import any updates
# 5. Push to remote
```

## Issue Types

- `bug` - Something broken that needs fixing
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature composed of multiple issues (supports hierarchical children)
- `chore` - Maintenance work (dependencies, tooling)

**Hierarchical children:** Epics can have child issues with dotted IDs (e.g., `bd-a3f8e9.1`, `bd-a3f8e9.2`). Children are auto-numbered sequentially. Up to 3 levels of nesting supported.

## Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (nice-to-have features, minor bugs)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

## Dependency Types

- `blocks` - Hard dependency (issue X blocks issue Y)
- `related` - Soft relationship (issues are connected)
- `parent-child` - Epic/subtask relationship
- `discovered-from` - Track issues discovered during work

Only `blocks` dependencies affect the ready work queue.

**Note:** When creating an issue with a `discovered-from` dependency, the new issue automatically inherits the parent's `source_repo` field.

## Output Formats

### JSON Output (Recommended for Agents)

Always use `--json` flag for programmatic use:

```bash
# Single issue
issues show bd-42 --json

# List of issues
issues ready --json

# Operation result
issues create "Issue" -p 1 --json
```

### Human-Readable Output

Default output without `--json`:

```bash
issues ready
# bd-42  Fix authentication bug  [P1, bug, in_progress]
# bd-43  Add user settings page  [P2, feature, open]
```

## Common Patterns for AI Agents

### Claim and Complete Work

```bash
# 1. Find available work
issues ready --json

# 2. Claim issue
issues update bd-42 --status in_progress --json

# 3. Work on it...

# 4. Close when done
issues close bd-42 --reason "Implemented and tested" --json
```

### Discover and Link Work

```bash
# While working on bd-100, discover a bug

# Old way (two commands):
issues create "Found auth bug" -t bug -p 1 --json  # Returns bd-101
issues dep add bd-101 bd-100 --type discovered-from

# New way (one command):
issues create "Found auth bug" -t bug -p 1 --deps discovered-from:bd-100 --json
```

### Batch Operations

```bash
# Update multiple issues at once
issues update bd-41 bd-42 bd-43 --priority 0 --json

# Close multiple issues
issues close bd-41 bd-42 bd-43 --reason "Batch completion" --json

# Add label to multiple issues
issues label add bd-41 bd-42 bd-43 urgent --json
```

### Session Workflow

```bash
# Start of session
issues ready --json  # Find work

# During session
issues create "..." -p 1 --json
issues update bd-42 --status in_progress --json
# ... work ...

# End of session (IMPORTANT!)
issues sync  # Force immediate sync, bypass debounce
```

**ALWAYS run `issues sync` at end of agent sessions** to ensure changes are committed/pushed immediately.

## See Also

- [AGENTS.md](../AGENTS.md) - Main agent workflow guide
- [DAEMON.md](DAEMON.md) - Daemon management and event-driven mode
- [GIT_INTEGRATION.md](GIT_INTEGRATION.md) - Git workflows and merge strategies
- [LABELS.md](../LABELS.md) - Label system guide
- [README.md](../README.md) - User documentation

# Labels in

Labels provide flexible, multi-dimensional categorization for issues beyond the structured fields (status, priority, type). Use labels for cross-cutting concerns, technical metadata, and contextual tagging without schema changes.

## Design Philosophy

**When to use labels vs. structured fields:**

- **Structured fields** (status, priority, type) → Core workflow state
  - Status: Where the issue is in the workflow (`open`, `in_progress`, `blocked`, `closed`)
  - Priority: How urgent (0-4)
  - Type: What kind of work (`bug`, `feature`, `task`, `epic`, `chore`)

- **Labels** → Everything else
  - Technical metadata (`backend`, `frontend`, `api`, `database`)
  - Domain/scope (`auth`, `payments`, `search`, `analytics`)
  - Effort estimates (`small`, `medium`, `large`)
  - Quality gates (`needs-review`, `needs-tests`, `breaking-change`)
  - Team/ownership (`team-infra`, `team-product`)
  - Release tracking (`v1.0`, `v2.0`, `backport-candidate`)

## Quick Start

```bash
# Add labels when creating issues
issues create "Fix auth bug" -t bug -p 1 -l auth,backend,urgent

# Add labels to existing issues
issues label add bd-42 security
issues label add bd-42 breaking-change

# List issue labels
issues label list bd-42

# Remove a label
issues label remove bd-42 urgent

# List all labels in use
issues label list-all

# Filter by labels (AND - must have ALL)
issues list --label backend,auth

# Filter by labels (OR - must have AT LEAST ONE)
issues list --label-any frontend,backend

# Combine filters
issues list --status open --priority 1 --label security
```

## Common Label Patterns

### 1. Technical Component Labels

Identify which part of the system:
```bash
backend
frontend
api
database
infrastructure
cli
ui
mobile
```

**Example:**
```bash
issues create "Add GraphQL endpoint" -t feature -p 2 -l backend,api
issues create "Update login form" -t task -p 2 -l frontend,auth,ui
```

### 2. Domain/Feature Area

Group by business domain:
```bash
auth
payments
search
analytics
billing
notifications
reporting
admin
```

**Example:**
```bash
issues list --label payments --status open  # All open payment issues
issues list --label-any auth,security       # Security-related work
```

### 3. Size/Effort Estimates

Quick effort indicators:
```bash
small     # < 1 day
medium    # 1-3 days
large     # > 3 days
```

**Example:**
```bash
# Find small quick wins
issues ready --json | jq '.[] | select(.labels[] == "small")'
```

### 4. Quality Gates

Track what's needed before closing:
```bash
needs-review
needs-tests
needs-docs
breaking-change
```

**Example:**
```bash
issues label add bd-42 needs-review
issues list --label needs-review --status in_progress
```

### 5. Release Management

Track release targeting:
```bash
v1.0
v2.0
backport-candidate
release-blocker
```

**Example:**
```bash
issues list --label v1.0 --status open    # What's left for v1.0?
issues label add bd-42 release-blocker
```

## Filtering by Labels

### AND Filtering (--label)
All specified labels must be present:

```bash
# Issues that are BOTH backend AND urgent
issues list --label backend,urgent

# Open bugs that need review AND tests
issues list --status open --type bug --label needs-review,needs-tests
```

### OR Filtering (--label-any)
At least one specified label must be present:

```bash
# Issues in frontend OR backend
issues list --label-any frontend,backend

# Security or auth related
issues list --label-any security,auth
```

### Combining AND/OR
Mix both filters for complex queries:

```bash
# Backend issues that are EITHER urgent OR a blocker
issues list --label backend --label-any urgent,release-blocker

# Frontend work that needs BOTH review and tests, but in any component
issues list --label needs-review,needs-tests --label-any frontend,ui,mobile
```

## Workflow Examples

### Triage Workflow
```bash
# Create untriaged issue
issues create "Crash on login" -t bug -p 1 -l needs-triage

# During triage, add context
issues label add bd-42 auth
issues label add bd-42 backend
issues label add bd-42 urgent
issues label remove bd-42 needs-triage

# Find untriaged issues
issues list --label needs-triage
```

### Quality Gate Workflow
```bash
# Start work
issues update bd-42 --status in_progress

# Mark quality requirements
issues label add bd-42 needs-tests
issues label add bd-42 needs-docs

# Before closing, verify
issues label list bd-42
# ... write tests and docs ...
issues label remove bd-42 needs-tests
issues label remove bd-42 needs-docs

# Close when gates satisfied
issues close bd-42
```

### Release Planning
```bash
# Tag issues for v1.0
issues label add bd-42 v1.0
issues label add bd-43 v1.0
issues label add bd-44 v1.0

# Track v1.0 progress
issues list --label v1.0 --status closed    # Done
issues list --label v1.0 --status open      # Remaining
issues stats  # Overall progress

# Mark critical items
issues label add bd-45 v1.0
issues label add bd-45 release-blocker
```

### Component-Based Work Distribution
```bash
# Backend team picks up work
issues ready --json | jq '.[] | select(.labels[]? == "backend")'

# Frontend team finds small tasks
issues list --status open --label frontend,small

# Find help-wanted items for new contributors
issues list --label help-wanted,good-first-issue
```

## Label Management

### Listing Labels
```bash
# Labels on a specific issue
issues label list bd-42

# All labels in database with usage counts
issues label list-all

# JSON output for scripting
issues label list-all --json
```

Output:
```json
[
  {"label": "auth", "count": 5},
  {"label": "backend", "count": 12},
  {"label": "frontend", "count": 8}
]
```

### Bulk Operations

Add labels in batch during creation:
```bash
issues create "Issue" -l label1,label2,label3
```

Script to add label to multiple issues:
```bash
# Add "needs-review" to all in_progress issues
issues list --status in_progress --json | jq -r '.[].id' | while read id; do
  issues label add "$id" needs-review
done
```

Remove label from multiple issues:
```bash
# Remove "urgent" from closed issues
issues list --status closed --label urgent --json | jq -r '.[].id' | while read id; do
  issues label remove "$id" urgent
done
```

## Integration with Git Workflow

Labels are automatically synced to `./issues.jsonl` along with all issue data:

```bash
# Make changes
issues create "Fix bug" -l backend,urgent
issues label add bd-42 needs-review

# Auto-exported after 5 seconds (or use git hooks for immediate export)
git add ./issues.jsonl
git commit -m "Add backend issue"

# After git pull, labels are auto-imported
git pull
issues list --label backend  # Fresh data including labels
```

## Markdown Import/Export

Labels are preserved when importing from markdown:

```markdown
# Fix Authentication Bug

### Type
bug

### Priority
1

### Labels
auth, backend, urgent, needs-review

### Description
Users can't log in after recent deployment.
```

```bash
issues create -f issue.md
# Creates issue with all four labels
```

## Best Practices

### 1. Establish Conventions Early
Document your team's label taxonomy:
```bash
# Add to project README or CONTRIBUTING.md
- Use lowercase, hyphen-separated (e.g., `good-first-issue`)
- Prefix team labels (e.g., `team-infra`, `team-product`)
- Use consistent size labels (`small`, `medium`, `large`)
```

### 2. Don't Overuse Labels
Labels are flexible, but too many can cause confusion. Prefer:
- 5-10 core technical labels (`backend`, `frontend`, `api`, etc.)
- 3-5 domain labels per project
- Standard process labels (`needs-review`, `needs-tests`)
- Release labels as needed

### 3. Clean Up Unused Labels
Periodically review:
```bash
issues label list-all
# Remove obsolete labels from issues
```

### 4. Use Labels for Filtering, Not Search
Labels are for categorization, not free-text search:
- ✅ Good: `backend`, `auth`, `urgent`
- ❌ Bad: `fix-the-login-bug`, `john-asked-for-this`

### 5. Combine with Dependencies
Labels + dependencies = powerful organization:
```bash
# Epic with labeled subtasks
issues create "Auth system rewrite" -t epic -p 1 -l auth,v2.0
issues create "Implement JWT" -t task -p 1 -l auth,backend --deps parent-child:bd-42
issues create "Update login UI" -t task -p 1 -l auth,frontend --deps parent-child:bd-42

# Find all v2.0 auth work
issues list --label auth,v2.0
```

## AI Agent Usage

Labels are especially useful for AI agents managing complex workflows:

```bash
# Auto-label discovered work
issues create "Found TODO in auth.go" -t task -p 2 -l auto-generated,technical-debt

# Filter for agent review
issues list --label needs-review --status in_progress --json

# Track automation metadata
issues label add bd-42 ai-generated
issues label add bd-42 needs-human-review
```

Example agent workflow:
```bash
# Agent discovers issues during refactor
issues create "Extract validateToken function" -t chore -p 2 \
  -l technical-debt,backend,auth,small \
  --deps discovered-from:bd-10

# Agent marks work for review
issues update bd-42 --status in_progress
# ... agent does work ...
issues label add bd-42 needs-review
issues label add bd-42 ai-generated

# Human reviews and approves
issues label remove bd-42 needs-review
issues label add bd-42 approved
issues close bd-42
```

## Advanced Patterns

### Component Matrix
Track issues across multiple dimensions:
```bash
# Backend + auth + high priority
issues list --label backend,auth --priority 1

# Any frontend work that's small
issues list --label-any frontend,ui --label small

# Critical issues across all components
issues list --priority 0 --label-any backend,frontend,infrastructure
```

### Sprint Planning
```bash
# Label issues for sprint
for id in bd-42 bd-43 bd-44 bd-45; do
  issues label add "$id" sprint-12
done

# Track sprint progress
issues list --label sprint-12 --status closed    # Velocity
issues list --label sprint-12 --status open      # Remaining
issues stats | grep "In Progress"                # Current WIP
```

### Technical Debt Tracking
```bash
# Mark debt
issues create "Refactor legacy parser" -t chore -p 3 -l technical-debt,large

# Find debt to tackle
issues list --label technical-debt --label small
issues list --label technical-debt --priority 1  # High-priority debt
```

### Breaking Change Coordination
```bash
# Identify breaking changes
issues label add bd-42 breaking-change
issues label add bd-42 v2.0

# Find all breaking changes for next major release
issues list --label breaking-change,v2.0

# Ensure they're documented
issues list --label breaking-change --label needs-docs
```

## Troubleshooting

### Labels Not Showing in List
Labels require explicit fetching. The `issues list` command shows issues but not labels in human output (only in JSON).

```bash
# See labels in JSON
issues list --json | jq '.[] | {id, labels}'

# See labels for specific issue
issues show bd-42 --json | jq '.labels'
issues label list bd-42
```

### Label Filtering Not Working
Check label names for exact matches (case-sensitive):
```bash
# These are different labels:
issues label add bd-42 Backend    # Capital B
issues list --label backend       # Won't match

# List all labels to see exact names
issues label list-all
```

### Syncing Labels with Git
Labels are included in `./issues.jsonl` export. If labels seem out of sync:
```bash
# Force export
issues export -o ./issues.jsonl

# After pull, force import
issues import -i ./issues.jsonl
```
## Renaming Prefix

Change the issue prefix for all issues in your database. This is useful if your prefix is too long or you want to standardize naming.

```bash
# Preview changes without applying
issues rename-prefix kw- --dry-run

# Rename from current prefix to new prefix
issues rename-prefix kw-

# JSON output
issues rename-prefix kw- --json
```

The rename operation:
- Updates all issue IDs (e.g., `knowledge-work-1` → `kw-1`)
- Updates all text references in titles, descriptions, design notes, etc.
- Updates dependencies and labels
- Updates the counter table and config

**Prefix validation rules:**
- Max length: 8 characters
- Allowed characters: lowercase letters, numbers, hyphens
- Must start with a letter
- Must end with a hyphen (or will be trimmed to add one)
- Cannot be empty or just a hyphen

Example workflow:
```bash
# You have issues like knowledge-work-1, knowledge-work-2, etc.
issues list  # Shows knowledge-work-* issues

# Preview the rename
issues rename-prefix kw- --dry-run

# Apply the rename
issues rename-prefix kw-

# Now you have kw-1, kw-2, etc.
issues list  # Shows kw-* issues
```

## Duplicate Detection

Find issues with identical content using automated duplicate detection:

```bash
# Find all content duplicates in the database
issues duplicates

# Show duplicates in JSON format
issues duplicates --json

# Automatically merge all duplicates
issues duplicates --auto-merge

# Preview what would be merged
issues duplicates --dry-run

# Detect duplicates during import
issues import -i issues.jsonl --dedupe-after
```

**How it works:**
- Groups issues by content hash (title, description, design, acceptance criteria)
- Only groups issues with matching status (open with open, closed with closed)
- Chooses merge target by reference count (most referenced) or smallest ID
- Reports duplicate groups with suggested merge commands

**Example output:**

```
🔍 Found 3 duplicate group(s):

━━ Group 1: Fix authentication bug
→ bd-10 (open, P1, 5 references)
  bd-42 (open, P1, 0 references)
  Suggested: issues merge bd-42 --into bd-10

💡 Run with --auto-merge to execute all suggested merges
```

**AI Agent Workflow:**

1. **Periodic scans**: Run `issues duplicates` to check for duplicates
2. **During import**: Use `--dedupe-after` to detect duplicates after collision resolution
3. **Auto-merge**: Use `--auto-merge` to automatically consolidate duplicates
4. **Manual review**: Use `--dry-run` to preview merges before executing

## Merging Duplicate Issues

Consolidate duplicate issues into a single issue while preserving dependencies and references:

```bash
# Merge bd-42 and bd-43 into bd-41
issues merge bd-42 bd-43 --into bd-41

# Merge multiple duplicates at once
issues merge bd-10 bd-11 bd-12 --into bd-10

# Preview merge without making changes
issues merge bd-42 bd-43 --into bd-41 --dry-run

# JSON output
issues merge bd-42 bd-43 --into bd-41 --json
```

**What the merge command does:**
1. **Validates** all issues exist and prevents self-merge
2. **Closes** source issues with reason `Merged into bd-X`
3. **Migrates** all dependencies from source issues to target
4. **Updates** text references across all issue descriptions, notes, design, and acceptance criteria

**Example workflow:**

```bash
# You discover bd-42 and bd-43 are duplicates of bd-41
issues show bd-41 bd-42 bd-43

# Preview the merge
issues merge bd-42 bd-43 --into bd-41 --dry-run

# Execute the merge
issues merge bd-42 bd-43 --into bd-41
# ✓ Merged 2 issue(s) into bd-41

# Verify the result
issues show bd-41  # Now has dependencies from bd-42 and bd-43
issues dep tree bd-41  # Shows unified dependency tree
```

**Important notes:**
- Source issues are permanently closed (status: `closed`)
- All dependencies pointing to source issues are redirected to target
- Text references like "see bd-42" are automatically rewritten to "see bd-41"
- Operation cannot be undone (but git history preserves the original state)
- Not yet supported in daemon mode (use `--no-daemon` flag)

**AI Agent Workflow:**

When agents discover duplicate issues, they should:
1. Search for similar issues: `issues list --json | grep "similar text"`
2. Compare issue details: `issues show bd-41 bd-42 --json`
3. Merge duplicates: `issues merge bd-42 --into bd-41`
4. File a discovered-from issue if needed: `issues create "Found duplicates during bd-X" --deps discovered-from:bd-X`

## Git Worktrees

**⚠️ Important Limitation:** Daemon mode does not work correctly with `git worktree`.

**The Problem:**
Git worktrees share the same `.git` directory and thus share the same `.` database. The daemon doesn't know which branch each worktree has checked out, which can cause it to commit/push to the wrong branch.

**What you lose without daemon mode:**
- **Auto-sync** - No automatic commit/push of changes (use `issues sync` manually)
- **MCP server** - The -mcp server requires daemon mode for multi-repo support
- **Background watching** - No automatic detection of remote changes

**Solutions for Worktree Users:**

1. **Use `--no-daemon` flag** (recommended):
   ```bash
   issues --no-daemon ready
   issues --no-daemon create "Fix bug" -p 1
   issues --no-daemon update bd-42 --status in_progress
   ```

2. **Disable daemon via environment variable** (for entire worktree session):
   ```bash
   export _NO_DAEMON=1
   issues ready  # All commands use direct mode
   ```

3. **Disable auto-start** (less safe, still warns):
   ```bash
   export _AUTO_START_DAEMON=false
   ```

**Automatic Detection:**
issues automatically detects when you're in a worktree and shows a prominent warning if daemon mode is active. The `--no-daemon` mode works correctly with worktrees since it operates directly on the database without shared state.

**Why It Matters:**
The daemon maintains its own view of the current working directory and git state. When multiple worktrees share the same `.` database, the daemon may commit changes intended for one branch to a different branch, leading to confusion and incorrect git history.

## Handling Git Merge Conflicts

**With hash-based IDs (v0.20.1+), ID collisions are eliminated.** Different issues get different hash IDs, so concurrent creation doesn't cause conflicts.

### Understanding Same-ID Scenarios

When you encounter the same ID during import, it's an **update operation**, not a collision:

- Hash IDs are content-based and remain stable across updates
- Same ID + different fields = normal update to existing issue
- issues automatically applies updates when importing

**Preview changes before importing:**
```bash
# After git merge or pull
issues import -i ./issues.jsonl --dry-run

# Output shows:
# Exact matches (idempotent): 15
# New issues: 5
# Updates: 3
#
# Issues to be updated:
#   bd-a3f2: Fix authentication (changed: priority, status)
#   bd-b8e1: Add feature (changed: description)
```

### Git Merge Conflicts

The conflicts you'll encounter are **git merge conflicts** in the JSONL file when the same issue was modified on both branches (different timestamps/fields). This is not an ID collision.

**Resolution:**
```bash
# After git merge creates conflict
git checkout --theirs ./.jsonl  # Accept remote version
# OR
git checkout --ours ./.jsonl    # Keep local version
# OR manually resolve in editor (keep line with newer updated_at)

# Import the resolved JSONL
issues import -i ./.jsonl

# Commit the merge
git add ./.jsonl
git commit
```

### Advanced: Intelligent Merge Tools

For Git merge conflicts in `./issues.jsonl`, consider using **[-merge](https://github.com/neongreen/mono/tree/main/-merge)** - a specialized merge tool by @neongreen that:

- Matches issues across conflicted JSONL files
- Merges fields intelligently (e.g., combines labels, picks newer timestamps)
- Resolves conflicts automatically where possible
- Leaves remaining conflicts for manual resolution
- Works as a Git/jujutsu merge driver

After using -merge to resolve the git conflict, just run `issues import` to update your database.

## Custom Git Hooks

For immediate export (no 5-second wait) and guaranteed import after git operations, install the git hooks:

### Using the Installer

```bash
cd examples/git-hooks
./install.sh
```

### Manual Setup

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
issues export -o ./issues.jsonl
git add ./issues.jsonl
```

Create `.git/hooks/post-merge`:
```bash
#!/bin/bash
issues import -i ./issues.jsonl
```

Create `.git/hooks/post-checkout`:
```bash
#!/bin/bash
issues import -i ./issues.jsonl
```

Make hooks executable:
```bash
chmod +x .git/hooks/pre-commit .git/hooks/post-merge .git/hooks/post-checkout
```

**Note:** Auto-sync is already enabled by default, so git hooks are optional. They're useful if you need immediate export or guaranteed import after git operations.

## Extensible Database

issues uses SQLite, which you can extend with your own tables and queries. This allows you to:

- Add custom metadata to issues
- Build integrations with other tools
- Implement custom workflows
- Create reports and analytics

**See [EXTENDING.md](EXTENDING.md) for complete documentation:**
- Database schema and structure
- Adding custom tables
- Joining with issue data
- Example integrations
- Best practices

**Example use case:**
```sql
-- Add time tracking table
CREATE TABLE time_entries (
    id INTEGER PRIMARY KEY,
    issue_id TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(issue_id) REFERENCES issues(id)
);

-- Query total time per issue
SELECT i.id, i.title, SUM(t.duration_minutes) as total_minutes
FROM issues i
LEFT JOIN time_entries t ON i.id = t.issue_id
GROUP BY i.id;
```

## Architecture: Daemon vs MCP vs

Understanding the role of each component:

###  (Core)
- **SQLite database** - The source of truth for all issues, dependencies, labels
- **Storage layer** - CRUD operations, dependency resolution, collision detection
- **Business logic** - Ready work calculation, merge operations, import/export
- **CLI commands** - Direct database access via `bd` command

### Local Daemon (Per-Project)
- **Lightweight RPC server** - Runs at `./bd.sock` in each project
- **Auto-sync coordination** - Debounced export (5s), git integration, import detection
- **Process isolation** - Each project gets its own daemon for database safety
- **LSP model** - Similar to language servers, one daemon per workspace
- **No global daemon** - Removed in v0.16.0 to prevent cross-project pollution
- **Exclusive lock support** - External tools can prevent daemon interference (see [EXCLUSIVE_LOCK.md](EXCLUSIVE_LOCK.md))

### MCP Server (Optional)
- **Protocol adapter** - Translates MCP calls to daemon RPC or direct CLI
- **Workspace routing** - Finds correct `./bd.sock` based on working directory
- **Stateless** - Doesn't cache or store any issue data itself
- **Editor integration** - Makes issues available to Claude, Cursor, and other MCP clients
- **Single instance** - One MCP server can route to multiple project daemons

**Key principle**: The daemon and MCP server are thin layers. All heavy lifting (dependency graphs, collision resolution, merge logic) happens in the core issues storage layer.

**Why per-project daemons?**
- Complete database isolation between projects
- Git worktree safety (each worktree can disable daemon independently)
- No risk of committing changes to wrong branch
- Simpler mental model - one project, one database, one daemon
- Follows LSP/language server architecture patterns

## Next Steps

- **[README.md](README.md)** - Core features and quick start
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[FAQ.md](FAQ.md)** - Frequently asked questions
- **[CONFIG.md](CONFIG.md)** - Configuration system guide
- **[EXTENDING.md](EXTENDING.md)** - Database extension patterns

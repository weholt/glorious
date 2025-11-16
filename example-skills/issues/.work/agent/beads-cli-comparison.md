# Beads CLI vs Reference Implementation Comparison

## Command Mapping

| Beads Command | Reference Implementation | Status | Notes |
|---------------|-------------------------|--------|-------|
| `bd info` | ❌ Not present | ⚠️ MISSING | Database path, daemon status check |
| `bd create` | ✅ `create_issue()` | ✅ MATCH | Full feature parity |
| `bd update` | ✅ `update_issue()` | ✅ MATCH | Multi-field updates |
| `bd edit` | ❌ Not present | ⚠️ SKIP | Human-only, opens $EDITOR |
| `bd close` | ✅ `close_issue()` | ✅ MATCH | With reason parameter |
| `bd reopen` | ✅ `reopen_issue()` | ✅ MATCH | With reason parameter |
| `bd show` | ✅ `show_issue()` | ✅ MATCH | Multi-ID support |
| `bd list` | ✅ `list_issues()` | ✅ MATCH | 20+ filters |
| `bd ready` | ✅ `ready_issues()` | ✅ MATCH | Unblocked work queue |
| `bd stale` | ✅ `stale_issues()` | ✅ MATCH | Old issues detection |
| `bd dep add` | ✅ `add_dependency()` | ✅ MATCH | Cycle detection |
| `bd dep remove` | ❌ Not present | ⚠️ MISSING | Referenced in Beads but not in reference |
| `bd dep tree` | ✅ `dependency_tree()` | ✅ MATCH | Text/mermaid/json output |
| `bd label add` | ✅ `add_label()` | ✅ MATCH | Multi-ID batch support |
| `bd label remove` | ✅ `remove_label()` | ✅ MATCH | Multi-ID batch support |
| `bd label list` | ✅ `list_labels()` | ✅ MATCH | Per-issue labels |
| `bd label list-all` | ✅ `list_all_labels()` | ✅ MATCH | Global label stats |
| `bd cycles` | ✅ `detect_cycles()` | ✅ MATCH | Full cycle detection |
| `bd cleanup` | ❌ Not present | ⚠️ MISSING | Bulk delete closed issues |
| `bd duplicates` | ❌ Not present | ⚠️ MISSING | Find/merge duplicates |
| `bd merge` | ❌ Not present | ⚠️ MISSING | Merge duplicate issues |
| `bd compact` | ❌ Not present | ⚠️ MISSING | AI-powered memory decay |
| `bd restore` | ✅ `restore_issue()` | ✅ MATCH | Restore archived |
| `bd rename-prefix` | ❌ Not present | ⚠️ MISSING | Rename issue ID prefix |
| `bd import` | ❌ Not present | ⚠️ MISSING | Import from JSONL |
| `bd migrate` | ❌ Not present | ⚠️ SKIP | Database schema migration |
| `bd daemons` | ❌ Not present | ⚠️ SKIP | Daemon management (separate feature) |
| `bd sync` | ❌ Not present | ⚠️ SKIP | Git integration (separate feature) |
| `bd stats` | ✅ `stats()` | ✅ MATCH | Project statistics |
| `bd comment add` | ✅ `add_comment()` | ✅ MATCH | Add comment |
| `bd comment list` | ✅ `list_comments()` | ✅ MATCH | Show all comments |
| `bd blocked` | ✅ `blocked_issues()` | ✅ MATCH | Show blocked issues |
| `bd bulk-create` | ✅ `bulk_create()` | ✅ MATCH | Create from markdown |

## Feature Gap Analysis


### ✅ Present in Both (20 commands)


1. create - Full template support, dependencies, custom IDs

2. update - Multi-field updates

3. close/reopen - With reason tracking

4. show - Multi-ID support

5. list - 20+ filters (status, priority, labels, text search, dates)

6. ready - Unblocked work queue with sorting

7. stale - Find stale issues by days/status

8. dep add - With cycle detection

9. dep tree - Text/mermaid/json visualization

10. label add/remove - Batch operations

11. label list/list-all - Per-issue and global stats

12. cycles - Full cycle detection

13. stats - Comprehensive project stats

14. comment add/list - Comment management

15. blocked - Show blocked issues with blockers

16. restore - Restore archived issues

17. bulk-create - Create from markdown file


### ⚠️ In Beads, Missing from Reference (8 commands)


1. **info** - Database path and daemon status check
   - Priority: MEDIUM
   - Complexity: LOW
   - Note: Simple introspection command

2. **dep remove** - Remove dependency
   - Priority: HIGH
   - Complexity: LOW
   - Note: Critical CRUD operation, likely oversight in reference

3. **cleanup** - Bulk delete closed issues
   - Priority: MEDIUM
   - Complexity: MEDIUM
   - Features: --older-than, --cascade, --dry-run

4. **duplicates** - Find duplicate issues
   - Priority: LOW
   - Complexity: HIGH
   - Note: AI-powered feature, out of scope for MVP

5. **merge** - Merge duplicate issues
   - Priority: LOW
   - Complexity: HIGH
   - Note: Depends on duplicates detection

6. **compact** - Memory decay (compress old issues)
   - Priority: LOW
   - Complexity: HIGH
   - Note: AI-powered, requires LLM integration

7. **rename-prefix** - Rename issue ID prefix
   - Priority: LOW
   - Complexity: MEDIUM
   - Note: Administrative feature

8. **import** - Import from JSONL
   - Priority: MEDIUM
   - Complexity: MEDIUM
   - Note: Useful for data migration


### ⛔ In Beads, Explicitly Excluded (3 commands)


1. **edit** - Human-only, opens $EDITOR
   - Not for programmatic use
   - Agents should use `update` instead

2. **migrate** - Database schema migration
   - Separate concern (Alembic handles this)

3. **daemons** - Daemon management
   - Separate feature (out of scope for CLI MVP)

4. **sync** - Git integration
   - Separate feature (out of scope for CLI MVP)


### ✅ In Reference, Not in Beads (0 commands)


- Reference implementation is a **subset** of Beads

## Critical Observations


### 1. Missing CRUD Operation

**`dep remove`** is mentioned in Beads but not in reference implementation:

- Beads: `bd dep remove <id> <id>`

- Reference: ❌ Missing

- **Action Required:** Must implement to complete dependency management


### 2. Filter Feature Parity

Both implementations support:

- Status, priority, type filters

- Label filters (AND/OR logic)

- Text search (title, description, notes)

- Date range filters (created, updated, closed)

- Empty/null checks (no-assignee, no-labels, empty-description)

- Priority ranges (min/max)

- Assignee filtering

Reference implementation has **more filter options** than Beads shows:

- `--epic` filter

- `--parent` filter

- `--has-blockers` / `--no-blockers`


### 3. Dependency Features

Beads shows:

- `discovered-from` dependency type with automatic source_repo inheritance

- Epic hierarchical children (auto-numbered IDs like `bd-a3f8e9.1`)

Reference implementation has:

- Full `DependencyType` enum: BLOCKS, RELATED, PARENT_CHILD, DISCOVERED_FROM

- **No hierarchical child auto-numbering** (different from Beads)


### 4. Epic Management

Beads shows:

- Create epic: `bd create "Epic" -t epic`

- Auto-numbered children: `bd-a3f8e9.1`, `bd-a3f8e9.2`

Reference implementation has:

- Epic entity and epic-set/epic-clear commands

- **No auto-numbered hierarchical children**


### 5. Output Modes

Both support:

- `--json` flag for programmatic output

- Human-readable table output (default)

Reference implementation uses Rich library for terminal output.

## Recommended Implementation Strategy


### Phase 1: Core MVP (Reference Implementation Baseline)

Extract all 20 commands from reference implementation as-is:

1. create, update, close, reopen, show, list

2. dep add, dep tree, cycles

3. label add/remove/list/list-all

4. ready, blocked, stale, stats

5. comment add/list

6. restore, bulk-create


### Phase 2: Critical Gaps (HIGH priority)


1. **dep remove** - Complete CRUD operations for dependencies

2. **info** - Database introspection command


### Phase 3: Nice-to-Have (MEDIUM priority)


3. **cleanup** - Bulk delete with filters and dry-run

4. **import** - Import from JSONL for data migration


### Phase 4: Advanced (LOW priority - defer)


5. **duplicates** - AI-powered duplicate detection

6. **merge** - Merge duplicate issues

7. **compact** - AI-powered memory decay

8. **rename-prefix** - Administrative feature


### Phase 5: Epic Enhancements (FUTURE)


9. Hierarchical child auto-numbering for epics (Beads feature)

## CLI Name
Per user request: CLI should be called **`issues`** when used in terminal.

Command format:
```bash
issues create "Title" -t bug -p 1
issues list --status open
issues ready --json
```

## Architecture Decisions


### 1. Command Structure

Follow reference implementation:

- Typer-based CLI

- Rich terminal output

- JSON mode for all commands

- Batch operations where applicable


### 2. Filtering

Use reference implementation filters (superset of Beads):

- All 20+ filter parameters

- AND/OR label logic

- Date ranges

- Empty/null checks

- Priority ranges


### 3. Dependencies

Use reference implementation:

- Full `DependencyType` enum

- Cycle detection algorithm

- Graph service for traversal


### 4. Output

Match reference implementation:

- Rich tables for human output

- JSON for programmatic use

- Error handling with best-effort execution

## Next Steps

1. ✅ Extract reference implementation as baseline (20 commands)

2. ⚠️ Implement missing CRUD: `dep remove`

3. ⚠️ Implement `info` command for database introspection

4. 📋 Create task breakdown using spec-to-task.prompt.md format

5. 🎯 Execute extraction plan in 6 groups

6. ✅ Achieve 70%+ test coverage

7. 📖 Document CLI reference for `issues` command

## Summary

**Reference Implementation Coverage: 20/28 Beads commands (71%)**

**Critical Missing:**

- `dep remove` (CRUD gap)

**Important Missing:**

- `info` (introspection)

- `cleanup` (bulk operations)

- `import` (data migration)

**Deferred (out of scope):**

- AI-powered features (duplicates, merge, compact)

- Daemon management

- Git integration

- Database migration (handled by Alembic)

- Human-only editor integration

**Decision:** Start with reference implementation baseline (20 commands), add critical gaps, defer advanced features.

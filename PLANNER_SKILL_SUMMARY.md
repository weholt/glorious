# Planner Skill - Comprehensive Summary

**Last Updated:** 2025-11-17  
**Version:** 0.1.0  
**Package:** glorious-planner

---

## Overview

The Planner skill is an action queue management and task prioritization system for Glorious Agents. It provides a structured way to manage tasks with priority-based sorting, status tracking, and project organization.

### Core Purpose
- Manage task queues for agent workflows
- Prioritize work based on importance and priority levels
- Track task status through state machine (queued → running → blocked → done)
- Integrate with issue tracking systems

---

## Architecture

### Package Structure
```
planner/
├── src/glorious_planner/
│   ├── __init__.py
│   ├── skill.py          # Main skill implementation
│   └── schema.sql        # Database schema
├── tests/
│   └── test_planner.py
└── pyproject.toml
```

### Database Schema

**Table: `planner_queue`**

| Column | Type | Description | Default |
|--------|------|-------------|---------|
| id | INTEGER | Primary key, auto-increment | - |
| issue_id | TEXT | Issue identifier (required) | - |
| priority | INTEGER | Task priority (-100 to 100) | 0 |
| status | TEXT | Task status | 'queued' |
| project_id | TEXT | Project identifier | NULL |
| tags | TEXT | Task tags (currently unused) | NULL |
| important | INTEGER | Important flag (0 or 1) | 0 |
| created_at | TEXT | Creation timestamp | CURRENT_TIMESTAMP |
| updated_at | TEXT | Last update timestamp | NULL |

**Indexes:**
- `idx_planner_status_priority`: Composite index on (status, priority DESC)
- `idx_planner_project`: Index on project_id

### State Machine

Tasks flow through the following states:
```
queued → running → done
           ↓
        blocked → queued (manual transition)
```

**Status Types:**
- `queued`: Task is waiting to be picked up
- `running`: Task is currently being worked on
- `blocked`: Task is blocked by dependencies or issues
- `done`: Task is completed

---

## Commands & API

### CLI Commands

#### 1. **add** - Add a task to the queue
```bash
uv run agent skill planner add <issue_id> [OPTIONS]

Options:
  --priority INTEGER      Task priority (-100 to 100) [default: 0]
  --project-id TEXT       Project identifier
  --important             Mark task as important
```

**Examples:**
```bash
# Add a simple task
uv run agent skill planner add issue-12345

# Add high-priority important task
uv run agent skill planner add issue-12345 --priority 50 --important

# Add task to specific project
uv run agent skill planner add issue-12345 --project-id my-project
```

#### 2. **next** - Get the next task to work on
```bash
uv run agent skill planner next [OPTIONS]

Options:
  --respect-important / --no-respect-important  [default: respect-important]
```

**Priority Logic:**
- With `--respect-important` (default): Sorts by important flag first, then priority
- Without: Sorts only by priority

**Output:**
```
Next task: #42 - issue-12345 ⭐
  Priority: 50
  Project: my-project
```

#### 3. **update** - Update task status
```bash
uv run agent skill planner update <task_id> --status <status>

Status values: queued, running, blocked, done
```

**Examples:**
```bash
# Mark task as running
uv run agent skill planner update 42 --status running

# Mark task as done
uv run agent skill planner update 42 --status done

# Block a task
uv run agent skill planner update 42 --status blocked
```

#### 4. **list** - List tasks in the queue
```bash
uv run agent skill planner list [OPTIONS]

Options:
  --status TEXT    Filter by status [default: queued]
  --limit INTEGER  Maximum results [default: 20]
```

**Output Format:**
- Rich table with columns: ID, Issue, Priority, Flags, Project
- Sorted by: important DESC, priority DESC, created_at ASC
- Important tasks marked with ⭐

#### 5. **delete** - Remove a task from the queue
```bash
uv run agent skill planner delete <task_id>
```

#### 6. **sync** - Sync tasks from issue tracker (placeholder)
```bash
uv run agent skill planner sync --project-id <project_id>
```

**Note:** Currently a placeholder; real implementation would fetch from issues skill.

---

## Programmatic API

### Functions

#### `init_context(ctx: SkillContext)`
Initialize the skill with database context.

#### `add_task(issue_id, priority=0, project_id="", important=False) -> int`
Add a task to the queue programmatically.

**Validation:**
- `issue_id`: Required, 1-200 characters
- `priority`: Integer between -100 and 100
- `project_id`: Max 200 characters
- `important`: Boolean

**Returns:** Task ID (int)

**Raises:** `ValidationException` on validation failure

#### `get_next_task(respect_important=True) -> dict | None`
Get the highest priority task from the queue.

**Returns:**
```python
{
    "id": 42,
    "issue_id": "issue-12345",
    "priority": 50,
    "project_id": "my-project",
    "important": True
}
```

#### `search(query: str, limit: int = 10) -> list[SearchResult]`
Universal search API for finding tasks.

**Search Fields:**
- issue_id (partial match, case-insensitive)
- project_id (partial match, case-insensitive)

**Scoring Algorithm:**
```python
base_score = 0.5
normalized_priority = priority / 200.0
score = base_score + normalized_priority
if important:
    score += 0.3
score = clamp(score, 0.0, 1.0)
```

**Returns:** List of `SearchResult` objects with metadata

---

## Features

### ✅ Currently Implemented

1. **Priority-based Task Queue**
   - Numeric priority system (-100 to 100)
   - Higher values = higher priority

2. **Important Flag**
   - Boolean flag to mark critical tasks
   - Takes precedence over priority in sorting

3. **Status Tracking**
   - Four-state status system
   - Timestamp tracking (created_at, updated_at)

4. **Project Organization**
   - Group tasks by project_id
   - Filter and search by project

5. **Universal Search Integration**
   - Searchable through global search system
   - Relevance scoring based on priority and importance

6. **Input Validation**
   - Pydantic-based validation for add_task
   - Clear error messages on validation failure

7. **Rich CLI Output**
   - Colored console output
   - Formatted tables for list views
   - Visual indicators (⭐ for important)

### 🔧 Partially Implemented

1. **Tags System**
   - Database column exists but not used in code
   - No CLI interface for tags

2. **Issue Tracker Sync**
   - Command exists but is a placeholder
   - Needs integration with issues skill

### ❌ Not Implemented

1. **Dependencies Between Tasks**
   - No way to express task dependencies
   - No blocking/waiting based on other tasks

2. **Time-based Features**
   - No due dates
   - No scheduling
   - No time estimates

3. **Assignment**
   - No task assignment to users/agents
   - No ownership tracking

4. **History/Audit Trail**
   - No history of status changes
   - No audit log

5. **Bulk Operations**
   - No bulk add/update/delete
   - No batch processing

6. **Advanced Filtering**
   - Limited filter options in list command
   - No multi-field filtering
   - No saved filters

7. **Statistics/Analytics**
   - No task completion metrics
   - No velocity tracking
   - No burndown charts

---

## Integration Points

### Current Integrations

1. **Universal Search**
   - Provides `search()` function for global queries
   - Returns standardized `SearchResult` objects

2. **SkillContext**
   - Uses shared SQLite database via context
   - Follows skill initialization pattern

3. **Rich Console**
   - Consistent CLI output with other skills
   - Color-coded status messages

### Potential Integrations

1. **Issues Skill**
   - Sync tasks from issue tracker
   - Create issues from tasks
   - Bidirectional updates

2. **Notes Skill**
   - Attach notes to tasks
   - Link task discussions

3. **Automations Skill**
   - Automatic task transitions
   - Trigger actions on status changes

4. **Telemetry Skill**
   - Track task completion times
   - Measure agent productivity

5. **AI Skill**
   - AI-suggested priorities
   - Intelligent task grouping
   - Predictive scheduling

---

## Use Cases

### 1. Agent Workflow Management
```bash
# Agent picks next task
uv run agent skill planner next

# Agent starts working
uv run agent skill planner update 42 --status running

# Agent completes task
uv run agent skill planner update 42 --status done
```

### 2. Issue Tracker Integration
```bash
# Sync high-priority issues
uv run agent skill planner sync --project-id critical-bugs

# Work through synced tasks
uv run agent skill planner list --status queued
uv run agent skill planner next
```

### 3. Multi-Project Management
```bash
# Add tasks for different projects
uv run agent skill planner add bug-123 --project-id frontend --priority 10
uv run agent skill planner add bug-456 --project-id backend --priority 20

# List tasks by project (via search)
uv run agent search --skill planner "frontend"
```

### 4. Important Task Handling
```bash
# Mark critical task as important
uv run agent skill planner add security-issue --important --priority 100

# Important tasks automatically come first
uv run agent skill planner next
```

---

## Design Patterns

### 1. Input Validation Pattern
Uses Pydantic models for type-safe input validation:
```python
class AddTaskInput(SkillInput):
    issue_id: str = Field(..., min_length=1, max_length=200)
    priority: int = Field(0, ge=-100, le=100)
    # ...

@validate_input
def add_task(...):
    # Function is guaranteed to receive valid input
```

### 2. Context Management Pattern
Global context variable for database access:
```python
_ctx: SkillContext | None = None

def init_context(ctx: SkillContext) -> None:
    global _ctx
    _ctx = ctx
```

### 3. CLI + API Pattern
Dual interface: CLI for humans, API for automation:
```python
# API function (core logic)
def add_task(...) -> int:
    # ... implementation

# CLI wrapper (user-facing)
@app.command()
def add(...) -> None:
    task_id = add_task(...)
    console.print(...)  # User feedback
```

---

## Current Limitations

### Functional Limitations

1. **No Task Dependencies**
   - Can't express "task A blocks task B"
   - No automatic status propagation
   - Manual coordination required

2. **Limited Status Model**
   - Only 4 states may be too restrictive
   - No substates (e.g., "code review", "testing")
   - No custom statuses

3. **No Time Management**
   - Can't track estimates vs actuals
   - No due dates or deadlines
   - No scheduling capabilities

4. **Single-dimension Priority**
   - Priority is just a number
   - No multi-criteria prioritization
   - No priority calculation algorithms

5. **No Collaboration Features**
   - Can't assign tasks to specific agents
   - No task handoff mechanism
   - No collaboration history

### Technical Limitations

1. **Tags Not Implemented**
   - Database column exists but unused
   - No tag-based filtering or search

2. **No Transaction Management**
   - Direct SQL execution
   - No rollback on errors
   - Limited error recovery

3. **Search Limitations**
   - Only searches issue_id and project_id
   - No full-text search
   - No fuzzy matching

4. **No Bulk Operations**
   - One task at a time
   - No CSV import/export
   - No batch updates

---

## Future Enhancement Ideas

### Near-term (Low-hanging Fruit)

1. **Implement Tags System**
   - Add tags parameter to add command
   - Filter by tags in list command
   - Search by tags

2. **Enhanced List Filtering**
   - Filter by multiple statuses
   - Filter by priority range
   - Filter by date range

3. **Task Dependencies**
   - Add "blocks" relationship
   - Add "depends_on" relationship
   - Visual dependency graph

4. **Bulk Operations**
   - Import from CSV/JSON
   - Bulk status updates
   - Batch delete by criteria

5. **Better Status Management**
   - Add "in_review" status
   - Add "paused" status
   - Custom status definitions

### Mid-term (Requires Design)

1. **Time Tracking**
   - Add estimated_hours field
   - Add actual_hours field
   - Track time per status
   - Calculate velocity metrics

2. **Assignment & Ownership**
   - Assign tasks to agents
   - Track who completed what
   - Agent workload balancing

3. **Smart Prioritization**
   - AI-suggested priorities
   - Multi-factor priority calculation
   - Dynamic re-prioritization

4. **Workflow Automation**
   - Auto-transition on conditions
   - Notifications on status changes
   - Integration with automations skill

5. **Advanced Search**
   - Full-text search on all fields
   - Fuzzy matching
   - Saved search queries
   - Search templates

### Long-term (Strategic Features)

1. **Sprint/Iteration Planning**
   - Group tasks into sprints
   - Sprint capacity planning
   - Burndown charts
   - Velocity tracking

2. **Kanban Board View**
   - Visual task board
   - Drag-and-drop status changes
   - WIP limits per status
   - Swim lanes by project

3. **Reporting & Analytics**
   - Task completion rates
   - Time-to-completion metrics
   - Bottleneck analysis
   - Productivity dashboards

4. **Integration Ecosystem**
   - Bidirectional sync with GitHub Issues
   - Jira integration
   - Slack notifications
   - Calendar integration

5. **Machine Learning Features**
   - Predict task completion time
   - Suggest similar tasks
   - Auto-categorize tasks
   - Anomaly detection

---

## Testing

### Current Test Coverage

**File:** `tests/test_planner.py`

Two basic test cases:
1. `test_add_task`: Verifies add command executes
2. `test_list_tasks`: Verifies list command executes

**Coverage Status:** Minimal (only smoke tests)

### Testing Gaps

1. **No Unit Tests**
   - API functions not tested directly
   - No validation testing
   - No error case testing

2. **No Integration Tests**
   - No database state verification
   - No multi-command workflows
   - No search function testing

3. **No Edge Case Tests**
   - Empty queue behavior
   - Invalid input handling
   - Concurrent access scenarios

### Recommended Test Suite

```python
# Unit Tests
- test_add_task_validation
- test_priority_bounds
- test_status_transitions
- test_search_scoring
- test_get_next_task_priority

# Integration Tests
- test_add_and_retrieve_task
- test_task_lifecycle
- test_important_flag_precedence
- test_project_filtering
- test_concurrent_task_updates

# Edge Cases
- test_empty_queue_next
- test_invalid_status_update
- test_duplicate_issue_ids
- test_priority_overflow
```

---

## Configuration

### Dependencies

**Runtime:**
- `glorious-agents>=0.1.0` - Core framework
- `typer` - CLI framework
- `pydantic` - Data validation
- `rich` - Console output

**Development:**
- `pytest>=8.3.0` - Testing framework
- `pytest-cov>=5.0.0` - Coverage reporting

### Database

- **Type:** SQLite (via SkillContext)
- **Schema:** `schema.sql` auto-applied on initialization
- **Location:** Shared with other skills in context database

### Entry Point

```toml
[project.entry-points."glorious_agents.skills"]
planner = "glorious_planner.skill:app"
```

---

## Performance Considerations

### Current Performance Profile

1. **Database Queries**
   - Simple indexed queries
   - Limited joins (none currently)
   - Efficient for queues under 10,000 tasks

2. **Scalability**
   - Linear search performance with indexes
   - No pagination (limit parameter only)
   - Single database instance (no sharding)

3. **Memory Usage**
   - Minimal in-memory state
   - Results fetched on-demand
   - No caching layer

### Optimization Opportunities

1. **Add Caching**
   - Cache frequently accessed tasks
   - Cache search results
   - Invalidate on updates

2. **Batch Operations**
   - Bulk insert API
   - Batch status updates
   - Transaction batching

3. **Query Optimization**
   - Add covering indexes
   - Optimize search queries
   - Consider materialized views

4. **Pagination**
   - Add offset/page parameter
   - Cursor-based pagination
   - Streaming results

---

## Related Skills

### Direct Dependencies
- None (standalone skill)

### Common Integrations
1. **issues** - Issue tracking and management
2. **notes** - Task documentation
3. **automations** - Automated task workflows
4. **telemetry** - Task metrics and analytics

### Complementary Skills
1. **orchestrator** - Multi-skill workflow coordination
2. **feedback** - Task review and feedback
3. **ai** - AI-assisted task management

---

## Documentation & Resources

### Internal Documentation
- Package description in `pyproject.toml`
- Inline docstrings in `skill.py`
- Command help text via Typer

### Example Usage
See Commands & API section above for CLI examples

### Schema Documentation
See Database Schema section above

---

## Maintenance Notes

### Code Quality
- Type hints used consistently
- Pydantic validation for inputs
- Rich output for user feedback

### Known Issues
1. Prompts skill loading error (unrelated to planner)
2. Tags field exists but unused
3. Sync command is placeholder

### Future Refactoring Needs
1. Extract database queries to separate module
2. Add proper transaction management
3. Implement comprehensive test suite
4. Add configuration file support
5. Create data migration system

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Commands | 6 |
| Public API Functions | 3 |
| Database Tables | 1 |
| Database Indexes | 2 |
| Status States | 4 |
| Lines of Code | ~266 |
| Test Coverage | Minimal |
| Active Integrations | 1 (universal search) |

---

## Conclusion

The Planner skill provides a solid foundation for task queue management with priority-based sorting and status tracking. While functional for basic use cases, there are significant opportunities for enhancement:

**Strengths:**
- Simple, clear API
- Good separation of CLI and programmatic interfaces
- Flexible priority system
- Integration with universal search

**Opportunities:**
- Add task dependencies
- Implement time tracking
- Enhance filtering and search
- Build reporting capabilities
- Improve test coverage

The skill is well-positioned to become a comprehensive project planning tool with the proposed enhancements, particularly the focus command (issue-e0e776) which would add workflow guidance for agents.

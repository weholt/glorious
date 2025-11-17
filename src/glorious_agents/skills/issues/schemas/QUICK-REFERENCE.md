# Issue Import Schema - Quick Reference

## Minimal Example

```json
{
  "project_id": "my-project",
  "items": [
    {
      "title": "My First Task",
      "type": "task"
    }
  ]
}
```

## Full Example

```json
{
  "project_id": "my-project",
  "items": [
    {
      "id": "epic-main",
      "title": "Main Epic",
      "description": "## Overview\nDetailed description",
      "type": "epic",
      "status": "open",
      "priority": 1,
      "assignee": "agent-main",
      "labels": ["backend", "api"],
      "start_date": "2025-01-01T00:00:00Z",
      "target_date": "2025-03-31T23:59:59Z",
      "subtasks": [
        {
          "title": "Sub Task",
          "type": "task",
          "priority": 0,
          "epic_id": "epic-main",
          "labels": ["backend"],
          "dependencies": [
            {
              "issue_id": "other-task-id",
              "type": "depends-on"
            }
          ]
        }
      ]
    }
  ]
}
```

## Field Reference

| Field | Required | Type | Values |
|-------|----------|------|--------|
| `project_id` | ✅ | string | Any valid project ID |
| `items` | ✅ | array | Array of Issue objects |

### Issue Object Fields

| Field | Required | Type | Values | Description |
|-------|----------|------|--------|-------------|
| `title` | ✅ | string | 1-500 chars | Issue title |
| `type` | ✅ | enum | `epic`, `feature`, `task`, `bug`, `chore` | Issue type |
| `id` | ❌ | string | `[a-z0-9-]+` | Custom ID (auto-gen if omitted) |
| `description` | ❌ | string | Markdown | Detailed description |
| `status` | ❌ | enum | `open`, `in_progress`, `blocked`, `resolved`, `closed`, `archived` | Default: `open` |
| `priority` | ❌ | int | 0-4 | 0=Critical, 4=Backlog. Default: 2 |
| `assignee` | ❌ | string | - | Assigned user/agent |
| `epic_id` | ❌ | string | Epic ID | Parent epic (for tasks/features) |
| `parent_epic_id` | ❌ | string | Epic ID | Parent epic (for sub-epics) |
| `labels` | ❌ | array | string[] | Tags for categorization |
| `dependencies` | ❌ | array | Dependency[] | Issue dependencies |
| `subtasks` | ❌ | array | Issue[] | Nested child issues (for epics) |
| `start_date` | ❌ | string | ISO 8601 | Epic start date |
| `target_date` | ❌ | string | ISO 8601 | Epic target date |
| `metadata` | ❌ | object | Any | Custom metadata |

### Dependency Object

| Field | Required | Type | Values |
|-------|----------|------|--------|
| `issue_id` | ✅ | string | Valid issue ID |
| `type` | ✅ | enum | `blocks`, `depends-on`, `related-to` |

## Priority Guide

| Priority | Value | Symbol | Use For |
|----------|-------|--------|---------|
| Critical | 0 | 🔴 | Security, blockers, data loss |
| High | 1 | 🟠 | Urgent features/bugs |
| Medium | 2 | 🟡 | Normal work (default) |
| Low | 3 | 🟢 | Nice-to-have |
| Backlog | 4 | ⚪ | Future ideas |

## Type Guide

| Type | Icon | Use For | Can Have Subtasks? |
|------|------|---------|-------------------|
| `epic` | 📦 | Large features/initiatives | ✅ Yes |
| `feature` | ✨ | User-facing functionality | ❌ No |
| `task` | ✅ | Technical implementation | ❌ No |
| `bug` | 🐛 | Defects and issues | ❌ No |
| `chore` | 🔧 | Non-functional work | ❌ No |

## Hierarchy Patterns

### Pattern 1: Epic with Sub-Epics
```
Epic
├── Sub-Epic (parent_epic_id = Epic)
│   ├── Task (epic_id = Sub-Epic)
│   └── Feature (epic_id = Sub-Epic)
└── Sub-Epic (parent_epic_id = Epic)
    └── Task (epic_id = Sub-Epic)
```

### Pattern 2: Epic with Direct Tasks
```
Epic
├── Task (epic_id = Epic)
├── Feature (epic_id = Epic)
└── Bug (epic_id = Epic)
```

### Pattern 3: Flat List
```
Task
Task
Feature
Bug
```

## Dependency Types

```
Task A --depends-on--> Task B    (A needs B completed first)
Task A --blocks--> Task B         (A must complete before B can start)
Task A --related-to--> Task B     (A and B are related)
```

## Common Labels

**Technology**: `backend`, `frontend`, `database`, `api`, `cli`
**Category**: `security`, `performance`, `documentation`, `testing`
**Status**: `urgent`, `blocked`, `needs-review`, `breaking-change`
**Component**: `auth`, `payments`, `notifications`, `ui`

## Description Template

```markdown
## Overview
[Brief description of what needs to be done]

## Requirements
- Requirement 1
- Requirement 2
- Requirement 3

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests written
- [ ] Documentation updated

## Technical Notes
[Optional: Implementation details, constraints, etc.]
```

## Validation

```bash
# Validate your JSON
python validate.py your-file.json
```

**Common Errors:**
- Missing `title` or `type`
- Invalid type (must be epic/feature/task/bug/chore)
- Invalid priority (must be 0-4)
- Invalid status
- ID pattern mismatch (only lowercase letters, numbers, hyphens)

## Tips

✅ **DO:**
- Use 2-3 level hierarchies max
- Make tasks atomic (1-2 days work)
- Set realistic priorities
- Include acceptance criteria
- Define necessary dependencies
- Use consistent labels

❌ **DON'T:**
- Make hierarchies >3 levels deep
- Use vague titles ("Fix stuff")
- Mark everything critical
- Create circular dependencies
- Mix label styles

## Example Workflows

### Simple Task List
```json
{
  "project_id": "cleanup",
  "items": [
    {"title": "Remove deprecated code", "type": "chore"},
    {"title": "Update dependencies", "type": "task"}
  ]
}
```

### Feature with Subtasks
```json
{
  "project_id": "auth",
  "items": [{
    "id": "epic-auth",
    "title": "User Authentication",
    "type": "epic",
    "priority": 1,
    "subtasks": [
      {"title": "JWT service", "type": "task", "priority": 0, "epic_id": "epic-auth"},
      {"title": "Login endpoint", "type": "feature", "priority": 0, "epic_id": "epic-auth"}
    ]
  }]
}
```

### Bug Fix Campaign
```json
{
  "project_id": "bugfixes",
  "items": [
    {
      "title": "Fix memory leak",
      "type": "bug",
      "priority": 0,
      "labels": ["critical", "performance"]
    },
    {
      "title": "Fix login timeout",
      "type": "bug",
      "priority": 1,
      "labels": ["auth", "urgent"]
    }
  ]
}
```

## Next Steps

1. **See full docs**: `README.md`
2. **LLM guide**: `LLM-GUIDE.md`
3. **Full example**: `example-auth-system.json`
4. **Validate**: `python validate.py your-file.json`
5. **Import**: (to be implemented)

## Files in This Directory

- `issue-import-schema.json` - JSON Schema definition
- `README.md` - Complete documentation
- `LLM-GUIDE.md` - Guide for LLM generation
- `example-auth-system.json` - Full working example
- `validate.py` - Validation script
- `QUICK-REFERENCE.md` - This file

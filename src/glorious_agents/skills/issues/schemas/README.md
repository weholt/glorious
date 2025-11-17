# Issue Import JSON Schema

## Overview

This directory contains the JSON schema for importing issues, epics, and sub-epics into the issue tracker. Use this schema when asking an LLM to generate task lists from specifications.

## Schema File

- **`issue-import-schema.json`**: Complete JSON Schema (Draft-07) for issue import format

## Purpose

The schema enables:
1. **Automated task list generation** from specifications
2. **Structured epic hierarchies** with parent-child relationships
3. **Dependency management** between issues
4. **Validation** of import data before processing

## Key Features

### Epic Hierarchies

The schema supports multi-level epic hierarchies:

```
Epic (Level 1)
├── Sub-Epic (Level 2)
│   ├── Task
│   ├── Feature
│   └── Task
└── Sub-Epic (Level 2)
    ├── Task
    └── Bug
```

### Supported Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | No | Custom issue ID (auto-generated if omitted) |
| `title` | string | Yes | Issue title/summary (1-500 chars) |
| `description` | string | No | Detailed description (supports markdown) |
| `type` | enum | Yes | `epic`, `feature`, `task`, `bug`, `chore` |
| `status` | enum | No | `open` (default), `in_progress`, `blocked`, `resolved`, `closed`, `archived` |
| `priority` | integer | No | 0-4 (0=Critical, 1=High, 2=Medium, 3=Low, 4=Backlog) |
| `assignee` | string\|null | No | Assigned user/agent |
| `epic_id` | string\|null | No | Parent epic (for tasks/features) |
| `parent_epic_id` | string\|null | No | Parent epic (for sub-epics) |
| `labels` | array[string] | No | Tags for categorization |
| `dependencies` | array[object] | No | Issue dependencies |
| `subtasks` | array[Issue] | No | Nested child issues (for epics) |
| `start_date` | string\|null | No | ISO 8601 date (for epics) |
| `target_date` | string\|null | No | ISO 8601 date (for epics) |
| `metadata` | object | No | Custom metadata |

### Dependency Types

- **`blocks`**: This issue blocks another issue
- **`depends-on`**: This issue depends on another issue
- **`related-to`**: This issue is related to another issue

## Usage with LLMs

### Prompt Template

When asking an LLM to generate a task list from a specification:

```
Generate a task list in JSON format following this schema: <attach issue-import-schema.json>

Specification:
[Your specification here]

Requirements:
1. Create a top-level epic for the major feature
2. Break down into sub-epics for major components
3. Create specific tasks for implementation steps
4. Set appropriate priorities (0=Critical, 1=High, 2=Medium)
5. Add labels for categorization
6. Define dependencies where applicable
7. Include detailed descriptions with acceptance criteria

Output only valid JSON matching the schema.
```

### Example Prompt

```
Generate a task list in JSON format for implementing a REST API with authentication.

Use the attached schema (issue-import-schema.json) and include:
- Main epic for "REST API Development"
- Sub-epics for: Authentication, Core API, Testing, Documentation
- Specific tasks for each sub-epic
- Proper priority levels
- Dependencies between tasks
- Labels for backend, security, testing, etc.
```

## Example Structure

### Simple Task List

```json
{
  "project_id": "project-api",
  "items": [
    {
      "title": "Setup Express server",
      "type": "task",
      "priority": 0,
      "labels": ["backend", "setup"]
    },
    {
      "title": "Create user routes",
      "type": "feature",
      "priority": 1,
      "labels": ["backend", "api"],
      "dependencies": [
        {"issue_id": "task-setup", "type": "depends-on"}
      ]
    }
  ]
}
```

### Epic with Sub-Epics

```json
{
  "project_id": "project-auth",
  "items": [
    {
      "id": "epic-auth",
      "title": "Authentication System",
      "type": "epic",
      "priority": 1,
      "labels": ["backend", "security"],
      "target_date": "2025-03-31T23:59:59Z",
      "subtasks": [
        {
          "id": "epic-core-auth",
          "title": "Core Authentication",
          "type": "epic",
          "priority": 1,
          "parent_epic_id": "epic-auth",
          "labels": ["backend", "core"],
          "subtasks": [
            {
              "title": "Implement JWT generation",
              "type": "task",
              "priority": 0,
              "epic_id": "epic-core-auth",
              "labels": ["backend", "jwt"]
            },
            {
              "title": "Create login endpoint",
              "type": "feature",
              "priority": 0,
              "epic_id": "epic-core-auth",
              "labels": ["backend", "api"]
            }
          ]
        },
        {
          "id": "epic-middleware",
          "title": "Auth Middleware",
          "type": "epic",
          "priority": 1,
          "parent_epic_id": "epic-auth",
          "labels": ["backend", "middleware"],
          "subtasks": [
            {
              "title": "JWT validation middleware",
              "type": "task",
              "priority": 1,
              "epic_id": "epic-middleware",
              "labels": ["backend", "middleware"]
            }
          ]
        }
      ]
    }
  ]
}
```

## Validation

### Using JSON Schema Validators

```bash
# Validate with Python jsonschema
pip install jsonschema
python -c "
import json
from jsonschema import validate

with open('issue-import-schema.json') as f:
    schema = json.load(f)
    
with open('your-task-list.json') as f:
    data = json.load(f)
    
validate(instance=data, schema=schema)
print('Valid!')
"
```

### Common Validation Errors

1. **Missing required fields**: Must have `title` and `type`
2. **Invalid type**: Must be one of: `epic`, `feature`, `task`, `bug`, `chore`
3. **Invalid priority**: Must be integer 0-4
4. **Invalid status**: Must be one of defined statuses
5. **ID pattern mismatch**: Must match `^[a-z0-9-]+$`

## Import Implementation

The schema defines the format. Import functionality needs to be implemented to:

1. **Parse JSON**: Load and validate against schema
2. **Create issues**: Insert issues into database
3. **Establish relationships**: Link epics, sub-epics, tasks
4. **Handle dependencies**: Create dependency edges
5. **Apply labels**: Associate labels with issues

### Recommended Import Order

1. Create all epics (top-level first)
2. Create all sub-epics (with parent references)
3. Create tasks/features/bugs (with epic references)
4. Create dependencies between issues
5. Apply labels to all issues

## Tips for LLM-Generated Task Lists

### Good Practices

1. **Clear hierarchy**: Use 2-3 levels (Epic → Sub-Epic → Task)
2. **Atomic tasks**: Each task should be independently completable
3. **Priority consistency**: Critical tasks (P0) should be rare
4. **Descriptive titles**: Use verb phrases ("Implement X", "Create Y")
5. **Rich descriptions**: Include acceptance criteria and details
6. **Logical labels**: Use consistent labeling scheme
7. **Realistic dependencies**: Only define necessary blockers

### Anti-Patterns to Avoid

❌ **Too many epic levels** (>3 levels deep)
❌ **Vague tasks** ("Do the thing")
❌ **Everything critical** (all priority 0)
❌ **Missing dependencies** (tasks with implicit dependencies)
❌ **Inconsistent labels** (mixing conventions)
❌ **Circular dependencies** (A blocks B, B blocks A)

## Integration with Issue Tracker

Once you have a JSON file matching this schema, you can import it using:

```bash
# Future import command (to be implemented)
uv run agent issues import task-list.json

# Or programmatically
from issue_tracker.import import import_from_json
import_from_json("task-list.json", project_id="my-project")
```

## Schema Evolution

The schema is versioned using `$schema`. When updating:

1. Maintain backward compatibility when possible
2. Version schema files (`issue-import-schema-v2.json`)
3. Update this documentation
4. Provide migration guide for breaking changes

## See Also

- **Issue Tracker Documentation**: Core issue tracking concepts
- **Epic Management**: Managing epic hierarchies
- **Dependency Management**: Working with issue dependencies
- **Label System**: Using labels effectively

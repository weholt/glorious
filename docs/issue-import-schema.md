# Issue Import JSON Schema

## Overview

A comprehensive JSON schema for importing issues, epics, and sub-epics into the issue tracker system. This schema enables LLMs to generate structured task lists from specifications that can be directly imported.

## Location

Schema files are located in: `src/glorious_agents/skills/issues/schemas/`

### Files

- **`issue-import-schema.json`** - Complete JSON Schema (Draft-07)
- **`README.md`** - Comprehensive documentation
- **`LLM-GUIDE.md`** - Guide for LLMs generating task lists
- **`example-auth-system.json`** - Full example with epic hierarchies
- **`validate.py`** - Validation script (requires `jsonschema` package)

## Key Features

### 1. Epic Hierarchies

Supports multi-level epic structures:

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

### 2. Complete Issue Attributes

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Custom issue ID (optional, auto-generated if omitted) |
| `title` | string | Issue title (required) |
| `description` | string | Markdown description |
| `type` | enum | `epic`, `feature`, `task`, `bug`, `chore` |
| `status` | enum | `open`, `in_progress`, `blocked`, `resolved`, `closed`, `archived` |
| `priority` | integer | 0-4 (0=Critical, 4=Backlog) |
| `assignee` | string | Assigned user/agent |
| `epic_id` | string | Parent epic for tasks/features |
| `parent_epic_id` | string | Parent epic for sub-epics |
| `labels` | array | Tags for categorization |
| `dependencies` | array | Issue dependencies (blocks, depends-on, related-to) |
| `subtasks` | array | Nested child issues (for epics) |
| `start_date` | string | ISO 8601 date (for epics) |
| `target_date` | string | ISO 8601 date (for epics) |

### 3. Dependency Management

Three dependency types:
- **blocks**: This issue blocks another
- **depends-on**: This issue depends on another
- **related-to**: Informational relationship

### 4. Priority System

| Priority | Value | Use Case |
|----------|-------|----------|
| Critical | 0 | Security issues, blockers, data loss |
| High | 1 | Must-have features, urgent bugs |
| Medium | 2 | Normal priority (default) |
| Low | 3 | Nice-to-have features |
| Backlog | 4 | Future considerations |

## Usage with LLMs

### Step 1: Provide the Schema

When asking an LLM to generate a task list, include the schema:

```
Generate a task list from this specification in JSON format.
Use the attached schema: issue-import-schema.json

[Your specification here]
```

### Step 2: LLM Generates JSON

The LLM will generate structured JSON like:

```json
{
  "project_id": "project-name",
  "items": [
    {
      "id": "epic-feature",
      "title": "Feature Development",
      "type": "epic",
      "priority": 1,
      "subtasks": [
        {
          "title": "Implement core functionality",
          "type": "task",
          "priority": 0,
          "epic_id": "epic-feature"
        }
      ]
    }
  ]
}
```

### Step 3: Validate (Optional)

```bash
cd src/glorious_agents/skills/issues/schemas
python validate.py your-task-list.json
```

### Step 4: Import (Future)

```bash
# To be implemented
uv run agent issues import your-task-list.json
```

## Example: Authentication System

See `example-auth-system.json` for a complete example featuring:

- Main epic: "User Authentication System"
- Sub-epics: "Core Authentication", "Auth Middleware", "Testing"
- Multiple tasks and features under each sub-epic
- Dependencies between tasks
- Proper priority levels
- Rich markdown descriptions
- Labels for categorization
- Target dates for epics

## Schema Structure

### Root Object

```json
{
  "project_id": "string (required)",
  "items": "array of Issue objects (required)"
}
```

### Issue Object

```json
{
  "id": "string (optional)",
  "title": "string (required)",
  "description": "string (optional)",
  "type": "epic|feature|task|bug|chore (required)",
  "status": "open|in_progress|blocked|resolved|closed|archived",
  "priority": "0-4 (default: 2)",
  "assignee": "string or null",
  "epic_id": "string or null (for tasks/features)",
  "parent_epic_id": "string or null (for sub-epics)",
  "labels": ["array", "of", "strings"],
  "dependencies": [
    {
      "issue_id": "string (required)",
      "type": "blocks|depends-on|related-to (required)"
    }
  ],
  "subtasks": ["array", "of", "Issue", "objects"],
  "start_date": "ISO 8601 string or null",
  "target_date": "ISO 8601 string or null",
  "metadata": {"custom": "fields"}
}
```

## Benefits

1. **Standardized Format**: Consistent structure for all imports
2. **LLM-Friendly**: Easy for LLMs to generate correctly
3. **Validation**: JSON Schema enables automated validation
4. **Flexible**: Supports simple flat lists or complex hierarchies
5. **Complete**: All issue attributes captured
6. **Documentation**: Rich descriptions with markdown support

## Best Practices

### For Specifications

1. **Be specific**: Clear requirements lead to better task breakdowns
2. **Include context**: Background helps LLMs understand priorities
3. **Mention constraints**: Dependencies, deadlines, technical requirements

### For Generated JSON

1. **Clear hierarchy**: 2-3 levels maximum (Epic → Sub-Epic → Task)
2. **Atomic tasks**: Each task independently completable
3. **Realistic priorities**: Not everything is critical
4. **Rich descriptions**: Include acceptance criteria
5. **Logical dependencies**: Only necessary blockers
6. **Consistent labels**: Use standard naming conventions

## Integration

### Current Status

- ✅ JSON Schema defined
- ✅ Documentation complete
- ✅ LLM guide created
- ✅ Example files provided
- ✅ Validation script available
- ⏳ Import functionality (to be implemented)

### Future Import API

```python
from issue_tracker.import import import_from_json

# Import from file
result = import_from_json("task-list.json")

# Import from dict
result = import_from_dict(json_data, project_id="my-project")

# Returns:
# {
#   "created": 15,
#   "epics": ["epic-id-1", "epic-id-2"],
#   "issues": ["issue-1", "issue-2", ...],
#   "errors": []
# }
```

## See Also

- **Schema Files**: `src/glorious_agents/skills/issues/schemas/`
- **LLM Guide**: `LLM-GUIDE.md` for detailed generation instructions
- **Example**: `example-auth-system.json` for reference implementation
- **Issue Tracker**: Core issue tracking documentation

## Contributing

When updating the schema:

1. Update `issue-import-schema.json`
2. Update examples to match
3. Update documentation
4. Test validation script
5. Update LLM guide if needed

## Validation

### With Python

```python
import json
from jsonschema import validate

with open('issue-import-schema.json') as f:
    schema = json.load(f)
    
with open('your-task-list.json') as f:
    data = json.load(f)
    
validate(instance=data, schema=schema)  # Raises ValidationError if invalid
```

### With Script

```bash
python validate.py your-task-list.json
```

### Common Errors

- Missing `title` or `type` (required fields)
- Invalid `type` value (must be epic/feature/task/bug/chore)
- Invalid `priority` (must be 0-4)
- Invalid `status` (must be one of defined statuses)
- ID pattern mismatch (must match `^[a-z0-9-]+$`)

## Notes

- Schema follows JSON Schema Draft-07
- All timestamps use ISO 8601 format
- IDs must be lowercase alphanumeric with hyphens
- Descriptions support markdown formatting
- Labels should be lowercase with hyphens
- Circular dependencies are not validated by schema (handle in import logic)

## Example Use Cases

### 1. New Feature Development

Generate comprehensive task breakdown for implementing a new feature with proper epic structure.

### 2. Bug Fix Campaign

Create organized list of bugs with priorities and dependencies.

### 3. Documentation Sprint

Structure documentation tasks as epic with subtasks for each section.

### 4. Refactoring Project

Break down large refactoring into manageable, dependent tasks.

### 5. API Development

Organize API endpoints by resource type with testing and documentation tasks.

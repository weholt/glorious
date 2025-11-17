# LLM Guide: Generating Task Lists from Specifications

This guide helps you (as an LLM) generate properly structured task lists from specifications that can be directly imported into the issue tracker.

## Quick Start

When asked to create a task list from a specification:

1. **Read the JSON schema** (`issue-import-schema.json`)
2. **Understand the hierarchy**: Epic → Sub-Epic → Task/Feature
3. **Generate valid JSON** matching the schema
4. **Use the examples** as templates

## Schema Structure

```
{
  "project_id": "project-name",
  "items": [
    {
      "title": "Required",
      "type": "epic|feature|task|bug|chore",
      "priority": 0-4,
      "epic_id": "parent-epic-id",      // for tasks/features
      "parent_epic_id": "parent-epic-id", // for sub-epics
      "subtasks": [...],                // nested items
      "labels": [...],
      "dependencies": [...]
    }
  ]
}
```

## Priority Levels

| Priority | Value | When to Use |
|----------|-------|-------------|
| Critical | 0 | Security issues, blockers, data loss risks |
| High | 1 | Must-have features, urgent bugs |
| Medium | 2 | Normal features and tasks (default) |
| Low | 3 | Nice-to-have features |
| Backlog | 4 | Future considerations |

## Issue Types

- **epic**: Large feature or initiative (can have subtasks)
- **feature**: User-facing functionality
- **task**: Technical work (implementation, refactoring)
- **bug**: Defect or issue
- **chore**: Non-functional work (docs, cleanup, config)

## Hierarchical Structure

### Pattern 1: Epic with Sub-Epics

Use for large projects with multiple components:

```
Epic: "Complete Authentication System"
├── Sub-Epic: "Core Authentication"
│   ├── Task: "JWT token generation"
│   ├── Feature: "Login endpoint"
│   └── Feature: "Refresh token flow"
├── Sub-Epic: "Authorization"
│   ├── Task: "RBAC middleware"
│   └── Feature: "Permission system"
└── Task: "Documentation"
```

**JSON Example:**
```json
{
  "id": "epic-auth",
  "title": "Complete Authentication System",
  "type": "epic",
  "subtasks": [
    {
      "id": "epic-core",
      "title": "Core Authentication",
      "type": "epic",
      "parent_epic_id": "epic-auth",
      "subtasks": [
        {
          "title": "JWT token generation",
          "type": "task",
          "epic_id": "epic-core"
        }
      ]
    }
  ]
}
```

### Pattern 2: Epic with Direct Tasks

Use for smaller projects:

```
Epic: "API Documentation"
├── Task: "Write OpenAPI spec"
├── Task: "Create usage examples"
└── Task: "Deploy docs site"
```

### Pattern 3: Flat Task List

Use for simple work:

```json
{
  "project_id": "project-x",
  "items": [
    {"title": "Task 1", "type": "task", "priority": 1},
    {"title": "Task 2", "type": "task", "priority": 2}
  ]
}
```

## Dependencies

Define dependencies when tasks must be completed in order:

```json
{
  "title": "Create login endpoint",
  "dependencies": [
    {
      "issue_id": "task-jwt-generation",
      "type": "depends-on"
    }
  ]
}
```

**Dependency Types:**
- `depends-on`: Current task needs the other task completed first
- `blocks`: Current task blocks the other task
- `related-to`: Informational relationship

## Labels

Use consistent labels for categorization:

**Technology:** `backend`, `frontend`, `database`, `api`
**Category:** `security`, `performance`, `documentation`, `testing`
**Status:** `urgent`, `blocked`, `needs-review`
**Component:** `auth`, `payments`, `notifications`

```json
{
  "labels": ["backend", "security", "api", "urgent"]
}
```

## Descriptions

Write detailed descriptions with:

1. **Overview**: What needs to be done
2. **Requirements**: Specific requirements
3. **Acceptance Criteria**: Checklist of completion criteria

**Template:**
```markdown
## Overview
[Brief description]

## Requirements
- Requirement 1
- Requirement 2

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests written
```

**Example:**
```json
{
  "description": "## Overview\nImplement JWT token service\n\n## Requirements\n- Generate access tokens\n- Validate tokens\n- Handle expiration\n\n## Acceptance Criteria\n- [ ] Token generation\n- [ ] Token validation\n- [ ] Unit tests\n- [ ] Error handling"
}
```

## Common Patterns

### Authentication System

```json
{
  "project_id": "auth-system",
  "items": [{
    "id": "epic-auth",
    "type": "epic",
    "title": "Authentication System",
    "priority": 1,
    "labels": ["backend", "security"],
    "subtasks": [
      {
        "title": "JWT token service",
        "type": "task",
        "priority": 0,
        "epic_id": "epic-auth"
      },
      {
        "title": "Login endpoint",
        "type": "feature",
        "priority": 0,
        "epic_id": "epic-auth",
        "dependencies": [
          {"issue_id": "task-jwt", "type": "depends-on"}
        ]
      }
    ]
  }]
}
```

### Database Migration

```json
{
  "title": "Database schema migration",
  "type": "task",
  "priority": 0,
  "labels": ["database", "migration"],
  "description": "## Overview\nCreate users table\n\n## Schema\n```sql\nCREATE TABLE users (...);\n```"
}
```

### Bug Fix

```json
{
  "title": "Fix memory leak in background worker",
  "type": "bug",
  "priority": 0,
  "labels": ["bug", "performance", "critical"],
  "description": "## Issue\nMemory usage grows over time\n\n## Root Cause\n[Analysis]\n\n## Fix\n[Solution]"
}
```

## Validation Checklist

Before generating JSON, ensure:

- ✅ `project_id` is specified
- ✅ All items have `title` and `type`
- ✅ Priorities are 0-4
- ✅ Epic IDs are consistent
- ✅ Dependencies reference valid issue IDs
- ✅ Labels are lowercase with hyphens
- ✅ Descriptions use markdown
- ✅ No circular dependencies

## Generation Workflow

### Step 1: Analyze Specification

Break down the specification into:
- Major features (epics)
- Components (sub-epics)
- Specific tasks

### Step 2: Create Hierarchy

```
Specification: "Build a REST API with auth"

↓

Epic: REST API Development
├── Sub-Epic: Authentication
├── Sub-Epic: Core API
├── Sub-Epic: Testing
└── Sub-Epic: Documentation
```

### Step 3: Define Tasks

For each sub-epic, list specific implementation tasks:

```
Sub-Epic: Authentication
├── Task: Setup JWT library
├── Feature: Login endpoint
├── Feature: Logout endpoint
└── Task: Write tests
```

### Step 4: Set Priorities

- Security: Priority 0-1
- Core features: Priority 1-2
- Documentation: Priority 2-3

### Step 5: Add Dependencies

Identify blocking relationships:
```
Task: Login endpoint
  depends-on: JWT library setup
  depends-on: User database schema
```

### Step 6: Generate JSON

Use the structure from examples, filling in all fields.

### Step 7: Validate

Check that JSON matches schema (use validate.py if available).

## Full Example

**Specification:**
> "Create a blog API with posts, comments, and user authentication"

**Generated JSON:**
```json
{
  "project_id": "blog-api",
  "items": [
    {
      "id": "epic-blog-api",
      "title": "Blog API Development",
      "type": "epic",
      "priority": 1,
      "labels": ["backend", "api"],
      "target_date": "2025-03-31T23:59:59Z",
      "subtasks": [
        {
          "id": "epic-auth",
          "title": "User Authentication",
          "type": "epic",
          "priority": 0,
          "parent_epic_id": "epic-blog-api",
          "labels": ["backend", "security"],
          "subtasks": [
            {
              "title": "JWT authentication service",
              "type": "task",
              "priority": 0,
              "epic_id": "epic-auth",
              "labels": ["backend", "jwt"]
            },
            {
              "title": "User registration endpoint",
              "type": "feature",
              "priority": 0,
              "epic_id": "epic-auth",
              "labels": ["backend", "api"]
            },
            {
              "title": "Login endpoint",
              "type": "feature",
              "priority": 0,
              "epic_id": "epic-auth",
              "labels": ["backend", "api"]
            }
          ]
        },
        {
          "id": "epic-posts",
          "title": "Blog Posts API",
          "type": "epic",
          "priority": 1,
          "parent_epic_id": "epic-blog-api",
          "labels": ["backend", "api"],
          "subtasks": [
            {
              "title": "Create post endpoint",
              "type": "feature",
              "priority": 1,
              "epic_id": "epic-posts",
              "labels": ["backend", "api", "crud"],
              "dependencies": [
                {"issue_id": "epic-auth", "type": "depends-on"}
              ]
            },
            {
              "title": "List/Get posts endpoints",
              "type": "feature",
              "priority": 1,
              "epic_id": "epic-posts",
              "labels": ["backend", "api", "crud"]
            },
            {
              "title": "Update/Delete post endpoints",
              "type": "feature",
              "priority": 2,
              "epic_id": "epic-posts",
              "labels": ["backend", "api", "crud"]
            }
          ]
        },
        {
          "id": "epic-comments",
          "title": "Comments API",
          "type": "epic",
          "priority": 2,
          "parent_epic_id": "epic-blog-api",
          "labels": ["backend", "api"],
          "subtasks": [
            {
              "title": "Add comment endpoint",
              "type": "feature",
              "priority": 2,
              "epic_id": "epic-comments",
              "labels": ["backend", "api"]
            },
            {
              "title": "List comments for post",
              "type": "feature",
              "priority": 2,
              "epic_id": "epic-comments",
              "labels": ["backend", "api"]
            }
          ]
        },
        {
          "title": "API documentation",
          "type": "chore",
          "priority": 2,
          "epic_id": "epic-blog-api",
          "labels": ["documentation", "api"]
        },
        {
          "title": "Integration tests",
          "type": "task",
          "priority": 1,
          "epic_id": "epic-blog-api",
          "labels": ["testing", "integration"]
        }
      ]
    },
    {
      "title": "Database schema setup",
      "type": "task",
      "priority": 0,
      "labels": ["database", "schema"],
      "dependencies": [
        {"issue_id": "epic-blog-api", "type": "blocks"}
      ]
    }
  ]
}
```

## Tips

1. **Start with epics**: Define high-level structure first
2. **Break down**: Split into manageable tasks (1-2 days of work)
3. **Be specific**: Avoid vague titles like "Do the thing"
4. **Add context**: Rich descriptions help implementers
5. **Realistic priorities**: Not everything is critical
6. **Logical order**: Use dependencies for sequencing
7. **Consistent style**: Use similar formatting throughout

## Anti-Patterns

❌ **Too deep hierarchy** (>3 levels)
```json
Epic → Sub-Epic → Sub-Sub-Epic → Task  // Too complex!
```

❌ **Vague tasks**
```json
{"title": "Fix issues"}  // What issues?
```

❌ **Everything critical**
```json
{"priority": 0}  // If everything is critical, nothing is
```

❌ **Missing dependencies**
```json
// Login endpoint created before JWT service exists
```

❌ **Circular dependencies**
```json
A depends-on B
B depends-on A  // Circular!
```

## Output Format

Always output **valid JSON only** (no markdown code blocks, no explanations).

Good:
```
{"project_id": "my-project", "items": [...]}
```

Bad:
```
Here's the task list:
```json
{...}
```
```

## Validation

After generation, validate with:
```bash
python validate.py your-output.json
```

This ensures the JSON matches the schema before import.

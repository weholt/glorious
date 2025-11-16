# Instruction Templates Quick Reference

## What Are Instruction Templates?

Instruction templates are markdown files in `.issues/templates/` that define structured workflows with tasks, subtasks, and acceptance criteria. They help break down complex work into manageable pieces.

## Available Commands

```bash
# List all templates
uv run issues instructions list

# View a template (formatted)
uv run issues instructions show <template-name>

# View raw markdown
uv run issues instructions show <template-name> --raw

# Apply template (create issues)
uv run issues instructions apply <template-name>

# Apply with epic
uv run issues instructions apply <template-name> --epic "Epic Title"

# Preview without creating
uv run issues instructions apply <template-name> --dry-run

# Add prefix to all issue titles
uv run issues instructions apply <template-name> --prefix "[Project]"
```

## Built-in Templates

### analyze-codebase
Comprehensive codebase analysis (7 tasks)
- Project structure analysis
- Code quality assessment
- Testing coverage analysis
- Documentation review
- Technical debt identification
- Architecture documentation
- Dependency analysis

### feature-implementation
Feature development workflow (8 tasks)
- Requirements analysis
- Design and architecture
- Implementation
- Unit testing
- Integration testing
- Documentation
- Code review
- Deployment

### bug-investigation
Bug fix workflow (7 tasks)
- Bug reproduction
- Root cause analysis
- Fix design
- Implementation
- Testing
- Code review
- Deployment and verification

## Creating Your Own Templates

1. Create a markdown file in `.issues/templates/`
2. Follow the template format (see README.md in templates folder)
3. Use the instructions list command to verify it's detected

## Template Format

```markdown
# Template: Your Template Name

**Description**: Brief description

## Overview
High-level summary

## Tasks

### 1. Task Name
**Priority**: high/medium/low/critical/backlog
**Estimated Effort**: small/medium/large

**Description**: What needs to be done

**Subtasks**:
- [ ] Subtask 1
- [ ] Subtask 2

**Acceptance Criteria**:
- Criterion 1
- Criterion 2

---

### 2. Next Task
...
```

## Example Usage

```bash
# Preview what would be created
uv run issues instructions apply analyze-codebase --dry-run

# Create an epic with all tasks as subtasks
uv run issues instructions apply analyze-codebase --epic "Codebase Audit 2025"

# Create tasks with a prefix
uv run issues instructions apply feature-implementation --prefix "[Auth]" --epic "User Authentication"
```

## Tips

- Use `--dry-run` first to preview
- Create epics to group related tasks
- Use prefixes to organize issues by project/module
- Templates are just markdown - easy to customize
- Store your custom templates in `.issues/templates/`

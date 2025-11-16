# Instruction Templates

This folder contains reusable instruction templates for complex tasks and workflows. Each template defines a structured approach with tasks, subtasks, acceptance criteria, and issue documentation formats.

## Available Templates

### Analysis & Quality
- **analyze-codebase.md** - General codebase analysis (7 tasks)
- **best-practices-analysis.md** - Python best practices evaluation (8 tasks)
- **code-quality-analysis.md** - Deep quality & architecture review (8 tasks)
- **pythonic-refactoring.md** - Make code more Pythonic (8 tasks)

### Development Workflows
- **feature-implementation.md** - Feature development process (8 tasks)
- **bug-investigation.md** - Systematic bug fixing (7 tasks)

## Quick Start

```bash
# List all templates
uv run issues instructions-list

# View template details
uv run issues instructions-show <name>

# Preview what will be created (dry-run)
uv run issues instructions-apply <name> --dry-run

# Create issues from template
uv run issues instructions-apply <name> --epic "Epic Title"

# With task prefix
uv run issues instructions-apply <name> --epic "Title" --prefix "[Module]"

# Show raw markdown
uv run issues instructions-show <name> --raw
```

## Usage Workflow

1. **Select Template**: Choose based on your goal
2. **Preview**: Run with `--dry-run` to see tasks
3. **Create Epic**: Apply template to create structured issues
4. **Execute Tasks**: Work through systematically
5. **Document Findings**: Write to `.work/agent/issues/[priority].md`
6. **Track Progress**: Create sub-issues for specific fixes
7. **Complete**: Move done items to history

## Template Structure

Each template should be a markdown file with:

1. **Header**: Title and description
2. **Tasks**: Breakdown of work into tasks and subtasks
3. **Instructions**: Specific guidance for each task
4. **Acceptance Criteria**: How to verify completion

## Example Template Names

- `analyze-codebase.md` - Full codebase analysis workflow
- `feature-implementation.md` - Feature development process
- `refactoring.md` - Code refactoring guidelines
- `testing-strategy.md` - Test coverage expansion
- `bug-investigation.md` - Debugging workflow

## Template Format

```markdown
# Template: [Name]

**Description**: Brief description of when to use this template

## Overview
High-level summary of the workflow

## Tasks

### 1. [Task Name]
**Priority**: high/medium/low
**Estimated Effort**: small/medium/large

**Description**: What needs to be done

**Subtasks**:
- [ ] Subtask 1
- [ ] Subtask 2

**Acceptance Criteria**:
- Criterion 1
- Criterion 2

---

### 2. [Next Task]
...
```

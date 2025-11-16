# Using Analysis and Refactoring Templates

## Overview

You now have six comprehensive instruction templates available for analyzing and improving your codebase. These templates can be applied to create structured workflows with tasks, subtasks, and acceptance criteria.

## Available Templates

### 1. analyze-codebase
**Purpose**: General codebase analysis
**Tasks**: 7 (Structure, Quality, Testing, Documentation, Technical Debt, Architecture, Dependencies)
**Best For**: Initial project assessment, onboarding new team members

```bash
uv run issues instructions apply analyze-codebase --epic "Project Analysis 2025"
```

### 2. best-practices-analysis
**Purpose**: Comprehensive Python best practices evaluation
**Tasks**: 8 (Style, Design, Architecture, Testing, Documentation, Security, Performance, Tooling)
**Best For**: Quality audits, preparing for production, team standards review

```bash
uv run issues instructions apply best-practices-analysis --epic "Code Quality Q1 2025"
```

### 3. code-quality-analysis
**Purpose**: Deep dive into code quality issues
**Tasks**: 8 (Duplication, Structure, Protocols, Anti-patterns, Dead Code, Dependencies, Config, APIs)
**Best For**: Refactoring planning, technical debt reduction, architecture improvements

```bash
uv run issues instructions apply code-quality-analysis --epic "Technical Debt Sprint"
```

### 4. pythonic-refactoring
**Purpose**: Make code more Pythonic and idiomatic
**Tasks**: 8 (Idioms, Type Hints, Data Structures, Context Managers, Stdlib, Organization, Errors, Imports)
**Best For**: Code modernization, improving readability, leveraging Python features

```bash
uv run issues instructions apply pythonic-refactoring --epic "Code Modernization"
```

### 5. feature-implementation
**Purpose**: Structured feature development workflow
**Tasks**: 8 (Requirements, Design, Implementation, Testing, Integration, Documentation, Review, Deployment)
**Best For**: New feature development, ensuring complete implementation

```bash
uv run issues instructions apply feature-implementation --epic "User Authentication" --prefix "[Auth]"
```

### 6. bug-investigation
**Purpose**: Systematic bug fixing workflow
**Tasks**: 7 (Reproduction, Root Cause, Fix Design, Implementation, Testing, Review, Deployment)
**Best For**: Critical bugs, systematic debugging, preventing regressions

```bash
uv run issues instructions apply bug-investigation --epic "Fix Database Deadlock"
```

## Workflow: From Template to Completed Work

### Phase 1: Planning and Issue Creation

1. **Select Template**: Choose based on your goal
2. **Preview First**: Always dry-run to see what will be created
   ```bash
   uv run issues instructions apply <template-name> --dry-run
   ```

3. **Create Epic and Tasks**: Apply template to create structured issues
   ```bash
   uv run issues instructions apply <template-name> --epic "Epic Title"
   ```

4. **Review Created Issues**: Check that issues were created correctly
   ```bash
   uv run issues list --status open
   ```

### Phase 2: Executing Analysis Templates

Analysis templates (best-practices, code-quality, pythonic) work differently:

1. **Run the Analysis**: Go through each task systematically
2. **Document Findings**: Write to `.work/agent/issues/[priority].md`
3. **Use Issue Templates**: Each template provides formats for findings
4. **Break Down Large Findings**: Create sub-issues for complex problems

**Example: Running Code Quality Analysis**

```bash
# Step 1: Create the analysis epic
uv run issues create "Code Quality Analysis Q1" --type epic --priority high

# Step 2: Create task for each analysis area
uv run issues create "Code Duplication Detection" \
  --deps subtask-of:EPIC-001 --priority high

# Step 3: Perform analysis and document findings
# (Manual work - use tools like ruff, mypy, radon, etc.)

# Step 4: Create trackable issues for findings
uv run issues create "Consolidate parse_date functions" \
  --deps subtask-of:EPIC-001 --priority high \
  --description "Found in 3 locations, 92% similar code"
```

### Phase 3: Breaking Down Large Jobs

**Strategy for Complex Analysis Work**:

1. **Epic Level**: Overall goal (e.g., "Codebase Refactoring 2025")
2. **Task Level**: Major analysis areas (e.g., "Code Duplication Detection")
3. **Finding Level**: Specific issues found (documented in `.work/agent/issues/`)
4. **Sub-Issue Level**: Actionable fixes (created as individual issues)

**Example Hierarchy**:

```
EPIC-001: Code Quality Analysis Q1
├── TASK-001: Code Duplication Detection
│   ├── DUPL-001: parse_date duplicated (3 locations)
│   │   └── ISSUE-015: Consolidate parse_date into utils.datetime
│   └── DUPL-002: validation logic duplicated (5 locations)
│       └── ISSUE-016: Create shared validation module
├── TASK-002: Structural Violations
│   └── STRUCT-001: Business logic in API layer
│       ├── ISSUE-017: Move user creation to domain service
│       └── ISSUE-018: Move subscription logic to service layer
```

**Creating This Structure**:

```bash
# 1. Epic
uv run issues create "Code Quality Analysis Q1" --type epic

# 2. Tasks (linked to epic)
uv run issues create "Code Duplication Detection" --deps subtask-of:EPIC-001

# 3. Document findings in .work/agent/issues/high.md
# (Use templates provided in each analysis task)

# 4. Create actionable issues from findings
uv run issues create "Consolidate parse_date into utils.datetime" \
  --priority high \
  --description "Remove duplication from 3 modules" \
  --label refactoring
```

## Issue Documentation Format

Each analysis template provides issue formats. Here's the general pattern:

```markdown
---
id: "CATEGORY-XXX"
title: "Brief issue title"
description: "One-line summary"
created: 2025-11-13
section: relevant-section
tags: [tag1, tag2, tag3]
type: [enhancement|duplication|structural-violation|bug]
priority: [critical|high|medium|low]
status: [proposed|in-progress|completed|blocked]
---

**Detailed Description**

Location: `path/to/file.py:line_number`

Current State: [What exists now]

Issue: [What's wrong]

Impact: [Why it matters]

Recommended Fix: [How to resolve]

Code Examples:
```python
# Before
...

# After
...
```
```

## Progressive Work Strategy

### Week 1: Discovery
- Apply analysis templates
- Document all findings
- Don't fix anything yet
- Categorize by priority

### Week 2: Prioritization
- Review all findings
- Estimate effort for each
- Identify quick wins
- Create fix issues for high priority items

### Week 3-N: Execution
- Work through issues by priority
- Fix critical items first
- Batch similar small fixes
- Run tests after each change
- Move completed to history

## Using Multiple Templates Together

**Comprehensive Project Improvement**:

```bash
# Week 1: High-level analysis
uv run issues instructions apply analyze-codebase --epic "Project Assessment"

# Week 2: Deep quality dive
uv run issues instructions apply code-quality-analysis --epic "Quality Audit"

# Week 3: Best practices check
uv run issues instructions apply best-practices-analysis --epic "Standards Review"

# Week 4: Pythonic improvements
uv run issues instructions apply pythonic-refactoring --epic "Code Modernization"
```

## Tips for Success

### Do's
- **Always dry-run first** to see what will be created
- **Use epics** to group related work
- **Be systematic** - complete one task before moving to next
- **Document findings** in `.work/agent/issues/` as you discover them
- **Create sub-issues** for complex problems
- **Move completed work** to history file
- **Run tests** after each change
- **Commit frequently** with clear messages

### Don'ts
- **Don't skip documentation** - findings must be written down
- **Don't fix while analyzing** - complete analysis first
- **Don't batch too much** - small PRs are better
- **Don't ignore low priority** - they accumulate into big problems
- **Don't work without tests** - add tests before refactoring
- **Don't forget history** - move completed issues to history.md

## Automation Commands

```bash
# List all templates
uv run issues instructions list

# Show template details
uv run issues instructions show <template-name>

# Show raw markdown
uv run issues instructions show <template-name> --raw

# Preview without creating
uv run issues instructions apply <template-name> --dry-run

# Create with epic
uv run issues instructions apply <template-name> --epic "Epic Title"

# Create with prefix
uv run issues instructions apply <template-name> --prefix "[Module]"

# List open issues
uv run issues list --status open

# Show issue details
uv run issues show <issue-id>
```

## Real-World Example

**Scenario**: Improve code quality of the issue-tracker project

**Step 1: Plan**
```bash
# Preview what work is involved
uv run issues instructions show code-quality-analysis
uv run issues instructions apply code-quality-analysis --dry-run
```

**Step 2: Create Structure**
```bash
# Create epic and tasks
uv run issues instructions apply code-quality-analysis \
  --epic "Issue Tracker Quality Improvements Q1 2025"
```

**Step 3: Execute First Task (Code Duplication)**
```bash
# Manual analysis using tools
uv run ruff check src/
uv run radon cc src/ -a

# Document findings in .work/agent/issues/high.md
# Use DUPL-XXX format from template

# Create fix issues
uv run issues create "Consolidate datetime parsing" \
  --priority high --label refactoring
```

**Step 4: Fix Issues**
```bash
# Make changes, run tests
uv run pytest tests/ -v

# Mark task complete, move to next
```

**Step 5: Track Progress**
```bash
# Review status
uv run issues list --status open
uv run issues list --status closed
```

## Customizing Templates

Templates are just markdown files in `.issues/templates/`. You can:

1. **Edit existing templates** to match your workflow
2. **Create new templates** for your specific needs
3. **Add sections** relevant to your project
4. **Adjust priorities** based on your standards

Just follow the format in existing templates and they'll work automatically!

## Summary

You now have a powerful system for:
- 📋 **Planning** work with structured templates
- 🔍 **Analyzing** code systematically
- 📝 **Documenting** findings consistently
- 🎯 **Breaking down** large jobs into manageable pieces
- ✅ **Tracking** progress through completion

Start with a dry-run, create your epic, work through tasks systematically, and watch your code quality improve!

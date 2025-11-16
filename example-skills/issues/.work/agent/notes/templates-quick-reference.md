# Quick Reference: Instruction Templates

## Available Templates

| Template | Tasks | Use Case |
|----------|-------|----------|
| `analyze-codebase` | 7 | General project analysis |
| `best-practices-analysis` | 8 | Python best practices audit |
| `code-quality-analysis` | 8 | Deep quality & architecture review |
| `pythonic-refactoring` | 8 | Make code more Pythonic |
| `feature-implementation` | 8 | New feature workflow |
| `bug-investigation` | 7 | Systematic bug fixing |

## Essential Commands

```bash
# List templates
uv run issues instructions list

# View template
uv run issues instructions show <name>

# Preview (dry-run)
uv run issues instructions apply <name> --dry-run

# Create issues
uv run issues instructions apply <name> --epic "Title"

# With prefix
uv run issues instructions apply <name> --epic "Title" --prefix "[Module]"
```

## Typical Workflow

1. **Plan**: `instructions show <template>`
2. **Preview**: `instructions apply <template> --dry-run`
3. **Create**: `instructions apply <template> --epic "Title"`
4. **Execute**: Work through tasks
5. **Document**: Write findings to `.work/agent/issues/[priority].md`
6. **Track**: Create sub-issues for fixes
7. **Complete**: Move done items to `history.md`

## Issue Hierarchy

```
Epic (overall goal)
└── Task (major area)
    └── Finding (specific issue in .work/agent/issues/)
        └── Sub-issue (actionable fix)
```

## Priority Guide

- **Critical**: Security, data loss, broken functionality
- **High**: Tests, major design issues, architecture
- **Medium**: Style, docs, minor refactoring
- **Low**: Nice-to-have improvements

## File Locations

- Templates: `.issues/templates/*.md`
- Findings: `.work/agent/issues/[priority].md`
- History: `.work/agent/issues/history.md`
- Notes: `.work/agent/notes/`

## Analysis Templates Issue Format

```markdown
---
id: "CATEGORY-XXX"
title: "Brief description"
description: "Summary"
created: YYYY-MM-DD
section: area
tags: [tag1, tag2]
type: enhancement|duplication|structural-violation
priority: critical|high|medium|low
status: proposed|in-progress|completed|blocked
---

Detailed description with code examples and recommendations.
```

## Example: Running Full Analysis

```bash
# Week 1: Overview
uv run issues instructions apply analyze-codebase --epic "Q1 Assessment"

# Week 2: Deep dive
uv run issues instructions apply code-quality-analysis --epic "Quality Review"

# Week 3: Standards
uv run issues instructions apply best-practices-analysis --epic "Standards Audit"

# Week 4: Modernize
uv run issues instructions apply pythonic-refactoring --epic "Code Modernization"
```

## Tips

✅ Always dry-run first
✅ Use epics to group work
✅ Document findings systematically
✅ Create sub-issues for complex fixes
✅ Move completed work to history
✅ Run tests after changes

❌ Don't fix while analyzing
❌ Don't skip documentation
❌ Don't batch too much
❌ Don't ignore low priority items

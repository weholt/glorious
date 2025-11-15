# Issues Skill - Usage Guide

## Overview

Track and manage issues with status and priority levels.

## Commands

### Create an Issue

```powershell
uv run agent issues create "Fix the bug" --description "Details here" --priority high
```

### List Issues

```powershell
# List open issues (default)
uv run agent issues list

# List closed issues
uv run agent issues list --status closed

# List more issues
uv run agent issues list --limit 20
```

### Get Issue Details

```powershell
uv run agent issues get 123
```

### Update an Issue

```powershell
uv run agent issues update 123 --title "New title" --status in_progress --priority high
```

### Close an Issue

```powershell
uv run agent issues close 123
```

## Auto-Creation from Notes

Issues are automatically created when you add a note with "todo" or "issue" tags:

```powershell
uv run agent notes add "Fix the parser bug" --tags "todo,bug"
# This automatically creates an issue linked to the note
```

## Status Values

- `open` - Issue is open (default)
- `in_progress` - Work in progress
- `closed` - Issue is closed

## Priority Values

- `low` - Low priority
- `medium` - Medium priority (default)
- `high` - High priority

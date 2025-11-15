# Notes Skill - Usage Guide

## Overview

The notes skill allows you to store and search persistent text notes.

## Commands

### Add a Note

```powershell
uv run agent notes add "Your note content here" --tags "tag1,tag2"
```

### List Recent Notes

```powershell
uv run agent notes list
uv run agent notes list --limit 20
```

### Search Notes

```powershell
uv run agent notes search "search query"
```

### Get a Specific Note

```powershell
uv run agent notes get 123
```

### Delete a Note

```powershell
uv run agent notes delete 123
```

## Examples

```powershell
# Add a note
uv run agent notes add "Remember to refactor the parser" --tags "todo,refactor"

# Search for refactor notes
uv run agent notes search "refactor"

# List recent notes
uv run agent notes list
```

## Tips

- Use tags to organize notes
- Full-text search supports SQLite FTS5 query syntax
- Notes are stored in the agent's shared database

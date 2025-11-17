# Notes Skill - Usage Guide

## Overview

The notes skill allows you to store and search persistent text notes with importance levels for prioritization.

## Importance Levels

Notes can be marked with three importance levels:
- **Normal** (default): Regular notes
- **Important** (★): Important topics that need attention
- **Critical** (⚠): Critical information that must not be missed

## Commands

### Add a Note

```powershell
# Add a normal note
uv run agent notes add "Your note content here" --tags "tag1,tag2"

# Add an important note
uv run agent notes add "Key architectural decision" --important

# Add a critical note
uv run agent notes add "Security vulnerability found" --critical
```

### List Recent Notes

```powershell
# List all recent notes
uv run agent notes list

# List only important notes (important + critical)
uv run agent notes list --important

# List only critical notes
uv run agent notes list --critical

# Limit number of results
uv run agent notes list --limit 20
```

### Search Notes

```powershell
# Search all notes
uv run agent notes search "search query"

# Search only important notes
uv run agent notes search "query" --important

# Search only critical notes
uv run agent notes search "query" --critical
```

### Update Note Importance

```powershell
# Mark a note as important
uv run agent notes mark 123 --important

# Mark a note as critical
uv run agent notes mark 123 --critical

# Mark a note as normal (remove importance)
uv run agent notes mark 123 --normal
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
# Add a critical security note
uv run agent notes add "SQL injection vulnerability in user input" --critical --tags "security,urgent"

# Add an important architecture decision
uv run agent notes add "Decided to use event-driven architecture" --important --tags "architecture,decision"

# Search for security-related important notes
uv run agent notes search "security" --important

# List all critical notes
uv run agent notes list --critical

# Upgrade a note to critical
uv run agent notes mark 42 --critical
```

## Tips

- Use **critical** for information that must be addressed immediately (security issues, blockers)
- Use **important** for key decisions, learnings, and topics that need attention
- Important/critical notes appear first in search results and listings
- Use tags to organize notes by category
- Full-text search supports SQLite FTS5 query syntax
- Notes are stored in the agent's shared database
- Universal search automatically prioritizes important notes

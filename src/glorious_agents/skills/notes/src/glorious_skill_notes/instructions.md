# Notes Skill - Internal Instructions

For AI agents working with the notes skill.

## Purpose

The notes skill provides persistent storage for arbitrary text notes with full-text search capabilities and importance-based prioritization.

## Key Features

- Store notes with optional tags
- Three importance levels: normal (0), important (1), critical (2)
- Full-text search using SQLite FTS5 with importance-aware ranking
- Event publishing on note creation
- Automatic prioritization in search results

## Importance Levels

Use importance levels to differentiate key information:

- **Normal (0)**: Default for regular notes
- **Important (1)**: Key decisions, learnings, topics requiring attention
- **Critical (2)**: Security issues, blockers, must-address items

## When to Use Important/Critical

### Critical (importance=2)
- Security vulnerabilities
- Blocking issues
- Data loss risks
- Breaking changes that need immediate action

### Important (importance=1)
- Architectural decisions
- Key learnings from implementation
- Important feedback or insights
- Topics that need follow-up

### Normal (importance=0)
- General observations
- Regular documentation
- Low-priority reminders

## Events Published

- `note_created`: Published when a new note is added
  - Payload: `{"id": int, "tags": str, "content": str, "importance": int}`

## Callable APIs

### add_note(content: str, tags: str = "", importance: int = 0) -> int

Add a new note programmatically.

**Args:**
- content: Note text (1-100,000 chars)
- tags: Comma-separated tags
- importance: 0=normal, 1=important, 2=critical

**Returns:** Note ID

### search_notes(query: str) -> list[dict[str, Any]]

Search notes using FTS5 with importance-aware ordering.

**Returns:** List of matching notes with id, content, tags, created_at, importance (sorted by importance DESC, then relevance)

### search(query: str, limit: int = 10) -> list[SearchResult]

Universal search API that returns SearchResult objects with importance-boosted scores.

## Usage Pattern

When another skill needs to create an important note:

```python
from notes.skill import add_note

# Regular note
note_id = add_note("Completed refactoring", tags="refactor,done")

# Important note
note_id = add_note("Changed API contract - breaking change", tags="api,breaking", importance=1)

# Critical note
note_id = add_note("Security: SQL injection in auth module", tags="security,urgent", importance=2)
```

## Database Schema

- Table: `notes` (id, content, tags, created_at, updated_at, importance)
- FTS5: `notes_fts` (automatic sync via triggers)
- Index: `idx_notes_importance` (importance DESC, created_at DESC)

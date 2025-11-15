# Notes Skill - Internal Instructions

For AI agents working with the notes skill.

## Purpose

The notes skill provides persistent storage for arbitrary text notes with full-text search capabilities.

## Key Features

- Store notes with optional tags
- Full-text search using SQLite FTS5
- Event publishing on note creation

## Events Published

- `note_created`: Published when a new note is added
  - Payload: `{"id": int, "tags": str, "content": str}`

## Callable APIs

### add_note(content: str, tags: str = "") -> int

Add a new note programmatically.

**Returns:** Note ID

### search_notes(query: str) -> list[dict[str, Any]]

Search notes using FTS5.

**Returns:** List of matching notes with id, content, tags, created_at

## Usage Pattern

When another skill needs to create a note:

```python
from notes.skill import add_note

note_id = add_note("Important information", tags="important,todo")
```

## Database Schema

- Table: `notes` (id, content, tags, created_at, updated_at)
- FTS5: `notes_fts` (automatic sync via triggers)

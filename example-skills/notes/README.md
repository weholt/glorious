# Glorious Skill: Notes

Persistent notes with FTS5 full-text search for Glorious Agents.

## Features

- Store text notes with optional tags
- Full-text search using SQLite FTS5
- Event publishing on note creation
- Callable API for programmatic use

## Installation

```powershell
# Install from source
cd example-skills/notes
uv pip install -e .

# Or install from PyPI (when published)
uv pip install glorious-skill-notes
```

## Usage

After installation, the skill is automatically discovered:

```powershell
# List skills (notes should appear)
uv run agent skills list

# Add a note
uv run agent notes add "My important note" --tags "important,todo"

# List recent notes
uv run agent notes list

# Search notes
uv run agent notes search "important"

# Get specific note
uv run agent notes get 1

# Delete a note
uv run agent notes delete 1
```

## Programmatic API

```python
from glorious_skill_notes.skill import add_note, search_notes

# Add a note
note_id = add_note("Content here", tags="tag1,tag2")

# Search notes
results = search_notes("query")
for note in results:
    print(f"#{note['id']}: {note['content']}")
```

## Events

### Published Events

- `note_created`: Emitted when a new note is added
  - Payload: `{"id": int, "tags": str, "content": str}`

Other skills can subscribe to this event to react to note creation.

## Development

```powershell
cd example-skills/notes
uv sync --extra dev
uv run pytest
```

## License

MIT

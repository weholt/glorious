# Glorious Agents - Quick Start Guide

## Installation

```powershell
# Navigate to project
cd c:\dev\playground\glorious

# Install dependencies (includes dev tools)
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

## First Steps

### 1. Verify Installation

```powershell
# Check version
uv run agent version
# Output: Glorious Agents v0.1.0

# List loaded skills
uv run agent skills list
# Output: Shows notes and issues skills
```

### 2. Create an Agent Identity

```powershell
# Register an agent
uv run agent identity register --name "developer" --role "Software Developer" --project-id "myproject"

# Switch to the agent
uv run agent identity use developer

# Check current agent
uv run agent identity whoami

# List all agents
uv run agent identity list
```

### 3. Use the Notes Skill

```powershell
# Add a note
uv run agent notes add "Implement feature X" --tags "feature,todo"

# List recent notes
uv run agent notes list

# Search notes
uv run agent notes search "feature"

# Get specific note
uv run agent notes get 1

# Delete a note
uv run agent notes delete 1
```

### 4. Use the Issues Skill

```powershell
# Create an issue manually
uv run agent issues create "Fix bug in parser" --description "Details here" --priority high

# List open issues
uv run agent issues list

# List closed issues
uv run agent issues list --status closed

# Get issue details
uv run agent issues get 1

# Update an issue
uv run agent issues update 1 --status in_progress --priority high

# Close an issue
uv run agent issues close 1
```

### 5. Test Event Integration

```powershell
# Add a note with "todo" tag - this will auto-create an issue
uv run agent notes add "Refactor authentication module" --tags "todo,refactor"
# Output: Auto-created issue from note #X
#         Note X added successfully!

# Verify the issue was created
uv run agent issues list
# You'll see an issue titled "Follow-up for note #X"
```

## Development

### Run Tests

```powershell
# Run all unit tests
uv run pytest -m logic -q

# Run all integration tests
uv run pytest -m integration -q

# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html to see detailed coverage
```

### Code Quality

```powershell
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy src

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Creating Custom Skills

### 1. Scaffold a New Skill

```powershell
# Create skill directory structure
uv run agent skills create my_notes_parser

# This creates:
# skills/my_notes_parser/
#   ├── skill.json       (manifest)
#   ├── schema.sql       (database schema)
#   ├── skill.py         (implementation)
#   ├── instructions.md  (for agents)
#   └── usage.md        (for humans)
```

### 2. Edit the Skill

Edit `skills/my_notes_parser/skill.py`:

```python
"""My custom skill."""

import typer
from glorious_agents.core.context import SkillContext

app = typer.Typer(help="My custom skill")
_ctx: SkillContext | None = None

def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx
    
    # Subscribe to events
    ctx.subscribe("note_created", handle_note_created)

def handle_note_created(data: dict) -> None:
    """Handle note creation."""
    print(f"Note created: {data['id']}")

@app.command()
def hello(name: str = "World") -> None:
    """Say hello."""
    print(f"Hello {name}!")

# Add callable API functions
def process_note(note_id: int) -> str:
    """Process a note (callable API)."""
    if _ctx is None:
        raise RuntimeError("Context not initialized")
    
    # Access database
    cur = _ctx.conn.execute("SELECT content FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    
    if row:
        return f"Processed: {row[0]}"
    return "Note not found"
```

### 3. Define Dependencies

Edit `skills/my_notes_parser/skill.json`:

```json
{
  "name": "my_notes_parser",
  "version": "0.1.0",
  "description": "Parse and process notes",
  "entry_point": "my_notes_parser.skill:app",
  "schema_file": "schema.sql",
  "requires": ["notes"],
  "requires_db": true,
  "internal_doc": "instructions.md",
  "external_doc": "usage.md"
}
```

### 4. Reload Skills

```powershell
uv run agent skills reload

# Verify it loaded
uv run agent skills list

# Test the command
uv run agent my_notes_parser hello --name "Developer"
```

## Running the Daemon

```powershell
# Start daemon on default port
uv run agent daemon

# Or specify host and port
uv run agent daemon --host 127.0.0.1 --port 8765

# In another terminal, test the API
curl http://127.0.0.1:8765/skills
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Override default agent folder location
AGENT_FOLDER=C:\path\to\custom\agents

# Other settings...
```

Default agent folder: `.agent` in current directory

### Agent Data Locations

- **Master Registry**: `.agent/master.db` (all agents)
- **Active Agent File**: `.agent/active_agent` (current agent code)
- **Agent Database**: `.agent/agents/<code>/agent.db` (per agent)

## Troubleshooting

### Issue: Skills not loading

```powershell
# Check skills directory exists
ls skills

# Verify manifest files
ls skills/*/skill.json

# Check for syntax errors in skill.py files
uv run agent skills describe notes
```

### Issue: Database errors

```powershell
# Delete agent database to start fresh
Remove-Item -Force .agent/agents/default/agent.db

# Reinitialize
uv run agent skills reload
```

### Issue: Import errors

```powershell
# Reinstall in editable mode
uv sync --extra dev
```

## Next Steps

1. **Explore Skills**: Run `uv run agent skills describe notes` to see skill details
2. **Create Your Own**: Use `uv run agent skills create` to build custom skills
3. **Integrate Events**: Subscribe to topics for reactive workflows
4. **Deploy Daemon**: Run `uv run agent daemon` for API access
5. **Add Tests**: Write unit tests for your skills in `tests/unit/`

## Resources

- **Architecture**: See `focused-testing-architecture.md`
- **Specification**: See `chat.md` for design details
- **Tasks**: See `tasks.md` for implementation checklist
- **Summary**: See `IMPLEMENTATION.md` for completion status
- **Code**: Browse `src/glorious_agents/` for implementation

## Support

For issues or questions:
1. Check `IMPLEMENTATION.md` for status
2. Review test examples in `tests/`
3. Examine reference skills in `skills/notes/` and `skills/issues/`

---

**Happy coding with Glorious Agents!** 🎉

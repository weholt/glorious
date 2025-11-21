# Skill Authoring Guide

A comprehensive guide to creating, testing, and publishing skills for the Glorious Agents framework.

## Table of Contents

1. [Introduction](#introduction)
2. [Skill Structure](#skill-structure)
3. [Manifest Format](#manifest-format)
4. [Database Schema Design](#database-schema-design)
5. [Command Patterns](#command-patterns)
6. [Event Pub/Sub](#event-pubsub)
7. [Testing Skills](#testing-skills)
8. [Packaging](#packaging)
9. [Publishing](#publishing)
10. [Versioning](#versioning)
11. [Best Practices](#best-practices)
12. [Complete Example](#complete-example)

## Introduction

Skills are self-contained Python packages that extend the Glorious Agents framework with new capabilities. Each skill can:

- Define CLI commands using Typer
- Manage its own database schema
- Publish and subscribe to events
- Depend on other skills
- Provide documentation for both agents and humans

### Core Methodology

The framework uses a modern architecture with the following patterns:

**Context Management**: Skills receive a `SkillContext` instance via `init_context()` that provides:
- Database connection access
- Event bus for pub/sub messaging
- Configuration management
- Cached state

**Runtime Access**: Use `get_ctx()` from `glorious_agents.core.runtime` to access the global context singleton:
```python
from glorious_agents.core.runtime import get_ctx

ctx = get_ctx()
ctx.publish("event_name", {"data": "value"})
```

**Local Context Storage**: Store the context reference in your skill module:
```python
from glorious_agents.core.context import SkillContext

_ctx: SkillContext | None = None

def init_context(ctx: SkillContext) -> None:
    global _ctx
    _ctx = ctx
```

**Service Layer** (Optional): For complex skills, use a service/repository architecture:
- Domain entities define your data models
- Repositories handle database operations
- Services implement business logic
- Unit of Work pattern manages transactions

See the `issues` and `feedback` skills for examples of this advanced pattern.

## Skill Structure

A typical skill package has the following structure:

```
my-skill/
├── src/
│   └── my_skill/
│       ├── __init__.py           # Package initialization
│       ├── skill.json            # Skill manifest (required)
│       ├── skill.py              # Main implementation (required)
│       ├── schema.sql            # Database schema (optional)
│       ├── instructions.md       # Agent documentation (optional)
│       └── usage.md              # User documentation (optional)
├── tests/
│   ├── __init__.py
│   ├── test_commands.py          # Command tests
│   └── test_events.py            # Event tests
├── pyproject.toml                # Project configuration
├── README.md                     # Package readme
└── LICENSE                       # License file
```

### Required Files

1. **skill.json**: Manifest with metadata and dependencies
2. **skill.py**: Implementation with Typer app and event handlers

### Optional Files

3. **schema.sql**: Database schema that auto-initializes
4. **instructions.md**: Internal docs for AI agents
5. **usage.md**: External docs for human users

## Manifest Format

The `skill.json` file defines your skill's metadata:

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "Short description of what the skill does",
  "requires": ["dependency-skill", "another-skill"],
  "schema_file": "schema.sql",
  "requires_db": true,
  "config_schema": {
    "type": "object",
    "properties": {
      "max_items": {
        "type": "integer",
        "default": 100,
        "description": "Maximum number of items to store"
      },
      "enable_notifications": {
        "type": "boolean",
        "default": true
      }
    }
  },
  "internal_doc": "instructions.md",
  "external_doc": "usage.md"
}
```

### Manifest Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Unique skill identifier (lowercase, hyphens) |
| `version` | string | ✅ | Semantic version (e.g., "1.0.0") |
| `description` | string | ✅ | One-line description of the skill |
| `requires` | array | ❌ | List of skill dependencies |
| `schema_file` | string | ❌ | SQL schema filename (auto-initializes) |
| `requires_db` | boolean | ❌ | Whether skill needs database access |
| `config_schema` | object | ❌ | JSON Schema for configuration |
| `internal_doc` | string | ❌ | Filename for agent documentation |
| `external_doc` | string | ❌ | Filename for user documentation |

### Naming Conventions

- Use lowercase letters and hyphens: `my-skill`
- Avoid underscores in skill names
- Python package names should use underscores: `my_skill`
- Keep names short and descriptive

## Database Schema Design

### Schema File Location

Place `schema.sql` in the same directory as `skill.json`. The framework will automatically execute it when the skill first loads.

### Schema Best Practices

```sql
-- Use IF NOT EXISTS to make schema idempotent
CREATE TABLE IF NOT EXISTS my_skill_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_my_skill_items_name 
ON my_skill_items(name);

CREATE INDEX IF NOT EXISTS idx_my_skill_items_created 
ON my_skill_items(created_at DESC);

-- Use triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_my_skill_items_timestamp
AFTER UPDATE ON my_skill_items
BEGIN
    UPDATE my_skill_items 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Create FTS5 table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS my_skill_items_fts 
USING fts5(name, value, content='my_skill_items', content_rowid='id');

-- Trigger to keep FTS5 in sync
CREATE TRIGGER IF NOT EXISTS my_skill_items_fts_insert
AFTER INSERT ON my_skill_items
BEGIN
    INSERT INTO my_skill_items_fts(rowid, name, value)
    VALUES (NEW.id, NEW.name, NEW.value);
END;

CREATE TRIGGER IF NOT EXISTS my_skill_items_fts_delete
AFTER DELETE ON my_skill_items
BEGIN
    DELETE FROM my_skill_items_fts WHERE rowid = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS my_skill_items_fts_update
AFTER UPDATE ON my_skill_items
BEGIN
    UPDATE my_skill_items_fts 
    SET name = NEW.name, value = NEW.value 
    WHERE rowid = NEW.id;
END;
```

### Table Naming Convention

Prefix all tables with your skill name to avoid conflicts:

```sql
CREATE TABLE IF NOT EXISTS my_skill_items (...);
CREATE TABLE IF NOT EXISTS my_skill_settings (...);
CREATE TABLE IF NOT EXISTS my_skill_logs (...);
```

### Common Patterns

#### Tagging

```sql
CREATE TABLE IF NOT EXISTS my_skill_tags (
    item_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (item_id, tag),
    FOREIGN KEY (item_id) REFERENCES my_skill_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_my_skill_tags_tag 
ON my_skill_tags(tag);
```

#### Soft Deletes

```sql
ALTER TABLE my_skill_items ADD COLUMN deleted_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_my_skill_items_deleted 
ON my_skill_items(deleted_at);
```

#### Metadata

```sql
CREATE TABLE IF NOT EXISTS my_skill_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Command Patterns

### Basic Command Structure

```python
import typer
from rich.console import Console
from glorious_agents.core.db import get_connection
from glorious_agents.core.runtime import get_ctx

app = typer.Typer()
console = Console()

@app.command()
def add(
    name: str = typer.Argument(..., help="Item name"),
    value: str = typer.Option("", help="Item value"),
) -> None:
    """Add a new item to the skill database.
    
    Example:
        $ agent my-skill add "My Item" --value "Some value"
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO my_skill_items (name, value) VALUES (?, ?)",
            (name, value)
        )
        conn.commit()
        item_id = cursor.lastrowid
        
        console.print(f"[green]Added item #{item_id}: {name}[/green]")
        
        # Publish event
        ctx = get_ctx()
        ctx.publish("my_skill_item_created", {
            "id": item_id,
            "name": name,
            "value": value
        })
    finally:
        conn.close()
```

### List Command with Filtering

```python
@app.command()
def list(
    limit: int = typer.Option(10, help="Maximum items to show"),
    offset: int = typer.Option(0, help="Items to skip"),
    sort: str = typer.Option("created_at", help="Sort field"),
) -> None:
    """List items with pagination and sorting."""
    from rich.table import Table
    
    conn = get_connection()
    try:
        cursor = conn.execute(
            f"SELECT id, name, value, created_at FROM my_skill_items "
            f"ORDER BY {sort} DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        
        table = Table(title="My Skill Items")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Value", style="yellow")
        table.add_column("Created", style="dim")
        
        for row in cursor:
            table.add_row(str(row[0]), row[1], row[2], row[3])
        
        console.print(table)
    finally:
        conn.close()
```

### Get Command

```python
@app.command()
def get(item_id: int = typer.Argument(..., help="Item ID")) -> None:
    """Get a specific item by ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT id, name, value, created_at FROM my_skill_items WHERE id = ?",
            (item_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            console.print(f"[red]Item #{item_id} not found[/red]")
            raise typer.Exit(code=1)
        
        console.print(f"\n[bold cyan]Item #{row[0]}[/bold cyan]")
        console.print(f"Name: {row[1]}")
        console.print(f"Value: {row[2]}")
        console.print(f"[dim]Created: {row[3]}[/dim]")
    finally:
        conn.close()
```

### Update Command

```python
@app.command()
def update(
    item_id: int = typer.Argument(..., help="Item ID"),
    name: str = typer.Option(None, help="New name"),
    value: str = typer.Option(None, help="New value"),
) -> None:
    """Update an existing item."""
    if not name and not value:
        console.print("[yellow]Nothing to update[/yellow]")
        return
    
    conn = get_connection()
    try:
        # Build dynamic update query
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if value:
            updates.append("value = ?")
            params.append(value)
        
        params.append(item_id)
        
        conn.execute(
            f"UPDATE my_skill_items SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        conn.commit()
        
        console.print(f"[green]Updated item #{item_id}[/green]")
        
        # Publish event
        ctx = get_ctx()
        ctx.publish("my_skill_item_updated", {"id": item_id})
    finally:
        conn.close()
```

### Delete Command

```python
@app.command()
def delete(
    item_id: int = typer.Argument(..., help="Item ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an item."""
    if not force:
        if not typer.confirm(f"Delete item #{item_id}?"):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    conn = get_connection()
    try:
        conn.execute("DELETE FROM my_skill_items WHERE id = ?", (item_id,))
        conn.commit()
        
        console.print(f"[green]Deleted item #{item_id}[/green]")
        
        # Publish event
        ctx = get_ctx()
        ctx.publish("my_skill_item_deleted", {"id": item_id})
    finally:
        conn.close()
```

### Search Command with FTS5

```python
@app.command()
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search items using full-text search."""
    from rich.table import Table
    
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT i.id, i.name, i.value, i.created_at
            FROM my_skill_items i
            JOIN my_skill_items_fts fts ON i.id = fts.rowid
            WHERE my_skill_items_fts MATCH ?
            ORDER BY rank
            LIMIT 20
            """,
            (query,)
        )
        
        table = Table(title=f"Search Results: {query}")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Value", style="yellow")
        
        count = 0
        for row in cursor:
            table.add_row(str(row[0]), row[1], row[2])
            count += 1
        
        if count == 0:
            console.print(f"[yellow]No results for: {query}[/yellow]")
        else:
            console.print(table)
            console.print(f"\n[dim]Found {count} results[/dim]")
    finally:
        conn.close()
```

## Event Pub/Sub

### Initializing Event Context

The `init_context()` function is called automatically when the skill loads. It's where you:
- Store the context reference for later use
- Subscribe to events from other skills
- Perform one-time initialization

```python
from glorious_agents.core.context import SkillContext

_ctx: SkillContext | None = None

def init_context(ctx: SkillContext) -> None:
    """Initialize skill context and subscribe to events.
    
    This function is called automatically when the skill loads.
    """
    global _ctx
    _ctx = ctx
    
    # Subscribe to events from other skills
    ctx.subscribe("note_created", handle_note_created)
    ctx.subscribe("issue_created", handle_issue_created)
    
    # You can also do initialization here
    setup_skill()

def setup_skill() -> None:
    """Perform one-time skill setup."""
    # Example: ensure required data exists
    from glorious_agents.core.db import get_connection
    
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO my_skill_metadata (key, value) VALUES (?, ?)",
            ("initialized", "true")
        )
        conn.commit()
    finally:
        conn.close()
```

### Publishing Events

```python
from glorious_agents.core.runtime import get_ctx

def publish_item_event(item_id: int, name: str, value: str) -> None:
    """Publish an event when an item is created."""
    ctx = get_ctx()
    ctx.publish("my_skill_item_created", {
        "id": item_id,
        "name": name,
        "value": value,
        "timestamp": datetime.now().isoformat()
    })
```

### Subscribing to Events

```python
def handle_note_created(data: dict[str, Any]) -> None:
    """Handle note creation events from the notes skill.
    
    Args:
        data: Event data containing note information
            {
                "id": int,
                "content": str,
                "tags": list[str]
            }
    """
    note_id = data["id"]
    content = data["content"]
    tags = data.get("tags", [])
    
    # Process the event
    if "my-skill" in tags:
        # Create a related item
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO my_skill_items (name, value) VALUES (?, ?)",
                (f"Note {note_id}", content)
            )
            conn.commit()
        finally:
            conn.close()
```

### Event Naming Conventions

Use past tense verbs for events:

- ✅ `note_created`, `issue_updated`, `plan_completed`
- ❌ `create_note`, `update_issue`, `complete_plan`

Prefix skill-specific events with skill name:

- ✅ `my_skill_item_created`, `my_skill_sync_completed`
- ❌ `item_created`, `sync_completed` (too generic)

### Standard Event Schema

Include standard fields in all events:

```python
{
    "id": 123,                              # Entity ID
    "timestamp": "2025-11-14T10:30:00",     # ISO 8601 timestamp
    "skill": "my-skill",                    # Source skill
    "version": "1.0.0",                     # Event schema version
    # ... skill-specific fields
}
```

## Input Validation

The framework provides a validation system for ensuring robust input handling:

### Using the @validate_input Decorator

The `@validate_input` decorator automatically validates function arguments against Pydantic schemas matching the function signature:

```python
import typer
from pydantic import Field
from rich.console import Console
from glorious_agents.core.db import get_connection
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

app = typer.Typer()
console = Console()

class AddItemInput(SkillInput):
    """Input validation schema for adding items.
    
    The schema class name should match the function name in PascalCase with 'Input' suffix.
    For function 'add_item', use 'AddItemInput'.
    """
    
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    value: str = Field("", max_length=1000, description="Item value")
    priority: int = Field(0, ge=0, le=10, description="Priority level (0-10)")

@validate_input  # Automatically uses AddItemInput for validation
def add_item(name: str, value: str = "", priority: int = 0) -> int:
    """Add a new item with validated inputs.
    
    The decorator finds AddItemInput by converting 'add_item' to 'AddItemInput'.
    
    Args:
        name: Item name (1-200 chars).
        value: Item value (max 1000 chars).
        priority: Priority level (0-10).
    
    Returns:
        Item ID.
    
    Raises:
        ValidationException: If input validation fails.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO my_skill_items (name, value, priority) VALUES (?, ?, ?)",
            (name, value, priority)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

@app.command()
def add(name: str, value: str = "", priority: int = 0) -> None:
    """Add a new item (CLI wrapper)."""
    try:
        item_id = add_item(name, value, priority)
        console.print(f"[green]Added item #{item_id}[/green]")
    except ValidationException as e:
        console.print(f"[red]Validation error: {e.message}[/red]")
        raise typer.Exit(1)
```

### Validation Features

- **Type checking**: Pydantic validates types automatically
- **Length constraints**: `min_length`, `max_length` for strings
- **Range constraints**: `ge` (>=), `le` (<=) for numbers
- **Custom validators**: Add custom validation logic with Pydantic
- **Automatic error messages**: Clear, actionable error messages

## Testing Skills

### Test Structure

```python
# tests/test_commands.py
import pytest
from typer.testing import CliRunner
from my_skill.skill import app

runner = CliRunner()

def test_add_command():
    """Test adding an item."""
    result = runner.invoke(app, ["add", "Test Item", "--value", "Test Value"])
    assert result.exit_code == 0
    assert "Added item" in result.output

def test_list_command():
    """Test listing items."""
    # Add test data
    runner.invoke(app, ["add", "Item 1"])
    runner.invoke(app, ["add", "Item 2"])
    
    # List items
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Item 1" in result.output
    assert "Item 2" in result.output

def test_get_command():
    """Test getting a specific item."""
    # Add test item
    result = runner.invoke(app, ["add", "Test Item"])
    
    # Extract ID from output
    import re
    match = re.search(r"#(\d+)", result.output)
    item_id = match.group(1)
    
    # Get the item
    result = runner.invoke(app, ["get", item_id])
    assert result.exit_code == 0
    assert "Test Item" in result.output

def test_delete_command():
    """Test deleting an item."""
    # Add test item
    result = runner.invoke(app, ["add", "Test Item"])
    item_id = extract_id(result.output)
    
    # Delete with force flag
    result = runner.invoke(app, ["delete", item_id, "--force"])
    assert result.exit_code == 0
    assert "Deleted" in result.output
```

### Testing Events

```python
# tests/test_events.py
import pytest
from unittest.mock import Mock, patch
from my_skill.skill import handle_note_created, init_context

def test_event_subscription():
    """Test that skill subscribes to events correctly."""
    mock_ctx = Mock()
    init_context(mock_ctx)
    
    # Verify subscriptions
    mock_ctx.subscribe.assert_called()
    calls = [call[0][0] for call in mock_ctx.subscribe.call_args_list]
    assert "note_created" in calls

def test_handle_note_created():
    """Test handling note creation events."""
    event_data = {
        "id": 123,
        "content": "Test note",
        "tags": ["my-skill", "important"]
    }
    
    # Call handler
    handle_note_created(event_data)
    
    # Verify database was updated
    from glorious_agents.core.db import get_connection
    conn = get_connection()
    cursor = conn.execute(
        "SELECT COUNT(*) FROM my_skill_items WHERE value = ?",
        ("Test note",)
    )
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 1
```

### Testing Database Operations

```python
# tests/conftest.py
import pytest
import tempfile
from pathlib import Path
from glorious_agents.core.db import init_skill_schema

@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    
    # Set test database path
    import os
    os.environ["GLORIOUS_AGENT_FOLDER"] = str(tmp_path)
    
    # Initialize schema
    schema_path = Path(__file__).parent.parent / "src" / "my_skill" / "schema.sql"
    init_skill_schema("my-skill", schema_path)
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()

def test_database_operations(test_db):
    """Test database CRUD operations."""
    from glorious_agents.core.db import get_connection
    
    conn = get_connection()
    
    # Insert
    cursor = conn.execute(
        "INSERT INTO my_skill_items (name, value) VALUES (?, ?)",
        ("Test", "Value")
    )
    item_id = cursor.lastrowid
    conn.commit()
    
    # Select
    cursor = conn.execute("SELECT name, value FROM my_skill_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    assert row == ("Test", "Value")
    
    # Update
    conn.execute("UPDATE my_skill_items SET value = ? WHERE id = ?", ("New Value", item_id))
    conn.commit()
    
    # Delete
    conn.execute("DELETE FROM my_skill_items WHERE id = ?", (item_id,))
    conn.commit()
    
    conn.close()
```

### Test Coverage

Run tests with coverage:

```bash
uv run pytest --cov=my_skill --cov-report=html
```

Aim for:
- **≥80% overall coverage**
- **100% coverage** for critical paths
- **All commands** tested
- **All event handlers** tested

## Packaging

### pyproject.toml

```toml
[project]
name = "glorious-my-skill"
version = "1.0.0"
description = "My skill for Glorious Agents"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}
keywords = ["glorious-agents", "agent", "skill"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
]

dependencies = [
    "glorious-agents>=0.1.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    "ruff>=0.1.0",
]

[project.entry-points."glorious.skills"]
my-skill = "my_skill.skill"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_skill"]
```

### Entry Point Format

The entry point must reference a module containing:
- `app`: A Typer app instance
- `init_context`: Optional function for event setup

```python
# src/my_skill/skill.py
import typer

app = typer.Typer()

# Optional: called during skill loading
def init_context(ctx):
    ctx.subscribe("note_created", handle_note_created)
```

## Publishing

### Pre-publish Checklist

- [ ] All tests pass
- [ ] Code coverage ≥80%
- [ ] Type checking passes
- [ ] Documentation is complete
- [ ] Examples are tested
- [ ] CHANGELOG.md is updated
- [ ] Version number is bumped

### Building

```bash
# Install build tools
uv pip install build

# Build distributions
python -m build

# Check dist/
ls dist/
# glorious-my-skill-1.0.0.tar.gz
# glorious_my_skill-1.0.0-py3-none-any.whl
```

### Publishing to PyPI

```bash
# Install twine
uv pip install twine

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation
uv pip install --index-url https://test.pypi.org/simple/ glorious-my-skill

# Upload to PyPI
twine upload dist/*
```

### Publishing to GitHub

```bash
git tag v1.0.0
git push origin v1.0.0
```

Create a GitHub release with:
- Release notes
- Binary wheels
- Source tarball

## Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New backwards-compatible functionality
- **PATCH**: Backwards-compatible bug fixes

### Version Bump Examples

```
1.0.0 → 1.0.1  # Bug fix
1.0.1 → 1.1.0  # New feature
1.1.0 → 2.0.0  # Breaking change
```

### Breaking Changes

Document breaking changes clearly:

```markdown
## [2.0.0] - 2025-11-14

### Breaking Changes

- Changed `add` command signature: now requires `--name` flag
- Removed deprecated `search_old` command
- Database schema change: added `status` column (migration required)

### Migration Guide

Run the migration script:

```bash
agent my-skill migrate --from 1.x --to 2.0
```

Or manually update your database:

```sql
ALTER TABLE my_skill_items ADD COLUMN status TEXT DEFAULT 'active';
```
```

## Best Practices

### Code Organization

1. **Keep skill.py focused**: Extract complex logic into separate modules
2. **Use type hints**: Full type annotations for all functions
3. **Write docstrings**: Document all public APIs
4. **Handle errors gracefully**: Catch exceptions and show user-friendly messages

### Database

1. **Use transactions**: Wrap multi-statement operations in transactions
2. **Add indexes**: Index frequently queried columns
3. **Use prepared statements**: Always use parameterized queries
4. **Close connections**: Use try/finally blocks
5. **Test migrations**: Test schema changes on real data

### Events

1. **Document event schema**: Clearly define event data structure
2. **Version events**: Include version field for compatibility
3. **Handle missing data**: Use `.get()` with defaults for optional fields
4. **Avoid blocking**: Keep event handlers fast
5. **Test event handlers**: Unit test all event handling logic

### Performance

1. **Batch operations**: Use executemany for bulk inserts
2. **Limit queries**: Always use LIMIT for unbounded queries
3. **Use indexes**: Add indexes for WHERE clauses
4. **Cache results**: Cache expensive computations
5. **Profile queries**: Use EXPLAIN QUERY PLAN

### Security

1. **Parameterized queries**: Never use string formatting for SQL
2. **Validate input**: Use `@validate_input` decorator for all public APIs
3. **Sanitize output**: Escape special characters in output
4. **Limit permissions**: Don't require admin privileges
5. **Review dependencies**: Keep dependencies minimal and updated

### Architecture Patterns

For complex skills, consider using:

1. **Service/Repository Pattern**: Separate business logic (services) from data access (repositories)
2. **Unit of Work**: Manage database transactions consistently
3. **Dependency Injection**: Use a `dependencies.py` module to create service instances
4. **Domain Entities**: Define data models as Pydantic or SQLModel classes
5. **Validation Layer**: Use `@validate_input` for all public APIs

Example structure for advanced skills:
```
my_skill/
├── skill.py              # CLI commands and framework integration
├── dependencies.py       # Service factory functions
├── service.py           # Business logic
├── repository.py        # Database operations
├── entities.py          # Domain models
└── migrations/          # Database migrations
```

See the `issues` and `feedback` skills in the codebase for complete examples.

### Testing

1. **Test all commands**: Every command should have tests
2. **Test error cases**: Test invalid input and edge cases
3. **Test events**: Test both publishing and handling
4. **Use fixtures**: Create reusable test fixtures
5. **Mock external dependencies**: Don't rely on external services

## Complete Example

Here's a complete, production-ready skill example:

### Directory Structure

```
glorious-example-skill/
├── src/
│   └── glorious_example/
│       ├── __init__.py
│       ├── skill.json
│       ├── skill.py
│       ├── schema.sql
│       ├── instructions.md
│       └── usage.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_commands.py
│   └── test_events.py
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

### skill.json

```json
{
  "name": "example",
  "version": "1.0.0",
  "description": "Example skill demonstrating best practices",
  "requires": [],
  "schema_file": "schema.sql",
  "requires_db": true,
  "config_schema": {
    "type": "object",
    "properties": {
      "max_items": {
        "type": "integer",
        "default": 100,
        "description": "Maximum items to store"
      }
    }
  },
  "internal_doc": "instructions.md",
  "external_doc": "usage.md"
}
```

### schema.sql

```sql
CREATE TABLE IF NOT EXISTS example_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_example_items_status 
ON example_items(status);

CREATE INDEX IF NOT EXISTS idx_example_items_created 
ON example_items(created_at DESC);

CREATE TRIGGER IF NOT EXISTS update_example_items_timestamp
AFTER UPDATE ON example_items
BEGIN
    UPDATE example_items 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

CREATE VIRTUAL TABLE IF NOT EXISTS example_items_fts 
USING fts5(title, content, content='example_items', content_rowid='id');

CREATE TRIGGER IF NOT EXISTS example_items_fts_insert
AFTER INSERT ON example_items
BEGIN
    INSERT INTO example_items_fts(rowid, title, content)
    VALUES (NEW.id, NEW.title, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS example_items_fts_delete
AFTER DELETE ON example_items
BEGIN
    DELETE FROM example_items_fts WHERE rowid = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS example_items_fts_update
AFTER UPDATE ON example_items
BEGIN
    UPDATE example_items_fts 
    SET title = NEW.title, content = NEW.content 
    WHERE rowid = NEW.id;
END;
```

### skill.py

```python
"""Example skill demonstrating best practices."""

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.db import get_connection
from glorious_agents.core.runtime import get_ctx

app = typer.Typer(help="Example skill commands")
console = Console()

_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize event subscriptions."""
    global _ctx
    _ctx = ctx
    ctx.subscribe("note_created", handle_note_created)


def handle_note_created(data: dict[str, Any]) -> None:
    """Handle note creation events."""
    if "example" in data.get("tags", []):
        console.print(f"[dim]Example skill: Note {data['id']} created[/dim]")


@app.command()
def add(
    title: str = typer.Argument(..., help="Item title"),
    content: str = typer.Option("", help="Item content"),
) -> None:
    """Add a new item.
    
    Example:
        $ agent example add "My Title" --content "Some content"
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO example_items (title, content) VALUES (?, ?)",
            (title, content),
        )
        conn.commit()
        item_id = cursor.lastrowid

        console.print(f"[green]✓ Added item #{item_id}: {title}[/green]")

        # Publish event (if context is initialized)
        # Note: _ctx is None only during testing or before init_context() is called
        if _ctx:
            _ctx.publish("example_item_created", {"id": item_id, "title": title})
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    finally:
        conn.close()


@app.command("list")
def list_items(
    status: str = typer.Option("active", help="Filter by status"),
    limit: int = typer.Option(10, help="Maximum items to show"),
) -> None:
    """List items with optional filtering."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT id, title, content, status, created_at
            FROM example_items
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (status, limit),
        )

        table = Table(title=f"Example Items ({status})")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Content", style="yellow")
        table.add_column("Created", style="dim")

        count = 0
        for row in cursor:
            table.add_row(str(row[0]), row[1], row[2] or "-", row[4])
            count += 1

        if count == 0:
            console.print(f"[yellow]No {status} items found[/yellow]")
        else:
            console.print(table)
    finally:
        conn.close()


@app.command()
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search items using full-text search."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT i.id, i.title, i.content
            FROM example_items i
            JOIN example_items_fts fts ON i.id = fts.rowid
            WHERE example_items_fts MATCH ?
            ORDER BY rank
            LIMIT 20
            """,
            (query,),
        )

        table = Table(title=f"Search: {query}")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Content", style="yellow")

        count = 0
        for row in cursor:
            table.add_row(str(row[0]), row[1], row[2] or "-")
            count += 1

        if count == 0:
            console.print(f"[yellow]No results for: {query}[/yellow]")
        else:
            console.print(table)
            console.print(f"\n[dim]Found {count} results[/dim]")
    finally:
        conn.close()


@app.command()
def archive(item_id: int = typer.Argument(..., help="Item ID")) -> None:
    """Archive an item."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE example_items SET status = 'archived' WHERE id = ?",
            (item_id,),
        )
        conn.commit()
        console.print(f"[green]✓ Archived item #{item_id}[/green]")
    finally:
        conn.close()
```

This guide covers everything you need to create professional, production-ready skills for the Glorious Agents framework. Happy skill building!

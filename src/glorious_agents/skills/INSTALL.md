# Example Skills

This directory contains example installable skill packages for the Glorious Agents framework.

## Available Skills

### Notes (`glorious-skill-notes`)
Full-text search enabled note-taking with FTS5. Publishes `note_created` events.

**Location**: `example-skills/notes/`

### Issues (`glorious-skill-issues`)
Issue tracking that auto-creates issues from tagged notes. Depends on notes skill.

**Location**: `example-skills/issues/`

## Installation

Install both skills from the project root:

```bash
# Install notes skill (no dependencies)
uv pip install -e example-skills/notes

# Install issues skill (depends on notes)
uv pip install -e example-skills/issues

# Reload skills to pick up new installations
uv run agent skills reload

# Verify installation
uv run agent skills list
```

## Testing Installation

After installation, test the skills:

```bash
# Test notes skill
uv run agent notes add "Test note" --tags test
uv run agent notes list

# Test issues skill with event integration
uv run agent notes add "Implement feature X" --tags todo
uv run agent issues list
# Should show auto-created issue

# Test direct issue creation
uv run agent issues create "Manual issue"
uv run agent issues list
```

## Creating Your Own Skills

Use these packages as templates:

1. Copy the package structure (pyproject.toml, src/, README.md)
2. Update package name and entry point in pyproject.toml
3. Implement skill.py with `init_context(ctx)` and Typer app
4. Create skill.json manifest with metadata
5. Add schema.sql if using database tables
6. Write instructions.md and usage.md for LLM context
7. Install with `uv pip install -e your-skill/`

## Entry Point Registration

Skills are auto-discovered via the `glorious_agents.skills` entry point group:

```toml
[project.entry-points."glorious_agents.skills"]
your_skill = "your_package.skill:app"
```

The framework will automatically find and load your skill when installed.

## Distribution

To distribute your skill:

1. Build the package: `uv build`
2. Publish to PyPI: `uv publish`
3. Users install with: `uv pip install glorious-skill-yourname`

Skills are fully independent packages that can be versioned and distributed separately from the framework.

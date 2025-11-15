# Example Skills - Installation Verified ✅

This directory contains production-ready, installable skill packages for the Glorious Agents framework.

## Verification Results

Both skills have been successfully installed and tested:

```bash
uv pip install -e example-skills/notes
uv pip install -e example-skills/issues
```

**Test Results:**
- ✅ Skills auto-discovered via entry points
- ✅ Metadata loaded correctly (version, dependencies)
- ✅ Notes skill: Add, list, search working
- ✅ Issues skill: Event integration working (auto-creates issues from "todo" tagged notes)
- ✅ Dependency resolution: Issues correctly depends on notes

## Available Skills

### Notes (`glorious-skill-notes`)

Full-text search enabled note-taking with FTS5. Publishes `note_created` events.

**Features:**
- Add notes with tags
- List recent notes
- Full-text search with FTS5
- Get/delete individual notes
- Event publishing for integration

**Installation:**
```bash
uv pip install -e example-skills/notes
```

**Documentation:** See [example-skills/notes/README.md](notes/README.md)

### Issues (`glorious-skill-issues`)

Issue tracking that auto-creates issues from tagged notes. Depends on notes skill.

**Features:**
- Create and manage issues
- Status tracking (open/closed)
- Priority levels
- Auto-create from notes with "todo" or "issue" tags
- Event-driven integration

**Installation:**
```bash
uv pip install -e example-skills/issues
```

**Documentation:** See [example-skills/issues/README.md](issues/README.md)

## Quick Start

Install both skills from project root:

```bash
# Install notes (no dependencies)
uv pip install -e example-skills/notes

# Install issues (depends on notes)
uv pip install -e example-skills/issues

# Verify installation
uv run agent skills list
```

Expected output:
```
               Loaded Skills                
┏━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Name   ┃ Version ┃ Origin     ┃ Requires ┃
┡━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ notes  │ 0.1.0   │ entrypoint │ -        │
│ issues │ 0.1.0   │ entrypoint │ notes    │
└────────┴─────────┴────────────┴──────────┘
```

## Testing Event Integration

Test the full event-driven workflow:

```bash
# Add a note with "todo" tag
uv run agent notes add "Implement user authentication" --tags todo

# Check that an issue was auto-created
uv run agent issues list

# Verify the issue references the note
uv run agent issues get 1
```

## Package Structure

Each skill package follows this structure:

```
example-skills/
└── skill-name/
    ├── pyproject.toml           # Package metadata + entry point
    ├── README.md                 # Installation and usage docs
    └── src/
        └── glorious_skill_name/
            ├── __init__.py       # Package version
            ├── skill.py          # Typer app + init_context()
            ├── skill.json        # Skill manifest
            ├── schema.sql        # Database schema (if needed)
            ├── instructions.md   # Internal doc for LLM
            └── usage.md          # External doc for LLM
```

## Entry Point Registration

Skills are auto-discovered via the `glorious_agents.skills` entry point group defined in `pyproject.toml`:

```toml
[project.entry-points."glorious_agents.skills"]
skill_name = "glorious_skill_name.skill:app"
```

The framework automatically:
1. Discovers installed packages with this entry point
2. Loads skill.json metadata from the package
3. Resolves dependencies between skills
4. Initializes database schemas
5. Loads Typer apps and registers with CLI

## Creating Your Own Skills

Use these packages as templates:

1. **Copy structure**: Start with notes or issues as a template
2. **Update pyproject.toml**: Change name, version, entry point
3. **Implement skill.py**: Add Typer commands and `init_context(ctx)`
4. **Create skill.json**: Define metadata and dependencies
5. **Add schema.sql**: If using database tables
6. **Write docs**: Update instructions.md and usage.md
7. **Install**: `uv pip install -e your-skill/`
8. **Test**: `uv run agent skills list` should show your skill

## Distribution

To distribute your skill to others:

1. Build the package: `uv build`
2. Publish to PyPI: `uv publish`
3. Users install with: `uv pip install glorious-skill-yourname`

Skills are fully independent packages that can be versioned and distributed separately from the framework.

## Notes

- **Local vs Entry Point**: Local skills in `skills/` directory take precedence over installed packages with the same name
- **Python Version**: Requires Python 3.13+ (matches framework requirement)
- **Dependencies**: Installable skills should declare dependency on `glorious-agents>=0.1.0`
- **Editable Mode**: Use `-e` flag during development for live code updates

# CodeAtlas Agent Guide

## Build Commands
```bash
uv run python scripts/build.py                    # Full pipeline
uv run python scripts/build.py --fix              # Auto-fix issues
uv run python scripts/build.py --integration all  # Include integration tests
uv run pytest tests/test_specific.py::test_name   # Single test
uv run pytest tests/ -k "pattern"                 # Pattern matching
uv run ruff format src/                           # Format only
uv run ruff check --fix src/                      # Lint only
uv run mypy src/code_atlas/                       # Type check only
```

## Issue Management
```bash
uv run issues list                         # List all issues
uv run issues create "Issue title"         # Create new issue
uv run issues show ISSUE-1                 # Show issue details
uv run issues update ISSUE-1 --status done # Update issue
uv run issues ready                        # List ready-to-work issues
uv run issues blocked                      # List blocked issues
uv run issues stats                        # Show statistics
```

**Note**: All issue tracking is handled via `uv run issues` commands. The old `.work/agent/issues/*.md` files are deprecated.

## Code Style
- **Imports**: Top of file only, grouped: stdlib → third-party → local (via ruff isort)
- **Types**: All functions typed with return types, strict mypy mode (disallow_untyped_defs)
- **Naming**: snake_case functions, PascalCase classes, UPPER_SNAKE_CASE constants
- **Line length**: 120 chars max
- **Error handling**: Specific exceptions with context, never bare except (use `# noqa: S112` if truly needed)
- **Docstrings**: Required for public APIs, use Google/NumPy style with Args/Returns
- **Tests**: 5s timeout max per test, 70%+ coverage required, use type hints in tests too

## Issue Management with CLI

**IMPORTANT**: Use `uv run issues` commands for all issue tracking - do NOT manually edit markdown files.

### Creating and Managing Issues

```bash
# Initialize issue tracker (first time only)
uv run issues init

# Create issues
uv run issues create "Bug: Fix memory leak" --priority 1
uv run issues create "Feature: Add export" --type feature --labels enhancement,export

# List and query issues
uv run issues list --status open
uv run issues list --priority 1 --assignee @me
uv run issues show ISSUE-123

# Update issues
uv run issues update ISSUE-123 --status in_progress
uv run issues close ISSUE-123
uv run issues reopen ISSUE-123

# Add labels and comments
uv run issues labels add ISSUE-123 bug critical
uv run issues comments add ISSUE-123 "Fixed in commit abc123"

# Manage dependencies
uv run issues dependencies add ISSUE-123 ISSUE-456 --type blocks
uv run issues dependencies tree ISSUE-123
uv run issues dependencies cycles  # Detect dependency cycles

# Work queues
uv run issues ready     # Issues ready to work on
uv run issues blocked   # Issues blocked by dependencies
uv run issues stale     # Issues not updated recently

# Get statistics
uv run issues stats
uv run issues info
```

### Why Use CLI Instead of Markdown Files

1. **Data Integrity**: SQLite database ensures consistency and prevents conflicts
2. **Validation**: CLI enforces business rules (no circular dependencies, valid statuses)
3. **Query Power**: Complex filtering, sorting, and aggregation
4. **Git Integration**: Automatic sync with git (via daemon)
5. **Team Collaboration**: Proper merge handling, no manual conflict resolution

### Legacy Files (Do Not Edit)

The `.work/agent/issues/` folder contains old markdown-based issues for historical reference only. All new issue management must use the CLI.

### Notes and Documentation

- For temporary notes during development, use `.work/agent/notes/` folder
- These are NOT issues - just scratch space for analysis and planning

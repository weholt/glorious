# Glorious Skill: Issues

Issue tracking skill for Glorious Agents. Automatically creates issues from notes tagged with "todo" or "issue".

## Features

- Create and manage issues with status tracking
- Auto-create issues from tagged notes (event-driven)
- List issues by status (open/closed/all)
- Close and reopen issues
- Depends on notes skill for event integration

## Installation

From the project root:

```bash
uv pip install -e example-skills/issues
```

This will automatically register the skill with the Glorious Agents framework.

## Usage

After installation, the skill is automatically discovered:

```bash
# Reload skills to pick up the new installation
uv run agent skills reload

# List all issues
uv run agent issues list

# Create an issue manually
uv run agent issues create "Fix the login bug"

# Close an issue
uv run agent issues close 1

# Reopen an issue
uv run agent issues reopen 1

# Auto-create issue from note (via event)
uv run agent notes add "Implement user authentication" --tags todo
# This will automatically create an issue
```

## Architecture

This skill demonstrates:
- **Event subscription**: Listens for `note_created` events from notes skill
- **Skill dependencies**: Requires notes skill in manifest
- **Callable API**: `create_issue()` can be called by other skills
- **Entry point registration**: Auto-discovered via `glorious_agents.skills` entry point

## Dependencies

- `glorious-agents>=0.1.0`
- `glorious-skill-notes>=0.1.0`

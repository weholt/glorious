<div align="center">

# 🌟 Glorious Agents

[![PyPI version](https://badge.fury.io/py/glorious-agents.svg)](https://badge.fury.io/py/glorious-agents)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/weholt/glorious-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/weholt/glorious-agents/actions/workflows/ci.yml)

**A modular framework for building AI agents with plug-and-play skills, shared state, and event-driven workflows.**

## Pre-alpha / Proof-of-concept

**NOTE!** This is under heavy development and should be considered Pre-alpha, and a Proof-of-concept. 
Do not **under any circumstances** used this in anything even remotly important.

Built for [uv](https://github.com/astral-sh/uv) 🚀

</div>

## What is it?

Glorious Agents lets you build AI-powered agents using **modular skills** that share a common database and communicate via events. Each agent has its own identity, database, and set of active skills.

**Key concepts:**
- **Skills**: Self-contained packages that add functionality (17 built-in: notes, issues, code analysis, automation, etc.)
- **Agents**: Named identities with isolated databases and project contexts
- **Events**: Skills communicate via pub/sub for complex workflows
- **Database**: Shared SQLite per agent with automatic schema initialization

## Installation

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install globally with all skills
uv tool install glorious-agents[all-skills]

# Or in a project
uv add glorious-agents[all-skills]
```

## Quick Start

```bash
# Initialize the framework
uvx agent init

# List available skills
uvx agent skills list
```

## Skill Examples

### Notes - Quick Note-Taking
```bash
# Add a note
uvx agent notes add "Remember to refactor auth module" --tags todo,backend

# List notes
uvx agent notes list --tags todo

# Search notes
uvx agent notes search "auth"

# Get specific note
uvx agent notes get 1
```

### Issues - Task Tracking
```bash
# Create an issue
uvx agent issues create "Fix login bug" --priority high --tags bug,security

# List open issues
uvx agent issues list --status open

# Update issue status
uvx agent issues update 1 --status in-progress

# Add a comment
uvx agent issues comment 1 "Found the root cause in auth.py"

# Close issue
uvx agent issues close 1
```

### Planner - Task Queue
```bash
# Add tasks to queue
uvx agent planner enqueue "Review PR #123" --priority high
uvx agent planner enqueue "Update documentation" --priority low

# Get next task
uvx agent planner next

# List all queued tasks
uvx agent planner list
```

### Code-Atlas - Codebase Analysis
```bash
# Scan codebase
uvx agent code-atlas scan ./src

# Ask questions about code
uvx agent code-atlas ask "Where is authentication handled?"

# Get refactoring suggestions
uvx agent code-atlas refactor-priorities
```

### Automations - Workflow Automation
```bash
# Create automation
uvx agent automations create "Daily Standup" \
  --trigger "cron:0 9 * * 1-5" \
  --action "issues list --status in-progress"

# List automations
uvx agent automations list

# Run automation manually
uvx agent automations run daily-standup
```

## Built-in Skills

**17 skills included:** `notes`, `issues`, `planner`, `code-atlas`, `automations`, `orchestrator`, `cache`, `linker`, `feedback`, `prompts`, `ai`, `telemetry`, `temporal`, `vacuum`, `sandbox`, `docs`, `migrate`

Install all: `uv tool install glorious-agents[all-skills]`
Install specific: `uv tool install glorious-agents[notes,issues,planner]`

## Creating Skills

Skills are Python packages with a manifest and CLI commands. Basic structure:

```python
# skill.py
import typer
from glorious_agents.core.runtime import get_skill_context

app = typer.Typer()

@app.command()
def hello(name: str = "World") -> None:
    """Say hello."""
    ctx = get_skill_context()
    print(f"Hello, {name}!")
    ctx.publish("greeting_sent", {"name": name})
```

```json
// skill.json
{
  "name": "my-skill",
  "version": "0.1.0",
  "description": "My custom skill",
  "requires_db": true
}
```

See [docs/skill-authoring.md](docs/skill-authoring.md) for details.



## Development

```bash
# Clone repo
git clone https://github.com/weholt/glorious-agents.git
cd glorious-agents

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run build pipeline (format, lint, type-check, test)
python scripts/build.py
```

## Architecture

- **SQLite**: Each agent has isolated database with WAL mode for concurrency
- **Skills**: Self-contained packages with CLI commands, database schemas, and event handlers
- **Events**: Pub/sub system for skill communication
- **Entry Points**: Skills auto-discovered via Python entry points

## Documentation

- [Skill Authoring Guide](docs/skill-authoring.md)
- [Quick Start Guide](QUICKSTART.md)
- [Version Scheme](VERSION_SCHEME.md) - Official versioning policy
- [Version Management](docs/version-management.md) - How to bump versions
- [Releasing Guide](RELEASING.md) - Release process
- [GitHub Issues](https://github.com/weholt/glorious-agents/issues)

## License

MIT License - see [LICENSE](LICENSE)

---

**Built with ❤️ for AI agents and their humans**


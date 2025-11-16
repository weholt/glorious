<div align="center">

# 🌟 Glorious Agents 🌟

### *A Modular, Skill-Based Agent Framework for AI-Powered Workflows*

[![PyPI version](https://badge.fury.io/py/glorious-agents.svg)](https://badge.fury.io/py/glorious-agents)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/weholt/glorious-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/weholt/glorious-agents/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/weholt/glorious-agents/branch/main/graph/badge.svg)](https://codecov.io/gh/weholt/glorious-agents)

---

**Glorious Agents** is a powerful, extensible framework for building AI agents with modular skills, shared state, and event-driven architecture. Design complex workflows, manage multiple agent identities, and extend functionality with plug-and-play skills.

**Built for [uv](https://github.com/astral-sh/uv)** - the blazingly fast Python package manager 🚀

[Features](#-key-features) • [Quick Start](#-quick-start) • [Skills](#-skills-ecosystem) • [Documentation](#-documentation) • [Contributing](#-contributing)

---

</div>

## 🎯 Key Features

### 🧩 Modular Architecture
- **Plug-and-Play Skills**: Discover and load skills from local folders, pip packages, or entry points
- **17 Built-in Skills**: Issues, notes, planner, code-atlas, automations, and more
- **Skill Dependencies**: Automatic dependency resolution with topological sorting
- **Hot Reloading**: Reload skills without restarting (development mode)

### 🤖 Multi-Agent Support
- **Multiple Identities**: Create and manage different agent personas
- **Isolated Databases**: Each agent has its own SQLite database
- **Context Switching**: Easily switch between agents
- **Role-Based**: Assign roles and projects to agents

### 💾 Shared Database
- **SQLite with WAL**: One database per agent, shared across all skills
- **Auto-Init Schemas**: Skills define SQL schemas that initialize automatically
- **Type-Safe**: Full SQLAlchemy/SQLModel support
- **Migrations**: Built-in migration support for schema evolution

### 📡 Event-Driven
- **Event Bus**: In-process pub/sub for loose coupling between skills
- **Skill Communication**: Skills can react to events from other skills
- **Async Support**: Event handlers can be synchronous or asynchronous
- **Event History**: Optional event logging and replay

### 🛠️ Developer Experience
- **CLI & Daemon**: Rich CLI interface + optional FastAPI daemon for RPC
- **Type-Safe**: Full type hints with mypy strict mode
- **Quality Gates**: Built-in testing, linting, and security scanning
- **Auto-Documentation**: Skills self-document their commands and features
- **Hot Reloading**: Fast development cycle with auto-reload

### 🔒 Production Ready
- **Tested**: Comprehensive test suite with 75%+ coverage
- **Type-Checked**: mypy strict mode ensures type safety
- **Linted**: ruff for fast, consistent code formatting
- **Secure**: Regular security scanning with bandit
- **CI/CD**: GitHub Actions for automated testing and deployment

## 💡 What is Glorious Agents?

Glorious Agents is a **modular framework** for building AI-powered agents that can:
- **Think**: Use AI skills to analyze, plan, and make decisions
- **Remember**: Store and recall information using a shared database
- **Act**: Execute tasks using specialized skills (notes, issues, code analysis, automation)
- **Communicate**: Skills talk to each other via events for complex workflows
- **Adapt**: Add new skills without modifying core framework

### Core Concepts

#### 🧩 Skills
Skills are **self-contained Python packages** that add functionality to your agent. Each skill:
- Has its own commands (via CLI)
- Can define database schemas
- Can publish and subscribe to events
- Can depend on other skills
- Self-documents its capabilities

**Example:** The `issues` skill provides task tracking, the `notes` skill handles note-taking, and `code-atlas` analyzes codebases.

#### 🤖 Agents
Agents are **identities** with their own:
- Name and role (e.g., "Dev Agent", "Research Assistant")
- Isolated database (all skills share this database)
- Configuration and state
- Project context

**Example:** You might have a "Backend Dev" agent for coding tasks and a "Documentation" agent for writing docs.

#### 📡 Events
Skills communicate via an **event bus**:
- Skills publish events (e.g., "note_created", "issue_updated")
- Other skills subscribe and react
- Enables loosely coupled workflows
- Supports async handlers

**Example:** When you create a note with `#create-issue` tag, the notes skill publishes an event, and the issues skill creates an issue automatically.

#### 💾 Shared Database
All skills share one **SQLite database** per agent:
- WAL mode for better concurrency
- Automatic schema initialization
- Migration support
- Type-safe with SQLModel

## 🚀 Quick Start

### Installation

**Glorious Agents is designed for [uv](https://github.com/astral-sh/uv)** - the blazingly fast Python package manager.

#### Recommended: Install as a uv Tool (Global CLI)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install glorious-agents with all skills
uv tool install glorious-agents[all-skills]

# Use from anywhere
uvx agent --help
uvx agent version
```

#### Alternative: Install in a Project
```bash
# Create a new project
uv init my-agent-project
cd my-agent-project

# Add glorious-agents to your project
uv add glorious-agents[all-skills]

# Use with uv run
uv run agent --help
```

#### For Development
```bash
# Clone and install
git clone https://github.com/weholt/glorious-agents.git
cd glorious-agents

# Sync dependencies
uv sync

# Run from source
uv run agent --help
```

> **Note:** While you can use `uv pip install`, the recommended approach is `uv tool install` for global CLI tools or `uv add` for project dependencies.

### Basic Usage

```bash
# Register an agent identity
uvx agent identity register --name "Dev Agent" --role "Development" --project-id myproject

# Switch to the agent
uvx agent identity use dev-agent

# Check current agent
uvx agent identity whoami

# List all agents
uvx agent identity list

# List available skills
uvx agent skills list

# Describe a skill in detail
uvx agent skills describe issues

# Use skills (examples)
uvx agent notes add "My first note" --tags important
uvx agent notes list
uvx agent notes search "first"

uvx agent issues create "Fix bug" --priority high --tags bug
uvx agent issues list

# Start the daemon for RPC access
uvx agent daemon --host 127.0.0.1 --port 8765
```

### Why uv?

- **Blazingly Fast**: 10-100x faster than pip
- **Reliable**: Reproducible installs with lockfiles
- **Modern**: Built for Python 3.7+
- **Compatible**: Drop-in replacement for pip/poetry/pipenv
- **Tool Management**: Global tools isolated from project environments

Learn more at [astral.sh/uv](https://github.com/astral-sh/uv)

## 🎨 Skills Ecosystem

Glorious Agents comes with **17 built-in skills** that provide a complete toolkit for AI agents:

### 📝 Knowledge Management

#### **issues** - Task & Issue Tracking
- ✓ 30+ commands for complete workflow management
- ✓ Dependencies, epics, comments, and labels
- ✓ Full-text search with templates
- ✓ Bulk operations and automation

#### **notes** - Note-Taking System
- ✓ Tagged notes with full-text search
- ✓ Auto-create issues from notes
- ✓ Export/import functionality

#### **code-atlas** - Codebase Intelligence
- ✓ Scan and analyze codebase structure
- ✓ AI-powered code Q&A
- ✓ Refactoring priorities
- ✓ Quality metrics

### 🤖 Workflow & Automation

#### **planner** - Task Queue Management
- ✓ Smart task prioritization
- ✓ Dependency resolution
- ✓ "Next task" suggestions

#### **automations** - Workflow Automation
- ✓ Trigger-based workflows
- ✓ Multi-step automation
- ✓ Integration templates

#### **orchestrator** - Intent Routing
- ✓ Natural language to skill routing
- ✓ Pattern matching
- ✓ Context management

### 💾 Storage & Utilities

#### **cache** - Ephemeral Storage
- ✓ TTL-based key-value store
- ✓ Fast temporary data storage

#### **linker** - Cross-References
- ✓ Semantic links between entities
- ✓ Graph traversal
- ✓ Relationship management

#### **feedback** - Outcome Tracking
- ✓ Success/failure tracking
- ✓ Learning from results
- ✓ Performance analytics

### 🎯 AI & Intelligence

#### **prompts** - Prompt Management
- ✓ Template storage and versioning
- ✓ Variable substitution
- ✓ Categorization

#### **ai** - AI Integration
- ✓ LLM connections
- ✓ Chat and embeddings
- ✓ Conversation history

### 📊 Monitoring & Analysis

#### **telemetry** - Action Logging
- ✓ Comprehensive action tracking
- ✓ Performance metrics
- ✓ Audit trails

#### **temporal** - Time Operations
- ✓ Date parsing and filtering
- ✓ Time-aware queries
- ✓ Scheduled operations

#### **vacuum** - Data Optimization
- ✓ Knowledge summarization
- ✓ Archive management
- ✓ Storage optimization

### 🛠️ Development Tools

#### **sandbox** - Isolated Execution
- ✓ Docker-based code execution
- ✓ Resource management
- ✓ Safe testing

#### **docs** - Documentation
- ✓ Auto-generation
- ✓ Documentation search
- ✓ Validation

#### **migrate** - Data Migration
- ✓ Schema evolution
- ✓ Data transformations
- ✓ Rollback support

---

### Installing Skills

```bash
# Install as global tool with all skills
uv tool install glorious-agents[all-skills]

# Or install specific skills only
uv tool install glorious-agents[notes,issues,planner]

# For project-based installation
uv add glorious-agents[all-skills]

# Or specific skills
uv add glorious-agents[notes,issues,planner]
```

## Architecture

### Directory Structure

```
glorious/
├── src/glorious_agents/          # Core framework
│   ├── core/
│   │   ├── db.py                 # Shared SQLite with WAL mode
│   │   ├── context.py            # EventBus and SkillContext
│   │   ├── runtime.py            # Singleton context accessor
│   │   ├── registry.py           # In-process skill registry
│   │   ├── loader.py             # Discovery and dependency resolution
│   │   ├── validation.py         # Skill manifest validation
│   │   └── daemon.py             # FastAPI RPC service
│   ├── cli.py                    # Main CLI entry point
│   ├── skills_cli.py             # Skills management commands
│   ├── identity_cli.py           # Agent identity commands
│   └── config.py                 # Configuration management
├── example-skills/               # Example skill implementations
│   ├── cache/                    # Ephemeral storage with TTL
│   ├── notes/                    # Note-taking with tags
│   ├── issues/                   # Issue tracking
│   ├── linker/                   # Semantic cross-references
│   ├── planner/                  # Action queue management
│   ├── telemetry/                # Agent action logging
│   ├── prompts/                  # Prompt template management
│   ├── feedback/                 # Outcome tracking
│   ├── sandbox/                  # Docker isolation
│   ├── orchestrator/             # Intent routing
│   ├── vacuum/                   # Knowledge distillation
│   └── temporal/                 # Time-aware filtering
├── tests/                        # Unit and integration tests
├── scripts/                      # Build and utility scripts
└── docs/                         # Documentation
```

### Agent Data Structure

```
~/.glorious/                      # Default agent folder
├── active_agent                  # Current agent code
├── master.db                     # Agent registry database
└── agents/
    ├── dev-agent/
    │   └── agent.db              # Dev agent's database
    ├── test-agent/
    │   └── agent.db              # Test agent's database
    └── prod-agent/
        └── agent.db              # Prod agent's database
```

## Configuration

Configuration is managed through environment variables with the `GLORIOUS_` prefix:

```env
# Agent data directory (default: ~/.glorious)
GLORIOUS_AGENT_FOLDER=/path/to/custom/folder

# Database names
GLORIOUS_DB_SHARED_NAME=glorious_shared.db
GLORIOUS_DB_MASTER_NAME=master.db

# Daemon settings
GLORIOUS_DAEMON_HOST=127.0.0.1
GLORIOUS_DAEMON_PORT=8765

# Skills directory
GLORIOUS_SKILLS_DIR=skills
```

Create a `.env` file in your project root or set environment variables directly.

## Event Catalog

The framework provides a standardized event system for skill communication:

### Core Events

| Event | Description | Data Schema |
|-------|-------------|-------------|
| `note_created` | Note was created | `{id: int, content: str, tags: list[str]}` |
| `note_updated` | Note was modified | `{id: int, content: str}` |
| `note_deleted` | Note was removed | `{id: int}` |
| `issue_created` | Issue was created | `{id: int, title: str, priority: str}` |
| `issue_updated` | Issue status changed | `{id: int, status: str}` |
| `issue_closed` | Issue was closed | `{id: int}` |
| `plan_enqueued` | Action added to queue | `{action: str, priority: int}` |
| `plan_completed` | Action finished | `{action: str, result: str}` |
| `scan_ready` | Cross-references updated | `{count: int}` |
| `vacuum_done` | Knowledge distillation complete | `{removed: int}` |

### Publishing Events

```python
from glorious_agents.core.runtime import get_skill_context

ctx = get_skill_context()
ctx.publish("note_created", {"id": 123, "content": "Test", "tags": ["important"]})
```

### Subscribing to Events

```python
from glorious_agents.core.context import SkillContext

def init_context(ctx: SkillContext) -> None:
    """Called during skill initialization."""
    ctx.subscribe("note_created", handle_note_created)

def handle_note_created(data: dict[str, Any]) -> None:
    """Handle note creation events."""
    print(f"Note created: {data['id']}")
```

## CLI Usage

### Identity Management

```bash
# Register a new agent
agent identity register --name "Code Reviewer" --role "Review PRs" --project-id myapp

# Switch active agent
agent identity use code-reviewer

# Show current agent
agent identity whoami

# List all agents
agent identity list
```

### Skills Management

```bash
# List loaded skills
agent skills list

# Show detailed skill info
agent skills describe cache

# Export skills metadata
agent skills export --format json
agent skills export --format md
agent skills export --skill cache --format json
```

### Example Skill Usage

```bash
# Notes skill
agent notes add "Implement feature X" --tags todo,feature
agent notes list
agent notes list --tags todo
agent notes search "feature"
agent notes get 1
agent notes delete 1

# Issues skill
agent issues create "Fix login bug" --priority high --tags bug,security
agent issues list
agent issues list --status open
agent issues update 1 --status in-progress
agent issues close 1
```

## Daemon RPC

Start the daemon for remote procedure calls:

```bash
agent daemon --host 0.0.0.0 --port 8765
```

Access endpoints:

```bash
# Health check
curl http://localhost:8765/health

# List skills
curl http://localhost:8765/skills

# Execute skill command (example)
curl -X POST http://localhost:8765/execute \
  -H "Content-Type: application/json" \
  -d '{"skill": "notes", "command": "list"}'
```

## Skill Development

Skills are self-contained Python packages with a specific structure. See [Skill Authoring Guide](docs/skill-authoring.md) for complete documentation.

### Quick Skill Structure

```
my-skill/
├── src/
│   └── my_skill/
│       ├── __init__.py
│       ├── skill.json          # Manifest
│       ├── skill.py            # Implementation
│       ├── schema.sql          # Database schema
│       ├── instructions.md     # Internal docs (for agents)
│       └── usage.md            # External docs (for users)
├── tests/
│   └── test_my_skill.py
└── pyproject.toml
```

### Skill Manifest (skill.json)

```json
{
  "name": "my-skill",
  "version": "0.1.0",
  "description": "Short description of what the skill does",
  "requires": ["dependency-skill"],
  "schema_file": "schema.sql",
  "requires_db": true
}
```

### Skill Implementation (skill.py)

```python
import typer
from glorious_agents.core.context import SkillContext
from glorious_agents.core.runtime import get_skill_context

app = typer.Typer()

def init_context(ctx: SkillContext) -> None:
    """Initialize skill context and subscribe to events."""
    ctx.subscribe("note_created", handle_note_created)

def handle_note_created(data: dict) -> None:
    """Handle note creation events."""
    print(f"Note created: {data['id']}")

@app.command()
def hello(name: str = "World") -> None:
    """Say hello."""
    print(f"Hello, {name}!")
    
    # Publish an event
    ctx = get_skill_context()
    ctx.publish("greeting_sent", {"name": name})
```

### Database Schema (schema.sql)

```sql
CREATE TABLE IF NOT EXISTS my_skill_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_my_skill_items_created 
ON my_skill_items(created_at);
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run only unit tests
uv run pytest -m logic

# Run only integration tests
uv run pytest -m integration

# Run specific test file
uv run pytest tests/unit/test_loader.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Type check
uv run mypy src

# Security scan
uv run bandit -r src
```

### Build Pipeline

Run the comprehensive build pipeline:

```bash
python scripts/build.py
```

This executes:
1. ✅ Dependency checks
2. ✅ Dependency sync
3. ✅ Code formatting
4. ✅ Code linting
5. ✅ Type checking
6. ✅ Security checks
7. ✅ Unit tests with coverage
8. ✅ Report generation

### Pre-commit Hooks

```bash
# Install hooks
uv run pre-commit install

# Run on all files
uv run pre-commit run --all-files

# Run on staged files
git add .
uv run pre-commit run
```

## Example Skills

The framework includes 10+ example skills demonstrating various patterns:

### 1. Cache (`glorious_cache`)
Short-term ephemeral storage with TTL support. Demonstrates basic CRUD operations and time-based cleanup.

**Commands**: `set`, `get`, `delete`, `clear`, `prune`

### 2. Notes (`glorious_skill_notes`)
Note-taking with tags and full-text search. Demonstrates FTS5 search and event publishing.

**Commands**: `add`, `list`, `get`, `search`, `delete`

### 3. Issues (`glorious_skill_issues`)
Issue tracking with status workflow. Demonstrates event subscriptions and status management.

**Commands**: `create`, `list`, `update`, `close`

### 4. Linker (`glorious_linker`)
Semantic cross-references between entities. Demonstrates relationship tracking.

**Commands**: `link`, `unlink`, `list`, `find`

### 5. Planner (`glorious_planner`)
Action queue management with priorities. Demonstrates queue operations.

**Commands**: `enqueue`, `dequeue`, `list`, `clear`

### 6. Telemetry (`glorious_telemetry`)
Agent action logging and metrics. Demonstrates observability.

**Commands**: `log`, `list`, `stats`, `clear`

### 7. Prompts (`glorious_prompts`)
Prompt template management with variables. Demonstrates template rendering.

**Commands**: `add`, `list`, `render`, `delete`

### 8. Feedback (`glorious_feedback`)
Outcome tracking for continuous improvement. Demonstrates feedback loops.

**Commands**: `record`, `list`, `stats`

### 9. Sandbox (`glorious_sandbox`)
Docker container isolation for code execution. Demonstrates external tool integration.

**Commands**: `run`, `list`, `stop`, `clean`

### 10. Orchestrator (`glorious_orchestrator`)
Intent routing to appropriate skills. Demonstrates orchestration patterns.

**Commands**: `route`, `register`, `list`

### Additional Skills

- **Vacuum (`glorious_vacuum`)**: Knowledge distillation and cleanup
- **Temporal (`glorious_temporal`)**: Time-aware filtering and scheduling

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `uv run pytest`
5. Run quality checks: `python scripts/build.py`
6. Commit: `git commit -am 'Add my feature'`
7. Push: `git push origin feature/my-feature`
8. Create a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write docstrings for public APIs
- Add tests for new features
- Update documentation
- Ensure all quality gates pass

## Architecture Decisions

### Why SQLite?

- **Simplicity**: No separate database server needed
- **Portability**: Single file per agent
- **Performance**: Fast for agent workloads with WAL mode
- **Reliability**: ACID compliance built-in
- **Concurrency**: WAL mode supports multiple readers + one writer

### Why Skills?

- **Modularity**: Easy to add/remove capabilities
- **Reusability**: Skills can be shared across projects
- **Isolation**: Each skill manages its own schema
- **Discovery**: Automatic loading via entry points
- **Dependencies**: Clear dependency tree

### Why Events?

- **Loose Coupling**: Skills don't need direct references
- **Extensibility**: New skills can hook into existing events
- **Async-Ready**: Foundation for future async support
- **Observability**: Easy to track system behavior

## Troubleshooting

### Skills Not Loading

```bash
# Check if skills are installed
uv pip list | grep glorious

# Verify entry points
python -c "from importlib.metadata import entry_points; print(entry_points(group='glorious.skills'))"

# Check for errors
agent skills list -v
```

### Database Issues

```bash
# Check database location
agent identity whoami

# Verify database file
ls ~/.glorious/agents/*/agent.db

# Check schema
sqlite3 ~/.glorious/agents/my-agent/agent.db ".tables"
```

### Type Checking Errors

```bash
# Run mypy with verbose output
uv run mypy src --show-error-codes

# Check specific file
uv run mypy src/glorious_agents/core/loader.py
```

## Performance Considerations

- **WAL Mode**: Enables concurrent reads while writing
- **Connection Pooling**: Reuse connections within the same process
- **Batch Operations**: Use transactions for multiple inserts/updates
- **Indexes**: Add indexes for frequently queried columns
- **FTS5**: Use full-text search for text-heavy queries
- **Lazy Loading**: Skills load only when first accessed

## Security Considerations

- **SQL Injection**: Use parameterized queries (framework enforces this)
- **File Access**: Skills operate in controlled directories
- **Event Data**: Validate event data schemas
- **Sandbox Skills**: Use Docker isolation for untrusted code
- **Database Encryption**: Consider SQLCipher for sensitive data

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [FastAPI](https://fastapi.tiangolo.com/) - Daemon RPC
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [SQLite](https://www.sqlite.org/) - Database
- [uv](https://github.com/astral-sh/uv) - Package management

## Support

- **Issues**: [GitHub Issues](https://github.com/weholt/glorious-agents/issues)
- **Discussions**: [GitHub Discussions](https://github.com/weholt/glorious-agents/discussions)
- **Documentation**: [docs/](docs/)

---

**Built with ❤️ for AI agents and their humans**

## Installing Skills

Glorious Agents has a modular skill system. Skills are located in `src/glorious_agents/skills/`.

### Using Extras (Recommended for Production)

Install skills using optional dependencies:

```bash
# As a global tool with specific skills
uv tool install glorious-agents[notes,planner,issues]

# As a global tool with all skills
uv tool install glorious-agents[all-skills]

# In a project with specific skills
uv add glorious-agents[notes,planner,issues]

# In a project with all skills  
uv add glorious-agents[all-skills]

# For development from source
uv pip install -e ".[all-skills]"
```

Available skill extras: `ai`, `automations`, `cache`, `code-atlas`, `docs`, `feedback`, `issues`, `linker`, `migrate`, `notes`, `orchestrator`, `planner`, `prompts`, `sandbox`, `telemetry`, `temporal`, `vacuum`, `all-skills`

### Interactive Installation (Great for Development)

Use the glorious TUI installer:

```bash
./install-skills.sh
```

This will present an interactive menu where you can:
- Select individual skills or all at once
- Use ranges (e.g., `1-5`) or lists (e.g., `1 3 7`)
- See installation progress in real-time
- Get a detailed summary of results

### Manual Installation

Install individual skills directly:

```bash
# Install a single skill
uv pip install -e ./src/glorious_agents/skills/notes

# Install multiple skills
uv pip install -e ./src/glorious_agents/skills/{notes,planner,issues}

# Install all skills
uv pip install -e ./src/glorious_agents/skills/*
```

### Available Skills

Run the installer to see all available skills with descriptions, or check `src/glorious_agents/skills/`.


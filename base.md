# Glorious Agents Framework - Complete Documentation

**Version:** 0.2.0  
**Status:** Pre-alpha / Proof-of-concept  
**Last Updated:** 2025-11-18

> **⚠️ WARNING**: This is under heavy development and should be considered Pre-alpha, and a Proof-of-concept. Do not use this in anything even remotely important.

---

## Table of Contents

1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Installation & Setup](#installation--setup)
4. [Core Features](#core-features)
5. [Skills Reference](#skills-reference)
6. [Agentic Workflow](#agentic-workflow)
7. [Development Guide](#development-guide)
8. [Testing](#testing)
9. [Planned Improvements](#planned-improvements)
10. [Technical Details](#technical-details)

---

## Overview

Glorious Agents is a modular framework for building AI agents with plug-and-play skills, shared state, and event-driven workflows. Built for [uv](https://github.com/astral-sh/uv).

### Key Concepts

- **Skills**: Self-contained packages that add functionality (17 built-in)
- **Agents**: Named identities with isolated databases and project contexts
- **Events**: Skills communicate via pub/sub for complex workflows
- **Database**: Shared SQLite per agent with automatic schema initialization

### Built-in Skills (17)

`notes`, `issues`, `planner`, `code-atlas`, `automations`, `orchestrator`, `cache`, `linker`, `feedback`, `prompts`, `ai`, `telemetry`, `temporal`, `vacuum`, `sandbox`, `docs`, `migrate`

---

## Core Architecture

### System Structure

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer (Typer)                     │
│  - Command handlers                                      │
│  - Input validation (Pydantic)                          │
│  - Output formatting (Rich)                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Skill System                           │
│  - Auto-discovery via entry points                      │
│  - Event pub/sub system                                 │
│  - Dependency resolution                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Database Layer                           │
│  - SQLite with WAL mode                                 │
│  - Per-agent isolation                                  │
│  - Automatic schema migrations                          │
└─────────────────────────────────────────────────────────┘
```

### Database Isolation

Each agent has its own isolated database:
- **Master Registry**: `.agent/master.db` (all agents)
- **Active Agent File**: `.agent/active_agent` (current agent code)
- **Agent Database**: `.agent/agents/<code>/agent.db` (per agent)

### Entry Point System

Skills are auto-discovered via Python entry points:

```toml
[project.entry-points."glorious_agents.skills"]
skill_name = "glorious_skill_name.skill:app"
```

The framework automatically:
1. Discovers installed packages with this entry point
2. Loads skill.json metadata from the package
3. Resolves dependencies between skills
4. Initializes database schemas
5. Registers Typer apps with CLI

---

## Installation & Setup

### Prerequisites

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Globally

```bash
# Install with all skills
uv tool install glorious-agents[all-skills]

# Use from anywhere
uvx agent --help
```

### Install in Project

```bash
# Create a new project
uv init my-agent-project
cd my-agent-project

# Add glorious-agents
uv add glorious-agents[all-skills]

# Use with uv run
uvx agent --help
```

### Development from Source

```bash
# Clone the repository
git clone https://github.com/weholt/glorious-agents.git
cd glorious-agents

# Install dependencies (includes dev tools)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### First Steps

```bash
# Initialize the framework
uvx agent init

# List available skills
uvx agent skills list

# Create an agent identity
uvx agent identity register --name "developer" --role "Software Developer"

# Switch to the agent
uvx agent identity use developer

# Verify
uvx agent identity whoami
```

---

## Core Features

### 1. Main CLI Commands

#### `agent version`
Display version information.

```bash
uvx agent version
```

#### `agent init`
Initialize workspace by generating AGENT-TOOLS.md and updating AGENTS.md.

```bash
uvx agent init
```

**What it does:**
- Scans all installed skills
- Generates AGENT-TOOLS.md with usage documentation
- Updates AGENTS.md with skill references
- Auto-updates when skills change

#### `agent info`
Display system information.

```bash
uvx agent info
```

Shows:
- Data folder location
- Active agent
- Database type and size
- Table counts

#### `agent search <query>`
Universal search across all skills.

```bash
# Search everything
uvx agent search "quantum physics"

# With limit
uvx agent search "authentication" --limit 20

# JSON output
uvx agent search "test" --json
```

**Searches across:**
- Issues: titles, descriptions, comments
- Notes: content and tags
- Automations: names, descriptions, triggers
- Workflows: names and intents
- Prompts: names and templates
- Telemetry: event categories
- Cache: keys and values
- Feedback: actions and contexts
- And more...

#### `agent daemon`
Start FastAPI daemon for RPC access.

```bash
# Default (127.0.0.1:8765)
uvx agent daemon

# Custom host/port
uvx agent daemon --host 0.0.0.0 --port 9000
```

### 2. Skills Management

#### `agent skills list`
List all loaded skills with metadata.

```bash
uvx agent skills list
```

#### `agent skills describe <skill>`
Show detailed information about a skill.

```bash
uvx agent skills describe notes
```

#### `agent skills reload [skill]`
Reload all skills or a specific skill.

```bash
# Reload all
uvx agent skills reload

# Reload specific
uvx agent skills reload notes
```

#### `agent skills export`
Export skills metadata.

```bash
# JSON format
uvx agent skills export --format json

# Markdown format
uvx agent skills export --format md

# Specific skill
uvx agent skills export --format json --skill notes
```

#### `agent skills check <skill>`
Health check for a skill.

```bash
uvx agent skills check notes
```

#### `agent skills doctor`
Diagnostic check for all skills.

```bash
uvx agent skills doctor
```

#### `agent skills config <skill>`
Manage skill configuration.

```bash
# Show all config
uvx agent skills config notes

# Show specific key
uvx agent skills config notes --key some_key

# Set value
uvx agent skills config notes --key test_key --set test_value

# Reset config
uvx agent skills config notes --reset
```

#### `agent skills migrate`
Manage database migrations.

```bash
# Check status
uvx agent skills migrate status

# Run migrations
uvx agent skills migrate up

# Revert migrations
uvx agent skills migrate down
```

### 3. Identity Management

#### `agent identity register`
Register a new agent identity.

```bash
uvx agent identity register \
  --name "Developer" \
  --role "Code Review" \
  --project-id "myproject"
```

Agent names are automatically converted to codes (e.g., "Developer" → "developer").

#### `agent identity use <code>`
Switch to a different agent.

```bash
uvx agent identity use developer
```

#### `agent identity whoami`
Show current agent details.

```bash
uvx agent identity whoami
```

#### `agent identity list`
List all registered agents.

```bash
uvx agent identity list
```

### 4. Event System

Skills communicate via pub/sub events:

```python
# Publishing events
ctx.publish("note_created", {"id": note_id, "content": content})

# Subscribing to events
ctx.subscribe("note_created", handle_note_created)

def handle_note_created(data: dict) -> None:
    print(f"Note created: {data['id']}")
```

**Common Events:**
- `note_created` - When a note is added
- `issue_created` - When an issue is created
- `task_completed` - When a task is finished

### 5. Universal Search API

Cross-skill search with relevance scoring:

```python
from glorious_agents.core.search import search_all_skills

results = search_all_skills(ctx, "architecture")
# Returns: list of {skill, id, type, content, metadata, score}
```

**Features:**
- Automatic relevance scoring
- Importance-based boosting
- Type-specific filtering
- Cross-skill aggregation

---

## Skills Reference

### Notes Skill

Persistent notes with full-text search and importance levels.

**Commands:**
- `add` - Add a new note
- `list` - List recent notes
- `search` - Full-text search
- `get` - Get specific note
- `delete` - Delete a note
- `mark` - Update importance level

**Importance Levels:**
- **Normal** (0): Regular notes
- **Important** (★, 1): Key decisions, topics needing attention
- **Critical** (⚠, 2): Security issues, blockers, must-address items

**Examples:**

```bash
# Add notes
uvx agent notes add "Regular note"
uvx agent notes add "Key decision" --important --tags "architecture"
uvx agent notes add "Security issue" --critical --tags "security,urgent"

# List notes
uvx agent notes list
uvx agent notes list --important  # Important + critical
uvx agent notes list --critical   # Critical only
uvx agent notes list --limit 20

# Search
uvx agent notes search "quantum"
uvx agent notes search "security" --important

# Update importance
uvx agent notes mark 123 --critical
uvx agent notes mark 123 --normal

# Get/Delete
uvx agent notes get 123
uvx agent notes delete 123
```

**Features:**
- SQLite FTS5 full-text search
- Tag-based organization
- Importance-based prioritization
- Event publishing (`note_created`)
- Universal search integration

**Database Schema:**

```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',
    importance INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_notes_importance 
  ON notes(importance DESC, created_at DESC);
```

---

### Issues Skill

Git-backed issue tracking with hierarchical relationships.

**Commands:**
- `create` - Create new issue
- `list` - List and filter issues
- `search` - Full-text search
- `show` - Display detailed information
- `update` - Update an issue
- `close` / `reopen` - Change status
- `delete` / `restore` - Remove/restore issues
- `bulk-*` - Bulk operations
- `ready` - List ready issues
- `blocked` - List blocked issues
- `stats` - Show statistics
- `stale` - Find stale issues
- `duplicates` - Find/merge duplicates
- `merge` - Merge duplicate issues
- `export` / `import` - JSONL import/export
- `cleanup` - Delete closed issues
- `compact` - Compress old issues
- `template_*` - Template management

**Examples:**

```bash
# Create issues
uvx agent issues create "Fix bug" --priority high --tags bug,security
uvx agent issues create "Add feature" --type feature --priority 2

# List and filter
uvx agent issues list
uvx agent issues list --status open
uvx agent issues list --filter "label:bug"
uvx agent issues ready --sort priority
uvx agent issues blocked

# Update
uvx agent issues update 1 --status in-progress --priority high
uvx agent issues close 1
uvx agent issues reopen 1

# Search
uvx agent issues search "authentication"

# Bulk operations
uvx agent issues bulk-update --filter "label:refactor" --add-label technical-debt
uvx agent issues bulk-close --filter "label:wontfix" --reason "Out of scope"
uvx agent issues bulk-label-add --filter "priority:1" --labels urgent

# Dependencies
uvx agent issues dependencies add ISSUE-123 ISSUE-456 --type blocks
uvx agent issues dependencies tree ISSUE-100
uvx agent issues dependencies cycles

# Maintenance
uvx agent issues stale --days 30
uvx agent issues duplicates --auto-merge
uvx agent issues compact --days 90 --priority 3
uvx agent issues cleanup --older-than 180

# Import/Export
uvx agent issues export backup.jsonl
uvx agent issues import backup.jsonl

# Templates
uvx agent issues template_save "bug_template" --type bug --priority 2
uvx agent issues template_list
uvx agent issues template_show bug_template
```

**Features:**
- Hierarchical relationships (parent/child, blocks/blocked-by)
- Priority and status tracking
- Label management
- Dependency graph with cycle detection
- Memory decay (compact old issues)
- Template system
- Full integration with notes (auto-create from "todo" tags)

---

### Planner Skill

Action queue management with priorities and state machine.

**Commands:**
- `add` - Add task to queue
- `next` - Get next task to work on
- `update` - Update task status
- `list` - List tasks in queue
- `sync` - Sync tasks from issue tracker
- `delete` - Delete a task

**Examples:**

```bash
# Add tasks
uvx agent planner add "Review PR #123" --priority high
uvx agent planner add "Update docs" --priority low --context "Related to ISSUE-123"

# Get next task
uvx agent planner next

# List tasks
uvx agent planner list

# Sync from issues
uvx agent planner sync

# Update status
uvx agent planner update TASK-501 --status in_progress
uvx agent planner update TASK-501 --status completed

# Delete
uvx agent planner delete TASK-501
```

**Features:**
- Priority-based queue
- State machine (pending → in_progress → completed)
- Issue tracker integration
- Context storage

---

### Cache Skill

Short-term ephemeral storage with TTL support.

**Commands:**
- `set` - Set cache entry
- `get` - Get cache entry
- `list` - List all entries
- `prune` - Remove expired entries
- `warmup` - Warmup with project data
- `delete` - Delete entry

**Examples:**

```bash
# Set cache
uvx agent cache set "key1" "value1"
uvx agent cache set "key2" "value2" --ttl 3600  # Expires in 1 hour
uvx agent cache set "key3" "value3" --kind "test"

# Get cache
uvx agent cache get "key1"

# List
uvx agent cache list
uvx agent cache list --kind "test"

# Prune
uvx agent cache prune  # Remove expired
uvx agent cache prune --expired-only false  # Remove all

# Warmup
uvx agent cache warmup --project-id "myproject"

# Delete
uvx agent cache delete "key1"
```

**Features:**
- TTL-based expiration
- Kind-based categorization
- Automatic pruning
- Binary value support

---

### AI Skill

LLM completions, embeddings, and semantic search.

**Commands:**
- `complete` - Generate LLM completion
- `embed` - Generate embeddings
- `semantic` - Semantic search
- `history` - View completion history

**Examples:**

```bash
# Completions
uvx agent ai complete "Explain quantum computing"
uvx agent ai complete "Write a poem" --model gpt-4 --provider openai
uvx agent ai complete "Analyze code" --max-tokens 2000 --json

# Embeddings
uvx agent ai embed "Some text to embed"
uvx agent ai embed "Document content" --model text-embedding-ada-002

# Semantic search
uvx agent ai semantic "quantum physics" --top-k 5

# History
uvx agent ai history --limit 20
uvx agent ai history --json
```

**Setup:**

```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

**Features:**
- Multi-provider support (OpenAI, Anthropic)
- Embedding generation
- Semantic search with cosine similarity
- Completion history tracking

---

### Automations Skill

Declarative event-driven automations.

**Commands:**
- `create` - Create automation
- `create-from-file` - Create from YAML/JSON
- `list` - List automations
- `show` - Show details
- `enable` / `disable` - Control state
- `delete` - Remove automation
- `executions` - View execution history

**Examples:**

```bash
# Create automation
uvx agent automations create \
  "Log notes" \
  "note.created" \
  '[{"type":"log","message":"Note created"}]'

# With condition
uvx agent automations create \
  "Alert" \
  "issue.created" \
  '[{"type":"publish","topic":"alert","data":{}}]' \
  --condition 'data.get("priority") == 1'

# From file
uvx agent automations create-from-file automation.yaml

# List and show
uvx agent automations list --enabled
uvx agent automations show auto-abc123

# Control
uvx agent automations enable auto-abc123
uvx agent automations disable auto-abc123
uvx agent automations delete auto-abc123

# History
uvx agent automations executions
uvx agent automations executions --automation auto-abc123
```

**YAML Format:**

```yaml
name: "Log new issues"
description: "Log when issues are created"
trigger_topic: "issue.created"
trigger_condition: 'data.get("priority") == 1'
actions:
  - type: log
    message: "High priority issue created!"
  - type: publish
    topic: "notifications.high"
    data: {}
```

**Action Types:**
- `log` - Print message
- `publish` - Publish event

---

### Code-Atlas Skill

Python codebase structure and metrics analyzer.

**Commands:**
- `scan` - Scan codebase and generate index
- `rank` - Rank files by refactor priority
- `check` - Check against quality rules
- `agent` - Query for agent integration (JSON output)
- `watch` - Watch for file changes
- `watch-status` - Check watch daemon status
- `stop-watch` - Stop watch daemon

**Examples:**

```bash
# Scan codebase
uvx agent code-atlas scan ./src

# Rank by refactor priority
uvx agent code-atlas rank

# Check quality rules
uvx agent code-atlas check

# Agent query (JSON)
uvx agent code-atlas agent "Where is authentication handled?"

# Watch mode
uvx agent code-atlas watch src/ &
uvx agent code-atlas watch-status
uvx agent code-atlas stop-watch
```

**Features:**
- AST-based code analysis
- Complexity metrics
- Refactor prioritization
- Quality rule checking
- Git integration
- Live file watching

---

### Telemetry Skill

Agent action logging and observability.

**Commands:**
- `log` - Log telemetry event
- `stats` - Show event statistics
- `list` - List recent events
- `export` - Export telemetry data

**Examples:**

```bash
# Log events
uvx agent telemetry log "test-category" "test message"
uvx agent telemetry log "category" "message" --skill "notes"
uvx agent telemetry log "category" "message" --duration 1500

# View stats
uvx agent telemetry stats --group-by category
uvx agent telemetry stats --group-by skill

# List events
uvx agent telemetry list
uvx agent telemetry list --category "test"
```

**Features:**
- Event categorization
- Skill attribution
- Duration tracking
- Statistical analysis

---

### Feedback Skill

Action outcome tracking and learning.

**Commands:**
- `record` - Record action feedback
- `list` - List recent feedback
- `stats` - Show feedback statistics

**Examples:**

```bash
# Record feedback
uvx agent feedback record "implement_auth" \
  --outcome success \
  --context "Used JWT with refresh tokens" \
  --notes "Works well, consider rate limiting"

# View feedback
uvx agent feedback list --limit 10
uvx agent feedback stats
```

**Features:**
- Success/failure tracking
- Context preservation
- Learning from outcomes

---

### Prompts Skill

Prompt template management and versioning.

**Commands:**
- `register` - Register new template
- `list` - List all templates
- `render` - Render template with variables
- `delete` - Delete template

**Examples:**

```bash
# Register template
uvx agent prompts register \
  "code_review" \
  "Review {{file}} for: 1) Security 2) Performance 3) Style"

# List templates
uvx agent prompts list

# Render with variables
uvx agent prompts render code_review --var file=auth.py

# Delete
uvx agent prompts delete code_review
```

**Features:**
- Variable substitution
- Version management
- Template reuse

---

### Temporal Skill

Time-aware filtering across skills.

**Commands:**
- `parse` - Parse time specification
- `filter-since` - Show filter query
- `examples` - Show examples

**Examples:**

```bash
# Parse time
uvx agent temporal parse "7d"
uvx agent temporal parse "3h"

# Filter examples
uvx agent temporal filter-since "7d"
uvx agent temporal examples
```

**Features:**
- Relative time parsing (7d, 3h, etc.)
- Filter query generation
- Cross-skill time filtering

---

### Vacuum Skill

Knowledge distillation and optimization.

**Commands:**
- `run` - Run vacuum operation
- `history` - Show vacuum history

**Examples:**

```bash
# Run vacuum
uvx agent vacuum run --mode summarize
uvx agent vacuum run --mode dedupe

# View history
uvx agent vacuum history
```

**Modes:**
- `summarize` - Compress verbose content
- `dedupe` - Remove duplicates

---

### Docs Skill

Structured documentation management with epic linking.

**Commands:**
- `create` - Create new document
- `get` - Get document by ID
- `update` - Update document
- `list` - List all documents
- `search_docs` - Search by content
- `export_doc` - Export to markdown
- `versions` - List version history

**Examples:**

```bash
# Create document
uvx agent docs create "Architecture Doc" --content "Content here"
uvx agent docs create --from-file design.md

# Get and list
uvx agent docs get doc-123
uvx agent docs list

# Search
uvx agent docs search "architecture"

# Export
uvx agent docs export_doc doc-123 output.md

# Versions
uvx agent docs versions doc-123
```

**Features:**
- Version control
- Epic linking
- Markdown export
- Full-text search

---

### Orchestrator Skill

Intent routing and multi-tool workflows.

**Commands:**
- `run` - Execute workflow from natural language
- `list` - List workflow history
- `status` - Check workflow status

**Examples:**

```bash
# Run workflow
uvx agent orchestrator run "Create a note about testing"

# List workflows
uvx agent orchestrator list

# Check status
uvx agent orchestrator status 1
```

**Features:**
- Natural language intent parsing
- Multi-skill orchestration
- Workflow state management

---

### Linker Skill

Semantic cross-references between entities.

**Commands:**
- `add` - Add link between entities
- `list` - List all links
- `context` - Get context bundle
- `rebuild` - Rebuild links
- `delete` - Delete link

**Examples:**

```bash
# Add links
uvx agent linker add "related" --a "note:1" --b "issue:2"
uvx agent linker add "blocks" --a "issue:1" --b "issue:2" --weight 5.0

# List links
uvx agent linker list

# Get context
uvx agent linker context "note:1"

# Rebuild
uvx agent linker rebuild

# Delete
uvx agent linker delete 1
```

**Features:**
- Entity relationships
- Weight-based importance
- Context bundling
- Automatic discovery

---

### Migrate Skill

Database export, import, backup, and restore.

**Commands:**
- `export` - Export to JSON files
- `import` - Import from JSON files
- `backup` - Create database backup
- `restore` - Restore from backup
- `info` - Show database/export info

**Examples:**

```bash
# Export
uvx agent migrate export ./export-dir
uvx agent migrate export ./export-dir --db /path/to/custom.db

# Import
uvx agent migrate import ./export-dir
uvx agent migrate import ./export-dir --no-backup

# Backup
uvx agent migrate backup ./backup.db
uvx agent migrate backup ./backup.db --db /path/to/custom.db

# Restore
uvx agent migrate restore ./backup.db

# Info
uvx agent migrate info ./export-dir
uvx agent migrate info /path/to/database.db
```

**Features:**
- JSON format for versioning
- Automatic backup before import/restore
- Portable data format
- Metadata preservation

---

### Sandbox Skill

Docker-based isolated execution.

**Commands:**
- `run` - Run code in isolated container
- `list` - List sandbox containers
- `logs` - Get logs from sandbox
- `cleanup` - Clean up stopped containers

**Examples:**

```bash
# Run code
uvx agent sandbox run python script.py

# List containers
uvx agent sandbox list

# Get logs
uvx agent sandbox logs container-id

# Cleanup
uvx agent sandbox cleanup
```

**Features:**
- Docker isolation
- Language-agnostic
- Log capture
- Automatic cleanup

---

## Agentic Workflow

### Core Principle

**Start with Context → Plan → Execute → Learn → Iterate**

Each skill has a specific role in the development lifecycle. Use them together for maximum efficiency.

### Phase 1: Context Gathering

**Objective:** Understand the codebase, current state, and requirements.

```bash
# Check planner queue
uvx agent planner list

# Review existing issues
uvx agent issues ready 
uvx agent issues stats

# Scan codebase
uvx agent code-atlas scan .

# Check quality
uvx agent code-atlas rank

# Universal search
uvx agent search "authentication" --limit 10

# Check notes
uvx agent notes search "relevant keyword"
```

### Phase 2: Planning

**Objective:** Break down work into trackable, prioritized issues.

```bash
# Create main issue
uvx agent issues create "Feature: Add authentication" \
  --type feature \
  --priority 2 \
  --labels backend,security

# Create sub-tasks
uvx agent issues create "Design auth schema" --priority 1 --type task
uvx agent issues dependencies add ISSUE-123 ISSUE-456 --type blocks

# Use templates
uvx agent issues template_save "bug_template" --type bug --priority 2

# Sync to planner
uvx agent planner sync
```

### Phase 3: Execution

**Objective:** Work through tasks systematically.

```bash
# Get next task
uvx agent planner next

# Update status
uvx agent issues update ISSUE-123 --status in_progress

# Take notes
uvx agent notes add "Decided to use bcrypt" --tags "security,auth,ISSUE-123"

# Cache results
uvx agent cache set "test_results" "42 passed" --ttl 3600

# Run quality checks
uvx agent code-atlas check
```

### Phase 4: Feedback & Learning

**Objective:** Record outcomes and improve.

```bash
# Record feedback
uvx agent feedback record "implement_auth" \
  --outcome success \
  --notes "Works well, consider rate limiting"

# Update issue
uvx agent issues close ISSUE-123

# Update planner
uvx agent planner update TASK-ID --status completed
```

### Phase 5: Maintenance

**Objective:** Keep knowledge base clean.

```bash
# Find stale issues
uvx agent issues stale --days 30

# Find duplicates
uvx agent issues duplicates --auto-merge

# Compact old issues
uvx agent issues compact --days 90 --priority 3

# Prune cache
uvx agent cache prune

# Run vacuum
uvx agent vacuum run
```

### Best Practices

1. **Always Start with Context** - Run `atlas scan` and `issues stats`
2. **Create Issues First, Code Second** - Break down work
3. **Document Decisions** - Tag notes with issue IDs
4. **Record Feedback Always** - Success or failure
5. **Use Templates** - Save time on repetitive tasks
6. **Maintain Clean State** - Regular cleanup
7. **Leverage Dependencies** - Block dependent issues
8. **Cache Smartly** - Use TTL appropriately
9. **Watch for Feedback** - Use atlas watch during development
10. **Export Regularly** - Backup your knowledge

---

## Development Guide

### Creating Custom Skills

#### 1. Scaffold Structure

```
my-skill/
├── pyproject.toml           # Package metadata
├── README.md                 # Documentation
└── src/
    └── glorious_my_skill/
        ├── __init__.py       # Version
        ├── skill.py          # Commands
        ├── skill.json        # Manifest
        ├── schema.sql        # Database schema
        ├── instructions.md   # LLM internal doc
        └── usage.md          # LLM external doc
```

#### 2. Define Entry Point

`pyproject.toml`:

```toml
[project]
name = "glorious-skill-myskill"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["glorious-agents>=0.1.0"]

[project.entry-points."glorious_agents.skills"]
myskill = "glorious_my_skill.skill:app"
```

#### 3. Implement Skill

`skill.py`:

```python
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

#### 4. Create Manifest

`skill.json`:

```json
{
  "name": "my-skill",
  "version": "0.1.0",
  "description": "My custom skill",
  "requires_db": true,
  "requires": [],
  "internal_doc": "instructions.md",
  "external_doc": "usage.md"
}
```

#### 5. Install and Test

```bash
# Install in editable mode
uv pip install -e ./my-skill

# Verify
uvx agent skills list

# Test
uvx agent myskill hello --name "Developer"
```

### Skill Requirements

**Must Have:**
- `app` - Typer instance
- `init_context(ctx)` - Initialization function
- `skill.json` - Metadata manifest

**Optional:**
- `schema.sql` - Database schema
- `instructions.md` - Internal LLM documentation
- `usage.md` - External LLM documentation

---

## Testing

### Test Structure

```
tests/
├── unit/                     # Unit tests
│   ├── test_config.py
│   ├── test_context.py
│   └── test_isolation.py
└── integration/              # Integration tests
    ├── test_main_cli.py      # Main CLI tests
    ├── test_skills_cli.py    # Skills management
    ├── test_identity_cli.py  # Identity management
    ├── test_cross_skill.py   # Cross-skill integration
    ├── test_error_handling.py # Error handling
    └── skills/               # Skill-specific tests
        ├── test_notes.py
        ├── test_issues.py
        └── test_*.py
```

### Running Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Specific test file
uv run pytest tests/integration/test_main_cli.py -v

# With coverage
uv run pytest --cov=src --cov-report=html

# Parallel execution
uv run pytest -n auto
```

### Test Isolation

All integration tests use the `isolated_env` fixture:

```python
def test_example(isolated_env):
    """Test with complete isolation."""
    result = run_agent_cli(['notes', 'add', 'Test'], isolated_env=isolated_env)
    assert result['success']
```

**Isolation Features:**
- Temporary directory per test
- Separate database
- No workspace contamination
- Automatic cleanup

### Test Statistics

- **Total Test Cases:** 290+
- **Integration Tests:** 200+
- **Unit Tests:** 90+
- **Skills Covered:** All 17 skills
- **CLI Coverage:** 100% of main commands

---

## Planned Improvements

### 1. Major Refactoring Proposal

**Status:** Proposed  
**Target:** v0.6.0+

**Key Changes:**
- SQLAlchemy/SQLModel ORM integration
- Dependency injection pattern
- Repository pattern for data access
- Service layer abstraction
- Protocol-based abstractions
- Elimination of 90%+ code duplication

**Benefits:**
- 60% reduction in boilerplate
- 100% type safety
- Easy testing with DI
- Database flexibility
- Clear architecture

**Migration Plan:**
- Phase 1: Foundation (Weeks 1-2)
- Phase 2: Base Classes (Weeks 2-3)
- Phase 3: Skill Refactoring (Weeks 3-6)
- Phase 4: Cleanup (Week 7)

### 2. Importance System Enhancements

**Current:** Implemented for notes  
**Future:**

- [ ] Time-based auto-downgrade
- [ ] Importance inheritance
- [ ] Cross-skill dashboard
- [ ] Notifications for critical items
- [ ] Analytics on usage patterns
- [ ] Planner integration

### 3. Performance Improvements

- [ ] Connection pooling
- [ ] Query optimization
- [ ] Index analysis
- [ ] Caching strategy
- [ ] Async operations

### 4. New Features

- [ ] GraphQL API support
- [ ] Real-time event streaming
- [ ] Advanced query DSL
- [ ] Plugin marketplace
- [ ] Skill templates via cookiecutter
- [ ] Visual workflow builder

### 5. Documentation

- [ ] Video tutorials
- [ ] Interactive examples
- [ ] API reference docs
- [ ] Migration guides
- [ ] Best practices cookbook

---

## Technical Details

### Database Schema Management

**Automatic Schema Initialization:**

1. Framework discovers skills
2. Loads `schema.sql` for each skill
3. Applies migrations in dependency order
4. Creates indices automatically

**Migration Support:**

```sql
-- migrations/001_add_importance.sql
ALTER TABLE notes ADD COLUMN importance INTEGER DEFAULT 0;
CREATE INDEX idx_notes_importance 
  ON notes(importance DESC, created_at DESC);
```

### Event System Architecture

**Pub/Sub Pattern:**

```python
class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
    
    def publish(self, topic: str, data: dict) -> None:
        """Publish event to all subscribers."""
        for handler in self._subscribers.get(topic, []):
            handler(data)
    
    def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
```

### Skill Loading Sequence

1. **Discovery:**
   - Scan `skills/` directory (local skills)
   - Query entry points (installed skills)

2. **Merge:**
   - Local skills override installed skills
   - Combine metadata

3. **Dependency Resolution:**
   - Topological sort with Kahn's algorithm
   - Detect circular dependencies

4. **Schema Initialization:**
   - Apply `schema.sql` for each skill
   - Run pending migrations

5. **Loading:**
   - Import skill module
   - Get Typer app instance
   - Call `init_context(ctx)`
   - Register commands

### Context Management

**SkillContext:**

```python
class SkillContext:
    def __init__(self, conn, event_bus, config):
        self.conn = conn          # Database connection
        self.event_bus = event_bus  # Event system
        self.config = config       # Configuration
    
    def publish(self, topic: str, data: dict) -> None:
        """Publish event."""
        self.event_bus.publish(topic, data)
    
    def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to events."""
        self.event_bus.subscribe(topic, handler)
```

### Universal Search Implementation

**Search Algorithm:**

1. Query each skill's search provider
2. Collect results with metadata
3. Apply relevance scoring
4. Boost importance-flagged items
5. Sort by score descending
6. Return unified results

**Scoring:**

```python
def calculate_score(result: dict) -> float:
    base_score = result.get('score', 0.5)
    
    # Boost important items
    importance = result.get('metadata', {}).get('importance', 0)
    importance_boost = importance * 0.3
    
    return min(1.0, base_score + importance_boost)
```

### Error Handling Strategy

**Graceful Degradation:**

```python
try:
    result = execute_command(args)
except SkillNotFoundError:
    print("Skill not installed")
    sys.exit(1)
except DatabaseError as e:
    print(f"Database error: {e}")
    # Attempt recovery
    recover_database()
except Exception as e:
    print(f"Unexpected error: {e}")
    log_error(e)
    sys.exit(1)
```

### Security Considerations

**SQL Injection Prevention:**
- Always use parameterized queries
- Never concatenate user input into SQL
- Validate all inputs

```python
# ✅ Safe
cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))

# ❌ Unsafe
cur.execute(f"SELECT * FROM notes WHERE id = {note_id}")
```

**Input Validation:**
- Sanitize file paths
- Validate email addresses
- Escape special characters
- Limit input sizes

### Performance Metrics

**Typical Operations:**

| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| Add note | 5-10 | SQLite insert |
| Search notes | 10-50 | FTS5 query |
| List issues | 20-100 | Depends on count |
| Universal search | 50-200 | Multi-skill query |
| Skill load | 100-500 | One-time startup |

---

## Appendix

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GLORIOUS_DATA_FOLDER` | Agent data directory | `.agent` |
| `DATA_FOLDER` | Alias for above | `.agent` |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| Master DB | `.agent/master.db` | All agents registry |
| Active Agent | `.agent/active_agent` | Current agent code |
| Agent DB | `.agent/agents/<code>/agent.db` | Per-agent database |
| AGENT-TOOLS.md | Workspace root | Generated tool docs |
| AGENTS.md | Workspace root | Agent instructions |

### CLI Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Skill not found |
| 4 | Database error |

---

## Resources

### Links

- **GitHub**: https://github.com/weholt/glorious-agents
- **PyPI**: https://pypi.org/project/glorious-agents/
- **Issues**: https://github.com/weholt/glorious-agents/issues

### Documentation Files

- [`QUICKSTART.md`](QUICKSTART.md) - Quick start guide
- [`RELEASING.md`](RELEASING.md) - Release process
- [`AGENTIC_WORKFLOW.md`](AGENTIC_WORKFLOW.md) - Workflow details
- [`AGENT-TOOLS.md`](AGENT-TOOLS.md) - Generated tool reference
- [`AGENTS.md`](AGENTS.md) - Agent instructions

### Community

- Report bugs via GitHub Issues
- Contribute via Pull Requests
- Follow semantic versioning
- Use pre-commit hooks

---

**Built with ❤️ for AI agents and their humans**

*Last Updated: 2025-11-18*
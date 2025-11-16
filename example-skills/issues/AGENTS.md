# dotwork Development Guide

## General instructions

- **IMPORTANT** Do not create summaries or explainations.
- **NO FUCKING SUMMARY DOCUMENTS**
- Focus on writing code, not talking.
- **NEVER** use `python -c` commands with multi-line code in terminal - it hangs the terminal
- Use separate Python files or simple single-line commands only
- **NEVER** print code to the terminal that should go into a file. Write directly to file. It hangs the terminal and stops the process.
- There is **NO** time constraints - fuck estimates, just finish your tasks
- There is **NO** legacy system to consider, no need for migration or fallback to legacy code while implementing
- **NEVER EVER** claim a task is "finished" or "complete" when it's NOT fully done - verify ALL requirements are met before claiming completion

## Development Workflows

### Essential Commands (ALWAYS use `uv`)

```bash
uv sync                    # Install dependencies
uv run python build.py    # Full quality pipeline (format, lint, type-check, test)
uv run python build.py --verbose  # Auto-fix issues with detailed output
uv run dotwork server      # Start MCP server locally
uv run pytest tests/      # Run tests only
```

### Docker Development

```bash
docker-compose up -d       # Start containerized server
# Exposes ports 8000 (MCP) and 8001 (web interface)
```

## Key Patterns & Conventions

### Environment-Aware Configuration

- Server automatically detects Docker vs local environment
- Uses different RAG implementations based on available dependencies
- Configuration via `.env` file with sensible Docker defaults

### Quality Standards (Enforced by build.py)

- **70%+ test coverage** required
- **5-second test timeout** for all tests
- **Ruff** for linting + formatting (replaces black/isort)
- **MyPy** type checking with relaxed config for BeautifulSoup complexity
- Security checks via `ruff --select S`

## File Organization Logic

- **`dotwork/`** - Main package
- **`tests/`** - All tests with strict timeout enforcement
- **`.env`** - Environment config (copied to Docker if exists)

## Common Pitfalls

- Always use `uv run` prefix for Python commands (never direct python)
- Tests must complete within 5 seconds (use minimal fixtures)
- Docker uses different defaults (HOST=0.0.0.0 vs localhost)

## Mandatory instructions

- Failure to follow these particular rules will result in **immidiate** termination.
- You are not allowed to write non-code related files, like summaries and explanation in markdown files, testscripts etc into the project structure other places than the `.work/agent` folder.
- Follow instructions given in specifications, taskslists and other reference material provided.
- Do not get creative outside the instructions given.
- Do not create nice-to-have fields in models not mentioned in the spec
- Do not create nice-to-have commands in clis or endpoints in APIs not mentioned in the spec
- Do not adjust the test coverage threshold.
- Finish a long coding session with a list of remaining work/issues, as a current status

## Development guide

- Run `uv run build.py` after each substantial change
    - Iterate until all checks pass
    - Write tests until coverage is 70%+
- Use `uv run build.py` to auto-fix formatting/linting issues
- Add tests for new features in `tests/`
- Follow existing code style and patterns
- **PORTS** should be configurable from `.env`.
    - Provide good defaults, but never hardcode values
- **MANDATORY** **IMPORTS** ALWAYS at the top of the file, NEVER inline
    - Use conditional imports at module level if needed (try/except at top)
    - Never use inline imports inside functions or methods


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
## Tools

- always use Context7 mcp tool for up to date documentation
- always use Sequential Thinking mcp for help to break tasks into atomic tasks
- always use Memory mcp to keep your context organized
- always use Playwright to create web ui integration tests

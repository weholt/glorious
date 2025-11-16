# issue-tracker

Git-backed issue tracking with hash IDs, hierarchical relationships, and MCP server.

## Features (Beads Feature Parity)

- **Hash-based collision-resistant IDs** (bd-a1b2 format, 4/5/6 char progressive scaling)
- **Hierarchical child IDs** (bd-abc.1, bd-abc.2, up to 3 levels deep)
- **Git-backed JSONL storage** (one file per issue)
- **Auto-sync with 5-second debounce**
- **Background daemon** for RPC and sync operations
- **Optional Agent Mail** for <100ms real-time coordination
- **MCP server** for Claude Desktop integration
- **4 dependency types**: blocks, related, parent-child, discovered-from
- **Label system** with AND/OR filtering
- **Advanced filtering**: text search, date ranges, priority ranges
- **Duplicate detection and merging**
- **Compaction/memory decay** for old closed issues
- **Web UI** for monitoring

## Installation

```bash
# Base installation (SQLite)
pip install issue-tracker

# With Agent Mail support
pip install issue-tracker[agentmail]

# With PostgreSQL support
pip install issue-tracker[postgres]
```

## Usage

### CLI

```bash
# Create issue
issue-tracker create "Fix login bug" -t bug -p 1 -l auth,backend

# List issues
issue-tracker list --status open --label urgent

# Add dependencies
issue-tracker blocks bd-a1b2 bd-def

# Start daemon
issue-tracker daemon start
```

### MCP Server (Claude Desktop)

```json
{
  "mcpServers": {
    "beads": {
      "command": "issue-tracker",
      "args": ["mcp-server"]
    }
  }
}
```

### As Library

```python
from issue_tracker import IssueService, DependencyType

service = IssueService(jsonl_repo, git_sync)

issue = service.create_issue(
    title="Fix login bug",
    priority=IssuePriority.HIGH,
    issue_type=IssueType.BUG,
    labels=["urgent", "security"],
)
```

## Usage as Glorious Skill

Issue-tracker can be used as a skill in the glorious-agents framework:

```bash
# Install both packages
pip install glorious-agents issue-tracker

# Use via agent command
agent issues create "My issue"
agent issues list
agent issues dependencies add ISS-ID1 ISS-ID2
```

Skills are automatically discovered via Python entry points. The CLI remains available as both `issues` and `agent issues`.

## Development

```bash
uv sync
uv run python scripts/build.py
```

## License

MIT

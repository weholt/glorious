# Issues Skill

## Purpose
Git-backed issue tracking with hierarchical relationships, hash-based IDs, and dependency graphs.

## Commands

### Creation
- `agent issues create <title>` - Create new issue
  - `--description TEXT` - Issue description
  - `--type TYPE` - Issue type (bug, feature, task, epic)
  - `--priority PRIORITY` - Priority (low, medium, high, critical)
  - `--assignee NAME` - Assign to person
  - `--labels LABEL` - Add labels (comma-separated)

### Management
- `agent issues list` - List issues
  - `--status STATUS` - Filter by status
  - `--type TYPE` - Filter by type
  - `--assignee NAME` - Filter by assignee
  - `--format FORMAT` - Output format (table, json, simple)
- `agent issues show <id>` - Show issue details
- `agent issues update <id>` - Update issue
  - `--title TEXT` - New title
  - `--description TEXT` - New description
  - `--status STATUS` - New status (open, in-progress, blocked, done, cancelled)
  - `--priority PRIORITY` - New priority
- `agent issues delete <id>` - Delete issue

### Relationships
- `agent issues dependencies add <issue-id> <dependency-id>` - Add dependency
- `agent issues dependencies remove <issue-id> <dependency-id>` - Remove dependency
- `agent issues dependencies list <issue-id>` - List dependencies
- `agent issues dependencies graph` - Show dependency graph

### Epics
- `agent issues epics create <title>` - Create epic
- `agent issues epics list` - List epics
- `agent issues epics add-issue <epic-id> <issue-id>` - Add issue to epic
- `agent issues epics remove-issue <epic-id> <issue-id>` - Remove issue from epic

### Labels
- `agent issues labels create <name>` - Create label
- `agent issues labels list` - List labels
- `agent issues labels add <issue-id> <label>` - Add label to issue
- `agent issues labels remove <issue-id> <label>` - Remove label from issue

### Comments
- `agent issues comments add <issue-id> <text>` - Add comment
- `agent issues comments list <issue-id>` - List comments
- `agent issues comments update <comment-id> <text>` - Update comment
- `agent issues comments delete <comment-id>` - Delete comment

### Analysis
- `agent issues stats` - Show statistics
- `agent issues export` - Export issues
  - `--format FORMAT` - Export format (json, markdown)
  - `--output FILE` - Output file path

### Instructions
- `agent issues instructions show` - Show issue instructions/templates
- `agent issues instructions update <id> <text>` - Update instructions

## Typical Workflow

1. **Create issue:** `agent issues create "Fix login bug" --description "Users can't login" --type bug`
2. **Create epic:** `agent issues epics create "Authentication improvements"`
3. **Add to epic:** `agent issues epics add-issue EPIC-ID ISS-ID`
4. **Update status:** `agent issues update ISS-ID --status in-progress`
5. **Add comment:** `agent issues comments add ISS-ID "Working on this"`
6. **Check dependencies:** `agent issues dependencies list ISS-ID`
7. **View graph:** `agent issues dependencies graph`
8. **Complete:** `agent issues update ISS-ID --status done`

## Storage
- Uses SQLite database at `.issues/issues.db` (configurable)
- Git integration for version control
- Hash-based IDs (ISS-XXXX format)

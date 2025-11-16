# Docs Skill

Structured documentation management for Glorious Agents.

## Features

- **Document Storage**: Store long-form documentation in database
- **Epic Linking**: Link documents to epics for organization
- **Version History**: Full version tracking with rollback capability
- **Full-Text Search**: Fast search across all documents
- **Markdown Rendering**: Rich terminal display of markdown content
- **Export**: Export documents to .md files when needed

## Installation

```bash
uv pip install -e example-skills/docs
```

## Usage

### Create Documentation

```bash
# Create from content
uv run agent docs create "Security Plan" --content "# Security\n..."

# Create from file
uv run agent docs create "Integration Test Plan" \
  --content-file docs/INTEGRATION_TEST_PLAN.md \
  --epic epic-testing

# Custom ID
uv run agent docs create "Database Plan" \
  --content-file docs/DATABASE_CONSOLIDATION.md \
  --epic epic-database \
  --id doc-database
```

### View Documents

```bash
# View current version
uv run agent docs get doc-security

# View specific version
uv run agent docs get doc-security --version 2

# Raw output (no markdown rendering)
uv run agent docs get doc-security --no-render

# JSON output
uv run agent docs get doc-security --json
```

### Update Documents

```bash
# Update content
uv run agent docs update doc-security --content "New content..."

# Update from file
uv run agent docs update doc-security --content-file SECURITY.md

# Update title or epic
uv run agent docs update doc-security --title "New Title"
uv run agent docs update doc-security --epic epic-security-v2
```

### List and Search

```bash
# List all documents
uv run agent docs list

# List by epic
uv run agent docs list --epic epic-testing

# Search documents
uv run agent docs search "permission system"

# Universal search (across all skills)
uv run agent search "security plan"
```

### Version History

```bash
# List versions
uv run agent docs versions doc-security

# View specific version
uv run agent docs get doc-security --version 2
```

### Export

```bash
# Export to file
uv run agent docs export doc-security --output SECURITY.md

# Export to stdout
uv run agent docs export doc-security

# Export specific version
uv run agent docs export doc-security --version 1 --output SECURITY.v1.md
```

## Integration

### With Epics

Documents are linked to top-level epics:

```
doc-testing-plan → epic-testing
  └── epic-testing-infrastructure
      └── issue-5cc5e4
  └── epic-testing-workflows
      └── issue-5f8ca7
```

### With Universal Search

Documents are automatically searchable via `uv run agent search`:

```bash
# Searches across issues, notes, docs, etc.
uv run agent search "isolation"
```

## Benefits

✅ Single source of truth in database  
✅ Searchable via universal search  
✅ Linked to epics and issues  
✅ Version history with rollback  
✅ Export to .md when needed  
✅ No scattered .md files  
✅ Integrated with workflow  

## Schema

Documents are stored in `docs_documents` table with full-text search support.
Version history is maintained in `docs_versions` table.

See `schema.sql` for details.

# Database Consolidation Plan

**Issue**: [issue-bbca31](../issues/issue-bbca31.md)  
**Status**: Planning  
**Priority**: High

## Overview

Consolidate 3 separate SQLite databases into a single unified database with proper configuration management and .env support.

## Current State

### Existing Databases

1. **`.agent/agents/default/agent.db`** (38 rows, 9 tables)
   - `notes` - Knowledge capture
   - `notes_fts*` - Full-text search indexes
   - `_skill_schemas` - Schema version tracking
   - `issues` - Test data (legacy)
   - `testskill_data` - Test data

2. **`.issues/issues.db`** (605 rows, 12 tables)
   - `issues` - Issue tracking (112 issues)
   - `labels` - Issue labels
   - `issue_labels` - Many-to-many relationship
   - `comments` - Issue comments
   - `dependencies` - Issue dependencies (11)
   - `epics` - Epic tracking
   - `issues_fts*` - Full-text search indexes

3. **`.agent/master.db`** (1 row, 1 table)
   - `agents` - Agent identity registry

### Problems

- **Scattered Data**: 3 different locations, inconsistent paths
- **Complex Backup**: Need 3 separate export operations
- **No Configuration**: Hardcoded paths, no environment variables
- **Difficult Migration**: Can't easily move or share installations
- **Transaction Isolation**: Can't use atomic transactions across skills
- **Connection Overhead**: Multiple connections, file handles

## Proposed Solution

### Single Unified Database

**Location**: `~/.glorious/glorious-agents.db` (configurable via .env)

**Structure**: One database with prefixed tables

```
glorious-agents.db
├── notes_*           (from agent.db)
├── issues_*          (from issues.db)
├── agents_*          (from master.db)
├── cache_*           (future)
├── feedback_*        (future)
├── prompts_*         (future)
├── automations_*     (future)
├── planner_*         (future)
├── temporal_*        (future)
└── _skill_schemas    (unified)
```

### Environment Configuration

**`.env` file** (optional):
```bash
# Data directory location
GLORIOUS_DATA_DIR=~/.glorious

# Database path (overrides DATA_DIR/glorious-agents.db)
GLORIOUS_DB_PATH=/custom/path/glorious-agents.db

# Backward compatibility
GLORIOUS_LEGACY_MODE=false  # Auto-detect and migrate legacy DBs
```

**Fallback behavior**:
1. Check `GLORIOUS_DB_PATH` env var
2. Use `GLORIOUS_DATA_DIR/glorious-agents.db`
3. Default to `~/.glorious/glorious-agents.db`
4. If not exists, check legacy locations for migration

## Implementation Plan

### Task 1: Add .env Support [issue-5c841c]

**Priority**: High (foundation for all other tasks)

**Changes**:
- Add `python-dotenv` to dependencies (already in deps)
- Update `src/glorious_agents/config.py`:
  ```python
  from dotenv import load_dotenv
  
  class Config:
      def __init__(self):
          load_dotenv()  # Load .env file
          
          # Data directory (user can override)
          self.DATA_DIR = Path(os.getenv("GLORIOUS_DATA_DIR", 
                                         str(Path.home() / ".glorious")))
          
          # Database path (user can override)
          default_db = self.DATA_DIR / "glorious-agents.db"
          self.DB_PATH = Path(os.getenv("GLORIOUS_DB_PATH", str(default_db)))
          
          # Legacy mode
          self.LEGACY_MODE = os.getenv("GLORIOUS_LEGACY_MODE", "auto")
  ```

**Validation**:
- Test with .env file present
- Test with environment variables
- Test with defaults (no .env)
- Test path expansion (~/.glorious)

### Task 2: Design Unified Schema [issue-a798dd]

**Priority**: High (blocks migration script)

**Table Naming Convention**:
- Prefix: `<skill_name>_<table_name>`
- Example: `issues_issues`, `issues_labels`, `notes_notes`
- Special: `_skill_schemas` (no prefix, framework level)

**Schema Design**:

```sql
-- Framework tables (no prefix)
CREATE TABLE _skill_schemas (
    skill_name TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notes skill
CREATE TABLE notes_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE notes_fts USING fts5(
    content,
    tags,
    content=notes_notes,
    content_rowid=id
);

-- Issues skill
CREATE TABLE issues_issues (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE TABLE issues_labels (
    name TEXT PRIMARY KEY
);

CREATE TABLE issues_issue_labels (
    issue_id TEXT NOT NULL,
    label_name TEXT NOT NULL,
    PRIMARY KEY (issue_id, label_name),
    FOREIGN KEY (issue_id) REFERENCES issues_issues(id),
    FOREIGN KEY (label_name) REFERENCES issues_labels(name)
);

CREATE TABLE issues_dependencies (
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    type TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id, type),
    FOREIGN KEY (from_id) REFERENCES issues_issues(id),
    FOREIGN KEY (to_id) REFERENCES issues_issues(id)
);

-- Agent registry
CREATE TABLE agents_agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Future skills (placeholders)
-- cache_entries, feedback_actions, prompts_templates, etc.
```

**Documentation**:
- Create `docs/DATABASE_SCHEMA.md` with complete schema
- Document prefix conventions
- Add migration notes

### Task 3: Create Migration Script [issue-9b051b]

**Priority**: Medium (depends on schema design)

**Script**: `scripts/migrate_databases.py`

```python
"""Migrate from 3 databases to unified database."""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def backup_databases(src_paths: list[Path], backup_dir: Path):
    """Backup existing databases before migration."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for src in src_paths:
        if src.exists():
            dest = backup_dir / f"{src.stem}_{timestamp}.db"
            shutil.copy2(src, dest)
            print(f"Backed up {src} -> {dest}")

def migrate_table(src_conn, dest_conn, src_table, dest_table):
    """Migrate table with optional rename."""
    cursor = src_conn.execute(f"SELECT * FROM {src_table}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    if not rows:
        return 0
    
    placeholders = ",".join(["?"] * len(columns))
    insert_sql = f"INSERT INTO {dest_table} ({','.join(columns)}) VALUES ({placeholders})"
    
    dest_conn.executemany(insert_sql, rows)
    return len(rows)

def main():
    # Detect legacy databases
    agent_db = Path(".agent/agents/default/agent.db")
    issues_db = Path(".issues/issues.db")
    master_db = Path(".agent/master.db")
    
    # New unified database
    unified_db = Path("~/.glorious/glorious-agents.db").expanduser()
    unified_db.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup first
    backup_dir = Path(".glorious-backup")
    backup_databases([agent_db, issues_db, master_db], backup_dir)
    
    # Create unified database
    dest_conn = sqlite3.connect(unified_db)
    
    # Apply unified schema
    with open("docs/unified_schema.sql") as f:
        dest_conn.executescript(f.read())
    
    # Migrate data
    tables_migrated = {}
    
    # From agent.db
    if agent_db.exists():
        src = sqlite3.connect(agent_db)
        tables_migrated["notes"] = migrate_table(src, dest_conn, "notes", "notes_notes")
        # Migrate FTS indexes...
        src.close()
    
    # From issues.db
    if issues_db.exists():
        src = sqlite3.connect(issues_db)
        tables_migrated["issues"] = migrate_table(src, dest_conn, "issues", "issues_issues")
        tables_migrated["labels"] = migrate_table(src, dest_conn, "labels", "issues_labels")
        # ... more tables
        src.close()
    
    # From master.db
    if master_db.exists():
        src = sqlite3.connect(master_db)
        tables_migrated["agents"] = migrate_table(src, dest_conn, "agents", "agents_agents")
        src.close()
    
    dest_conn.commit()
    dest_conn.close()
    
    print("\n✅ Migration complete!")
    print(f"Unified database: {unified_db}")
    print(f"Backups: {backup_dir}")
    print(f"Tables migrated: {tables_migrated}")

if __name__ == "__main__":
    main()
```

**Features**:
- Auto-detect legacy databases
- Create backups before migration
- Apply unified schema
- Migrate all data with table renaming
- Report migration statistics
- Rollback capability

**Testing**:
- Test with all 3 databases present
- Test with only some databases
- Test with empty databases
- Verify data integrity after migration
- Test rollback procedure

### Task 4: Update Skills [issue-57e1e5]

**Priority**: Medium (depends on migration script)

**Changes per skill**:

1. Update schema files to use prefixes
2. Update SQL queries to use new table names
3. Update skill initialization
4. Test skill functionality

**Example** (issues skill):
```python
# Before
conn.execute("SELECT * FROM issues WHERE status = ?", (status,))

# After
conn.execute("SELECT * FROM issues_issues WHERE status = ?", (status,))
```

**Skills to update**:
- notes (notes → notes_notes, notes_fts → notes_fts)
- issues (issues → issues_issues, etc.)
- cache (new prefix: cache_)
- feedback (new prefix: feedback_)
- prompts (new prefix: prompts_)
- automations (new prefix: automations_)
- All other skills with database access

### Task 5: Backward Compatibility [issue-5a69ac]

**Priority**: Low (polish after core functionality)

**Auto-Migration**:
```python
def check_legacy_databases() -> bool:
    """Check if legacy databases exist."""
    legacy_paths = [
        Path(".agent/agents/default/agent.db"),
        Path(".issues/issues.db"),
        Path(".agent/master.db")
    ]
    return any(p.exists() for p in legacy_paths)

def auto_migrate_if_needed():
    """Auto-migrate legacy databases on first run."""
    if not config.DB_PATH.exists() and check_legacy_databases():
        print("🔄 Detected legacy databases. Migrating to unified database...")
        from scripts.migrate_databases import main
        main()
        print("✅ Migration complete!")
```

**User notices**:
- Detect legacy databases on startup
- Show migration prompt (with skip option)
- Log migration in notes
- Update documentation

## Migration Rollback

If migration fails or issues occur:

```bash
# Stop agent
# Restore from backup
cp .glorious-backup/agent_db_TIMESTAMP.db .agent/agents/default/agent.db
cp .glorious-backup/issues_db_TIMESTAMP.db .issues/issues.db
cp .glorious-backup/master_db_TIMESTAMP.db .agent/master.db

# Remove unified database
rm ~/.glorious/glorious-agents.db
```

## Benefits

### For Users
- ✅ Single backup file
- ✅ Configurable data location
- ✅ Easier to migrate between machines
- ✅ .env support for custom setups

### For Developers
- ✅ Single connection pool
- ✅ Atomic transactions across skills
- ✅ Simpler database management
- ✅ Consistent schema patterns

### For Operations
- ✅ One export/import operation
- ✅ Single file to backup
- ✅ Easier to inspect/debug
- ✅ Better SQLite performance

## Timeline

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| .env Support | High | 2h | None |
| Schema Design | High | 3h | .env support |
| Migration Script | Medium | 4h | Schema design |
| Update Skills | Medium | 6h | Migration script |
| Backward Compat | Low | 2h | Update skills |
| **Total** | | **17h** | Sequential |

## Testing Strategy

1. **Unit Tests**: Test each migration function
2. **Integration Tests**: Full migration with sample data
3. **Backward Compat**: Test auto-migration on fresh install
4. **Manual Testing**: Verify all skills work after migration
5. **Rollback Test**: Verify backup/restore works

## Success Criteria

- [ ] All 3 databases merged into one
- [ ] .env configuration working
- [ ] All skills functioning with new schema
- [ ] Auto-migration for legacy installations
- [ ] Complete backup before migration
- [ ] Documentation updated
- [ ] Tests passing (unit + integration)

## Related Issues

- [issue-bbca31](../issues/issue-bbca31.md) - Main tracking issue
- [issue-5c841c](../issues/issue-5c841c.md) - .env support
- [issue-a798dd](../issues/issue-a798dd.md) - Schema design
- [issue-9b051b](../issues/issue-9b051b.md) - Migration script
- [issue-57e1e5](../issues/issue-57e1e5.md) - Update skills
- [issue-5a69ac](../issues/issue-5a69ac.md) - Backward compatibility

## References

- [SQLite Best Practices](https://sqlite.org/bestpractice.html)
- [Python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Unified schema reference

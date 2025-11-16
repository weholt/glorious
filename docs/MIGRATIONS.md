# Database Migrations

## Overview

The Glorious Agents framework includes a migration system for versioned database schema changes. This allows skills to evolve their schemas safely over time.

## How It Works

### Migration Files

Migrations are SQL files stored in a `migrations/` directory within your skill. Files must follow the naming convention:

```
{version}_{description}.sql
```

Examples:
- `001_initial_schema.sql`
- `002_add_user_index.sql`
- `003_add_timestamps.sql`

### Automatic Migration

When a skill is loaded, the system automatically:
1. Checks for a `migrations/` directory
2. Compares current database version with available migrations
3. Applies pending migrations in order
4. Records applied migrations with checksums

### Migration Tracking

The system uses a `_migrations` table to track:
- Which skill the migration belongs to
- Version number
- Migration filename
- SHA256 checksum (prevents modification of applied migrations)
- Timestamp when applied

## Creating Migrations

### Option 1: Using CLI (Recommended)

```bash
# Create a new migration file
agent skills migrate create my_skill "add user preferences"

# This creates: migrations/001_add_user_preferences.sql
```

The file will contain a template:

```sql
-- Migration: add user preferences
-- Skill: my_skill
-- Version: 1
-- Created: 2025-11-16T00:00:00

-- Add your migration SQL here
ALTER TABLE users ADD COLUMN preferences TEXT;
CREATE INDEX idx_user_prefs ON users(preferences);
```

### Option 2: Manual Creation

Create `migrations/` directory in your skill and add numbered SQL files:

```
my-skill/
├── src/
│   └── my_skill/
│       ├── migrations/
│       │   ├── 001_initial_schema.sql
│       │   └── 002_add_columns.sql
│       ├── skill.py
│       └── skill.json
```

## Running Migrations

### Automatic (Default)

Migrations run automatically when skills are loaded. No action needed!

### Manual

```bash
# Run pending migrations for a skill
agent skills migrate run my_skill --dir ./path/to/migrations

# Check migration status
agent skills migrate status

# View migration history
agent skills migrate history
agent skills migrate history --skill my_skill
```

## Migration Best Practices

### 1. Idempotent Operations

Use `IF NOT EXISTS` and similar clauses:

```sql
-- Good
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY);
ALTER TABLE users ADD COLUMN email TEXT;  -- OK if column doesn't exist

-- Risky
CREATE TABLE users (id INTEGER PRIMARY KEY);  -- Fails if exists
```

### 2. Backward Compatible Changes

Add columns with defaults:

```sql
ALTER TABLE users ADD COLUMN active INTEGER DEFAULT 1;
```

### 3. Data Migrations

Include data transformations in the same migration:

```sql
-- Add column
ALTER TABLE orders ADD COLUMN status TEXT;

-- Populate existing rows
UPDATE orders SET status = 'completed' WHERE completed_at IS NOT NULL;
UPDATE orders SET status = 'pending' WHERE completed_at IS NULL;
```

### 4. Index Creation

Create indexes for new query patterns:

```sql
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
```

## Example: Converting Legacy Schema

If you have an existing skill with a `schema.sql` file:

### Step 1: Create migrations directory

```bash
mkdir -p my-skill/src/my_skill/migrations
```

### Step 2: Move schema to migration

```bash
mv my-skill/src/my_skill/schema.sql \
   my-skill/src/my_skill/migrations/001_initial_schema.sql
```

### Step 3: Add header to migration

```sql
-- Migration: Initial schema
-- Skill: my_skill
-- Version: 1
-- Created: 2025-11-16

-- (existing schema SQL)
CREATE TABLE IF NOT EXISTS my_table (...);
```

### Step 4: Test

The migration will run automatically on next skill load.

## Monitoring Migrations

### Check Status

```bash
# View all skills with migrations
agent skills migrate status

# Output:
# ┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
# ┃ Skill   ┃ Version ┃ Migrations ┃
# ┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
# │ issues  │ 3       │ 3          │
# │ notes   │ 2       │ 2          │
# └─────────┴─────────┴────────────┘
```

### View History

```bash
# Show all migration history
agent skills migrate history

# Show history for specific skill
agent skills migrate history --skill issues --limit 10
```

## Advanced: Rollback

**Warning**: Rollback only removes migration records, it does NOT undo SQL changes.

To revert schema changes, create a new migration:

```sql
-- Migration: Rollback user preferences
-- Skill: my_skill  
-- Version: 4

-- Undo changes from version 3
ALTER TABLE users DROP COLUMN preferences;
DROP INDEX IF EXISTS idx_user_prefs;
```

## Troubleshooting

### Migration Checksum Mismatch

**Error**: `Migration checksum mismatch! Do not modify applied migrations.`

**Cause**: You edited a migration file that was already applied.

**Solution**: 
1. Revert the file to original content, OR
2. Create a new migration with the desired changes

### Migration Failed

If a migration fails:
1. Check the error message
2. Fix the SQL in the migration file
3. The migration will retry on next load

### Starting Fresh

To reset migrations (development only):

```bash
# Delete migration records (does NOT drop tables!)
sqlite3 ~/.glorious/agents/default/agent.db \
  "DELETE FROM _migrations WHERE skill_name = 'my_skill';"

# Or drop all tables and rerun
sqlite3 ~/.glorious/agents/default/agent.db \
  "DROP TABLE my_table; DELETE FROM _migrations WHERE skill_name = 'my_skill';"
```

## Integration with Skills

The migration system integrates automatically with skill loading:

```python
# db.py automatically detects migrations/
def init_skill_schema(skill_name: str, schema_path: Path) -> None:
    migrations_dir = schema_path.parent / "migrations"
    if migrations_dir.exists():
        # Use migration system
        run_migrations(skill_name, migrations_dir)
    else:
        # Legacy: execute schema.sql directly
        # ...
```

No code changes needed in your skill!

## Example Workflow

### Adding a New Feature

1. **Create migration**:
```bash
cd my-skill
agent skills migrate create my_skill "add caching support"
```

2. **Edit migration file**:
```sql
-- migrations/003_add_caching_support.sql
CREATE TABLE IF NOT EXISTS cache_entries (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at);
```

3. **Test locally**:
```bash
# Reload skill to apply migration
agent skills reload my_skill

# Verify
agent skills migrate status --skill my_skill
```

4. **Commit**:
```bash
git add migrations/003_add_caching_support.sql
git commit -m "Add caching support to my_skill"
```

5. **Deploy**: Migration runs automatically on other systems when skill loads.

## Summary

- ✅ Automatic migration execution
- ✅ Version tracking with checksums
- ✅ Idempotent operations supported
- ✅ CLI tools for management
- ✅ Backward compatible with legacy schemas
- ✅ No skill code changes required

Migrations make schema evolution safe and trackable!

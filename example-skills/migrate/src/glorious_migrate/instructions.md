# Migrate Skill - Internal Documentation

## Purpose

The migrate skill provides universal export/import capabilities for database portability, backups, and migrations.

## Features

- **Full Export/Import**: Export/import entire database to/from JSON
- **Backup/Restore**: Simple database backup and restore
- **Schema Preservation**: Maintains table schemas during migration
- **Metadata Tracking**: Records export timestamps and statistics
- **Safe Operations**: Automatic backups before destructive operations

## Architecture

### Export Process
1. Connect to database
2. Extract table schemas
3. Export each table to JSON file
4. Create metadata file with statistics

### Import Process
1. Optionally backup existing database
2. Create schema from schema.sql
3. Import data from JSON files (INSERT OR REPLACE)
4. Commit changes

## File Structure

Exports create directory with:
- `schema.sql` - Table definitions
- `{table}.json` - Data for each table
- `metadata.json` - Export information

## Usage in Code

```python
from glorious_migrate.skill import export_database, import_database
from pathlib import Path

# Export
stats = export_database(
    Path("/path/to/db.db"),
    Path("/path/to/export/")
)

# Import
stats = import_database(
    Path("/path/to/db.db"),
    Path("/path/to/import/")
)
```

## Safety Features

- Automatic backups before imports
- INSERT OR REPLACE prevents conflicts
- Schema creation is idempotent
- Metadata tracking for verification

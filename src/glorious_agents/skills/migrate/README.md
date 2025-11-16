# Glorious Migrate Skill

Universal export/import system for database portability, backups, and migrations.

## Features

- **JSON Export/Import**: Human-readable data format
- **Full Database Migration**: Export and import complete databases
- **Backup/Restore**: Simple database backup operations
- **Schema Preservation**: Maintains table structures
- **Safe Operations**: Automatic backups before destructive changes

## Installation

```bash
cd example-skills/migrate
uv pip install -e .
```

## Quick Start

```bash
# Export database
agent migrate export ./my-export

# Import database
agent migrate import ./my-export

# Create backup
agent migrate backup ./backup.db

# Restore from backup
agent migrate restore ./backup.db

# Show info
agent migrate info ./my-export
agent migrate info ./database.db
```

## Use Cases

- **Backups**: Regular database backups
- **Migration**: Move data between environments
- **Version Control**: Export to JSON for git tracking
- **Sharing**: Export and share specific data
- **Debugging**: Inspect data in human-readable format

## Export Format

Exports create:
- `schema.sql` - Table definitions
- `{table}.json` - Data per table
- `metadata.json` - Export statistics

All in human-readable, editable JSON.

## Requirements

- Python 3.11+
- SQLite3 (built-in)

## License

MIT

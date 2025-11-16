# Migrate Skill Usage

Export, import, backup and restore databases for portability and safety.

## Commands

### export
Export database to JSON files:
```bash
agent migrate export ./export-dir
agent migrate export ./export-dir --db /path/to/custom.db
```

Creates directory with:
- `schema.sql` - Table schemas
- `{table}.json` - Table data
- `metadata.json` - Export info

### import
Import database from JSON files:
```bash
agent migrate import ./export-dir
agent migrate import ./export-dir --db /path/to/custom.db
agent migrate import ./export-dir --no-backup  # Skip backup
```

Automatically backs up existing database before import.

### backup
Create database backup:
```bash
agent migrate backup ./backup.db
agent migrate backup ./backup.db --db /path/to/custom.db
```

### restore
Restore from backup:
```bash
agent migrate restore ./backup.db
agent migrate restore ./backup.db --db /path/to/custom.db
```

Automatically backs up current database before restore.

### info
Show database or export information:
```bash
agent migrate info ./export-dir
agent migrate info /path/to/database.db
```

## Use Cases

### Regular Backups
```bash
# Daily backup
agent migrate backup ./backups/daily-$(date +%Y%m%d).db
```

### Migration Between Environments
```bash
# Export from dev
agent migrate export ./migration --db ~/.glorious/dev.db

# Import to prod
agent migrate import ./migration --db ~/.glorious/prod.db
```

### Data Sharing
```bash
# Export specific tables
agent migrate export ./shared-data

# Edit JSON files as needed

# Import elsewhere
agent migrate import ./shared-data
```

## JSON Format

Each table is exported as:
```json
[
  {"id": 1, "name": "value", ...},
  {"id": 2, "name": "value", ...}
]
```

Easy to edit, version control, and inspect.

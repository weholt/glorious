# Code-Atlas Skill

## Purpose
Analyze Python codebase structure, metrics, and dependencies.

## Commands

### `agent code-atlas scan <path>`
Scan a Python codebase and generate structure index.
- `--output FILE` - Output file path (default: code_index.json)
- `--incremental` - Use incremental caching (skip unchanged files)
- `--deep` - Enable deep analysis (call graphs, type coverage)
- `--verbose` - Show detailed progress

### `agent code-atlas watch <path>`
Watch for file changes and auto-update index.
- `--daemon` - Run in background
- `--interval SECONDS` - Check interval (default: 2)

### `agent code-atlas watch-status`
Show status of watch daemon.

### `agent code-atlas stop-watch <path>`
Stop watch daemon for a path.

### `agent code-atlas agent <path>`
Generate agent-friendly summary of codebase.
- `--verbose` - Include detailed analysis

### `agent code-atlas check <path>`
Check code quality metrics.
- `--min-score FLOAT` - Minimum quality score (default: 7.0)

### `agent code-atlas rank <path>`
Rank files by complexity and maintainability.

## Typical Usage

1. **First scan:** `agent code-atlas scan .`
2. **Agent analysis:** `agent code-atlas agent .`
3. **Quality check:** `agent code-atlas check . --min-score 7.0`
4. **Rank files:** `agent code-atlas rank .`
5. **Auto-update:** `agent code-atlas watch . --daemon`

## Output
- Generates `code_index.json` with structure data
- Can output Rich tables, JSON, or tree views
- Provides complexity and maintainability metrics

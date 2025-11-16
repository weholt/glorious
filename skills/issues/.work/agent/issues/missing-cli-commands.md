# Missing CLI Commands - Implementation Issues

**Created**: 2025-11-12  
**Priority**: HIGH  
**Status**: READY TO IMPLEMENT

## Overview

11 major commands missing from CLI implementation according to reference documentation:
1. cleanup (delete closed issues)
2. duplicates (find duplicate issues)
3. merge (merge duplicate issues)
4. compact (memory decay/compaction)
5. rename-prefix (change issue prefix)
6. edit (edit in $EDITOR - HUMAN ONLY)
7. export (export to JSONL)
8. import (import from JSONL)
9. init (initialize issue tracker)
10. cycles (dep subcommand - detect cycles)
11. --notes-contains filter (list command)

---

## Issue 1: Implement `cleanup` command

**Priority**: HIGH  
**Estimate**: 90 minutes  
**Files**: 
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/issue_service.py` (add cleanup method)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues cleanup --force --json                                   # Delete ALL closed issues
issues cleanup --older-than 30 --force --json                   # Delete closed >30 days ago
issues cleanup --dry-run --json                                 # Preview what would be deleted
issues cleanup --older-than 90 --cascade --force --json         # Delete old + dependents
```

**Features**:
- Delete closed issues
- Filter by age (--older-than N days)
- Dry-run mode (preview)
- Cascade mode (delete dependents)
- Force flag required (safety)
- JSON output

**Acceptance Criteria**:
- [ ] Command accepts all flags
- [ ] Requires --force for actual deletion
- [ ] --dry-run shows preview without deletion
- [ ] --older-than filters by days since closed
- [ ] --cascade deletes dependent issues
- [ ] Returns count of deleted issues
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Service Method**:
```python
def cleanup_issues(
    self,
    older_than_days: int | None = None,
    cascade: bool = False,
    dry_run: bool = False
) -> list[str]:
    """Delete closed issues, optionally by age and with cascade."""
```

---

## Issue 2: Implement `duplicates` command

**Priority**: HIGH  
**Estimate**: 120 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/duplicate_service.py` (new service)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues duplicates                    # Find all content duplicates
issues duplicates --json             # JSON format
issues duplicates --auto-merge       # Automatically merge all duplicates
issues duplicates --dry-run          # Preview what would be merged
```

**Features**:
- Find issues with identical content (hash-based)
- Group by content hash
- Choose merge target (most referenced or smallest ID)
- Auto-merge mode
- Dry-run preview
- JSON output

**Algorithm**:
1. Generate content hash (title + description + design + acceptance)
2. Group issues by hash
3. Only group matching status (open with open, closed with closed)
4. Choose target by reference count or ID
5. Report duplicate groups

**Acceptance Criteria**:
- [ ] Command detects content duplicates
- [ ] Groups by matching status
- [ ] --auto-merge executes merges
- [ ] --dry-run shows preview
- [ ] JSON output includes merge suggestions
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Service Method**:
```python
def find_duplicates(self) -> list[DuplicateGroup]:
    """Find issues with identical content."""

def auto_merge_duplicates(self, dry_run: bool = False) -> list[MergeResult]:
    """Automatically merge all duplicates."""
```

---

## Issue 3: Implement `merge` command

**Priority**: HIGH  
**Estimate**: 90 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/issue_service.py` (add merge method)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues merge bd-42 bd-43 --into bd-41 --json     # Merge multiple into target
issues merge bd-42 --into bd-41 --dry-run        # Preview merge
```

**Features**:
- Merge multiple source issues into target
- Close source issues with reason "Merged into bd-X"
- Migrate all dependencies to target
- Update text references in all issue fields
- Dry-run preview
- JSON output

**Operations**:
1. Validate all issues exist
2. Prevent self-merge
3. Close source issues
4. Migrate dependencies (from source → to target)
5. Update text references (descriptions, notes, design, acceptance)
6. Return merge stats

**Acceptance Criteria**:
- [ ] Command accepts multiple source IDs
- [ ] Validates target exists
- [ ] Closes source issues
- [ ] Migrates all dependencies
- [ ] Updates text references
- [ ] --dry-run shows preview
- [ ] JSON output
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Service Method**:
```python
def merge_issues(
    self,
    source_ids: list[str],
    target_id: str,
    dry_run: bool = False
) -> MergeResult:
    """Merge source issues into target."""
```

---

## Issue 4: Implement `compact` command

**Priority**: MEDIUM  
**Estimate**: 180 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/compact_service.py` (new service)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues compact --analyze --json                          # Get candidates
issues compact --analyze --tier 1 --limit 10 --json      # Limited batch
issues compact --apply --id bd-42 --summary summary.txt  # Apply compaction
issues compact --apply --id bd-42 --summary - < file.txt # From stdin
issues compact --stats --json                            # Show statistics
issues compact --auto --dry-run --all                    # Preview auto-compact
issues compact --auto --all --tier 1                     # Auto-compact tier 1
```

**Features**:
- Agent-driven compaction (--analyze, --apply)
- Legacy AI-powered compaction (--auto, requires ANTHROPIC_API_KEY)
- Tier-based priority (1=oldest/lowest priority)
- Summary application (from file or stdin)
- Statistics reporting
- Dry-run mode

**Acceptance Criteria**:
- [ ] --analyze returns candidates for review
- [ ] --apply accepts summary from file or stdin
- [ ] --stats shows compaction statistics
- [ ] --auto mode optional (AI-powered)
- [ ] Supports tier filtering
- [ ] --dry-run previews changes
- [ ] JSON output
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Note**: This is the most complex command. Consider implementing in phases:
1. Phase 1: --analyze and --stats (read-only)
2. Phase 2: --apply (write operations)
3. Phase 3: --auto (AI integration, optional)

---

## Issue 5: Implement `rename-prefix` command

**Priority**: HIGH  
**Estimate**: 60 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/prefix_service.py` (new service)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues rename-prefix kw- --dry-run   # Preview changes
issues rename-prefix kw- --json      # Apply rename
```

**Features**:
- Rename issue prefix for all issues
- Update all issue IDs (e.g., `knowledge-work-1` → `kw-1`)
- Update text references in titles, descriptions, notes, etc.
- Update dependencies and labels
- Update counter table and config
- Dry-run preview

**Validation Rules**:
- Max length: 8 characters
- Allowed: lowercase letters, numbers, hyphens
- Must start with letter
- Must end with hyphen (or auto-add)
- Cannot be empty or just hyphen

**Acceptance Criteria**:
- [ ] Command validates prefix format
- [ ] Updates all issue IDs
- [ ] Updates text references everywhere
- [ ] Updates dependencies
- [ ] Updates config
- [ ] --dry-run shows preview
- [ ] JSON output
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Service Method**:
```python
def rename_prefix(
    self,
    new_prefix: str,
    dry_run: bool = False
) -> RenameResult:
    """Rename issue prefix for all issues."""
```

---

## Issue 6: Implement `edit` command (HUMAN ONLY)

**Priority**: MEDIUM  
**Estimate**: 60 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `tests/integration/test_cli_basic.py`

**Specification**:
```bash
issues edit <id>                    # Edit description
issues edit <id> --title            # Edit title
issues edit <id> --design           # Edit design notes
issues edit <id> --notes            # Edit notes
issues edit <id> --acceptance       # Edit acceptance criteria
```

**Features**:
- Opens $EDITOR for editing fields
- Supports multiple fields: title, description, design, notes, acceptance
- HUMAN ONLY - NOT exposed via MCP server
- Validates input after edit
- Updates issue with new content

**Acceptance Criteria**:
- [ ] Command opens $EDITOR
- [ ] Supports all field types
- [ ] Validates edited content
- [ ] Updates issue on save
- [ ] Error handling for invalid $EDITOR
- [ ] NOT exposed in MCP server
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Note**: Add explicit comment in code that this is HUMAN ONLY and should not be exposed to AI agents.

---

## Issue 7: Implement `export` command

**Priority**: HIGH  
**Estimate**: 45 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/export_service.py` (may already exist in reference-code)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues export -o ./issues.jsonl
```

**Features**:
- Export all issues to JSONL file
- One issue per line (JSON Lines format)
- Include all fields (dependencies, labels, comments)
- Atomic write (temp file + rename)
- JSON output mode (shows stats)

**JSONL Format**:
```json
{"id":"bd-42","title":"Fix bug","status":"open","priority":1,...}
{"id":"bd-43","title":"Add feature","status":"closed","priority":2,...}
```

**Acceptance Criteria**:
- [ ] Command exports to specified file
- [ ] JSONL format (one JSON per line)
- [ ] Includes all issue data
- [ ] Atomic write operation
- [ ] Returns export stats
- [ ] JSON output mode
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Service Method**:
```python
def export_to_jsonl(self, output_path: Path) -> ExportStats:
    """Export all issues to JSONL file."""
```

---

## Issue 8: Implement `import` command

**Priority**: HIGH  
**Estimate**: 90 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/import_service.py` (may already exist in reference-code)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues import -i ./issues.jsonl --dry-run      # Preview changes
issues import -i ./issues.jsonl                # Import and update
issues import -i ./issues.jsonl --dedupe-after # Import + detect duplicates
```

**Features**:
- Import issues from JSONL file
- Dry-run preview (show what would change)
- Upsert behavior (create new, update existing)
- Handle missing parents (create tombstone placeholders)
- Dedupe-after mode (detect duplicates after import)
- Transaction safety

**Import Logic**:
1. Parse JSONL file
2. For each issue:
   - If ID exists: update fields
   - If ID missing but parent exists: create child
   - If parent missing: search JSONL history, create tombstone
3. Handle dependencies (best-effort resurrection)
4. Report stats (new, updated, errors)

**Acceptance Criteria**:
- [ ] Command imports from JSONL
- [ ] --dry-run shows preview
- [ ] Upsert behavior (create/update)
- [ ] Handles missing parents
- [ ] --dedupe-after detects duplicates
- [ ] Transaction safety
- [ ] JSON output
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Service Method**:
```python
def import_from_jsonl(
    self,
    input_path: Path,
    dry_run: bool = False,
    dedupe_after: bool = False
) -> ImportStats:
    """Import issues from JSONL file."""
```

---

## Issue 9: Implement `init` command

**Priority**: HIGH  
**Estimate**: 90 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- `src/issue_tracker/services/init_service.py` (new service)
- `tests/integration/test_cli_init_daemon.py`

**Specification**:
```bash
issues init
```

**Features**:
- Create `.issues/` directory structure
- Initialize SQLite database with schema
- Create configuration file (`.issues/config.json`)
- Auto-start daemon (if enabled)
- Git hooks prompt (optional)

**Directory Structure**:
```
.issues/
├── issues.db          # SQLite database
├── issues.jsonl       # JSONL export
├── config.json        # Configuration
├── daemon.pid         # Daemon PID
├── daemon.log         # Daemon logs
└── issues.sock        # Unix socket (Linux/Mac) or named pipe (Windows)
```

**Configuration Schema**:
```json
{
  "database_path": ".issues/issues.db",
  "issue_prefix": "issue",
  "daemon_mode": "poll",
  "auto_start_daemon": true,
  "sync_enabled": true,
  "sync_interval_seconds": 5,
  "export_path": ".issues/issues.jsonl"
}
```

**Acceptance Criteria**:
- [ ] Creates directory structure
- [ ] Initializes database with schema
- [ ] Creates config file with defaults
- [ ] Validates not already initialized
- [ ] JSON output mode
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Service Method**:
```python
def initialize_workspace(
    self,
    workspace: Path,
    config: dict[str, Any] | None = None
) -> InitResult:
    """Initialize issue tracker in workspace."""
```

---

## Issue 10: Implement `cycles` subcommand (under `dep`)

**Priority**: HIGH  
**Estimate**: 30 minutes  
**Files**:
- `src/issue_tracker/cli/app.py`
- Uses existing `IssueGraphService.detect_cycles()`
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues dep cycles
```

**Features**:
- Detect all dependency cycles in issue graph
- Report each cycle found
- JSON output mode

**Output Format**:
```
🔄 Dependency cycles detected:

Cycle 1: bd-42 → bd-43 → bd-44 → bd-42
Cycle 2: bd-10 → bd-11 → bd-10
```

**JSON Format**:
```json
{
  "cycles": [
    ["bd-42", "bd-43", "bd-44", "bd-42"],
    ["bd-10", "bd-11", "bd-10"]
  ],
  "count": 2
}
```

**Acceptance Criteria**:
- [ ] Command detects all cycles
- [ ] Reports each cycle path
- [ ] JSON output mode
- [ ] Uses IssueGraphService.detect_cycles()
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Implementation Note**: Service method already exists, just need CLI wrapper.

---

## Issue 11: Add `--notes-contains` filter to `list` command

**Priority**: MEDIUM  
**Estimate**: 15 minutes  
**Files**:
- `src/issue_tracker/cli/app.py` (update list command)
- `tests/integration/test_cli_advanced.py`

**Specification**:
```bash
issues list --notes-contains "TODO" --json
```

**Features**:
- Filter issues by notes field content
- Case-insensitive substring search
- Combine with other filters

**Implementation**:
Add parameter and filter logic matching existing `--title-contains` and `--desc-contains` patterns.

**Acceptance Criteria**:
- [ ] Parameter added to list command
- [ ] Case-insensitive substring search
- [ ] Filters issues with matching notes
- [ ] Combines with other filters
- [ ] JSON output
- [ ] Has integration tests
- [ ] 70%+ coverage maintained

**Code Location**: `src/issue_tracker/cli/app.py`, lines ~226-295 (in list_issues function)

---

## Implementation Order

**Phase 1 - High Priority (Critical for Agent Use)**:
1. init (required for workspace setup)
2. export (required for git sync)
3. import (required for git sync)
4. cycles (dep subcommand, completes dependency management)
5. cleanup (bulk operations)

**Phase 2 - High Priority (Duplicate Management)**:
6. duplicates (find duplicates)
7. merge (merge duplicates)

**Phase 3 - Medium Priority (Advanced Features)**:
8. rename-prefix (prefix management)
9. edit (human-only editing)
10. compact (memory decay, complex)

**Phase 4 - Quick Wins**:
11. --notes-contains (simple filter addition)

---

## Total Estimates

- **High Priority**: 645 minutes (~11 hours)
- **Medium Priority**: 255 minutes (~4 hours)
- **Total**: 900 minutes (~15 hours)

---

## References

- Reference documentation: `reference.md` (attached)
- Current CLI: `src/issue_tracker/cli/app.py`
- Existing services: `src/issue_tracker/services/`
- Reference implementations: `reference-code/backend/`

---

## Notes

- All commands must support `--json` output
- All commands need integration tests
- Maintain 70%+ test coverage
- Follow existing CLI patterns (Typer framework)
- Use service layer (not direct repository access)
- Import/export already partially implemented in reference-code
- Some services may need to be created (duplicate_service, compact_service, etc.)

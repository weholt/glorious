# CLI App.py Refactoring Status

## Goal
Reduce app.py from 4120 lines to under 3200 lines (ideally under 500 lines core logic)

## Progress
- **Start**: 4120 lines
- **Current**: 3195 lines  
- **Extracted**: 925 lines (22.5% reduction)
- **Remaining**: Need to extract ~2695 more lines to reach core-only target

## Completed Extractions

### 1. Instructions Module (250 lines)
- File: `src/issue_tracker/cli/commands/instructions.py`
- Commands: list, show, apply
- Mount: `app.add_typer(instructions_app, name="instructions")`
- **Status**: ✅ Extracted successfully

### 2. Comments Module (122 lines)
- File: `src/issue_tracker/cli/commands/comments.py`
- Commands: add, list, delete
- Mount: `app.add_typer(comments_app, name="comments")`
- **Status**: ✅ Extracted successfully

### 3. Labels Module (394 lines)
- File: `src/issue_tracker/cli/commands/labels.py`
- Commands: add, remove, set, list, all, bulk-add, bulk-remove
- Mount: `app.add_typer(labels_app, name="labels")`
- **Status**: ✅ Extracted successfully

### 4. Epics Module (179 lines)
- File: `src/issue_tracker/cli/commands/epics.py`
- Commands: add, remove, list, set, clear, all
- Mount: `app.add_typer(epics_app, name="epics")`
- **Status**: ✅ Extracted successfully

## Test Impact

**48 tests failing** due to command path changes:
- Old: `issues label-add issue-123 bug`
- New: `issues labels add issue-123 bug`

**Tests need updating** to use new subcommand structure. This is expected for this refactoring.

## Remaining Work

### High Priority Extractions (Large modules)
1. **Dependencies** (~700 lines) - dep-add, dep-remove, dep-list, blocking/blocked-by
2. **Daemon** (~500 lines) - start, stop, status, restart commands
3. **Core Issue Commands** (~800 lines) - create, list, show, update, close, delete, reopen
4. **Bulk Operations** (~200 lines) - bulk-close, bulk-update
5. **Stats/Utility** (~200 lines) - info, stats, validate

### Medium Priority
6. **Export/Import** (~100 lines) - export, import commands

## Technical Notes

- All extracted modules follow pattern: create Typer app, define commands, export as `app`
- Import pattern: `from issue_tracker.cli.commands import <module>_app`
- Mount pattern: `app.add_typer(<module>_app, name="<module_name>")`
- Service access via lazy import to avoid circular dependencies

## Next Steps

1. ~~Extract instructions~~ ✅
2. ~~Extract comments~~ ✅
3. ~~Extract labels~~ ✅
4. ~~Extract epics~~ ✅
5. **Extract dependencies** (next - 700 lines, biggest remaining module)
6. Extract daemon commands
7. Extract core issue commands
8. Extract bulk operations
9. Extract stats/utility
10. Update tests for new command structure

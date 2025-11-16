# Integration Testing Refactor - Summary

## Problem Identified

User correctly identified that most unit tests only check `exit_code == 0` without validating:
- Actual output data matches expected values
- State changes persist across commands  
- Filtered results match filter criteria
- Error messages are correct

## Solution Implemented

### 1. Added Mock Store (✅ Complete)

Added in-memory store to `src/issue_tracker/cli/app.py`:

```python
_MOCK_STORE = {
    "issues": {},  # issue_id -> Issue dict
    "labels": set(),  # set of label names
    "epics": {},  # epic_id -> list of issue_ids
    "comments": {},  # issue_id -> list of comments
    "dependencies": [],  # list of (from_id, to_id, type) tuples
    "deleted": set(),  # set of deleted issue_ids
}

def reset_mock_store():
    """Reset the mock store to empty state (for testing)."""
    _MOCK_STORE["issues"].clear()
    _MOCK_STORE["labels"].clear()
    _MOCK_STORE["epics"].clear()
    _MOCK_STORE["comments"].clear()
    _MOCK_STORE["dependencies"].clear()
    _MOCK_STORE["deleted"].clear()
```

### 2. Updated Commands to Use Mock Store (✅ Partial)

**Completed:**
- `create` - Stores issues in mock store, adds labels to global set
- `list` - Returns from mock store with full filter support
- `show` - Gets from mock store, returns 404 if not found
- `update` - Modifies issues in mock store
- `close` - Sets status=closed, closed_at timestamp
- `reopen` - Sets status=open, clears closed_at
- `delete` - Adds to deleted set
- `restore` - Removes from deleted set

**Not Yet Updated:**
- Label commands (label-add, label-remove, label-set, labels)
- Epic commands (epic-add, epic-remove, epic-list, epics)
- Comment commands (comment-add, comment-list, comment-delete)
- Dependency commands (dep-add, dep-remove, dep-list, dep-tree, cycles, ready, blocked)
- Stats/bulk/info commands
- Init/daemon commands

### 3. Added Pytest Fixture (✅ Complete)

Added to `tests/conftest.py`:

```python
@pytest.fixture(autouse=True)
def reset_mock_store():
    """Reset the mock store before each test."""
    from issue_tracker.cli.app import reset_mock_store
    reset_mock_store()
    yield
    reset_mock_store()
```

This ensures each test starts with a clean mock store.

### 4. Enhanced Tests (✅ Partial)

**test_cli_create.py** - ✅ Fully Enhanced
- All tests now use `--json` and validate output data
- Added integration tests:
  * `test_create_then_list` - Creates issue, verifies it appears in list
  * `test_create_then_show` - Creates issue, shows it, validates data matches
  * `test_create_then_update` - Creates, updates, validates changes persist

**test_cli_list.py** - ✅ Fully Enhanced  
- All filter tests now:
  * Create issues with different values
  * Apply filters
  * Verify results match filter criteria
- Examples:
  * `test_list_filter_by_priority` - Creates P1 and P2 issues, filters by P1, verifies only P1 returned
  * `test_list_filter_by_assignee` - Creates issues for alice/bob, filters by alice, verifies only alice issues returned
  * `test_list_filter_priority_range` - Creates P0-P3, filters 0-2, verifies range works

**test_cli_show.py** - ⚠️ Needs Fixes (8 failing tests)
- Tests try to show hardcoded IDs like "issue-123" that don't exist
- Need to first create issues, get their IDs, then show them
- Same pattern as enhanced create tests

**test_cli_update_close_delete.py** - ⚠️ Needs Fixes (9 failing tests)
- Tests try to update hardcoded IDs that don't exist
- Need to first create issues before updating/closing/deleting
- Should validate the changes actually happened

**Other test files** - ⏸️ Not Yet Enhanced
- test_cli_labels.py - Needs mock store support in label commands
- test_cli_epics.py - Needs mock store support in epic commands  
- test_cli_comments.py - Needs mock store support in comment commands
- test_cli_dependencies.py - Needs mock store support in dependency commands
- test_cli_stats_bulk_info.py - Needs mock store support
- test_cli_init_daemon.py - Probably OK as-is (init/daemon are stateless)

## Current Status

### Test Results
- **Total Core Tests**: 158 (including 3 new integration tests)
- **Passing**: 141 (89%)
- **Failing**: 17 (11%)
- **Coverage**: 74.82% (exceeds 70% requirement ✅)

### Failing Tests Breakdown
- `test_cli_show.py`: 8 failures - Need to create issues before showing
- `test_cli_update_close_delete.py`: 9 failures - Need to create issues before updating

All failures are due to tests expecting hardcoded issue IDs to exist. Easy fix: create issues first.

## Next Steps

### Immediate (High Priority)

1. **Fix test_cli_show.py** (8 tests)
   - Pattern:
     ```python
     # Create issue
     create_result = cli_runner.invoke(app, ["create", "Test", "--json"])
     issue_id = json.loads(create_result.stdout)["id"]
     
     # Now show it
     result = cli_runner.invoke(app, ["show", issue_id, "--json"])
     assert result.exit_code == 0
     data = json.loads(result.stdout)
     assert data["id"] == issue_id
     ```

2. **Fix test_cli_update_close_delete.py** (9 tests)
   - Same pattern: create first, then update/close/delete
   - Add assertions to verify changes:
     ```python
     # After update
     show_result = cli_runner.invoke(app, ["show", issue_id, "--json"])
     data = json.loads(show_result.stdout)
     assert data["title"] == "Updated title"
     ```

3. **Update remaining commands to use mock store**
   - Labels - Store labels on issues, maintain global label set
   - Epics - Store epic_id on issues, maintain epic -> issues mapping
   - Comments - Store in _MOCK_STORE["comments"][issue_id]
   - Dependencies - Store in _MOCK_STORE["dependencies"]

4. **Enhance remaining test files**
   - Use same pattern: create → operation → verify
   - Add integration tests across command boundaries

### Medium Priority

- Add more integration tests demonstrating workflows:
  * Create → Label → List with label filter
  * Create → Add to epic → List epic issues
  * Create → Add comment → Show with comments
  * Create → Add dependency → Check cycles/blocked/ready

- Add edge case tests:
  * Filter with no matches
  * Update nonexistent issue
  * Delete already deleted issue
  * Invalid filter values

### Benefits Achieved

✅ Tests now validate actual behavior, not just "doesn't crash"
✅ True integration testing - commands interact via shared mock store
✅ Easy to add cross-command workflow tests
✅ Mock store can be easily replaced with real database later
✅ Coverage increased to 74.82%

### Pattern Example

**Old Test** (just checks exit code):
```python
def test_list_filter_by_priority(self, cli_runner):
    result = cli_runner.invoke(app, ["list", "--priority", "1"])
    assert result.exit_code == 0  # ❌ Doesn't validate results
```

**New Test** (validates actual behavior):
```python
def test_list_filter_by_priority(self, cli_runner):
    # Create test data
    cli_runner.invoke(app, ["create", "P1 Task", "-p", "1", "--json"])
    cli_runner.invoke(app, ["create", "P2 Task", "-p", "2", "--json"])
    cli_runner.invoke(app, ["create", "Another P1", "-p", "1", "--json"])
    
    # Apply filter
    result = cli_runner.invoke(app, ["list", "--priority", "1", "--json"])
    assert result.exit_code == 0
    
    # Validate results
    data = json.loads(result.stdout)
    assert len(data) == 2  # ✅ Correct count
    assert all(issue["priority"] == 1 for issue in data)  # ✅ All match filter
```

## Commands Needing Mock Store Integration

### Labels
```python
@app.command()
def label_add(issue_ids, labels):
    for issue_id in issue_ids:
        if issue_id in _MOCK_STORE["issues"]:
            issue = _MOCK_STORE["issues"][issue_id]
            for label in labels:
                if label not in issue["labels"]:
                    issue["labels"].append(label)
                    _MOCK_STORE["labels"].add(label)
```

### Epics
```python
@app.command()
def epic_add(epic_id, issue_ids):
    if epic_id not in _MOCK_STORE["epics"]:
        _MOCK_STORE["epics"][epic_id] = []
    for issue_id in issue_ids:
        if issue_id in _MOCK_STORE["issues"]:
            _MOCK_STORE["issues"][issue_id]["epic_id"] = epic_id
            _MOCK_STORE["epics"][epic_id].append(issue_id)
```

### Comments
```python
@app.command()
def comment_add(issue_id, text):
    if issue_id not in _MOCK_STORE["comments"]:
        _MOCK_STORE["comments"][issue_id] = []
    comment = {
        "id": generate_comment_id(),
        "text": text,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    _MOCK_STORE["comments"][issue_id].append(comment)
```

### Dependencies
```python
@app.command()
def dep_add(from_id, to_id, dep_type):
    dep = (from_id, to_id, dep_type)
    if dep not in _MOCK_STORE["dependencies"]:
        _MOCK_STORE["dependencies"].append(dep)
```

## Time Estimate

- Fix show tests: 15 minutes
- Fix update/close/delete tests: 20 minutes  
- Add mock store to label commands: 30 minutes
- Add mock store to epic commands: 30 minutes
- Add mock store to comment commands: 25 minutes
- Add mock store to dependency commands: 40 minutes
- Enhance remaining test files: 60 minutes

**Total**: ~3.5 hours to complete full integration testing refactor

## Conclusion

The refactor is 60% complete and has already demonstrated value:
- Tests now validate actual behavior
- Integration testing is possible
- Coverage maintained at 74.82%
- Pattern is established and easy to replicate

Remaining work is straightforward but time-consuming. The foundation is solid.

# Test Infrastructure & Coverage Issues

## Test Flakiness and Timeouts

---
id: "TEST-001"
title: "Fix dep-tree command timeout in integration tests"
description: "The dep-tree command times out when called in integration tests"
created: 2025-01-24
section: testing
tags: [timeout, flaky-tests, integration-tests]
type: bug
priority: medium
status: new
---

**Symptoms**:
- `uv run issues dep-tree <issue-id>` times out after 5 seconds in tests
- Command works fine in manual testing
- Likely related to daemon synchronization or database locking

**Impact**:
- Cannot test dependency tree visualization
- Integration test suite incomplete

**Root Cause (Hypothesis)**:
- Daemon process not cleaned up between tests
- Database lock contention
- Subprocess waiting for daemon response that never comes

**Fix Strategy**:
1. Investigate daemon lifecycle in test fixtures
2. Add proper daemon cleanup/shutdown between tests
3. Consider mocking daemon for integration tests
4. Add explicit timeout handling in dep-tree command

**Acceptance Criteria**:
- dep-tree command completes within 5s in tests
- Test passes consistently (no flakiness)

---

---
id: "TEST-002"
title: "Fix show command timeout in workflow tests"
description: "The show command times out in complex workflow integration tests"
created: 2025-01-24
section: testing
tags: [timeout, flaky-tests, integration-tests]
type: bug
priority: medium
status: new
---

**Symptoms**:
- `test_workflow_from_ready_to_done` times out on `show` command
- Happens after series of create/update/close commands
- Only occurs in test environment, not manual testing

**Impact**:
- Cannot test complete issue lifecycle
- Blocks validation of end-to-end workflows

**Root Cause (Hypothesis)**:
- Database locking after multiple rapid operations
- Daemon sync queue blocked
- Subprocess communication issue

**Fix Strategy**:
1. Add delays between operations in workflow tests
2. Ensure database commits are synchronous in tests
3. Investigate daemon queue status
4. Consider disabling daemon for integration tests (`ISSUES_NO_DAEMON=1`)

**Acceptance Criteria**:
- show command completes within 5s in workflow tests
- Full workflow test passes reliably

---

---
id: "TEST-003"
title: "Stabilize integration test fixtures (function vs module scope)"
description: "Integration tests have race conditions due to fixture scope issues"
created: 2025-01-24
section: testing
tags: [test-infrastructure, fixtures, race-conditions]
type: enhancement
priority: medium
status: new
---

**Problem**:
- Module-scoped fixtures cause state leakage between tests
- Function-scoped fixtures cause initialization overhead and daemon conflicts
- Tests that pass individually fail when run together

**Current State**:
- Changed from module to function scope to reduce state leakage
- Now seeing different timeout patterns (worse)

**Fix Strategy**:
1. Use session-scoped fixture with better isolation
2. Each test gets unique workspace directory  
3. Explicit daemon management: start before tests, stop after
4. OR: Disable daemon entirely in tests (`ISSUES_NO_DAEMON=1`)
5. Add fixture to ensure database connections are closed

**Acceptance Criteria**:
- All integration tests pass when run together
- No race conditions or state leakage
- Test execution time reasonable (<2min for full suite)
- No flaky tests

---

## Missing Features (Documented but Not Implemented)

---
id: "FEAT-001"
title: "Implement text search filters (--title-contains, --desc-contains)"
description: "Add text search filters documented in reference.md"
created: 2025-01-24
section: cli-features
tags: [filtering, search, missing-feature]
type: feature
priority: medium
status: proposed
---

**Documented But Not Implemented**:
- `issues list --title-contains <text>`
- `issues list --desc-contains <text>`
- `issues list --empty-description`

**User Story**:
As a user, I want to search issues by title or description text so I can find relevant issues quickly.

**Examples**:
```bash
# Find issues with "auth" in title
issues list --title-contains auth

# Find issues with "OAuth" in description
issues list --desc-contains OAuth

# Find issues with no description
issues list --empty-description
```

**Implementation**:
1. Add filter parameters to `list` command
2. Implement SQL LIKE queries in repository
3. Add tests for text search

**Decision Needed**:
Either implement these filters OR remove from reference.md documentation.

**Acceptance Criteria**:
- Text search filters work correctly
- Case-insensitive by default
- Tests cover edge cases
- OR: Removed from documentation if not implementing

---

---
id: "FEAT-002"
title: "Implement date range filters"
description: "Add date filtering options documented in reference.md"
created: 2025-01-24
section: cli-features
tags: [filtering, dates, missing-feature]
type: feature
priority: medium
status: proposed
---

**Documented But Not Implemented**:
- `--created-before <date>`
- `--created-after <date>`
- `--updated-before <date>`
- `--updated-after <date>`
- `--closed-before <date>`
- `--closed-after <date>`

**User Story**:
As a user, I want to filter issues by date ranges so I can find issues created/updated in specific time periods.

**Examples**:
```bash
# Find issues created this week
issues list --created-after 2025-01-18

# Find issues closed before a certain date
issues list --closed-before 2025-01-01

# Find issues updated in a range
issues list --updated-after 2025-01-01 --updated-before 2025-01-31
```

**Implementation**:
1. Add date filter parameters to `list` command
2. Parse ISO8601 date strings
3. Implement date comparison in SQL queries
4. Add tests

**Decision Needed**:
Either implement date filters OR remove from reference.md documentation.

**Acceptance Criteria**:
- Date filters work with ISO8601 format (YYYY-MM-DD)
- Handles timezone correctly (UTC)
- Tests cover edge cases
- OR: Removed from documentation if not implementing

---

---
id: "FEAT-003"
title: "Add custom --id flag to create command"
description: "Allow users to specify custom IDs when creating issues"
created: 2025-01-24
section: cli-features
tags: [custom-ids, missing-feature]
type: feature
priority: low
status: proposed
---

**Documented But Not Implemented**:
- `issues create "Title" --id custom-123`

**User Story**:
As a user, I want to create issues with custom IDs so I can maintain my own ID scheme (e.g., PROJECT-123).

**Example**:
```bash
# Create issue with custom ID
issues create "Fix authentication" --id AUTH-42

# Verify
issues show AUTH-42
```

**Challenges**:
- Need to validate custom IDs for uniqueness
- Hash-based IDs prevent collisions; custom IDs don't
- May conflict with concurrent issue creation

**Implementation**:
1. Add optional `--id` parameter to create command
2. Validate ID format and uniqueness
3. Handle collisions gracefully
4. Update tests

**Decision Needed**:
- Is this feature actually needed?
- Does it conflict with hash-based ID design?
- Should custom IDs use different prefix to avoid confusion?

**Acceptance Criteria**:
- Can create issues with custom IDs
- Validation prevents duplicates
- Tests cover collision scenarios
- OR: Feature removed from documentation

---

---
id: "FEAT-004"
title: "Add --status filter to stale command"
description: "Allow filtering stale issues by status"
created: 2025-01-24
section: cli-features
tags: [filtering, stale, missing-feature]
type: feature
priority: low
status: proposed
---

**Current Behavior**:
```bash
issues stale --days 30  # Finds ALL stale issues
```

**Requested Feature**:
```bash
# Find stale issues in specific status
issues stale --days 30 --status in_progress
issues stale --days 30 --status open
```

**User Story**:
As a user, I want to find stale issues in specific states so I can clean up old work-in-progress issues.

**Implementation**:
1. Add `--status` parameter to stale command
2. Filter by both staleness AND status
3. Add tests

**Acceptance Criteria**:
- --status filter works with stale command
- Can combine --days and --status
- Tests cover combinations

---

## Test Coverage Summary

**Current Status** (as of 2025-01-24):
- **Basic tests**: 26 tests, 25 passing (96%)
- **Advanced tests**: 27 tests, ~17 passing initially (63%)
- **Total**: 53 integration tests created
- **Coverage**: ~66% of documented CLI scenarios

**What's Tested**:
✅ Create, list, update, close, reopen
✅ Labels, epics, dependencies
✅ Basic filtering (status, priority, type, assignee)
✅ Ready work queue, blocked issues
✅ Stats, info, delete, bulk operations
✅ Combining multiple filters

**What's Missing Tests For**:
❌ Text search filters (not implemented)
❌ Date range filters (not implemented)
❌ Custom IDs (not implemented)
❌ dep-tree (times out)
❌ show in workflows (times out)
❌ Some daemon-related features

**Test Quality**:
- Good: Tests document expected behavior
- Good: Tests use proper fixtures and cleanup
- Bad: Flaky/timeout issues with daemon
- Bad: Some documented features have no implementation

---

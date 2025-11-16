# Issues - low

## Missing CLI Commands

### Issue: Implement `label-list` command
**Priority**: LOW  
**Status**: TODO  
**Created**: 2025-11-12
**Description**: Add `issues label-list <id>` command to list labels for a specific issue.

**Notes**:
- Current workaround: Use `issues show <id>` which displays labels
- Spec location: `.work/agent/cli-specification.md` Phase 2, command 9 extension
- Implementation estimate: ~30 lines
- Very low priority - workaround exists

**Acceptance Criteria**:
- [ ] Command accepts `<id>` argument (issue ID)
- [ ] Lists all labels for the specified issue
- [ ] Supports `--json` output flag
- [ ] Returns error for non-existent issues
- [ ] Has unit and integration tests
- [ ] 70%+ test coverage maintained

---

### Issue: Implement `info` command
**Priority**: LOW  
**Status**: TODO  
**Created**: 2025-11-12
**Description**: Add `issues info` command for database introspection and system information.

**Notes**:
- Spec location: `.work/agent/cli-specification.md` Phase 8, command 25
- Implementation estimate: ~50 lines
- Use case: Debugging, admin tools
- Low priority - diagnostic tool

**Acceptance Criteria**:
- [ ] Command shows database path
- [ ] Shows total issues count  
- [ ] Shows last updated timestamp
- [ ] Shows database size
- [ ] Supports `--json` output flag
- [ ] Handles missing database gracefully
- [ ] Has unit and integration tests
- [ ] 70%+ test coverage maintained

**Output Format** (JSON):
```json
{
  "database_path": "/path/to/.issues/issues.db",
  "total_issues": 150,
  "last_updated": "2025-11-12T14:30:00Z",
  "database_size_bytes": 4096000
}
```

---


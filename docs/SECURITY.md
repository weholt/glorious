# Security and Skill Isolation

## Overview

Glorious Agents implements a permission-based isolation system to control what skills can access and modify. This ensures that skills run with least-privilege access by default, preventing unauthorized operations.

## Permission System

### Permission Types

Skills can be granted the following permissions:

- `DB_READ` - Read from the shared database
- `DB_WRITE` - Write to the shared database (INSERT, UPDATE, DELETE, CREATE, etc.)
- `FILESYSTEM_READ` - Read from the filesystem (not yet enforced)
- `FILESYSTEM_WRITE` - Write to the filesystem (not yet enforced)
- `NETWORK` - Access network resources (not yet enforced)
- `SUBPROCESS` - Spawn subprocesses (not yet enforced)
- `EVENT_PUBLISH` - Publish events to the event bus
- `EVENT_SUBSCRIBE` - Subscribe to events (default granted)
- `SKILL_CALL` - Call other skills (default granted)

### Default Permissions

By default, skills receive **read-only** access:

- ✅ `DB_READ` - Can query the database
- ✅ `EVENT_SUBSCRIBE` - Can listen to events
- ✅ `SKILL_CALL` - Can invoke other skills
- ❌ `DB_WRITE` - Cannot modify the database
- ❌ `EVENT_PUBLISH` - Cannot publish events
- ❌ All other permissions - Denied

### Core Skills Permissions

Core skills that manage persistent state are granted additional permissions:

**Write-enabled skills:**
- `issues`, `notes`, `planner`, `feedback`, `cache`
- `prompts`, `temporal`, `vacuum`, `atlas`, `automations`
- `ai`, `sandbox`, `telemetry`, `linker`, `migrate`

These skills have:
- ✅ `DB_WRITE` - Can modify their data
- ✅ `EVENT_PUBLISH` - Can notify other skills of changes

## Restricted Context

Skills receive a `RestrictedSkillContext` instead of the raw `SkillContext`. This wrapper:

1. **Database Access** - Wraps the connection with permission checks
2. **Event Bus** - Enforces publish/subscribe permissions
3. **Skill Calls** - Requires `SKILL_CALL` permission
4. **Shared Connection** - Prevents closing the shared database connection

### Example: Permission Enforcement

```python
# In a skill with read-only permissions (default)

# ✅ This works - reading is allowed
ctx.conn.execute("SELECT * FROM notes")

# ❌ This fails - no DB_WRITE permission
ctx.conn.execute("INSERT INTO notes VALUES (...)")
# Raises: PermissionError: Skill 'my_skill' does not have permission: db_write

# ❌ This fails - no EVENT_PUBLISH permission
ctx.publish("topic", {"data": "value"})
# Raises: PermissionError: Skill 'my_skill' does not have permission: event_publish
```

## Customizing Permissions

### For Development

To grant additional permissions to a skill during development:

```python
from glorious_agents.core.isolation import get_permission_registry, Permission

# Get the permission registry
registry = get_permission_registry()

# Get permissions for your skill
perms = registry.get("my_skill")

# Grant write access
perms.grant(Permission.DB_WRITE)
perms.grant(Permission.EVENT_PUBLISH)
```

### For Production

Edit the skill's manifest or update the permission registry defaults in `isolation.py`:

```python
def _setup_default_permissions(self) -> None:
    """Setup default permissions for known skills."""
    core_skills_write = [
        "my_skill",  # Add your skill here
        # ... existing skills
    ]
```

## Security Benefits

1. **Least Privilege** - Skills only get the permissions they need
2. **Audit Trail** - Permission checks are logged
3. **Fail-Safe** - Operations fail with clear errors if unauthorized
4. **Isolation** - Skills cannot interfere with each other's data without permission
5. **Shared Resource Protection** - Prevents closing or corrupting shared connections

## Future Enhancements

Planned security improvements:

- [ ] Filesystem access controls (read/write directories)
- [ ] Network access restrictions (allowed hosts/ports)
- [ ] Subprocess spawning limits
- [ ] Resource limits (CPU, memory, time)
- [ ] Process-level isolation (separate processes per skill)
- [ ] Container-based execution (Docker sandbox)
- [ ] Audit logging of all permission checks

## Testing

The isolation system includes comprehensive unit tests in `tests/unit/test_isolation.py`:

```bash
# Run isolation tests
uv run pytest tests/unit/test_isolation.py -v

# Check isolation coverage
uv run pytest tests/unit/test_isolation.py --cov=src/glorious_agents/core/isolation
```

## Troubleshooting

### PermissionError: does not have permission

**Cause:** The skill is attempting an operation it doesn't have permission for.

**Solution:**
1. Verify if the skill should have this permission
2. If yes, grant it via the permission registry
3. If no, update the skill to not attempt unauthorized operations

### Cannot close shared database connection

**Cause:** A skill attempted to close the shared database connection.

**Solution:** Remove the `conn.close()` call from your skill. The shared connection is managed by the framework.

## Related Issues

- [issue-5fd36a](../issues/issue-5fd36a.md) - Skill isolation implementation
- [issue-6557d3](../issues/issue-6557d3.md) - Security scanning with bandit
- [issue-b8fe5c](../issues/issue-b8fe5c.md) - Private attribute access

## References

- Source: `src/glorious_agents/core/isolation.py`
- Tests: `tests/unit/test_isolation.py`
- Context: `src/glorious_agents/core/context.py`

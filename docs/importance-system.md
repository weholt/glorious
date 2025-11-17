# Importance System for Notes

## Overview

The importance system allows you to differentiate and prioritize key topics, decisions, and information during implementation or planning. This ensures critical information doesn't get lost among regular notes.

## Importance Levels

The system provides three levels of importance:

| Level | Value | Icon | Usage |
|-------|-------|------|-------|
| **Normal** | 0 | - | Default for regular notes and observations |
| **Important** | 1 | ★ | Key decisions, learnings, topics requiring attention |
| **Critical** | 2 | ⚠ | Security issues, blockers, must-address items |

## Features

### 1. Visual Indicators
- Important notes are marked with ★ (star)
- Critical notes are marked with ⚠ (warning)
- Color coding: yellow for important, red for critical

### 2. Automatic Prioritization
- Search results automatically prioritize important/critical notes
- List commands show important notes first
- Universal search API boosts scores for important items

### 3. Filtering Capabilities
- Filter by importance level when listing or searching
- Quickly retrieve only critical or important notes
- Separate normal notes from priority items

### 4. Update Importance
- Change importance level of existing notes
- Upgrade notes to critical when issues arise
- Downgrade when issues are resolved

## Usage Examples

### Creating Notes with Importance

```bash
# Add a regular note
uv run agent notes add "Completed refactoring of auth module"

# Add an important note (architectural decision)
uv run agent notes add "Decided to use event-driven architecture for notifications" \
  --important --tags "architecture,decision"

# Add a critical note (security issue)
uv run agent notes add "SQL injection vulnerability found in user search" \
  --critical --tags "security,urgent"
```

### Listing Notes

```bash
# List all recent notes (important ones appear first)
uv run agent notes list

# List only important notes (includes critical)
uv run agent notes list --important

# List only critical notes
uv run agent notes list --critical
```

### Searching Notes

```bash
# Search all notes (important ones rank higher)
uv run agent notes search "authentication"

# Search only important notes
uv run agent notes search "api" --important

# Search only critical notes
uv run agent notes search "security" --critical
```

### Updating Importance

```bash
# Mark a note as important
uv run agent notes mark 123 --important

# Upgrade to critical
uv run agent notes mark 123 --critical

# Downgrade to normal
uv run agent notes mark 123 --normal
```

## When to Use Each Level

### Critical (⚠)
Use for information that requires immediate attention:
- **Security vulnerabilities**: SQL injection, XSS, authentication bypass
- **Blocking issues**: Can't proceed without resolution
- **Data loss risks**: Potential for data corruption or loss
- **Breaking changes**: Changes that break existing functionality
- **Production incidents**: Active issues affecting users

### Important (★)
Use for key information that needs attention but isn't urgent:
- **Architectural decisions**: Major design choices and rationale
- **Key learnings**: Important insights from implementation
- **Important feedback**: Critical feedback from reviews or testing
- **API changes**: Non-breaking but significant API modifications
- **Performance issues**: Notable performance concerns
- **Technical debt**: Significant debt that should be addressed
- **Follow-up items**: Topics that need future attention

### Normal (default)
Use for regular information:
- General observations and notes
- Documentation updates
- Routine reminders
- Low-priority todos
- Reference information

## Programmatic Usage

### Python API

```python
from glorious_agents.skills.notes.src.glorious_skill_notes.skill import add_note, search_notes

# Add notes with importance
normal_id = add_note("Regular observation")
important_id = add_note("Key decision made", importance=1)
critical_id = add_note("Security issue found", importance=2)

# Search returns results sorted by importance
results = search_notes("security")
for note in results:
    print(f"[{note['importance']}] {note['content']}")
```

### Universal Search Integration

The importance system integrates with the universal search API:

```python
from glorious_agents.core.search import search_all_skills

# Important notes get boosted scores
results = search_all_skills(ctx, "architecture")
# Results from notes skill will have higher scores if marked important/critical
```

## Benefits

1. **Never miss critical information**: Critical notes always surface first
2. **Prioritize work**: Easily identify what needs attention
3. **Reduce cognitive load**: Separate signal from noise
4. **Better context retrieval**: Search returns most relevant important notes
5. **Effective knowledge management**: Categorize information by priority
6. **Agent-friendly**: AI agents can better understand what's important

## Database Schema

The importance system is implemented via database migration:

```sql
-- Migration adds importance column
ALTER TABLE notes ADD COLUMN importance INTEGER DEFAULT 0;

-- Index for efficient importance queries
CREATE INDEX idx_notes_importance ON notes(importance DESC, created_at DESC);
```

## Integration with Other Skills

The importance concept can be extended to other skills:

- **Planner skill**: Already has `important` flag for tasks
- **Issues skill**: Could track critical issues separately
- **Future skills**: Any skill can adopt similar importance patterns

## Tips for Agents

When working as an AI agent:

1. **Mark important decisions as important**: If you make a key architectural choice, note it with `importance=1`
2. **Flag security concerns as critical**: Any security-related finding should be `importance=2`
3. **Use importance for feedback**: Important learnings from implementation should be marked
4. **Review important notes**: Before starting new work, check important notes: `notes list --important`
5. **Update importance**: If a critical issue is resolved, downgrade it to normal

## Future Enhancements

Potential improvements to the importance system:

- [ ] Time-based auto-downgrade (critical → important after X days)
- [ ] Importance inheritance (tasks created from critical notes are also marked important)
- [ ] Dashboard showing all important/critical items across skills
- [ ] Notifications/reminders for critical items
- [ ] Analytics on importance usage patterns
- [ ] Integration with planner priority scoring

## Migration

The importance system is added via database migration and is backward compatible:

- Existing notes default to `importance=0` (normal)
- No action required for existing notes
- Migration runs automatically on first use
- Can manually upgrade important existing notes using `mark` command

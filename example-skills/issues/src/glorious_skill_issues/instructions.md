# Issues Skill - Internal Instructions

For AI agents working with the issues skill.

## Purpose

Issue tracking system that integrates with the notes skill via events.

## Key Features

- Create and manage issues
- Auto-create issues from tagged notes
- Status and priority tracking
- Link issues to source notes

## Dependencies

- **notes**: Subscribes to `note_created` events

## Events

### Subscribed

- `note_created`: Auto-creates issue if note has "todo" or "issue" tag

### Published

- `issue_created`: Published when a new issue is created
  - Payload: `{"id": int, "title": str, "status": str, "priority": str}`

## Callable APIs

### create_issue(title, description, status, priority, source_note_id) -> int

Create a new issue programmatically.

### update_issue(issue_id, **kwargs) -> None

Update issue fields (title, description, status, priority).

## Integration Pattern

The issues skill automatically listens for notes tagged with "todo" or "issue" and creates tracking issues for them. This enables a workflow where quick notes can be upgraded to tracked issues automatically.

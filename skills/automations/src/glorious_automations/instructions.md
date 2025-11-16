# Automations Skill - Internal Documentation

## Purpose

The automations skill provides a declarative event-driven automation engine that responds to events and executes actions.

## Features

- **Event-Driven**: React to any event topic in the system
- **Conditional Triggers**: Filter events with Python expressions
- **Multiple Actions**: Chain multiple actions in sequence
- **Execution History**: Track all automation runs
- **Enable/Disable**: Control automation state without deletion

## Architecture

### Event Flow
1. Event published to topic
2. Automation checks condition (if any)
3. Actions executed in order
4. Result recorded in database

### Action Types

- **log**: Print message to console
- **publish**: Publish new event to topic

Future action types can be added by extending `_execute_automation`.

## Database Schema

### automations
Stores automation definitions with trigger and action configuration.

### automation_executions
Records each automation execution with status and results.

## Usage in Code

```python
from glorious_automations.skill import create, enable, disable

# Create automation
auto_id = create(
    name="Log new notes",
    trigger_topic="note.created",
    actions='[{"type": "log", "message": "Note created!"}]'
)

# Conditional automation
auto_id = create(
    name="Alert high priority",
    trigger_topic="issue.created",
    trigger_condition="data.get('priority') == 1",
    actions='[{"type": "publish", "topic": "alert.high", "data": {}}]'
)
```

## Integration

Automations automatically register with the event bus on initialization and respond to matching events.

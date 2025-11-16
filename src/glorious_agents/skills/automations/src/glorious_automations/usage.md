# Automations Skill Usage

Create declarative event-driven automations that respond to system events.

## Commands

### create
Create a new automation:
```bash
agent automations create "Log notes" "note.created" '[{"type":"log","message":"Note created"}]'
agent automations create "Alert" "issue.created" '[{"type":"publish","topic":"alert","data":{}}]' --condition 'data.get("priority") == 1'
```

### create-from-file
Create from YAML/JSON file:
```bash
agent automations create-from-file automation.yaml
```

Example YAML:
```yaml
name: "Log new issues"
description: "Log when issues are created"
trigger_topic: "issue.created"
trigger_condition: 'data.get("priority") == 1'
actions:
  - type: log
    message: "High priority issue created!"
  - type: publish
    topic: "notifications.high"
    data: {}
```

### list
List all automations:
```bash
agent automations list
agent automations list --enabled
agent automations list --json
```

### show
Show automation details:
```bash
agent automations show auto-abc123
agent automations show auto-abc123 --json
```

### enable/disable
Control automation state:
```bash
agent automations enable auto-abc123
agent automations disable auto-abc123
```

### delete
Remove automation:
```bash
agent automations delete auto-abc123
```

### executions
View execution history:
```bash
agent automations executions
agent automations executions --automation auto-abc123
agent automations executions --limit 50
```

## Action Types

### log
Print a message:
```json
{"type": "log", "message": "Your message here"}
```

### publish
Publish an event:
```json
{"type": "publish", "topic": "event.topic", "data": {"key": "value"}}
```

## Conditions

Use Python expressions to filter events:
```python
data.get("priority") == 1
data.get("status") == "critical"
data.get("count", 0) > 10
```

The `data` variable contains the event payload.

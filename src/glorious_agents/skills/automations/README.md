# Glorious Automations Skill

Declarative event-driven automation engine for the Glorious Agents framework.

## Features

- **Event-Driven**: Respond to any system event
- **Conditional Logic**: Filter events with Python expressions
- **Multiple Actions**: Execute sequences of actions
- **History Tracking**: Monitor execution results
- **Declarative Config**: Define automations in YAML or JSON

## Installation

```bash
cd example-skills/automations
uv pip install -e .
```

## Quick Start

```bash
# Create simple automation
agent automations create "Log notes" "note.created" '[{"type":"log","message":"Note!"}]'

# Create from file
cat > auto.yaml <<EOF
name: "Alert on priority issues"
trigger_topic: "issue.created"
trigger_condition: 'data.get("priority") == 1'
actions:
  - type: log
    message: "High priority issue detected!"
EOF

agent automations create-from-file auto.yaml

# List automations
agent automations list

# View executions
agent automations executions
```

## Action Types

- **log**: Print messages
- **publish**: Trigger new events

## Requirements

- Python 3.11+
- PyYAML for YAML support

## License

MIT

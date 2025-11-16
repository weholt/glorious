# Glorious Agents - Skills Documentation Plan

> **Created:** 2025-11-16  
> **Status:** Planning Phase  
> **Goal:** Ensure ALL features and commands for ALL 17 skills are comprehensively documented

## Overview

Currently, glorious-agents has 17 skills with varying levels of documentation. Most skills have README.md files, but are missing:
- `usage.md` (human-readable usage guides)
- `instructions.md` (AI agent-specific instructions)
- Complete command reference with examples
- Event system documentation
- Integration patterns

This plan ensures every skill is fully documented for both human users and AI agents.

## Current State

### Documentation Status by Skill

| Skill | README.md | usage.md | instructions.md | Status |
|-------|-----------|----------|-----------------|--------|
| ai | ✓ | ✗ | ✗ | Incomplete |
| automations | ✓ | ✗ | ✗ | Incomplete |
| cache | ✓ | ✗ | ✗ | Incomplete |
| code-atlas | ✓ | ✗ | ✗ | Incomplete |
| docs | ✓ | ✗ | ✗ | Incomplete |
| feedback | ✗ | ✗ | ✗ | Missing |
| issues | ✓ | ✗ | ✗ | Incomplete |
| linker | ✓ | ✗ | ✗ | Incomplete |
| migrate | ✓ | ✗ | ✗ | Incomplete |
| notes | ✓ | ✗ | ✗ | Incomplete |
| orchestrator | ✗ | ✗ | ✗ | Missing |
| planner | ✗ | ✗ | ✗ | Missing |
| prompts | ✗ | ✗ | ✗ | Missing |
| sandbox | ✗ | ✗ | ✗ | Missing |
| telemetry | ✗ | ✗ | ✗ | Missing |
| temporal | ✗ | ✗ | ✗ | Missing |
| vacuum | ✗ | ✗ | ✗ | Missing |

**Summary:**
- 10 skills have README.md
- 0 skills have usage.md
- 0 skills have instructions.md
- 7 skills have no documentation at all

## Issues Created

### High Priority

#### issue-6c1074: Create comprehensive skill documentation for all 17 skills
**Priority:** 🟠 High  
**Labels:** critical, documentation, skills

Document all features, commands, and use cases for every skill. Each skill needs:
1. usage.md (human-readable guide)
2. instructions.md (AI agent guide)
3. Full command documentation
4. Examples for common use cases
5. Integration patterns

#### issue-4055e7: Generate comprehensive AGENT-TOOLS.md with all skill commands
**Priority:** 🟠 High  
**Labels:** agent-tools, automation, documentation

Enhance `agent init` command to generate complete AGENT-TOOLS.md that includes:
1. All commands with full descriptions
2. Command parameters and options
3. Usage examples for each command
4. Sub-command documentation (e.g., issues dependencies, issues comments)
5. Event topics each skill publishes/subscribes to

### Medium Priority

#### issue-3642a0: Update README with complete skills reference table
**Priority:** 🟡 Medium  
**Labels:** documentation, readme

Create comprehensive skills reference in README:
1. Table with all 17 skills
2. Command count per skill
3. Key features summary
4. Common use cases
5. Dependencies between skills
6. Installation instructions per skill

#### issue-119dce: Create skill discovery and help system
**Priority:** 🟡 Medium  
**Labels:** cli, documentation, enhancement

Add commands to discover and learn about skills:
1. `agent skills describe <skill>` with full command list
2. `agent skills examples <skill>` with usage examples
3. `agent skills search <keyword>` to find relevant skills
4. `agent <skill> --examples` to show examples
5. Interactive skill explorer

#### issue-189361: Document skill event system and inter-skill communication
**Priority:** 🟡 Medium  
**Labels:** architecture, documentation, events

Create documentation for the event bus:
1. List all event topics
2. Which skills publish which events
3. Which skills subscribe to which events
4. Event payload schemas
5. Integration patterns
6. How to create event-driven workflows

### Low Priority

#### issue-c82ec6: Create skill usage tutorials and cookbook
**Priority:** 🟢 Low  
**Labels:** documentation, examples, tutorials

Create practical tutorials:
1. Beginner tutorials for each skill
2. Advanced patterns and combinations
3. Real-world workflow examples
4. Troubleshooting common issues
5. Best practices per skill
6. Performance tips

## Documentation Structure

Each skill should have the following documentation files:

### 1. README.md (Overview)
```markdown
# Skill Name

Brief description (1-2 sentences)

## Features
- Feature 1
- Feature 2
- ...

## Installation
pip install skill-package-name

## Quick Start
[3-5 line example]

## Documentation
- [Usage Guide](./usage.md) - For humans
- [Agent Instructions](./instructions.md) - For AI agents
```

### 2. usage.md (Human-Readable Guide)
```markdown
# Skill Name - Usage Guide

## Overview
Detailed explanation of what the skill does and when to use it.

## Commands

### command-name
Description of the command.

**Usage:**
```bash
agent skill-name command-name [OPTIONS]
```

**Options:**
- `--option1`: Description
- `--option2`: Description

**Examples:**
```bash
# Example 1
agent skill-name command-name --option1 value

# Example 2
agent skill-name command-name --option2 value
```

[Repeat for each command]

## Common Use Cases

### Use Case 1: [Name]
Description and example

### Use Case 2: [Name]
Description and example

## Integration with Other Skills
- Works with [skill-name] via [mechanism]
- Publishes events that [other-skill] can consume

## Troubleshooting
Common issues and solutions
```

### 3. instructions.md (AI Agent Guide)
```markdown
# Skill Name - Agent Instructions

## Purpose
What this skill is for and when agents should use it.

## Commands Reference

### Command: command-name
**When to use:** [situation]
**Parameters:** [required and optional]
**Returns:** [what it returns]
**Events:** [publishes/subscribes]

[Repeat for each command]

## Workflow Patterns

### Pattern 1: [Name]
Step-by-step workflow for common pattern

### Pattern 2: [Name]
Step-by-step workflow for common pattern

## Event Integration
- **Publishes:** event-topic-name (payload schema)
- **Subscribes:** event-topic-name (what it does with it)

## Best Practices for Agents
- Do this
- Don't do that
- Consider this

## Performance Considerations
- Caching strategies
- Batch operations
- Resource limits
```

## Implementation Plan

### Phase 1: Core Documentation Framework (Week 1)

#### Step 1: Create documentation templates
- [ ] Create README.md template
- [ ] Create usage.md template
- [ ] Create instructions.md template
- [ ] Document template usage

#### Step 2: Automate documentation generation
- [ ] Enhance `agent init` to extract commands from Typer
- [ ] Auto-generate command reference from help text
- [ ] Extract event topics from skill code
- [ ] Generate skeleton documentation files

#### Step 3: Document high-priority skills (issues, notes, code-atlas)
- [ ] Complete documentation for issues skill
- [ ] Complete documentation for notes skill  
- [ ] Complete documentation for code-atlas skill

### Phase 2: Core Skills Documentation (Week 2)

#### Step 4: Document workflow skills
- [ ] planner skill documentation
- [ ] orchestrator skill documentation
- [ ] automations skill documentation
- [ ] temporal skill documentation

#### Step 5: Document data skills
- [ ] cache skill documentation
- [ ] linker skill documentation
- [ ] feedback skill documentation
- [ ] telemetry skill documentation

### Phase 3: Specialized Skills Documentation (Week 3)

#### Step 6: Document utility skills
- [ ] prompts skill documentation
- [ ] vacuum skill documentation
- [ ] docs skill documentation
- [ ] migrate skill documentation

#### Step 7: Document advanced skills
- [ ] sandbox skill documentation
- [ ] ai skill documentation

### Phase 4: Integration Documentation (Week 4)

#### Step 8: Create comprehensive AGENT-TOOLS.md
- [ ] Enhance generator to include all commands
- [ ] Add command parameters and options
- [ ] Include usage examples
- [ ] Document sub-commands
- [ ] Add event system reference

#### Step 9: Update main README
- [ ] Create skills reference table
- [ ] Add installation matrix
- [ ] Document skill dependencies
- [ ] Add quick reference guide

#### Step 10: Create event system documentation
- [ ] Document all event topics
- [ ] Create event flow diagrams
- [ ] Show publisher/subscriber relationships
- [ ] Provide integration examples

### Phase 5: Advanced Documentation (Week 5)

#### Step 11: Create tutorials and cookbook
- [ ] Beginner tutorial for each skill
- [ ] Intermediate workflow tutorials
- [ ] Advanced integration patterns
- [ ] Troubleshooting guide

#### Step 12: Add discovery and help features
- [ ] Implement `agent skills describe`
- [ ] Implement `agent skills examples`
- [ ] Add `--examples` flag to all skills
- [ ] Create interactive explorer

## Skills Reference (To Be Documented)

### 1. **issues** - Issue Tracking
**Commands:** 30+ commands
**Key Features:**
- Create, list, update, close issues
- Dependencies and blocking relationships
- Epics and hierarchical structure
- Comments and labels
- Templates for reuse
- Full-text search
- Bulk operations
- Git integration

**Sub-commands:**
- `comments` - Manage issue comments
- `dependencies` - Manage dependencies and blocking
- `epics` - Manage epics
- `instructions` - Manage instruction templates
- `labels` - Manage labels
- `daemons` - Daemon management

### 2. **notes** - Note-Taking
**Commands:** ~8 commands
**Key Features:**
- Create and manage notes
- Tagging system
- Full-text search
- Export/import
- Auto-create issues from tagged notes

### 3. **code-atlas** - Codebase Analysis
**Commands:** ~15 commands
**Key Features:**
- Scan codebase structure
- Code quality ranking
- Refactor priority analysis
- Watch mode for live updates
- AI-powered code Q&A
- Best practices checking

### 4. **planner** - Task Queue Management
**Commands:** ~10 commands
**Key Features:**
- Task queue with priorities
- Next task selection
- Task dependencies
- Progress tracking
- Sync with issues
- Search tasks

### 5. **cache** - Ephemeral Storage
**Commands:** ~6 commands
**Key Features:**
- TTL-based caching
- Key-value storage
- Warmup/prune operations
- Statistics

### 6. **automations** - Workflow Automation
**Commands:** ~10 commands
**Key Features:**
- Define automated workflows
- Trigger-based execution
- Integration with skills
- Workflow templates
- Execution history

### 7. **prompts** - Prompt Management
**Commands:** ~8 commands
**Key Features:**
- Store prompt templates
- Variable substitution
- Versioning
- Categorization
- Rendering engine

### 8. **feedback** - Outcome Tracking
**Commands:** ~6 commands
**Key Features:**
- Record action outcomes
- Success/failure tracking
- Context and notes
- Statistics and trends
- Learning feedback loop

### 9. **telemetry** - Action Logging
**Commands:** ~6 commands
**Key Features:**
- Log agent actions
- Metrics and statistics
- Performance tracking
- Audit trail
- Query history

### 10. **linker** - Cross-Reference Management
**Commands:** ~8 commands
**Key Features:**
- Link entities across skills
- Semantic relationships
- Find related items
- Graph traversal

### 11. **temporal** - Time-Based Operations
**Commands:** ~6 commands
**Key Features:**
- Time range filtering
- Scheduled operations
- Time-aware queries
- Date parsing

### 12. **vacuum** - Knowledge Distillation
**Commands:** ~4 commands
**Key Features:**
- Compact old data
- Distill knowledge
- Optimize storage
- History tracking

### 13. **orchestrator** - Intent Routing
**Commands:** ~6 commands
**Key Features:**
- Route intents to skills
- Skill orchestration
- Pattern matching
- Execution coordination

### 14. **sandbox** - Isolated Execution
**Commands:** ~6 commands
**Key Features:**
- Docker-based isolation
- Safe code execution
- Resource limits
- Container management

### 15. **ai** - AI Integration
**Commands:** ~8 commands
**Key Features:**
- LLM integration
- Chat conversations
- Embeddings generation
- Model configuration

### 16. **docs** - Documentation Management
**Commands:** ~8 commands
**Key Features:**
- Generate documentation
- Update docs
- Validate docs
- Documentation search

### 17. **migrate** - Data Migration
**Commands:** ~6 commands
**Key Features:**
- Schema migrations
- Data transformations
- Version management
- Rollback support

## Event System Documentation

### Core Events (To Be Documented)

| Event Topic | Publisher | Subscribers | Payload |
|-------------|-----------|-------------|---------|
| `note_created` | notes | issues, linker | `{id, content, tags}` |
| `issue_created` | issues | telemetry, planner | `{id, title, priority}` |
| `issue_updated` | issues | telemetry | `{id, status, fields}` |
| `task_enqueued` | planner | telemetry | `{task_id, priority}` |
| `scan_complete` | code-atlas | feedback | `{files, metrics}` |
| [More events...] | | | |

## Success Criteria

Complete documentation means:

1. **Every skill has:**
   - ✓ README.md with overview
   - ✓ usage.md with complete command reference
   - ✓ instructions.md for AI agents
   - ✓ Examples for common use cases

2. **AGENT-TOOLS.md includes:**
   - ✓ All 17 skills listed
   - ✓ All commands with descriptions
   - ✓ Command parameters and options
   - ✓ Sub-command documentation
   - ✓ Event system reference

3. **README.md includes:**
   - ✓ Complete skills reference table
   - ✓ Installation instructions per skill
   - ✓ Quick start examples
   - ✓ Integration patterns

4. **Discovery system works:**
   - ✓ `agent skills describe <skill>` shows full info
   - ✓ `agent skills examples <skill>` shows examples
   - ✓ `agent <skill> --help` is comprehensive

5. **Event system documented:**
   - ✓ All event topics listed
   - ✓ Publisher/subscriber relationships clear
   - ✓ Event payload schemas defined
   - ✓ Integration examples provided

## Timeline Estimate

- **Phase 1 (Framework):** 1 week
- **Phase 2 (Core Skills):** 1 week
- **Phase 3 (Specialized Skills):** 1 week
- **Phase 4 (Integration):** 1 week
- **Phase 5 (Advanced):** 1 week

**Total:** 5 weeks for complete documentation

**Minimum Viable Documentation:** 2 weeks (Phases 1-2)

## Next Steps

1. **Immediate:** Create documentation templates (issue-6c1074)
2. **Next:** Enhance `agent init` to auto-generate docs (issue-4055e7)
3. **Then:** Document top 5 most-used skills
4. **Then:** Complete remaining skills
5. **Finally:** Create tutorials and cookbook

## Tools and Automation

### Documentation Generator

Create `scripts/generate_docs.py`:

```python
#!/usr/bin/env python3
"""Generate skill documentation from code."""

import typer
from pathlib import Path
from glorious_agents.core.loader import load_all_skills
from glorious_agents.core.registry import get_registry

def extract_commands(skill_app):
    """Extract all commands from a Typer app."""
    commands = []
    if hasattr(skill_app, "registered_commands"):
        for cmd in skill_app.registered_commands:
            commands.append({
                "name": cmd.name or cmd.callback.__name__,
                "help": cmd.help or cmd.callback.__doc__ or "",
                "params": [p.name for p in cmd.params],
            })
    return commands

def generate_usage_md(skill_name, commands):
    """Generate usage.md for a skill."""
    # Template-based generation
    pass

def generate_instructions_md(skill_name, commands):
    """Generate instructions.md for a skill."""
    # Template-based generation
    pass

def main():
    load_all_skills()
    registry = get_registry()
    
    for manifest in registry.list_all():
        skill_app = registry.get_app(manifest.name)
        commands = extract_commands(skill_app)
        
        # Generate documentation files
        generate_usage_md(manifest.name, commands)
        generate_instructions_md(manifest.name, commands)

if __name__ == "__main__":
    main()
```

### Documentation Validator

Create `scripts/validate_docs.py` to ensure:
- All skills have required files
- All commands are documented
- Examples are valid
- Links work

## Notes

### Python 3.13 Type Hint Issue
The planner skill has a type hint error that prevents it from loading. This should be fixed before documenting:
```python
# Current (broken):
def search(query: str, limit: int = 10) -> list[SearchResult]:

# Fix:
from typing import List
def search(query: str, limit: int = 10) -> List[SearchResult]:
```

### Documentation Priority
Focus first on skills that users will use most:
1. issues, notes, code-atlas (core workflow)
2. planner, cache, automations (productivity)
3. prompts, feedback, telemetry (enhancement)
4. Everything else (specialized use cases)

## Related Resources

- [AGENTIC_WORKFLOW.md](./AGENTIC_WORKFLOW.md) - Shows how skills work together
- [README.md](./README.md) - Main documentation
- [docs/skill-authoring.md](./docs/skill-authoring.md) - How to create skills

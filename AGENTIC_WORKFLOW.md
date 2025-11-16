# Agentic Coder Workflow

> **Purpose**: An optimized workflow for AI agents to efficiently manage, plan, and execute coding tasks using all available skills.

## 🎯 Core Principle

**Start with Context → Plan → Execute → Learn → Iterate**

Each skill has a specific role in the development lifecycle. Use them together for maximum efficiency.

---

## 📋 Workflow Phases

### Phase 1: Context Gathering & Analysis

**Objective**: Understand the codebase, current state, and requirements.

```bash
# 1. Check planner queue for ongoing work
uv run agent planner list

# 2. Review existing issues and their dependencies
uv run agent issues ready 
uv run agent issues stats
uv run agent issues dependencies tree <ISSUE-ID>  # For specific issue context

# 3. Scan codebase structure
uv run agent atlas scan .

# 4. Check code quality and get refactor priorities
uv run agent atlas rank

# 5. Universal search across all skills
uv run agent search "authentication" --limit 10
uv run agent search "bug fix" --json  # JSON output for parsing

# 6. Search specific skills (if you know where to look)
uv run agent notes search "relevant keyword"
uv run agent issues list --filter "label:bug"

# 7. Query codebase for specific patterns (agent-friendly JSON output)
uv run agent atlas --query "your question about code"
```

**Cache Warmup** (optional for large projects):
```bash
uv run agent cache warmup
```

---

### Phase 2: Issue Creation & Planning

**Objective**: Break down work into trackable, prioritized issues.

#### Creating Issues

```bash
# Create main feature/bug issue
uv run agent issues create "Feature: Add authentication" \
  --type feature \
  --priority 2 \
  --labels backend,security \
  --description "Implement JWT-based authentication system"

# Create sub-tasks with dependencies
uv run agent issues create "Design auth schema" --priority 1 --type task
uv run agent issues dependencies add ISSUE-123 ISSUE-456 --type blocks

# Bulk create from template or file
uv run agent issues bulk-create issues_template.jsonl
```

#### Using Templates

```bash
# Save reusable issue templates
uv run agent issues template_save "bug_template" \
  --type bug \
  --priority 2 \
  --labels bug,needs-triage

# List and use templates
uv run agent issues template_list
uv run agent issues template_show bug_template
```

#### Planning Work Queue

```bash
# Sync issues to planner queue
uv run agent planner sync

# Add specific tasks with priority
uv run agent planner add "Implement user model" \
  --priority high \
  --context "Related to ISSUE-123"

# View work queue
uv run agent planner list
```

---

### Phase 3: Execution

**Objective**: Work through tasks systematically with real-time tracking.

#### Get Next Task

```bash
# Get highest priority ready task
uv run agent planner next

# Or check ready issues directly
uv run agent issues ready --sort priority
```

#### During Development

```bash
# 1. Update task status
uv run agent planner update <TASK-ID> --status in_progress
uv run agent issues update ISSUE-123 --status in_progress

# 2. Add notes for context and decisions
uv run agent notes add "Decided to use bcrypt for password hashing" \
  --tags "security,auth,ISSUE-123"

# 3. Cache intermediate results (TTL-based)
uv run agent cache set "test_results" "42 passed, 3 failed" --ttl 3600

# 4. Watch for code changes (auto-update atlas index)
uv run agent atlas watch src/ &
uv run agent atlas watch-status  # Check watch daemon
```

#### Code Quality Checks

```bash
# Run quality checks against rules
uv run agent atlas check

# Re-rank refactor priorities after changes
uv run agent atlas rank
```

---

### Phase 4: Feedback & Learning

**Objective**: Record outcomes and improve future decision-making.

```bash
# Record action feedback (success/failure)
uv run agent feedback record "implement_auth" \
  --outcome success \
  --context "Used JWT with refresh tokens" \
  --notes "Works well, consider rate limiting"

# View feedback stats
uv run agent feedback stats
uv run agent feedback list --limit 10

# Update issue with resolution
uv run agent issues update ISSUE-123 \
  --status closed \
  --resolution "Implemented in commit abc123"

# Add closing comment
uv run agent issues comments add ISSUE-123 \
  "Fixed with JWT implementation. Tests passing."

# Update planner
uv run agent planner update <TASK-ID> --status completed
```

---

### Phase 5: Knowledge Management & Optimization

**Objective**: Maintain a clean, efficient knowledge base.

#### Periodic Maintenance

```bash
# Find and manage stale issues
uv run agent issues stale --days 30

# Find and merge duplicates
uv run agent issues duplicates --auto-merge

# Compact old/low-priority issues (memory decay)
uv run agent issues compact --days 90 --priority 3

# Clean up closed issues
uv run agent issues cleanup --older-than 180

# Prune expired cache
uv run agent cache prune
```

#### Knowledge Distillation

```bash
# Run vacuum to distill/optimize knowledge
uv run agent vacuum run

# View vacuum history
uv run agent vacuum history
```

#### Export/Import for Backup

```bash
# Export issues
uv run agent issues export backup.jsonl

# Import issues
uv run agent issues import backup.jsonl
```

---

## 🔄 Complete Task Lifecycle Example

### Scenario: Implement New Feature

```bash
# === CONTEXT ===
uv run agent atlas scan .
uv run agent issues stats
uv run agent search "api profile user"  # Universal search
uv run agent notes search "api"  # Specific skill search

# === PLANNING ===
# Create main issue
uv run agent issues create "Feature: Add user profile API" \
  --type feature \
  --priority 1 \
  --labels api,backend

# Create sub-tasks
uv run agent issues create "Design profile schema" --priority 1 --type task
uv run agent issues create "Implement GET /profile endpoint" --priority 2 --type task
uv run agent issues create "Add profile tests" --priority 2 --type task

# Set dependencies
uv run agent issues dependencies add ISSUE-102 ISSUE-101 --type blocks
uv run agent issues dependencies add ISSUE-103 ISSUE-102 --type blocks

# Sync to planner
uv run agent planner sync

# === EXECUTION ===
# Get next task
uv run agent planner next

# Start work
uv run agent issues update ISSUE-101 --status in_progress
uv run agent planner update TASK-501 --status in_progress

# Make notes during development
uv run agent notes add "Profile schema includes: username, email, avatar, bio" \
  --tags "ISSUE-101,schema"

# Run quality checks
uv run agent atlas check

# === FEEDBACK ===
# Record outcome
uv run agent feedback record "design_profile_schema" \
  --outcome success \
  --context "Used existing user model as base" \
  --notes "Added 4 new fields, migrations created"

# Close issue
uv run agent issues close ISSUE-101
uv run agent planner update TASK-501 --status completed

# === NEXT TASK ===
uv run agent planner next  # Automatically gets ISSUE-102 (unblocked)
```

---

## 🧠 Advanced Patterns

### 1. Universal Search

The `agent search` command queries all skills simultaneously, returning unified results:

```bash
# Search across all skills
uv run agent search "memory leak"
uv run agent search "authentication" --limit 20
uv run agent search "todo" --json  # Get JSON for parsing

# What gets searched:
# - Issues: titles, descriptions, comments
# - Notes: content and tags
# - Automations: names, descriptions, triggers
# - Workflows: names and intents
# - Prompts: names and templates
# - Telemetry: event categories and descriptions
# - Cache: keys and values
# - Feedback: actions and contexts
# - Links: entity types and IDs
# - Sandboxes: images and logs
# - Code Atlas: symbols and files
# - And more...

# Results include:
# - skill: Which skill the result came from
# - id: Item ID for direct access
# - type: Type of entity (issue, note, automation, etc.)
# - content: Searchable content
# - metadata: Additional context
# - score: Relevance score (0.0-1.0)
```

**Use cases:**
- Find related work across different skills
- Quick keyword lookup without knowing where data is
- Building context for new tasks
- Debugging by searching logs, issues, and notes together

### 2. Temporal Filtering

```bash
# Filter by time ranges
uv run agent temporal examples  # Show syntax

# Recent issues
uv run agent issues list --since "1 week ago"

# Feedback from specific period
uv run agent feedback list --since "2024-01-01"
```

### 3. Prompt Templates for Consistency

```bash
# Register reusable prompts
uv run agent prompts register code_review \
  "Review {{file}} for: 1) Security 2) Performance 3) Style"

# List templates
uv run agent prompts list

# Render with variables
uv run agent prompts render code_review --var file=auth.py
```

### 4. Bulk Operations

```bash
# Bulk update issues
uv run agent issues bulk-update --filter "label:refactor" --add-label technical-debt

# Bulk label management
uv run agent issues bulk-label-add --filter "priority:1" --labels urgent,sprint-5
uv run agent issues bulk-label-remove --filter "status:closed" --labels in-progress

# Bulk close with reason
uv run agent issues bulk-close --filter "label:wontfix" --reason "Out of scope"
```

### 5. Dependency Management

```bash
# View dependency tree
uv run agent issues dependencies tree ISSUE-100

# Find cycles (should be none!)
uv run agent issues dependencies cycles

# Check blocked issues
uv run agent issues blocked
```

### 6. Watch Mode for Live Updates

```bash
# Start watching codebase
uv run agent atlas watch src/ &

# Check status
uv run agent atlas watch-status

# Stop when done
uv run agent atlas stop-watch
```

---

## 📊 Monitoring & Health Checks

```bash
# Daily health check
uv run agent issues stats
uv run agent planner list
uv run agent feedback stats
uv run agent atlas rank | head -n 20

# Weekly maintenance
uv run agent issues stale --days 7
uv run agent issues duplicates
uv run agent cache prune
uv run agent vacuum run
```

---

## 🎯 Best Practices

### 1. **Always Start with Context**
   - Run `atlas scan` and `issues stats` before starting work
   - Use `agent search` to find related work across all skills
   - Search specific skills when you know where to look

### 2. **Create Issues First, Code Second**
   - Break down work into trackable issues
   - Set up dependencies to maintain order
   - Use planner to prioritize work

### 3. **Document Decisions in Notes**
   - Tag notes with issue IDs
   - Include "why" not just "what"
   - Makes knowledge searchable later

### 4. **Record Feedback Always**
   - Success or failure, record it
   - Builds learning over time
   - Helps avoid repeating mistakes

### 5. **Use Templates for Consistency**
   - Save issue templates for common patterns
   - Register prompt templates for repetitive tasks
   - Reduces cognitive load

### 6. **Maintain Clean State**
   - Regular cleanup of stale issues
   - Compact old low-priority items
   - Prune expired cache
   - Run vacuum periodically

### 7. **Leverage Dependencies**
   - Block issues that depend on others
   - Use `issues ready` to see what's unblocked
   - Check dependency trees to understand impact

### 8. **Cache Smartly**
   - Use TTL for temporary results
   - Warmup cache for large projects
   - Prune regularly to avoid bloat

### 9. **Watch for Live Feedback**
   - Use atlas watch during active development
   - Get real-time code quality updates
   - Stop watch when done to save resources

### 10. **Export Regularly**
   - Backup issues to JSONL
   - Version control your knowledge base
   - Makes recovery easy

---

## 🚀 Quick Start Checklist

New to a project? Follow this sequence:

```bash
# 1. Initialize
uv run agent issues init

# 2. Scan codebase
uv run agent atlas scan .

# 3. Review state
uv run agent issues stats
uv run agent atlas rank

# 4. Start watching (optional)
uv run agent atlas watch src/ &

# 5. Get to work!
uv run agent issues ready
uv run agent planner next
```

---

## 📖 Skill Reference Quick Links

| Skill | Primary Use Case | Key Commands |
|-------|-----------------|--------------|
| **search** | Universal search | `search <query>`, `search --json` |
| **atlas** | Codebase analysis | `scan`, `rank`, `check`, `watch` |
| **issues** | Issue tracking | `create`, `list`, `update`, `ready`, `blocked` |
| **planner** | Task queue | `add`, `next`, `update`, `sync` |
| **notes** | Knowledge capture | `add`, `search`, `list` |
| **feedback** | Learning | `record`, `stats`, `list` |
| **prompts** | Templates | `register`, `render`, `list` |
| **cache** | Temp storage | `set`, `get`, `warmup`, `prune` |
| **temporal** | Time filters | `parse`, `filter_since`, `examples` |
| **vacuum** | Optimization | `run`, `history` |

---

## 💡 Integration Tips

### With Git Workflow

```bash
# Before starting feature branch
uv run agent issues create "Feature: X" --priority 1
git checkout -b feature/ISSUE-123

# During development
uv run agent notes add "Implementation notes..." --tags "ISSUE-123"
uv run agent cache set "build_status" "passing"

# Before commit
uv run agent atlas check

# In commit message
git commit -m "feat: implement X (ISSUE-123)"

# After merge
uv run agent issues close ISSUE-123
uv run agent feedback record "feature_x" --outcome success
```

### With CI/CD

```bash
# In CI pipeline
uv run agent atlas scan .
uv run agent atlas check
uv run agent cache set "ci_run_$BUILD_ID" "$RESULTS" --ttl 86400
```

### With Code Review

```bash
# Before review
uv run agent atlas rank
uv run agent prompts render code_review --var file=$FILE

# After review feedback
uv run agent notes add "Code review feedback: ..." --tags "review,ISSUE-123"
uv run agent issues update ISSUE-123 --add-label needs-revision
```

---

## 🎓 Learning Path

1. **Week 1**: Master basics - `issues`, `atlas`, `notes`
2. **Week 2**: Add workflow - `planner`, `feedback`
3. **Week 3**: Optimize - `cache`, `prompts`, `temporal`
4. **Week 4**: Maintain - `vacuum`, bulk operations, templates

---

**Remember**: The goal is to build a feedback loop where each task makes the next one easier. Context → Plan → Execute → Learn → Repeat.

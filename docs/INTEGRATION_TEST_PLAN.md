# Integration Test Plan for All Example Skills

## Overview

Comprehensive integration testing suite for all 12 example skills following the AGENTIC_WORKFLOW.md phases.

**Main Issue:** [issue-74489d](../issues/issue-74489d.md)

## Goals

1. **Comprehensive Coverage** - Test all skills in realistic scenarios
2. **Workflow Validation** - Verify the 5-phase agentic workflow
3. **Integration Testing** - Ensure skills work together correctly
4. **Regression Prevention** - Catch breaking changes early
5. **Documentation** - Provide examples of proper skill usage

## Skills to Test

| Skill | Phase | Primary Functions |
|-------|-------|-------------------|
| `atlas` | Phase 1 | Code scanning, ranking, quality checks |
| `search` | Phase 1 | Universal search across skills |
| `notes` | Phase 1 | Knowledge capture and retrieval |
| `issues` | Phase 2 | Issue tracking and management |
| `planner` | Phase 2 | Task queue and prioritization |
| `cache` | Phase 3 | TTL-based caching |
| `prompts` | Phase 3 | Template management |
| `temporal` | Phase 3 | Time-based filtering |
| `feedback` | Phase 4 | Learning and outcomes |
| `automations` | Phase 4 | Event-driven actions |
| `ai` | Phase 4 | LLM integration |
| `vacuum` | Phase 5 | Knowledge distillation |
| `migrate` | Phase 5 | Data export/import |

## Task Breakdown

### Task 1: Setup Infrastructure [issue-5cc5e4]

**Priority:** High (must complete first)

**Deliverables:**
- `tests/integration/conftest.py` - Common fixtures
- `tests/integration/helpers.py` - Test utilities
- Base test class with standard assertions

**Fixtures needed:**
```python
@pytest.fixture
def isolated_db() -> Connection:
    """Isolated test database."""

@pytest.fixture
def test_context(isolated_db) -> SkillContext:
    """Test context with fresh DB."""

@pytest.fixture
def loaded_skills(test_context) -> dict[str, Any]:
    """All skills loaded and initialized."""

@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer CLI test runner."""
```

**Helpers needed:**
- `invoke_skill_command(skill, command, args)` - Execute CLI commands
- `verify_event_published(topic, data)` - Check event bus
- `assert_db_table_exists(table_name)` - DB inspection
- `create_test_issue()` - Test data factory
- `create_test_note()` - Test data factory

### Task 2: Context Gathering Tests [issue-b98068]

**Dependencies:** Task 1

**Skills:** atlas, search, notes

**Test Cases:**

#### Atlas Tests
```python
def test_atlas_scan_codebase()
def test_atlas_rank_refactor_priorities()
def test_atlas_check_quality_rules()
def test_atlas_query_codebase()
def test_atlas_watch_mode()
```

#### Search Tests
```python
def test_search_across_all_skills()
def test_search_with_limit()
def test_search_json_output()
def test_search_relevance_scoring()
```

#### Notes Tests
```python
def test_notes_add_with_tags()
def test_notes_search_by_query()
def test_notes_list_recent()
def test_notes_search_api()
```

### Task 3: Planning Tests [issue-0bc3aa]

**Dependencies:** Task 1

**Skills:** issues, planner

**Test Cases:**

#### Issues Tests
```python
def test_issues_create_with_metadata()
def test_issues_update_status()
def test_issues_list_with_filters()
def test_issues_ready_unblocked()
def test_issues_blocked_by_deps()
def test_issues_dependencies_add()
def test_issues_dependencies_tree()
def test_issues_dependencies_cycles()
def test_issues_bulk_operations()
def test_issues_templates()
def test_issues_stale_detection()
def test_issues_duplicates()
def test_issues_export_import()
```

#### Planner Tests
```python
def test_planner_add_task()
def test_planner_next_priority()
def test_planner_update_status()
def test_planner_list_queue()
```

### Task 4: Execution Tests [issue-4d28af]

**Dependencies:** Task 1

**Skills:** cache, prompts, temporal

**Test Cases:**

#### Cache Tests
```python
def test_cache_set_get()
def test_cache_ttl_expiration()
def test_cache_prune_expired()
def test_cache_warmup()
def test_cache_delete()
def test_cache_clear()
```

#### Prompts Tests
```python
def test_prompts_register_template()
def test_prompts_render_with_variables()
def test_prompts_list_templates()
def test_prompts_update_template()
```

#### Temporal Tests
```python
def test_temporal_parse_relative()
def test_temporal_parse_absolute()
def test_temporal_filter_since()
def test_temporal_examples()
```

### Task 5: Feedback Tests [issue-9e3092]

**Dependencies:** Task 1

**Skills:** feedback, automations, ai

**Test Cases:**

#### Feedback Tests
```python
def test_feedback_record_success()
def test_feedback_record_failure()
def test_feedback_stats()
def test_feedback_list()
def test_feedback_search_api()
```

#### Automations Tests
```python
def test_automations_create()
def test_automations_trigger_on_event()
def test_automations_list()
def test_automations_disable()
```

#### AI Tests
```python
def test_ai_embeddings_if_available()
def test_ai_query_if_available()
def test_ai_graceful_degradation()
```

### Task 6: Knowledge Management Tests [issue-927386]

**Dependencies:** Task 1

**Skills:** vacuum, migrate

**Test Cases:**

#### Vacuum Tests
```python
def test_vacuum_run_distillation()
def test_vacuum_history()
def test_vacuum_stats()
```

#### Migrate Tests
```python
def test_migrate_export()
def test_migrate_import()
def test_migrate_backup_restore()
```

### Task 7: Cross-Skill Workflows [issue-5f8ca7]

**Dependencies:** Tasks 2-6

**Test complete workflows across multiple skills**

**Test Cases:**

#### Workflow 1: Issue Lifecycle
```python
def test_workflow_issue_to_completion():
    """
    1. Create issue with issues skill
    2. Add to planner queue
    3. Get next task from planner
    4. Update issue status
    5. Record feedback
    6. Verify events published
    """
```

#### Workflow 2: Code Quality to Issues
```python
def test_workflow_atlas_to_issues():
    """
    1. Atlas scans codebase
    2. Finds quality violations
    3. Publishes scan_ready event
    4. Automation creates issues for violations
    5. Issues added to planner
    """
```

#### Workflow 3: Universal Search
```python
def test_workflow_search_all_skills():
    """
    1. Create data in multiple skills
    2. Search for common term
    3. Verify results from all skills
    4. Check relevance scoring
    """
```

#### Workflow 4: Event-Driven Automation
```python
def test_workflow_event_chain():
    """
    1. Create automation listening to issue_created
    2. Create issue
    3. Verify automation triggered
    4. Check downstream effects
    """
```

#### Workflow 5: Knowledge Lifecycle
```python
def test_workflow_knowledge_management():
    """
    1. Create issues and notes
    2. Run vacuum to distill
    3. Export with migrate
    4. Clear database
    5. Import back
    6. Verify data integrity
    """
```

## Testing Strategy

### Isolation

- Each test uses isolated database
- Reset context between tests
- Clean up test data after each test
- Use temporary directories for file operations

### Assertion Patterns

```python
# Standard assertions
assert result is not None
assert len(items) > 0
assert "expected" in output

# DB assertions
assert_table_exists("issues")
assert_row_count("notes", 5)
assert_column_value("issues", "id", issue_id, "status", "open")

# Event assertions
assert_event_published("issue_created", {"id": issue_id})
assert_event_count("scan_ready", 1)

# CLI assertions
assert_exit_code(result, 0)
assert_output_contains(result, "success")
assert_json_output(result, {"status": "ok"})
```

### Coverage Goals

- **Line Coverage:** 80%+ for integration tests
- **Skill Coverage:** All 12 skills tested
- **Workflow Coverage:** All 5 phases validated
- **Permission Coverage:** Test restricted contexts

### Test Execution

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific phase
uv run pytest tests/integration/test_phase1_context.py -v

# Run with coverage
uv run pytest tests/integration/ --cov=src --cov-report=html

# Run workflows only
uv run pytest tests/integration/test_workflows.py -v

# Parallel execution
uv run pytest tests/integration/ -n auto
```

## Success Criteria

- [ ] All 12 skills have integration tests
- [ ] All 5 workflow phases covered
- [ ] Cross-skill workflows tested
- [ ] Event bus integration verified
- [ ] Permission system validated
- [ ] 80%+ integration test coverage
- [ ] All tests pass in CI/CD
- [ ] Documentation complete

## Timeline Estimate

| Task | Effort | Dependencies |
|------|--------|-------------|
| Setup Infrastructure | 4 hours | None |
| Context Gathering Tests | 3 hours | Infrastructure |
| Planning Tests | 4 hours | Infrastructure |
| Execution Tests | 3 hours | Infrastructure |
| Feedback Tests | 3 hours | Infrastructure |
| Knowledge Management | 2 hours | Infrastructure |
| Cross-Skill Workflows | 4 hours | All phase tests |
| **Total** | **23 hours** | Sequential |

## Related Documentation

- [AGENTIC_WORKFLOW.md](../AGENTIC_WORKFLOW.md) - Workflow reference
- [SECURITY.md](../docs/SECURITY.md) - Permission system
- [pytest documentation](https://docs.pytest.org/) - Testing framework

## Notes

- Use `@pytest.mark.integration` for all integration tests
- Use `@pytest.mark.slow` for tests >2 seconds
- Mock external dependencies (network, filesystem when not testing those)
- Keep tests idempotent and independent
- Use descriptive test names: `test_<skill>_<action>_<expected_result>`

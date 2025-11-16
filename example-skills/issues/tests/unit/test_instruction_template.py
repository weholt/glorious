"""Tests for instruction template parser and manager."""

from pathlib import Path

import pytest

from issue_tracker.templates.instruction_template import (
    InstructionTemplate,
    InstructionTemplateManager,
    InstructionTemplateParser,
    TaskDefinition,
)


def test_task_definition_defaults():
    """Test TaskDefinition default values."""
    task = TaskDefinition(number=1, title="Test Task")
    assert task.number == 1
    assert task.title == "Test Task"
    assert task.priority == "medium"
    assert task.effort == "medium"
    assert task.description == ""
    assert task.subtasks == []
    assert task.acceptance_criteria == []


def test_instruction_template_defaults():
    """Test InstructionTemplate default values."""
    template = InstructionTemplate(name="test", title="Test", description="Test desc")
    assert template.name == "test"
    assert template.title == "Test"
    assert template.description == "Test desc"
    assert template.overview == ""
    assert template.tasks == []
    assert template.notes == []
    assert template.file_path is None


def test_parser_parse_basic():
    """Test parsing basic template."""
    content = """# Template: Test Template
**Description**: This is a test

## Overview
Test overview

### 1. First Task
**Priority**: high
**Effort**: 3

Task description here
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert template.name == "test"
    assert template.title == "Test Template"
    assert template.description == "This is a test"
    assert "Test overview" in template.overview
    assert len(template.tasks) == 1
    assert template.tasks[0].number == 1
    assert template.tasks[0].title == "First Task"


def test_parser_without_template_prefix():
    """Test parsing template without 'Template:' prefix."""
    content = """# Simple Title
**Description**: Simple description
"""
    template = InstructionTemplateParser.parse(content, "simple")
    assert template.title == "Simple Title"
    assert template.description == "Simple description"


def test_parser_parse_tasks():
    """Test parsing multiple tasks."""
    content = """# Test

### 1. Task One
**Priority**: high
**Estimated Effort**: 5
**Description**: Task one description

**Subtasks**:
- [ ] Subtask A
- [ ] Subtask B

**Acceptance Criteria**:
- Criterion 1
- Criterion 2

### 2. Task Two
**Priority**: low
**Estimated Effort**: 2
**Description**: Task two description
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert len(template.tasks) == 2
    
    task1 = template.tasks[0]
    assert task1.number == 1
    assert task1.title == "Task One"
    assert task1.priority == "high"
    assert task1.effort == "5"
    assert "Task one description" in task1.description
    assert len(task1.subtasks) == 2
    assert task1.subtasks[0] == "Subtask A"
    assert len(task1.acceptance_criteria) == 2
    
    task2 = template.tasks[1]
    assert task2.number == 2
    assert task2.title == "Task Two"


def test_parser_parse_notes():
    """Test parsing notes section."""
    content = """# Test

## Notes
- Note one
- Note two
- Note three
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert len(template.notes) == 3
    assert template.notes[0] == "Note one"
    assert template.notes[1] == "Note two"


def test_template_manager_list_templates(tmp_path):
    """Test listing templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    # Create test templates
    (templates_dir / "test1.md").write_text("# Template: Test One\n**Description**: First")
    (templates_dir / "test2.md").write_text("# Template: Test Two\n**Description**: Second")
    (templates_dir / "not-template.txt").write_text("Not a template")
    
    manager = InstructionTemplateManager(templates_dir)
    templates = manager.list_templates()
    
    assert len(templates) == 2
    names = [t[0] for t in templates]
    assert "test1" in names
    assert "test2" in names


def test_template_manager_list_templates_empty(tmp_path):
    """Test listing templates in empty directory."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    manager = InstructionTemplateManager(templates_dir)
    templates = manager.list_templates()
    
    assert len(templates) == 0


def test_template_manager_load_template(tmp_path):
    """Test loading a template."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    content = """# Template: Test Template
**Description**: Test description

### 1. Task One
**Priority**: high

Task description
"""
    (templates_dir / "test.md").write_text(content)
    
    manager = InstructionTemplateManager(templates_dir)
    template = manager.load_template("test")
    
    assert template is not None
    assert template.name == "test"
    assert template.title == "Test Template"
    assert len(template.tasks) == 1


def test_template_manager_load_nonexistent(tmp_path):
    """Test loading non-existent template."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    manager = InstructionTemplateManager(templates_dir)
    template = manager.load_template("missing")
    
    assert template is None


def test_template_manager_get_template_content(tmp_path):
    """Test getting raw template content."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    content = "# Test Content"
    (templates_dir / "test.md").write_text(content)
    
    manager = InstructionTemplateManager(templates_dir)
    result = manager.get_template_content("test")
    
    assert result == content


def test_template_manager_get_content_nonexistent(tmp_path):
    """Test getting content of non-existent template."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    manager = InstructionTemplateManager(templates_dir)
    result = manager.get_template_content("missing")
    
    assert result is None


def test_template_manager_creates_directory(tmp_path):
    """Test manager creates templates directory if missing."""
    templates_dir = tmp_path / "templates"
    
    manager = InstructionTemplateManager(templates_dir)
    templates = manager.list_templates()
    
    assert templates_dir.exists()
    assert len(templates) == 0


def test_parser_without_description():
    """Test parsing template without description."""
    content = """# Test Template

### 1. Task One
Task description
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert template.title == "Test Template"
    assert template.description == ""


def test_parser_without_overview():
    """Test parsing template without overview section."""
    content = """# Test
**Description**: Test desc

### 1. Task
Task body
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert template.overview == ""


def test_parser_task_without_priority():
    """Test parsing task without priority."""
    content = """# Test

### 1. Task
Task description
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert len(template.tasks) == 1
    assert template.tasks[0].priority == "medium"


def test_parser_task_without_description():
    """Test parsing task without description."""
    content = """# Test

### 1. Task
**Priority**: high
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert len(template.tasks) == 1
    assert template.tasks[0].description == ""


def test_parser_without_notes():
    """Test parsing template without notes."""
    content = """# Test

### 1. Task
Task body
"""
    template = InstructionTemplateParser.parse(content, "test")
    assert template.notes == []

"""Tests for instruction template commands."""

import json

import pytest
from typer.testing import CliRunner

from issue_tracker.cli.commands.instructions import app

runner = CliRunner()


@pytest.fixture
def templates_dir(tmp_path, monkeypatch):
    """Create temporary templates directory."""
    templates = tmp_path / "templates"
    templates.mkdir()

    # Mock get_issues_folder to return tmp_path
    def mock_get_issues_folder():
        return str(tmp_path)

    # Patch where it's imported (in the module)
    from issue_tracker.cli import dependencies

    monkeypatch.setattr(dependencies, "get_issues_folder", mock_get_issues_folder)

    return templates


def test_list_templates_empty(templates_dir):
    """Test listing templates when none exist."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No instruction templates found" in result.stdout


def test_list_templates_with_templates(templates_dir):
    """Test listing templates."""
    (templates_dir / "template1.md").write_text("# Template: Test One\n**Description**: First")
    (templates_dir / "template2.md").write_text("# Template: Test Two\n**Description**: Second")

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "template1" in result.stdout
    assert "Test One" in result.stdout
    assert "template2" in result.stdout


def test_list_templates_json(templates_dir):
    """Test listing templates as JSON."""
    (templates_dir / "template1.md").write_text("# Template: Test One\n**Description**: First")

    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) == 1
    assert data[0]["name"] == "template1"
    assert data[0]["title"] == "Test One"


def test_show_template_raw(templates_dir):
    """Test showing template raw content."""
    content = "# Template Content"
    (templates_dir / "test.md").write_text(content)

    result = runner.invoke(app, ["show", "test", "--raw"])
    assert result.exit_code == 0
    assert content in result.stdout


def test_show_template_raw_not_found(templates_dir):
    """Test showing non-existent template."""
    result = runner.invoke(app, ["show", "missing", "--raw"])
    assert result.exit_code == 1
    assert "not found" in result.stdout or "not found" in result.stderr


def test_show_template_parsed(templates_dir):
    """Test showing parsed template."""
    content = """# Template: Test Template
**Description**: Test description

## Overview
Test overview

### 1. Task One
**Priority**: high
**Estimated Effort**: 3
**Description**: Task one description

**Subtasks**:
- [ ] Subtask 1

## Notes
- Note 1
- Note 2
"""
    (templates_dir / "test.md").write_text(content)

    result = runner.invoke(app, ["show", "test"])
    assert result.exit_code == 0
    assert "Test Template" in result.stdout
    assert "Task One" in result.stdout
    assert "high" in result.stdout


def test_show_template_json(templates_dir):
    """Test showing template as JSON."""
    content = """# Template: Test Template
**Description**: Test description

### 1. Task One
**Priority**: high
**Estimated Effort**: 3
**Description**: Task description
"""
    (templates_dir / "test.md").write_text(content)

    result = runner.invoke(app, ["show", "test", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["name"] == "test"
    assert data["title"] == "Test Template"
    assert len(data["tasks"]) == 1


def test_show_template_not_found(templates_dir):
    """Test showing non-existent parsed template."""
    result = runner.invoke(app, ["show", "missing"])
    assert result.exit_code == 1
    assert "not found" in result.stdout or "not found" in result.stderr

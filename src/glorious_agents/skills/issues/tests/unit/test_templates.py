"""Tests for template module."""

import json
from pathlib import Path

import pytest


class TestTemplate:
    """Test basic Template class."""

    def test_create_template(self):
        """Test creating a basic template."""
        from issue_tracker.templates.template_manager import Template

        template = Template(
            name="test",
            title="Test Issue",
            description="Test description",
            type="bug",
            priority=1,
            labels=["urgent", "backend"],
            assignee="alice",
        )

        assert template.name == "test"
        assert template.title == "Test Issue"
        assert template.type == "bug"
        assert template.priority == 1
        assert template.labels == ["urgent", "backend"]
        assert template.assignee == "alice"

    def test_template_defaults(self):
        """Test template with default values."""
        from issue_tracker.templates.template_manager import Template

        template = Template(name="minimal")

        assert template.name == "minimal"
        assert template.title == ""
        assert template.description == ""
        assert template.type == "task"
        assert template.priority == 2
        assert template.labels == []
        assert template.assignee is None

    def test_template_to_dict(self):
        """Test converting template to dictionary."""
        from issue_tracker.templates.template_manager import Template

        template = Template(
            name="test",
            title="Test",
            labels=["tag1", "tag2"],
        )

        data = template.to_dict()

        assert data["name"] == "test"
        assert data["title"] == "Test"
        assert data["labels"] == ["tag1", "tag2"]
        assert "type" in data
        assert "priority" in data

    def test_template_from_dict(self):
        """Test creating template from dictionary."""
        from issue_tracker.templates.template_manager import Template

        data = {
            "name": "fromdict",
            "title": "From Dict",
            "description": "Created from dict",
            "type": "feature",
            "priority": 0,
            "labels": ["new"],
            "assignee": "bob",
        }

        template = Template.from_dict(data)

        assert template.name == "fromdict"
        assert template.title == "From Dict"
        assert template.type == "feature"
        assert template.priority == 0
        assert template.assignee == "bob"

    def test_template_from_dict_with_defaults(self):
        """Test creating template from dict with missing fields."""
        from issue_tracker.templates.template_manager import Template

        data = {"name": "minimal"}

        template = Template.from_dict(data)

        assert template.name == "minimal"
        assert template.title == ""
        assert template.type == "task"
        assert template.priority == 2


class TestTemplateManager:
    """Test template manager functionality."""

    def test_save_and_load_template(self, tmp_path: Path):
        """Test saving and loading a template."""
        from issue_tracker.templates.template_manager import Template, TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        template = Template(
            name="test",
            title="Test Issue",
            description="A test template",
            type="task",
            priority=2,
            labels=["test"],
        )

        manager.save_template(template)
        loaded = manager.load_template("test")

        assert loaded is not None
        assert loaded.name == "test"
        assert loaded.title == "Test Issue"
        assert loaded.description == "A test template"
        assert loaded.labels == ["test"]

    def test_load_nonexistent_template(self, tmp_path: Path):
        """Test loading a template that doesn't exist."""
        from issue_tracker.templates.template_manager import TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        template = manager.load_template("nonexistent")

        assert template is None

    def test_list_templates(self, tmp_path: Path):
        """Test listing available templates."""
        from issue_tracker.templates.template_manager import Template, TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        manager.save_template(Template(name="first", title="First"))
        manager.save_template(Template(name="second", title="Second"))
        manager.save_template(Template(name="third", title="Third"))

        templates = manager.list_templates()

        assert len(templates) == 3
        assert "first" in templates
        assert "second" in templates
        assert "third" in templates

    def test_list_templates_empty_dir(self, tmp_path: Path):
        """Test listing templates in empty directory."""
        from issue_tracker.templates.template_manager import TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        templates = manager.list_templates()

        assert len(templates) == 0

    def test_delete_template(self, tmp_path: Path):
        """Test deleting a template."""
        from issue_tracker.templates.template_manager import Template, TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        manager.save_template(Template(name="todelete", title="Delete Me"))

        # Verify it exists
        assert manager.load_template("todelete") is not None

        # Delete it
        result = manager.delete_template("todelete")
        assert result is True

        # Verify it's gone
        assert manager.load_template("todelete") is None

    def test_delete_nonexistent_template(self, tmp_path: Path):
        """Test deleting a template that doesn't exist."""
        from issue_tracker.templates.template_manager import TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        result = manager.delete_template("nonexistent")
        assert result is False

    def test_template_manager_creates_dir(self, tmp_path: Path):
        """Test that template manager creates directory if it doesn't exist."""
        from issue_tracker.templates.template_manager import TemplateManager

        templates_dir = tmp_path / "new" / "templates"

        # Directory doesn't exist yet
        assert not templates_dir.exists()

        # Manager should create it
        manager = TemplateManager(templates_dir)

        assert templates_dir.exists()
        assert templates_dir.is_dir()

    def test_save_template_with_all_fields(self, tmp_path: Path):
        """Test saving template with all possible fields."""
        from issue_tracker.templates.template_manager import Template, TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        template = Template(
            name="complete",
            title="Complete Template",
            description="Has all fields",
            type="feature",
            priority=0,
            labels=["ui", "ux", "frontend"],
            assignee="alice",
        )

        manager.save_template(template)
        loaded = manager.load_template("complete")

        assert loaded is not None
        assert loaded.title == "Complete Template"
        assert loaded.description == "Has all fields"
        assert loaded.type == "feature"
        assert loaded.priority == 0
        assert loaded.labels == ["ui", "ux", "frontend"]
        assert loaded.assignee == "alice"

    def test_overwrite_existing_template(self, tmp_path: Path):
        """Test overwriting an existing template."""
        from issue_tracker.templates.template_manager import Template, TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)

        # Save initial template
        template1 = Template(name="test", title="Original")
        manager.save_template(template1)

        # Save updated template with same name
        template2 = Template(name="test", title="Updated")
        manager.save_template(template2)

        # Load and verify it's the updated version
        loaded = manager.load_template("test")
        assert loaded is not None
        assert loaded.title == "Updated"

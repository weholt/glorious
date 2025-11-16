"""Template manager for issue creation templates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Template:
    """Template for creating issues with predefined defaults."""

    name: str
    title: str = ""
    description: str = ""
    type: str = "task"
    priority: int = 2
    labels: list[str] = field(default_factory=list)
    assignee: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "priority": self.priority,
            "labels": self.labels,
            "assignee": self.assignee,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Template:
        """Create template from dictionary."""
        return cls(
            name=data["name"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            type=data.get("type", "task"),
            priority=data.get("priority", 2),
            labels=data.get("labels", []),
            assignee=data.get("assignee"),
        )


class TemplateManager:
    """Manages issue templates."""

    def __init__(self, templates_dir: Path):
        """Initialize template manager.

        Args:
            templates_dir: Directory to store template files
        """
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def save_template(self, template: Template) -> None:
        """Save a template to disk.

        Args:
            template: Template to save
        """
        template_file = self.templates_dir / f"{template.name}.json"
        with open(template_file, "w") as f:
            json.dump(template.to_dict(), f, indent=2)

    def load_template(self, name: str) -> Template | None:
        """Load a template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        template_file = self.templates_dir / f"{name}.json"
        if not template_file.exists():
            return None

        with open(template_file) as f:
            data = json.load(f)
        return Template.from_dict(data)

    def list_templates(self) -> list[str]:
        """List all available template names.

        Returns:
            List of template names
        """
        return [f.stem for f in self.templates_dir.glob("*.json")]

    def delete_template(self, name: str) -> bool:
        """Delete a template.

        Args:
            name: Template name

        Returns:
            True if deleted, False if not found
        """
        template_file = self.templates_dir / f"{name}.json"
        if template_file.exists():
            template_file.unlink()
            return True
        return False

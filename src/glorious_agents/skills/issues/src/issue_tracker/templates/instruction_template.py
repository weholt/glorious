"""Instruction template manager for complex task workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["TaskDefinition", "InstructionTemplate", "InstructionTemplateParser", "InstructionTemplateManager"]


@dataclass
class TaskDefinition:
    """Definition of a task from an instruction template."""

    number: int
    title: str
    priority: str = "medium"
    effort: str = "medium"
    description: str = ""
    subtasks: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass
class InstructionTemplate:
    """Template containing instructions for complex workflows."""

    name: str
    title: str
    description: str
    overview: str = ""
    tasks: list[TaskDefinition] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    file_path: Path | None = None


class InstructionTemplateParser:
    """Parser for markdown instruction templates."""

    @staticmethod
    def parse(content: str, name: str, file_path: Path | None = None) -> InstructionTemplate:
        """Parse markdown template content.

        Args:
            content: Markdown template content
            name: Template name
            file_path: Optional path to template file

        Returns:
            Parsed instruction template
        """
        template = InstructionTemplate(name=name, title="", description="", file_path=file_path)

        # Parse header
        title_match = re.search(r"^#\s+(?:Template:\s+)?(.+)", content, re.MULTILINE)
        if title_match:
            template.title = title_match.group(1).strip()

        desc_match = re.search(r"\*\*Description\*\*:\s*(.+)", content, re.MULTILINE)
        if desc_match:
            template.description = desc_match.group(1).strip()

        # Parse overview
        overview_match = re.search(r"##\s+Overview\s*\n+(.*?)(?=\n##|\Z)", content, re.DOTALL | re.MULTILINE)
        if overview_match:
            template.overview = overview_match.group(1).strip()

        # Parse tasks
        task_sections = re.finditer(r"###\s+(\d+)\.\s+(.+?)\n(.*?)(?=\n###|\n##|\Z)", content, re.DOTALL | re.MULTILINE)

        for match in task_sections:
            task_num = int(match.group(1))
            task_title = match.group(2).strip()
            task_content = match.group(3)

            task = TaskDefinition(number=task_num, title=task_title)

            # Extract priority
            priority_match = re.search(r"\*\*Priority\*\*:\s*(\w+)", task_content)
            if priority_match:
                task.priority = priority_match.group(1).lower()

            # Extract effort
            effort_match = re.search(r"\*\*Estimated Effort\*\*:\s*(\w+)", task_content)
            if effort_match:
                task.effort = effort_match.group(1).lower()

            # Extract description
            desc_match = re.search(r"\*\*Description\*\*:\s*(.+?)(?=\n\*\*|\Z)", task_content, re.DOTALL)
            if desc_match:
                task.description = desc_match.group(1).strip()

            # Extract subtasks
            subtasks_match = re.search(r"\*\*Subtasks\*\*:\s*\n((?:- \[[ x]\].+\n?)+)", task_content, re.MULTILINE)
            if subtasks_match:
                subtask_lines = subtasks_match.group(1).strip().split("\n")
                task.subtasks = [re.sub(r"^- \[[ x]\]\s*", "", line.strip()) for line in subtask_lines if line.strip()]

            # Extract acceptance criteria
            criteria_match = re.search(r"\*\*Acceptance Criteria\*\*:\s*\n((?:-.+\n?)+)", task_content, re.MULTILINE)
            if criteria_match:
                criteria_lines = criteria_match.group(1).strip().split("\n")
                task.acceptance_criteria = [
                    re.sub(r"^-\s*", "", line.strip()) for line in criteria_lines if line.strip()
                ]

            template.tasks.append(task)

        # Parse notes section
        notes_match = re.search(r"##\s+Notes\s*\n+(.*?)(?=\n##|\Z)", content, re.DOTALL | re.MULTILINE)
        if notes_match:
            note_lines = notes_match.group(1).strip().split("\n")
            template.notes = [
                re.sub(r"^-\s*", "", line.strip())
                for line in note_lines
                if line.strip() and line.strip().startswith("-")
            ]

        return template


class InstructionTemplateManager:
    """Manager for instruction-based templates."""

    def __init__(self, templates_dir: Path) -> None:
        """Initialize instruction template manager.

        Args:
            templates_dir: Directory containing markdown template files
        """
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, name: str) -> InstructionTemplate | None:
        """Load an instruction template by name.

        Args:
            name: Template name (without .md extension)

        Returns:
            Parsed template or None if not found
        """
        template_file = self.templates_dir / f"{name}.md"
        if not template_file.exists():
            return None

        content = template_file.read_text(encoding="utf-8")
        return InstructionTemplateParser.parse(content, name, template_file)

    def list_templates(self) -> list[tuple[str, str]]:
        """List all available instruction templates.

        Returns:
            List of (name, title) tuples
        """
        templates = []
        for md_file in self.templates_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue

            name = md_file.stem
            # Quick parse for title only
            content = md_file.read_text(encoding="utf-8")
            title_match = re.search(r"^#\s+(?:Template:\s+)?(.+)", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else name

            templates.append((name, title))

        return sorted(templates)

    def get_template_content(self, name: str) -> str | None:
        """Get raw template content.

        Args:
            name: Template name

        Returns:
            Raw markdown content or None if not found
        """
        template_file = self.templates_dir / f"{name}.md"
        if not template_file.exists():
            return None

        return template_file.read_text(encoding="utf-8")

    def save_template(self, name: str, content: str) -> None:
        """Save a template file.

        Args:
            name: Template name (without .md extension)
            content: Markdown content
        """
        template_file = self.templates_dir / f"{name}.md"
        template_file.write_text(content, encoding="utf-8")

    def delete_template(self, name: str) -> bool:
        """Delete a template.

        Args:
            name: Template name

        Returns:
            True if deleted, False if not found
        """
        template_file = self.templates_dir / f"{name}.md"
        if template_file.exists():
            template_file.unlink()
            return True
        return False

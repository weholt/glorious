"""Instructions template commands."""

import json
from typing import Any

import typer

from issue_tracker.domain import DependencyType

app = typer.Typer(
    name="instructions",
    help="Manage instruction templates for workflows",
    no_args_is_help=True,
)

__all__ = ["app", "list_templates", "apply_template"]


def get_issue_service() -> Any:
    """Import and return issue service (avoids circular import)."""
    from issue_tracker.cli.app import get_issue_service as _get_issue_service

    return _get_issue_service()


@app.command(name="list")
def list_templates(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all available instruction templates."""
    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_issues_folder
        from issue_tracker.templates.instruction_template import InstructionTemplateManager

        issues_folder = Path(get_issues_folder())
        templates_dir = issues_folder / "templates"
        manager = InstructionTemplateManager(templates_dir)

        templates = manager.list_templates()

        if json_output:
            typer.echo(json.dumps([{"name": name, "title": title} for name, title in templates]))
        else:
            if not templates:
                typer.echo("No instruction templates found")
                typer.echo(f"\nAdd markdown templates to: {templates_dir}")
            else:
                typer.echo("Available instruction templates:\n")
                for name, title in templates:
                    typer.echo(f"  {name}")
                    typer.echo(f"    {title}\n")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="show")
def show_template(
    name: str = typer.Argument(..., help="Template name"),
    raw: bool = typer.Option(False, "--raw", help="Show raw markdown"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Display an instruction template."""
    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_issues_folder
        from issue_tracker.templates.instruction_template import InstructionTemplateManager

        issues_folder = Path(get_issues_folder())
        templates_dir = issues_folder / "templates"
        manager = InstructionTemplateManager(templates_dir)

        if raw:
            content = manager.get_template_content(name)
            if content is None:
                typer.echo(f"Template '{name}' not found", err=True)
                raise typer.Exit(1)
            typer.echo(content)
        else:
            template = manager.load_template(name)
            if template is None:
                typer.echo(f"Template '{name}' not found", err=True)
                raise typer.Exit(1)

            if json_output:
                output = {
                    "name": template.name,
                    "title": template.title,
                    "description": template.description,
                    "overview": template.overview,
                    "tasks": [
                        {
                            "number": t.number,
                            "title": t.title,
                            "priority": t.priority,
                            "effort": t.effort,
                            "description": t.description,
                            "subtasks": t.subtasks,
                            "acceptance_criteria": t.acceptance_criteria,
                        }
                        for t in template.tasks
                    ],
                    "notes": template.notes,
                }
                typer.echo(json.dumps(output, indent=2))
            else:
                typer.echo(f"# {template.title}\n")
                typer.echo(f"{template.description}\n")

                if template.overview:
                    typer.echo(f"## Overview\n{template.overview}\n")

                typer.echo(f"## Tasks ({len(template.tasks)} total)\n")
                for task in template.tasks:
                    typer.echo(f"{task.number}. {task.title}")
                    typer.echo(f"   Priority: {task.priority} | Effort: {task.effort}")
                    if task.subtasks:
                        typer.echo(f"   Subtasks: {len(task.subtasks)}")
                    typer.echo()

                if template.notes:
                    typer.echo("## Notes")
                    for note in template.notes:
                        typer.echo(f"  - {note}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="apply")
def apply_template(
    name: str = typer.Argument(..., help="Template name"),
    epic_title: str | None = typer.Option(None, "--epic", help="Create epic with this title"),
    prefix: str | None = typer.Option(None, "--prefix", help="Prefix for issue titles"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be created"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Apply instruction template by creating issues from tasks."""
    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_issues_folder
        from issue_tracker.templates.instruction_template import InstructionTemplateManager

        issues_folder = Path(get_issues_folder())
        templates_dir = issues_folder / "templates"
        manager = InstructionTemplateManager(templates_dir)

        template = manager.load_template(name)
        if template is None:
            typer.echo(f"Template '{name}' not found", err=True)
            raise typer.Exit(1)

        created_issues = []
        epic_id = None

        # Create service once for all operations (avoid multiple sessions)
        if not dry_run:
            service = get_issue_service()

        # Create epic if requested
        if epic_title and not dry_run:
            from issue_tracker.domain import IssueType

            epic = service.create_issue(
                title=epic_title,
                type=IssueType.EPIC,
                description=f"{template.description}\n\n{template.overview}",
            )
            epic_id = epic.id
            created_issues.append({"type": "epic", "id": epic.id, "title": epic.title})

        # Create issues from tasks
        priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3, "backlog": 4}

        for task in template.tasks:
            issue_title = f"{prefix} {task.title}" if prefix else task.title

            # Build description
            desc_parts = [task.description]
            if task.subtasks:
                desc_parts.append("\n## Subtasks")
                for subtask in task.subtasks:
                    desc_parts.append(f"- [ ] {subtask}")
            if task.acceptance_criteria:
                desc_parts.append("\n## Acceptance Criteria")
                for criterion in task.acceptance_criteria:
                    desc_parts.append(f"- {criterion}")

            issue_desc = "\n".join(desc_parts)
            priority_num = priority_map.get(task.priority, 2)

            if dry_run:
                created_issues.append(
                    {
                        "type": "task",
                        "title": issue_title,
                        "priority": task.priority,
                        "effort": task.effort,
                        "epic": epic_title if epic_title else None,
                    }
                )
            else:
                issue = service.create_issue(
                    title=issue_title,
                    description=issue_desc,
                    priority=priority_num,
                )

                # Link to epic if created (tasks depend on their epic)
                if epic_id:
                    service.add_dependency(issue.id, epic_id, DependencyType.DEPENDS_ON)

                created_issues.append({"type": "task", "id": issue.id, "title": issue.title, "priority": task.priority})

        if json_output:
            typer.echo(json.dumps({"template": name, "issues": created_issues}))
        else:
            if dry_run:
                typer.echo(f"Would create from template '{name}':\n")
                if epic_title:
                    typer.echo(f"Epic: {epic_title}")
                typer.echo(f"\n{len(template.tasks)} tasks:")
                for issue in created_issues:
                    if issue["type"] == "task":
                        typer.echo(f"  - {issue['title']} [{issue['priority']}]")
            else:
                typer.echo(f"Created {len(created_issues)} issues from template '{name}'")
                if epic_id:
                    typer.echo(f"\nEpic: {epic_id}")
                for issue in created_issues:
                    if issue["type"] == "task":
                        typer.echo(f"  {issue['id']}: {issue['title']}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

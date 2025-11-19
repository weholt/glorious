"""Epic management commands."""

import builtins
import json

import typer

app = typer.Typer(name="epics", help="Manage epics")

__all__ = ["app", "add", "remove"]


@app.command(name="add")
def add(
    epic_id: str = typer.Argument(..., help="Epic ID"),
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to add"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Add issue to an epic."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        results = []
        for issue_id in issue_ids:
            # Set epic on issue
            service.set_epic(issue_id, epic_id)

            if not json_output:
                typer.echo(f"Added {issue_id} to epic {epic_id}")
            else:
                results.append({"epic_id": epic_id, "issue_id": issue_id})

        if json_output:
            typer.echo(json.dumps(results if len(results) > 1 else results[0]))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="remove")
def remove(
    epic_id: str = typer.Argument(..., help="Epic ID"),
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to remove"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Remove issue from an epic."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        results = []
        for issue_id in issue_ids:
            # Clear epic on issue
            service.clear_epic(issue_id)

            if not json_output:
                typer.echo(f"Removed {issue_id} from epic {epic_id}")
            else:
                results.append({"epic_id": epic_id, "issue_id": issue_id, "removed": True})

        if json_output:
            typer.echo(json.dumps(results if len(results) > 1 else results[0]))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="list")
def list_epic(
    epic_id: str = typer.Argument(..., help="Epic ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List issues in an epic."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Get issues by epic ID
        issues_list = service.list_issues(epic_id=epic_id)

        # Convert to dicts
        issues = [{"id": issue.id, "title": issue.title} for issue in issues_list]

        if json_output:
            typer.echo(json.dumps(issues))
        else:
            if not issues:
                typer.echo(f"No issues in epic {epic_id}")
            else:
                for issue in issues:
                    typer.echo(f"{issue['id']}: {issue['title']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="set")
def set_epic(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    epic_id: str = typer.Argument(..., help="Epic ID to assign to"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Assign issue to an epic (spec-compliant command).

    Sets the epic_id field on the specified issue.

    Examples:
        issues epics set issue-123 epic-456
        issues epics set issue-123 epic-456 --json
    """
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Set epic on issue (validates that epic exists)
        service.set_epic(issue_id, epic_id)

        # Get updated issue
        issue = service.get_issue(issue_id)

        if json_output:
            typer.echo(json.dumps({"id": issue.id, "epic_id": issue.epic_id}))
        else:
            typer.echo(f"Assigned {issue_id} to epic {epic_id}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="clear")
def clear(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Remove issue from its epic (spec-compliant command).

    Clears the epic_id field on the specified issue.

    Examples:
        issues epics clear issue-123
        issues epics clear issue-123 --json
    """
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Clear epic on issue
        service.clear_epic(issue_id)

        # Get updated issue
        issue = service.get_issue(issue_id)

        if json_output:
            typer.echo(json.dumps({"id": issue.id, "epic_id": None}))
        else:
            typer.echo(f"Cleared epic from {issue_id}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="all")
def list_all(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all epics."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Get all issues and collect unique epics
        all_issues = service.list_issues()
        epic_counts: dict[str, int] = {}

        for issue in all_issues:
            if issue.epic_id:
                epic_counts[issue.epic_id] = epic_counts.get(issue.epic_id, 0) + 1

        # Convert to list
        epics_data = [{"epic_id": eid, "issue_count": count} for eid, count in epic_counts.items()]

        if json_output:
            typer.echo(json.dumps(epics_data))
        else:
            if not epics_data:
                typer.echo("No epics found")
            else:
                for epic in epics_data:
                    typer.echo(f"{epic['epic_id']}: {epic['issue_count']} issues")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="tree")
def tree(
    epic_id: str | None = typer.Argument(None, help="Epic ID to show tree for (shows all if not specified)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show epic hierarchy tree.

    Displays epics and sub-epics in a tree structure with their issues.

    Examples:
        issues epics tree
        issues epics tree epic-testing
        issues epics tree epic-testing --json
    """
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()
        all_issues = service.list_issues()

        def build_epic_tree(parent_id: str | None = None, indent: int = 0) -> list[dict]:
            """Recursively build epic tree."""
            tree_data = []
            prefix = "  " * indent
            connector = "└── " if indent > 0 else ""

            for issue in all_issues:
                # Normalize None and "" to None for comparison
                issue_parent = issue.epic_id if issue.epic_id else None
                expected_parent = parent_id if parent_id else None

                if issue.type.value == "epic" and issue_parent == expected_parent:
                    # This is an epic at this level
                    epic_issues = [i for i in all_issues if i.epic_id == issue.id and i.type.value != "epic"]
                    issue_count = len(epic_issues)

                    epic_data = {"id": issue.id, "title": issue.title, "issue_count": issue_count, "children": []}

                    if not json_output:
                        typer.echo(f"{prefix}{connector}{issue.id}: {issue.title} ({issue_count} issues)")

                    # Recursively add child epics
                    children = build_epic_tree(issue.id, indent + 1)
                    epic_data["children"] = children

                    tree_data.append(epic_data)

            return tree_data

        if epic_id:
            # Show tree starting from specific epic
            epic = service.get_issue(epic_id)
            if not epic or epic.type.value != "epic":
                typer.echo(f"Error: {epic_id} is not an epic", err=True)
                raise typer.Exit(1)

            epic_issues = [i for i in all_issues if i.epic_id == epic_id and i.type.value != "epic"]

            if not json_output:
                typer.echo(f"{epic_id}: {epic.title} ({len(epic_issues)} issues)")

            tree_data = build_epic_tree(epic_id, 1)

            if json_output:
                typer.echo(
                    json.dumps(
                        {"id": epic_id, "title": epic.title, "issue_count": len(epic_issues), "children": tree_data}
                    )
                )
        else:
            # Show all top-level epics
            tree_data = build_epic_tree(None, 0)

            if json_output:
                typer.echo(json.dumps(tree_data))
            elif not tree_data:
                typer.echo("No epics found")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

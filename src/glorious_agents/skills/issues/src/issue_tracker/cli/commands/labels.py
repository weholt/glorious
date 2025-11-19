"""Label management commands."""

import builtins
import json

import typer

from issue_tracker.domain import IssuePriority, IssueStatus, IssueType

app = typer.Typer(name="labels", help="Manage issue labels")

__all__ = ["app", "add", "remove"]


@app.command(name="add")
def add(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    labels: builtins.list[str] = typer.Argument(..., help="Label(s) to add"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Add labels to an issue."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        issue = service.get_issue(issue_id)
        if not issue:
            typer.echo(f"Issue {issue_id} not found", err=True)
            raise typer.Exit(1)

        # Add each label
        for label_name in labels:
            issue = issue.add_label(label_name)

        service.uow.issues.save(issue)
        service.uow.session.commit()

        if not json_output:
            typer.echo(f"Added labels to {issue_id}")
        else:
            result = {
                "id": issue.id,
                "labels": issue.labels,
            }
            typer.echo(json.dumps(result))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="remove")
def remove(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    labels: builtins.list[str] = typer.Argument(..., help="Label(s) to remove"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Remove labels from an issue."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        issue = service.get_issue(issue_id)
        if not issue:
            typer.echo(f"Issue {issue_id} not found", err=True)
            raise typer.Exit(1)

        # Remove each label
        for label_name in labels:
            issue = issue.remove_label(label_name)

        service.uow.issues.save(issue)
        service.uow.session.commit()

        if not json_output:
            typer.echo(f"Removed labels from {issue_id}")
        else:
            result = {
                "id": issue.id,
                "labels": issue.labels,
            }
            typer.echo(json.dumps(result))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="set")
def set_labels(
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Set labels on an issue."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Parse labels from last argument
        labels_str = issue_ids[-1] if len(issue_ids) > 1 else ""
        ids = issue_ids[:-1] if len(issue_ids) > 1 else issue_ids
        new_labels = [label.strip() for label in labels_str.split(",") if label.strip()] if labels_str else []

        results = []
        for issue_id in ids:
            # Get current issue to determine which labels to remove
            issue = service.get_issue(issue_id)
            if not issue:
                if not json_output:
                    typer.echo(f"Issue not found: {issue_id}", err=True)
                raise typer.Exit(1)

            # Remove all current labels
            for label in issue.labels:
                service.remove_label_from_issue(issue_id, label)

            # Add new labels
            for label in new_labels:
                service.add_label_to_issue(issue_id, label)

            if not json_output:
                typer.echo(f"Set labels on {issue_id}")
            else:
                results.append({"id": issue_id, "labels": new_labels})

        if json_output:
            typer.echo(json.dumps(results[0] if len(results) == 1 else results))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="list")
def list_labels(
    issue_id: str | None = typer.Argument(None, help="Issue ID (optional - omit to list all labels)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List labels. If issue_id provided, list labels for that issue. Otherwise, list all labels with counts.

    Examples:
        issues labels list                  # List all labels with counts
        issues labels list issue-123        # List labels for specific issue
        issues labels list --json           # List all labels as JSON
    """
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        if issue_id:
            # List labels for specific issue
            issue = service.get_issue(issue_id)
            if not issue:
                typer.echo(f"Issue {issue_id} not found", err=True)
                raise typer.Exit(1)

            if json_output:
                typer.echo(json.dumps({"id": issue.id, "labels": issue.labels}))
            else:
                if not issue.labels:
                    typer.echo(f"No labels on {issue_id}")
                else:
                    typer.echo(f"Labels for {issue_id}:")
                    for label in issue.labels:
                        typer.echo(f"  {label}")
        else:
            # List all labels with counts
            issues = service.list_issues()

            # Count label usage
            label_counts: dict[str, int] = {}
            for issue in issues:
                for label in issue.labels:
                    label_counts[label] = label_counts.get(label, 0) + 1

            if json_output:
                result = [{"label": label, "count": count} for label, count in sorted(label_counts.items())]
                typer.echo(json.dumps(result))
            else:
                if not label_counts:
                    typer.echo("No labels found")
                else:
                    typer.echo("All labels:")
                    for label, count in sorted(label_counts.items()):
                        typer.echo(f"  {label}: {count}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="all")
def list_all(
    count: bool = typer.Option(False, "--count", help="Show usage counts"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all labels."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Get all unique labels from all issues
        all_issues = service.list_issues()
        label_set = set()
        label_counts: dict[str, int] = {}

        for issue in all_issues:
            for label in issue.labels:
                label_set.add(label)
                if count:
                    label_counts[label] = label_counts.get(label, 0) + 1

        # Convert to list and sort
        all_labels = sorted(list(label_set))

        if count:
            labels_with_count = [{"name": label, "count": label_counts.get(label, 0)} for label in all_labels]

            if json_output:
                typer.echo(json.dumps(labels_with_count))
            else:
                if not labels_with_count:
                    typer.echo("No labels found")
                else:
                    for item in labels_with_count:
                        typer.echo(f"{item['name']}: {item['count']}")
        else:
            label_dicts = [{"name": label} for label in all_labels]
            if json_output:
                typer.echo(json.dumps(label_dicts))
            else:
                if not all_labels:
                    typer.echo("No labels found")
                else:
                    for label in all_labels:
                        typer.echo(label["name"])
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="bulk-add")
def bulk_add(
    labels: str = typer.Argument(..., help="Comma-separated label(s) to add"),
    issue_ids: builtins.list[str] | None = typer.Argument(
        None, help="Issue ID(s) to update (optional if using filters)"
    ),
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    type: str | None = typer.Option(None, "--type", help="Filter by type"),
    priority: int | None = typer.Option(None, "--priority", help="Filter by priority"),
    assignee: str | None = typer.Option(None, "--assignee", help="Filter by assignee"),
    label_filter: str | None = typer.Option(None, "--label", help="Filter by existing labels"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Add labels to multiple issues (by IDs or filters).

    Examples:
        issues labels bulk-add "urgent,backend" issue-1 issue-2
        issues labels bulk-add "reviewed" --status open --type bug
    """
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()
        label_list = [label.strip() for label in labels.split(",")]

        # Get issues either from IDs or filters - best-effort approach
        issues_to_process = []
        failures = []

        if issue_ids:
            for iid in issue_ids:
                try:
                    issue = service.get_issue(iid)
                    if issue is None:
                        failures.append({"id": iid, "error": f"Issue not found: {iid}"})
                    else:
                        issues_to_process.append(issue)
                except Exception as e:
                    failures.append({"id": iid, "error": str(e)})
        else:
            # Apply filters
            status_filter = IssueStatus(status) if status else None
            type_filter = IssueType(type) if type else None
            priority_filter = IssuePriority(priority) if priority is not None else None

            issues_to_process = service.list_issues(
                status=status_filter,
                priority=priority_filter,
                issue_type=type_filter,
                assignee=assignee,
            )

            # Additional filter by labels
            if label_filter:
                filter_labels = [lbl.strip() for lbl in label_filter.split(",")]
                issues_to_process = [i for i in issues_to_process if any(lbl in i.labels for lbl in filter_labels)]

        if not issues_to_process and not failures:
            typer.echo("No issues found matching criteria", err=True)
            raise typer.Exit(1)

        # Process each issue with error handling
        successes = []
        for issue in issues_to_process:
            try:
                for label_name in label_list:
                    issue = issue.add_label(label_name)
                service.uow.issues.save(issue)
                successes.append({"id": issue.id, "labels": issue.labels})
            except Exception as e:
                failures.append({"id": issue.id, "error": str(e)})

        service.uow.session.commit()

        # Return results
        if json_output:
            typer.echo(json.dumps({"successes": successes, "failures": failures}))
        else:
            if successes:
                typer.echo(f"✓ Added labels {labels} to {len(successes)} issue(s)")
            if failures:
                typer.echo(f"✗ Failed on {len(failures)} issue(s)", err=True)
                for fail in failures:
                    typer.echo(f"  {fail['id']}: {fail['error']}", err=True)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="bulk-remove")
def bulk_remove(
    labels: str = typer.Argument(..., help="Comma-separated label(s) to remove"),
    issue_ids: builtins.list[str] | None = typer.Argument(
        None, help="Issue ID(s) to update (optional if using filters)"
    ),
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    type: str | None = typer.Option(None, "--type", help="Filter by type"),
    priority: int | None = typer.Option(None, "--priority", help="Filter by priority"),
    assignee: str | None = typer.Option(None, "--assignee", help="Filter by assignee"),
    label_filter: str | None = typer.Option(None, "--label", help="Filter by existing labels"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Remove labels from multiple issues (by IDs or filters).

    Examples:
        issues labels bulk-remove "wontfix" issue-1 issue-2
        issues labels bulk-remove "duplicate" --status closed
    """
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()
        label_list = [label.strip() for label in labels.split(",")]

        # Get issues either from IDs or filters - best-effort approach
        issues_to_process = []
        failures = []

        if issue_ids:
            for iid in issue_ids:
                try:
                    issue = service.get_issue(iid)
                    if issue is None:
                        failures.append({"id": iid, "error": f"Issue not found: {iid}"})
                    else:
                        issues_to_process.append(issue)
                except Exception as e:
                    failures.append({"id": iid, "error": str(e)})
        else:
            # Apply filters
            status_filter = IssueStatus(status) if status else None
            type_filter = IssueType(type) if type else None
            priority_filter = IssuePriority(priority) if priority is not None else None

            issues_to_process = service.list_issues(
                status=status_filter,
                priority=priority_filter,
                issue_type=type_filter,
                assignee=assignee,
            )

            # Additional filter by labels
            if label_filter:
                filter_labels = [lbl.strip() for lbl in label_filter.split(",")]
                issues_to_process = [i for i in issues_to_process if any(lbl in i.labels for lbl in filter_labels)]

        if not issues_to_process and not failures:
            typer.echo("No issues found matching criteria", err=True)
            raise typer.Exit(1)

        # Process each issue with error handling
        successes = []
        for issue in issues_to_process:
            try:
                for label_name in label_list:
                    issue = issue.remove_label(label_name)
                service.uow.issues.save(issue)
                successes.append({"id": issue.id, "labels": issue.labels})
            except Exception as e:
                failures.append({"id": issue.id, "error": str(e)})

        service.uow.session.commit()

        # Return results
        if json_output:
            typer.echo(json.dumps({"successes": successes, "failures": failures}))
        else:
            if successes:
                typer.echo(f"✓ Removed labels {labels} from {len(successes)} issue(s)")
            if failures:
                typer.echo(f"✗ Failed on {len(failures)} issue(s)", err=True)
                for fail in failures:
                    typer.echo(f"  {fail['id']}: {fail['error']}", err=True)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

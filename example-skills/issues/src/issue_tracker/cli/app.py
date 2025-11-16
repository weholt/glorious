"""Main CLI application - issue tracker."""

import builtins
import json
from datetime import UTC
from typing import Any

import typer

from issue_tracker.cli.commands import comments_app, dependencies_app, epics_app, instructions_app, labels_app
from issue_tracker.cli.formatters import format_datetime_iso, format_priority_emoji, issue_to_dict
from issue_tracker.domain import (
    IssuePriority,
    IssueStatus,
    IssueType,
)

app = typer.Typer(
    name="issues",
    help="Issue tracker command-line interface",
    no_args_is_help=True,
)


# Global verbose callback
@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Global options for all commands."""
    if verbose:
        from issue_tracker.cli.logging_utils import set_verbose

        set_verbose(True)


# Global service instances (set by tests or use real services)
_SERVICE_OVERRIDE: dict[str, Any] = {
    "issue_service": None,
    "graph_service": None,
    "stats_service": None,
}


def set_service(name: str, service: Any) -> None:
    """Set service instance for testing (used by test fixtures)."""
    _SERVICE_OVERRIDE[name] = service


def get_issue_service():
    """Get issue service instance (from override or create new)."""
    if _SERVICE_OVERRIDE["issue_service"] is not None:
        return _SERVICE_OVERRIDE["issue_service"]
    from issue_tracker.cli.dependencies import get_issue_service

    return get_issue_service()


def get_graph_service():
    """Get graph service instance (from override or create new)."""
    if _SERVICE_OVERRIDE["graph_service"] is not None:
        return _SERVICE_OVERRIDE["graph_service"]
    from issue_tracker.cli.dependencies import get_issue_graph_service

    return get_issue_graph_service()


def get_stats_service():
    """Get stats service instance (from override or create new)."""
    if _SERVICE_OVERRIDE["stats_service"] is not None:
        return _SERVICE_OVERRIDE["stats_service"]
    from issue_tracker.cli.dependencies import get_issue_stats_service

    return get_issue_stats_service()


def _update_agents_md(agents_md_path):
    """Update or create AGENTS.md with issue CLI instructions."""

    issue_cli_section = """
## Issue Management with CLI

**IMPORTANT**: Use `uv run issues` commands for all issue tracking - do NOT manually edit markdown files.

### Creating and Managing Issues

```bash
# Initialize issue tracker (first time only)
uv run issues init

# Create issues
uv run issues create "Bug: Fix memory leak" --priority 1
uv run issues create "Feature: Add export" --type feature --labels enhancement,export

# List and query issues
uv run issues list --status open
uv run issues list --priority 1 --assignee @me
uv run issues show ISSUE-123

# Update issues
uv run issues update ISSUE-123 --status in_progress
uv run issues close ISSUE-123
uv run issues reopen ISSUE-123

# Add labels and comments
uv run issues labels add ISSUE-123 bug critical
uv run issues comments add ISSUE-123 "Fixed in commit abc123"

# Manage dependencies
uv run issues dependencies add ISSUE-123 ISSUE-456 --type blocks
uv run issues dependencies tree ISSUE-123
uv run issues dependencies cycles  # Detect dependency cycles

# Work queues
uv run issues ready     # Issues ready to work on
uv run issues blocked   # Issues blocked by dependencies
uv run issues stale     # Issues not updated recently

# Get statistics
uv run issues stats
uv run issues info
```

### Why Use CLI Instead of Markdown Files

1. **Data Integrity**: SQLite database ensures consistency and prevents conflicts
2. **Validation**: CLI enforces business rules (no circular dependencies, valid statuses)
3. **Query Power**: Complex filtering, sorting, and aggregation
4. **Git Integration**: Automatic sync with git (via daemon)
5. **Team Collaboration**: Proper merge handling, no manual conflict resolution

### Legacy Files (Do Not Edit)

The `.work/agent/issues/` folder contains old markdown-based issues for historical reference only. All new issue management must use the CLI.

### Notes and Documentation

- For temporary notes during development, use `.work/agent/notes/` folder
- These are NOT issues - just scratch space for analysis and planning
"""

    if agents_md_path.exists():
        # Read existing content
        content = agents_md_path.read_text()

        import re

        # Remove old note-taking section if it exists
        old_section_pattern = r"## Note-taking, issue reporting and task management.*?(?=\n## |\Z)"
        content = re.sub(old_section_pattern, "", content, flags=re.DOTALL)

        # Check if issue management section already exists
        if "## Issue Management with CLI" in content:
            # Replace existing section
            pattern = r"## Issue Management with CLI.*?(?=\n## |\Z)"
            content = re.sub(pattern, issue_cli_section.strip(), content, flags=re.DOTALL)
        else:
            # Append new section before "## Tools" if it exists, otherwise at the end
            if "## Tools" in content:
                content = content.replace("## Tools", f"{issue_cli_section.strip()}\n\n## Tools")
            else:
                content = content.rstrip() + "\n\n" + issue_cli_section.strip() + "\n"

        agents_md_path.write_text(content)
    else:
        # Create new AGENTS.md with issue CLI section
        content = f"""# Agent Development Guide

{issue_cli_section.strip()}
"""
        agents_md_path.write_text(content)


# Phase 1: Core Issue Management


@app.command()
def create(
    title: str = typer.Argument("", help="Issue title"),
    type: str = typer.Option("task", "-t", "--type"),
    priority: int = typer.Option(2, "-p", "--priority"),
    description: str = typer.Option("", "-d", "--description"),
    assignee: str | None = typer.Option(None, "-a", "--assignee"),
    label: str | None = typer.Option(None, "-l", "--label", "--labels"),
    issue_id: str | None = typer.Option(None, "--id"),
    deps: str | None = typer.Option(None, "--deps", help="Dependencies in format type:issue-id"),
    discovered_from: str | None = typer.Option(
        None, "--discovered-from", help="Issue ID this was discovered from (agent workflow)"
    ),
    file: str | None = typer.Option(None, "-f", "--file", help="Create issues from file"),
    template: str | None = typer.Option(None, "--template", help="Use template for default values"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Create a new issue with specified properties.

    Args:
        title: The issue title (required)
        type: Issue type (task, bug, feature, epic, chore). Defaults to task.
        priority: Priority level from 0 (critical) to 4 (backlog). Defaults to 2 (medium).
        description: Detailed description of the issue
        assignee: Username of person assigned to this issue
        label: Comma-separated list of labels to apply
        issue_id: Custom issue ID (auto-generated if not provided)
        deps: Dependencies in format 'type:issue-id' (e.g., 'blocks:issue-123')
        discovered_from: Issue ID that led to discovery of this issue (agent workflow)
        file: Path to file containing issues to create in bulk
        json_output: Output result as JSON

    Returns:
        Prints created issue ID or JSON representation

    Raises:
        typer.Exit: If title is empty, type is invalid, or priority is out of range

    Examples:
        Create a simple task:
            $ issues create "Fix login bug"

        Create a high-priority bug:
            $ issues create "Critical error" --type bug --priority 1

        Create with labels:
            $ issues create "Add tests" --label "testing,improvement"

        Create issue discovered during another:
            $ issues create "Fix database query" --discovered-from issue-123
    """
    from issue_tracker.cli.logging_utils import verbose_error, verbose_log, verbose_step, verbose_success

    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_db_url, get_issues_folder

        verbose_log("Create command started", title=title, type=type, priority=priority)
        verbose_log("Database URL", url=get_db_url())

        # Load template if specified
        if template:
            from issue_tracker.templates import TemplateManager

            issues_folder = Path(get_issues_folder())
            templates_dir = issues_folder / "templates"
            manager = TemplateManager(templates_dir)

            tmpl = manager.load_template(template)
            if not tmpl:
                typer.echo(f"Error: Template '{template}' not found", err=True)
                raise typer.Exit(1)

            # Apply template defaults (CLI args override template)
            if not title and tmpl.title:
                title = tmpl.title
            if type == "task" and tmpl.type:
                type = tmpl.type
            if priority == 2 and tmpl.priority:
                priority = tmpl.priority
            if not description and tmpl.description:
                description = tmpl.description
            if not assignee and tmpl.assignee:
                assignee = tmpl.assignee
            if not label and tmpl.labels:
                label = ",".join(tmpl.labels)

            verbose_log("Template loaded", name=template)

        # Get service
        verbose_step("Initializing issue service")
        service = get_issue_service()
        verbose_success("Service initialized")

        # Handle bulk file creation
        if file:
            verbose_step(f"Reading issues from file: {file}")
            from pathlib import Path

            file_path = Path(file)
            if not file_path.exists():
                typer.echo(f"Error: File not found: {file}", err=True)
                raise typer.Exit(1)

            content = file_path.read_text()

            # Parse markdown sections (# Title or ## Title)
            import re

            sections = re.split(r"^#{1,2}\s+(.+)$", content, flags=re.MULTILINE)

            created_issues = []
            # sections is [preamble, title1, content1, title2, content2, ...]
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    issue_title = sections[i].strip()
                    issue_desc = sections[i + 1].strip()

                    verbose_log(f"Creating issue: {issue_title}")

                    # Use defaults from flags or template
                    issue = service.create_issue(
                        title=issue_title,
                        description=issue_desc,
                        issue_type=IssueType(type) if type else IssueType.TASK,
                        priority=IssuePriority(priority) if priority is not None else IssuePriority.MEDIUM,
                        assignee=assignee,
                        project_id="default",
                        labels=[lbl.strip() for lbl in label.split(",")] if label else [],
                    )
                    service.uow.session.commit()

                    created_issues.append(
                        {
                            "id": issue.id,
                            "title": issue.title,
                            "description": issue.description[:50] + "..."
                            if len(issue.description) > 50
                            else issue.description,
                        }
                    )

            if json_output:
                typer.echo(json.dumps(created_issues))
            else:
                typer.echo(f"Created {len(created_issues)} issue(s) from {file}:")
                for issue_data in created_issues:
                    typer.echo(f"  - {issue_data['id']}: {issue_data['title']}")

            verbose_success(f"Bulk creation completed: {len(created_issues)} issues")
            return

        # Validate title
        if not title or title.strip() == "":
            verbose_error("Empty title provided")
            typer.echo("Error: Title is required", err=True)
            raise typer.Exit(1)

        verbose_step("Validating input parameters")

        # Validate type
        try:
            issue_type = IssueType(type)
            verbose_log("Issue type validated", type=type)
        except ValueError:
            verbose_error(f"Invalid issue type: {type}")
            typer.echo(f"Error: Invalid type '{type}'", err=True)
            raise typer.Exit(1)

        # Validate priority
        try:
            issue_priority = IssuePriority(priority)
            verbose_log("Priority validated", priority=priority)
        except ValueError:
            verbose_error(f"Invalid priority: {priority}")
            typer.echo(f"Error: Invalid priority '{priority}'", err=True)
            raise typer.Exit(1)

        # Parse labels
        labels = [lbl.strip() for lbl in label.split(",")] if label else []
        if labels:
            verbose_log("Labels parsed", count=len(labels), labels=labels)

        # Parse deps (for now just validate format)
        if deps:
            if ":" not in deps:
                verbose_error(f"Invalid dependency format: {deps}")
                typer.echo(f"Error: Invalid dependency format '{deps}'. Expected 'type:issue-id'", err=True)
                raise typer.Exit(1)
            verbose_log("Dependencies parsed", deps=deps)

        # Create issue via service
        verbose_step("Creating issue in database", f"title={title}")
        issue = service.create_issue(
            title=title,
            description=description or "",
            issue_type=issue_type,
            priority=issue_priority,
            assignee=assignee,
            project_id="default",
            labels=labels,  # Pass labels during creation
            custom_id=issue_id,  # Pass custom ID if provided
        )
        verbose_log("Committing transaction")
        service.uow.session.commit()  # Commit the session directly, not via UoW
        verbose_success(f"Issue created with ID: {issue.id}")

        # Add discovered-from dependency if specified
        if discovered_from:
            from issue_tracker.domain.entities.dependency import DependencyType

            verbose_step(f"Adding discovered-from dependency to {discovered_from}")
            graph_service = get_graph_service()
            graph_service.add_dependency(discovered_from, issue.id, DependencyType.DISCOVERED_FROM)
            verbose_success(f"Added discovered-from link: {discovered_from} -> {issue.id}")

        # Refresh issue to get updated data
        verbose_step("Refreshing issue data")
        issue = service.get_issue(issue.id)
        verbose_success("Issue data refreshed")

        # Convert to dict for output
        verbose_step("Preparing output")
        issue_dict = issue_to_dict(issue)

        # Output
        if json_output:
            verbose_log("Outputting JSON")
            typer.echo(json.dumps(issue_dict))
        else:
            verbose_log("Outputting human-readable format")
            typer.echo(f"Created issue: {issue.id}")

        verbose_success("Create command completed successfully")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="list")
def list_issues(
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    priority: int | None = typer.Option(None, "--priority", help="Filter by exact priority"),
    priority_min: int | None = typer.Option(None, "--priority-min", help="Minimum priority"),
    priority_max: int | None = typer.Option(None, "--priority-max", help="Maximum priority"),
    type: str | None = typer.Option(None, "--type", help="Filter by type"),
    assignee: str | None = typer.Option(None, "--assignee", help="Filter by assignee"),
    no_assignee: bool = typer.Option(False, "--no-assignee", help="Show unassigned issues only"),
    label: str | None = typer.Option(None, "--label", help="Filter by labels (AND logic)"),
    label_any: str | None = typer.Option(None, "--label-any", help="Filter by labels (OR logic)"),
    no_labels: bool = typer.Option(False, "--no-labels", help="Show issues with no labels"),
    epic: str | None = typer.Option(None, "--epic", help="Filter by epic"),
    title_contains: str | None = typer.Option(None, "--title-contains", help="Filter by title substring"),
    desc_contains: str | None = typer.Option(None, "--desc-contains", help="Filter by description substring"),
    notes_contains: str | None = typer.Option(None, "--notes-contains", help="Filter by notes substring"),
    empty_description: bool = typer.Option(False, "--empty-description", help="Show issues with no description"),
    created_after: str | None = typer.Option(None, "--created-after", help="Filter by created after date (YYYY-MM-DD)"),
    created_before: str | None = typer.Option(
        None, "--created-before", help="Filter by created before date (YYYY-MM-DD)"
    ),
    updated_after: str | None = typer.Option(None, "--updated-after", help="Filter by updated after date (YYYY-MM-DD)"),
    updated_before: str | None = typer.Option(
        None, "--updated-before", help="Filter by updated before date (YYYY-MM-DD)"
    ),
    closed_after: str | None = typer.Option(None, "--closed-after", help="Filter by closed after date (YYYY-MM-DD)"),
    closed_before: str | None = typer.Option(None, "--closed-before", help="Filter by closed before date (YYYY-MM-DD)"),
    limit: int | None = typer.Option(None, "--limit", help="Limit number of results"),
    sort: str = typer.Option("created", "--sort", help="Sort by field (priority, created, updated)"),
    reverse: bool = typer.Option(False, "--reverse", help="Reverse sort order"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List and filter issues with advanced query options.

    Supports filtering by status, priority, type, assignee, labels, and epic.
    Results can be sorted and limited.

    Examples:
        List all open bugs:
            $ issues list --status open --type bug

        List high-priority unassigned tasks:
            $ issues list --priority 1 --no-assignee

        List issues with specific labels (AND logic):
            $ issues list --label "urgent,backend"
    """
    try:
        service = get_issue_service()

        # Parse filter parameters
        status_filter = IssueStatus(status) if status else None
        type_filter = IssueType(type) if type else None
        priority_filter = IssuePriority(priority) if priority is not None else None
        label_filters = [lbl.strip() for lbl in label.split(",")] if label else []

        # Get issues from service
        issues = service.list_issues(
            status=status_filter,
            priority=priority_filter,
            issue_type=type_filter,
            assignee=assignee,
            epic_id=epic,
            limit=limit,
            offset=0,
        )

        # Apply additional filters not supported by service layer
        if label_filters:
            issues = [i for i in issues if any(lbl in i.labels for lbl in label_filters)]
        if priority_min is not None:
            issues = [i for i in issues if int(i.priority) >= priority_min]
        if priority_max is not None:
            issues = [i for i in issues if int(i.priority) <= priority_max]
        if no_assignee:
            issues = [i for i in issues if not i.assignee]
        if no_labels:
            issues = [i for i in issues if not i.labels]

        # Text search filters
        if title_contains:
            issues = [i for i in issues if title_contains.lower() in i.title.lower()]
        if desc_contains:
            issues = [i for i in issues if i.description and desc_contains.lower() in i.description.lower()]
        if notes_contains:
            issues = [
                i for i in issues if hasattr(i, "notes") and i.notes and notes_contains.lower() in i.notes.lower()
            ]
        if empty_description:
            issues = [i for i in issues if not i.description or i.description.strip() == ""]

        # Date range filters
        from datetime import datetime

        if created_after:
            cutoff = datetime.fromisoformat(created_after).replace(tzinfo=None)
            issues = [i for i in issues if i.created_at.replace(tzinfo=None) > cutoff]
        if created_before:
            cutoff = datetime.fromisoformat(created_before).replace(tzinfo=None)
            issues = [i for i in issues if i.created_at.replace(tzinfo=None) < cutoff]
        if updated_after:
            cutoff = datetime.fromisoformat(updated_after).replace(tzinfo=None)
            issues = [i for i in issues if i.updated_at.replace(tzinfo=None) > cutoff]
        if updated_before:
            cutoff = datetime.fromisoformat(updated_before).replace(tzinfo=None)
            issues = [i for i in issues if i.updated_at.replace(tzinfo=None) < cutoff]
        if closed_after:
            cutoff = datetime.fromisoformat(closed_after).replace(tzinfo=None)
            issues = [i for i in issues if i.closed_at and i.closed_at.replace(tzinfo=None) > cutoff]
        if closed_before:
            cutoff = datetime.fromisoformat(closed_before).replace(tzinfo=None)
            issues = [i for i in issues if i.closed_at and i.closed_at.replace(tzinfo=None) < cutoff]

        # Convert to dicts
        issue_dicts = []
        for issue in issues:
            issue_dicts.append(issue_to_dict(issue))

        # Output
        if json_output:
            typer.echo(json.dumps(issue_dicts))
        else:
            if not issue_dicts:
                typer.echo("No issues found")
            else:
                for issue_dict in issue_dicts:
                    typer.echo(f"{issue_dict['id']}: {issue_dict['title']}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (supports FTS5 syntax)"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum number of results"),
    include_closed: bool = typer.Option(False, "--include-closed", help="Include closed issues"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Full-text search across issue titles and descriptions using FTS5.
    
    Supports SQLite FTS5 query syntax for advanced searches.
    
    Examples:
        Simple search:
            $ issues search "memory leak"
        
        Field-specific search:
            $ issues search "title:authentication"
        
        Phrase search:
            $ issues search '"database connection"'
        
        Proximity search:
            $ issues search "memory NEAR/3 leak"
        
        Boolean operators:
            $ issues search "bug AND (frontend OR backend)"
    """
    try:
        from sqlmodel import Session
        
        from issue_tracker.cli.dependencies import get_engine
        from issue_tracker.services.search_service import SearchService
        
        engine = get_engine()
        session = Session(engine)
        
        try:
            search_service = SearchService(session)
            results = search_service.search(
                query=query,
                limit=limit,
                include_closed=include_closed
            )
            
            if json_output:
                # Get full issue details for JSON output
                service = get_issue_service()
                issue_results = []
                for result in results:
                    try:
                        issue = service.get_issue(result.issue_id)
                        if issue:
                            issue_dict = issue_to_dict(issue)
                            issue_dict["search_rank"] = result.rank
                            issue_dict["snippet"] = result.snippet
                            issue_results.append(issue_dict)
                    except Exception:
                        continue
                
                typer.echo(json.dumps(issue_results))
            else:
                if not results:
                    typer.echo("No results found")
                else:
                    typer.echo(f"Found {len(results)} result(s):\n")
                    for i, result in enumerate(results, 1):
                        typer.echo(f"{i}. {result.issue_id} (rank: {result.rank:.2f})")
                        typer.echo(f"   {result.snippet}")
                        typer.echo()
        finally:
            session.close()
    
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def show(
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to show"),
    comments: bool = typer.Option(False, "--comments", help="Show comments"),
    history: bool = typer.Option(False, "--history", help="Show history"),
    deps: bool = typer.Option(False, "--deps", help="Show dependencies"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Display detailed information about one or more issues.

    Shows full issue details including title, description, status, priority,
    labels, and optionally comments and dependencies.

    Examples:
        Show single issue:
            $ issues show issue-abc123

        Show multiple issues with comments:
            $ issues show issue-123 issue-456 --comments

        Show with all details as JSON:
            $ issues show issue-789 --comments --deps --json
    """
    try:
        from issue_tracker.domain.exceptions import NotFoundError

        service = get_issue_service()
        graph_service = get_graph_service()
        results = []
        not_found = []

        for issue_id in issue_ids:
            try:
                issue = service.get_issue(issue_id)
            except NotFoundError:
                not_found.append(issue_id)
                if not json_output:
                    typer.echo(f"Issue {issue_id} not found")
                continue

            if not issue:
                not_found.append(issue_id)
                if not json_output:
                    typer.echo(f"Issue {issue_id} not found")
                continue

            # Convert to dict
            issue_data = issue_to_dict(issue)

            # Add optional data
            if comments:
                comment_list = service.list_comments(issue_id)
                issue_data["comments"] = [
                    {
                        "id": c.id,
                        "author": c.author,
                        "text": c.text,
                        "created_at": format_datetime_iso(c.created_at),
                    }
                    for c in comment_list
                ]

            if history:
                issue_data["history"] = []  # History not implemented yet

            if deps:
                # Get dependencies from graph service
                dependencies = graph_service.get_dependencies(issue_id)
                dependents = graph_service.get_dependents(issue_id)
                issue_data["dependencies"] = {
                    "depends_on": [{"id": d[0], "type": d[1]} for d in dependencies],
                    "depended_by": [{"id": d[0], "type": d[1]} for d in dependents],
                }

            results.append(issue_data)

            if not json_output:
                typer.echo(f"ID: {issue_id}")
                typer.echo(f"Title: {issue_data['title']}")
                if issue_data["description"]:
                    typer.echo(f"Description: {issue_data['description']}")
                typer.echo(f"Type: {issue_data['type']}")
                typer.echo(f"Status: {issue_data['status']}")
                typer.echo(f"Priority: {format_priority_emoji(issue_data['priority'])}")
                if issue_data["assignee"]:
                    typer.echo(f"Assignee: {issue_data['assignee']}")
                if issue_data["labels"]:
                    typer.echo(f"Labels: {', '.join(issue_data['labels'])}")
                if issue_data["epic_id"]:
                    typer.echo(f"Epic: {issue_data['epic_id']}")
                typer.echo(f"Created: {issue_data['created_at']}")
                typer.echo(f"Updated: {issue_data['updated_at']}")
                if issue_data["closed_at"]:
                    typer.echo(f"Closed: {issue_data['closed_at']}")
                typer.echo("")  # Blank line between issues

        if json_output:
            if len(issue_ids) == 1:
                # Single issue: return the issue object directly
                output_data = results[0] if results else None
            else:
                # Multiple issues: return a mapping of issue-id -> issue-data
                output_data = {issue_data["id"]: issue_data for issue_data in results}
            
            typer.echo(json.dumps(output_data))

        if not_found:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def update(
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to update"),
    title: str | None = typer.Option(None, "--title", help="New title"),
    priority: int | None = typer.Option(None, "-p", "--priority", help="New priority"),
    assignee: str | None = typer.Option(None, "-a", "--assignee", help="New assignee"),
    description: str | None = typer.Option(None, "-d", "--description", help="New description"),
    status: str | None = typer.Option(None, "--status", "-s", help="New status"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Update an issue."""
    try:
        from issue_tracker.domain.exceptions import NotFoundError

        service = get_issue_service()

        # Validate status if provided
        if status is not None:
            valid_statuses = ["open", "in_progress", "blocked", "resolved", "closed", "archived"]
            if status not in valid_statuses:
                typer.echo(f"Error: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}", err=True)
                raise typer.Exit(1)

        results = []
        for issue_id in issue_ids:
            try:
                # Get existing issue
                issue = service.get_issue(issue_id)
            except NotFoundError:
                typer.echo(f"Issue {issue_id} not found", err=True)
                raise typer.Exit(1)

            if not issue:
                typer.echo(f"Issue {issue_id} not found", err=True)
                raise typer.Exit(1)

            # Update via service
            if status is not None:
                # Use transition_issue for status changes
                issue = service.transition_issue(
                    issue_id=issue_id,
                    new_status=IssueStatus(status),
                )
                service.uow.session.commit()

            # Update other fields if provided
            if any([title, description, priority is not None, assignee]):
                issue = service.update_issue(
                    issue_id=issue_id,
                    title=title,
                    description=description,
                    priority=IssuePriority(priority) if priority is not None else None,
                    assignee=assignee,
                )
                service.uow.session.commit()

            # If nothing was updated, just get the issue
            if not any([status, title, description, priority is not None, assignee]):
                issue = service.get_issue(issue_id)

            # Convert to dict
            issue_dict = issue_to_dict(issue)

            if not json_output:
                typer.echo(f"Updated issue {issue_id}")
            else:
                results.append(issue_dict)

        if json_output:
            if len(results) == 1:
                typer.echo(json.dumps(results[0]))
            else:
                typer.echo(json.dumps(results))

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def close(
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to close"),
    reason: str | None = typer.Option(None, "--reason", help="Reason for closing"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Close an issue."""
    try:
        service = get_issue_service()
        results = []

        for issue_id in issue_ids:
            issue = service.close_issue(issue_id)
            service.uow.session.commit()

            issue_dict = {
                "id": issue.id,
                "status": issue.status.value,
                "closed_at": format_datetime_iso(issue.closed_at),
            }

            if not json_output:
                typer.echo(f"Closed issue {issue_id}")
            else:
                results.append(issue_dict)

        if json_output:
            if len(results) == 1:
                typer.echo(json.dumps(results[0]))
            else:
                typer.echo(json.dumps(results))

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def reopen(
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to reopen"),
    reason: str | None = typer.Option(None, "--reason", help="Reason for reopening"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Reopen a closed issue."""
    try:
        service = get_issue_service()
        results = []

        for issue_id in issue_ids:
            issue = service.reopen_issue(issue_id)
            service.uow.session.commit()

            if not json_output:
                typer.echo(f"Reopened issue {issue_id}")
            else:
                issue_dict = {
                    "id": issue.id,
                    "status": issue.status.value,
                    "closed_at": None,
                }
                results.append(issue_dict)

        if json_output:
            if len(results) == 1:
                typer.echo(json.dumps(results[0]))
            else:
                typer.echo(json.dumps(results))

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def delete(
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to delete"),
    force: bool = typer.Option(False, "--force", help="Force delete without confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Delete an issue."""
    try:
        if not force:
            typer.echo("Error: --force flag required for deletion", err=True)
            raise typer.Exit(1)

        service = get_issue_service()
        results = []

        for issue_id in issue_ids:
            service.delete_issue(issue_id)

            if not json_output:
                typer.echo(f"Deleted issue {issue_id}")
            else:
                results.append({"id": issue_id, "deleted": True})

        if json_output:
            if len(results) == 1:
                typer.echo(json.dumps(results[0]))
            else:
                typer.echo(json.dumps(results))

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def restore(
    issue_ids: builtins.list[str] = typer.Argument(..., help="Issue ID(s) to restore"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Restore a deleted issue."""
    try:
        # Note: Service layer doesn't have restore - deleted issues are gone
        # This command is kept for backwards compatibility but does nothing
        results = []
        for issue_id in issue_ids:
            if not json_output:
                typer.echo(f"Warning: Issue {issue_id} cannot be restored (not implemented)")
            else:
                results.append({"id": issue_id, "restored": False, "error": "not implemented"})

        if json_output:
            if len(results) == 1:
                typer.echo(json.dumps(results[0]))
            else:
                typer.echo(json.dumps(results))

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="bulk-close")
def bulk_close(
    reason: str = typer.Argument(..., help="Reason for closing"),
    issue_ids: builtins.list[str] | None = typer.Argument(
        None, help="Issue ID(s) to close (optional if using filters)"
    ),
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    type: str | None = typer.Option(None, "--type", help="Filter by type"),
    priority: int | None = typer.Option(None, "--priority", help="Filter by priority"),
    assignee: str | None = typer.Option(None, "--assignee", help="Filter by assignee"),
    label_filter: str | None = typer.Option(None, "--label", help="Filter by labels"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Close multiple issues with shared reason (by IDs or filters).

    Examples:
        issues bulk-close "Fixed in v2.0" issue-1 issue-2 issue-3
        issues bulk-close "Duplicate" --status open --label "duplicate"
    """
    try:
        service = get_issue_service()

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
                closed_issue = service.close_issue(issue.id)
                successes.append(
                    {
                        "id": closed_issue.id,
                        "status": closed_issue.status.value,
                        "closed_at": format_datetime_iso(closed_issue.closed_at),
                    }
                )
            except Exception as e:
                failures.append({"id": issue.id, "error": str(e)})

        service.uow.session.commit()

        # Return results
        if json_output:
            typer.echo(json.dumps({"successes": successes, "failures": failures}))
        else:
            if successes:
                typer.echo(f"✓ Closed {len(successes)} issue(s) with reason: {reason}")
            if failures:
                typer.echo(f"✗ Failed on {len(failures)} issue(s)", err=True)
                for fail in failures:
                    typer.echo(f"  {fail['id']}: {fail['error']}", err=True)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="bulk-update")
def bulk_update(
    issue_ids: builtins.list[str] | None = typer.Argument(
        None, help="Issue ID(s) to update (optional if using filters)"
    ),
    new_status: str | None = typer.Option(None, "--new-status", help="New status to set"),
    new_priority: int | None = typer.Option(None, "--new-priority", help="New priority to set"),
    new_assignee: str | None = typer.Option(None, "--new-assignee", help="New assignee to set"),
    status: str | None = typer.Option(None, "--status", help="Filter by current status"),
    type: str | None = typer.Option(None, "--type", help="Filter by type"),
    priority: int | None = typer.Option(None, "--priority", help="Filter by current priority"),
    assignee: str | None = typer.Option(None, "--assignee", help="Filter by current assignee"),
    label_filter: str | None = typer.Option(None, "--label", help="Filter by labels"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Update multiple issues at once (by IDs or filters).

    Examples:
        issues bulk-update issue-1 issue-2 --new-priority 0
        issues bulk-update --status open --type bug --new-assignee alice
        issues bulk-update --label "urgent" --new-priority 0 --new-status in_progress
    """
    try:
        service = get_issue_service()

        # Validate new_status if provided
        if new_status and new_status not in ["open", "in_progress", "blocked", "resolved", "closed", "archived"]:
            typer.echo(f"Error: Invalid status '{new_status}'", err=True)
            raise typer.Exit(1)

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
                # Update status if requested
                if new_status:
                    issue = service.transition_issue(issue.id, IssueStatus(new_status))

                # Update other fields if requested
                if new_priority is not None or new_assignee:
                    issue = service.update_issue(
                        issue_id=issue.id,
                        priority=IssuePriority(new_priority) if new_priority is not None else None,
                        assignee=new_assignee,
                    )

                successes.append(
                    {
                        "id": issue.id,
                        "status": issue.status.value,
                        "priority": int(issue.priority),
                        "assignee": issue.assignee,
                    }
                )
            except Exception as e:
                failures.append({"id": issue.id, "error": str(e)})

        service.uow.session.commit()

        # Return results
        if json_output:
            typer.echo(json.dumps({"successes": successes, "failures": failures}))
        else:
            if successes:
                typer.echo(f"✓ Updated {len(successes)} issue(s)")
            if failures:
                typer.echo(f"✗ Failed on {len(failures)} issue(s)", err=True)
                for fail in failures:
                    typer.echo(f"  {fail['id']}: {fail['error']}", err=True)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Workflow commands - ready and blocked
@app.command()
def ready(
    limit: int | None = typer.Option(None, "--limit", help="Limit number of results"),
    sort_by: str = typer.Option("priority", "--sort-by", help="Sort by: priority, age, type, score"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List ready issues with configurable sorting.

    Shows issues that are ready to work on (no blocking dependencies).

    Sorting options:
        priority: By priority level (default)
        age: By creation date (oldest first)
        type: By issue type
        score: By custom score (priority + age combination)

    Examples:
        issues ready                        # Default: sorted by priority
        issues ready --sort-by age          # Oldest issues first
        issues ready --sort-by score        # Combined priority + age score
        issues ready --limit 5              # Show top 5 ready issues
    """
    try:
        from datetime import datetime

        from issue_tracker.domain.entities.issue import IssueStatus

        graph_service = get_graph_service()

        # Validate sort option
        valid_sorts = ["priority", "age", "type", "score"]
        if sort_by not in valid_sorts:
            typer.echo(f"Error: Invalid sort option '{sort_by}'. Must be one of: {', '.join(valid_sorts)}", err=True)
            raise typer.Exit(1)

        # Get ready issues from service (open/in-progress with no blockers)
        ready_issues_entities = graph_service.get_ready_queue(status_filter=[IssueStatus.OPEN, IssueStatus.IN_PROGRESS])

        # Apply sorting
        if sort_by == "priority":
            # Sort by priority (0=critical first)
            ready_issues_entities = sorted(ready_issues_entities, key=lambda x: int(x.priority))
        elif sort_by == "age":
            # Sort by creation date (oldest first)
            ready_issues_entities = sorted(ready_issues_entities, key=lambda x: x.created_at)
        elif sort_by == "type":
            # Sort by type (bug, feature, task, epic, chore)
            type_order = {"bug": 0, "feature": 1, "task": 2, "epic": 3, "chore": 4}
            ready_issues_entities = sorted(ready_issues_entities, key=lambda x: type_order.get(x.type.value, 99))
        elif sort_by == "score":
            # Custom score: priority weight + age weight
            # Lower score = higher priority
            now = datetime.now()

            def calculate_score(issue):
                """Calculate issue score based on priority and age."""
                priority_weight = int(issue.priority) * 10  # 0-40
                days_old = (now - issue.created_at.replace(tzinfo=None)).days
                age_weight = min(days_old, 30)  # Cap at 30 days
                return priority_weight - age_weight  # Older issues get lower (better) score

            ready_issues_entities = sorted(ready_issues_entities, key=calculate_score)

        # Apply limit
        if limit:
            ready_issues_entities = ready_issues_entities[:limit]

        # Convert to dicts with metadata
        ready_issues = []
        for issue in ready_issues_entities:
            ready_issues.append(
                {
                    "id": issue.id,
                    "title": issue.title,
                    "priority": int(issue.priority),
                    "type": issue.type.value,
                    "status": issue.status.value,
                    "created_at": format_datetime_iso(issue.created_at),
                }
            )

        if json_output:
            typer.echo(json.dumps(ready_issues))
        else:
            if not ready_issues:
                typer.echo("No ready issues")
            else:
                typer.echo(f"Ready issues (sorted by {sort_by}):\n")
                for issue in ready_issues:
                    priority_label = format_priority_emoji(issue["priority"])
                    typer.echo(f"  {issue['id']}: {issue['title']}")
                    typer.echo(f"    Priority: {priority_label}, Type: {issue['type']}, Status: {issue['status']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def blocked(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List blocked issues."""
    try:
        from issue_tracker.domain.entities.dependency import DependencyType
        from issue_tracker.domain.entities.issue import IssueStatus

        service = get_issue_service()
        graph_service = get_graph_service()

        # Get all open issues
        all_issues = service.list_issues(status=IssueStatus.OPEN)

        # Find blocked issues and their blockers
        blocked_issues_data = []
        for issue in all_issues:
            # Get blocking dependencies (incoming)
            blocking_deps = graph_service.get_dependents(issue.id, dependency_type=DependencyType.BLOCKS)
            # Get depends-on dependencies (outgoing)
            depends_on_deps = graph_service.get_dependencies(issue.id, dependency_type=DependencyType.DEPENDS_ON)

            if blocking_deps or depends_on_deps:
                blocked_by = []
                for dep in blocking_deps:
                    blocked_by.append({"blocker": dep.from_issue_id, "type": "blocks"})
                for dep in depends_on_deps:
                    blocked_by.append({"blocker": dep.to_issue_id, "type": "depends-on"})

                blocked_issues_data.append({"id": issue.id, "title": issue.title, "blocked_by": blocked_by})

        if json_output:
            typer.echo(json.dumps(blocked_issues_data))
        else:
            if not blocked_issues_data:
                typer.echo("No blocked issues")
            else:
                for issue in blocked_issues_data:
                    blockers = ", ".join([b["blocker"] for b in issue["blocked_by"]])
                    typer.echo(f"{issue['id']}: {issue['title']} (blocked by: {blockers})")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Stats and utility commands
@app.command()
def info(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show database and system information (spec-compliant command).

    Displays database path, total issues, and last updated timestamp.

    Examples:
        issues info
        issues info --json
    """
    try:
        from datetime import UTC, datetime
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_db_url

        service = get_issue_service()

        # Get database info
        db_url = get_db_url()

        # Extract path from sqlite:/// URL
        if db_url.startswith("sqlite:///"):
            db_path = db_url[10:]  # Remove 'sqlite:///'
        else:
            db_path = db_url

        db_file = Path(db_path)

        # Get database size if it exists
        db_size = db_file.stat().st_size if db_file.exists() else 0

        # Get total issues
        all_issues = service.list_issues()
        total_issues = len(all_issues)

        # Get last updated timestamp (most recent updated_at)
        last_updated = None
        if all_issues:
            most_recent = max(all_issues, key=lambda i: i.updated_at)
            last_updated = format_datetime_iso(most_recent.updated_at)

        info_data = {
            "database_path": str(db_file.absolute()),
            "total_issues": total_issues,
            "last_updated": last_updated or format_datetime_iso(datetime.now(UTC)),
            "database_size_bytes": db_size,
        }

        if json_output:
            typer.echo(json.dumps(info_data))
        else:
            typer.echo("Database Information:")
            typer.echo(f"  Path: {info_data['database_path']}")
            typer.echo(f"  Total Issues: {info_data['total_issues']}")
            typer.echo(f"  Last Updated: {info_data['last_updated']}")
            typer.echo(f"  Database Size: {info_data['database_size_bytes']} bytes")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def stats(
    by: str | None = typer.Option(None, "--by", help="Group by field (status, priority, type, assignee)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show issue statistics."""
    try:
        service = get_issue_service()

        # Get all issues
        all_issues = service.list_issues()

        # Calculate stats
        stats_data: dict[str, Any] = {
            "total": len(all_issues),
            "by_status": {},
            "by_priority": {},
            "by_type": {},
            "by_assignee": {},
        }

        for issue in all_issues:
            # Group by status
            status_key = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
            stats_data["by_status"][status_key] = stats_data["by_status"].get(status_key, 0) + 1

            # Group by priority
            priority_key = str(issue.priority.value if hasattr(issue.priority, "value") else issue.priority)
            stats_data["by_priority"][priority_key] = stats_data["by_priority"].get(priority_key, 0) + 1

            # Group by type
            type_key = issue.type.value if hasattr(issue.type, "value") else str(issue.type)
            stats_data["by_type"][type_key] = stats_data["by_type"].get(type_key, 0) + 1

            # Group by assignee
            assignee_key = issue.assignee if issue.assignee else "unassigned"
            stats_data["by_assignee"][assignee_key] = stats_data["by_assignee"].get(assignee_key, 0) + 1

        if json_output:
            typer.echo(json.dumps(stats_data))
        else:
            typer.echo(f"Total issues: {stats_data['total']}")
            if by:
                typer.echo(f"\nGrouped by {by}:")
                group: dict[str, Any] = stats_data.get(f"by_{by}", {})
                if not group:
                    typer.echo("  (no data)")
                else:
                    for key, count in group.items():
                        typer.echo(f"  {key}: {count}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def stale(
    days: int = typer.Option(30, "--days", help="Days since last activity"),
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Find stale issues."""
    try:
        from datetime import UTC, datetime, timedelta

        from issue_tracker.domain.entities.issue import IssueStatus

        service = get_issue_service()

        # Get issues (filter by status if provided, otherwise get open issues)
        if status:
            status_filter = IssueStatus(status)
            all_issues = service.list_issues(status=status_filter)
        else:
            all_issues = service.list_issues(status=IssueStatus.OPEN)

        # Filter by staleness (updated_at older than X days)
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        stale_issues_entities = []
        for issue in all_issues:
            if issue.updated_at:
                # Make naive datetime timezone-aware for comparison
                updated = issue.updated_at.replace(tzinfo=UTC) if issue.updated_at.tzinfo is None else issue.updated_at
                if updated < cutoff_date:
                    stale_issues_entities.append(issue)

        # Convert to dicts
        stale_issues = [
            {"id": issue.id, "title": issue.title, "status": issue.status.value} for issue in stale_issues_entities
        ]

        if json_output:
            typer.echo(json.dumps(stale_issues))
        else:
            if not stale_issues:
                status_msg = f" in status '{status}'" if status else ""
                typer.echo(f"No stale issues{status_msg} (inactive for {days}+ days)")
            else:
                status_msg = f" in status '{status}'" if status else ""
                typer.echo(f"Stale issues{status_msg} (inactive for {days}+ days):")
                for issue in stale_issues:
                    typer.echo(f"{issue['id']}: {issue['title']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="bulk-create")
def bulk_create(
    file: str = typer.Argument(..., help="File containing issues"),
    type: str = typer.Option("task", "--type", help="Default issue type"),
    priority: int = typer.Option(2, "-p", "--priority", help="Default priority"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Bulk create issues from file."""
    try:
        from pathlib import Path

        from issue_tracker.domain.entities.issue import IssueType
        from issue_tracker.domain.value_objects import IssuePriority

        service = get_issue_service()

        file_path = Path(file)
        if not file_path.exists():
            typer.echo(f"Error: File not found: {file}", err=True)
            raise typer.Exit(1)

        # Parse markdown file - simple parsing: lines starting with # are titles
        content = file_path.read_text()
        titles = [line.strip("# ").strip() for line in content.split("\n") if line.startswith("# ")]

        # Create issues using service
        created = []
        for title in titles:
            issue = service.create_issue(
                title=title,
                description=None,
                issue_type=IssueType(type),
                priority=IssuePriority(priority),
                assignee=None,
                labels=[],
            )
            created.append({"id": issue.id, "title": issue.title})

        if json_output:
            typer.echo(json.dumps(created))
        else:
            typer.echo(f"Created {len(created)} issues")
            for issue in created:
                typer.echo(f"  {issue['id']}: {issue['title']}")
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Initialization and daemon commands
@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Force re-initialization"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Initialize workspace with database and configuration."""
    from issue_tracker.cli.logging_utils import (
        verbose_error,
        verbose_log,
        verbose_section,
        verbose_step,
        verbose_success,
    )

    try:
        import os
        from pathlib import Path

        verbose_section("Initializing Issue Tracker Workspace")

        # Use ISSUES_FOLDER from environment (set by CLI entry point)
        issues_folder = os.environ.get("ISSUES_FOLDER", "./.issues")
        issues_dir = Path(issues_folder)
        db_path = issues_dir / "issues.db"
        config_path = issues_dir / "config.json"

        verbose_log("Configuration", folder=issues_folder, db=str(db_path))

        # Check if already initialized (only check db and config, not the directory itself)
        already_initialized = db_path.exists() and config_path.exists()
        if already_initialized and not force:
            verbose_error(f"Workspace already initialized at {issues_dir}")
            typer.echo("Error: Workspace already initialized. Use --force to reinitialize.", err=True)
            raise typer.Exit(1)

        if force and already_initialized:
            verbose_log("Force flag enabled, will reinitialize existing workspace")

        # Create directory structure (idempotent - won't affect existing files)
        verbose_step("Creating directory structure", str(issues_dir))
        issues_dir.mkdir(parents=True, exist_ok=True)
        verbose_success(f"Created directory: {issues_dir}")

        # Update environment for this session
        os.environ["ISSUES_DB_PATH"] = str(db_path)
        verbose_log("Set ISSUES_DB_PATH environment variable", path=str(db_path))

        # Run Alembic migrations to create schema
        verbose_step("Setting up database schema")
        try:
            db_url = f"sqlite:///{db_path.absolute()}"

            # Import all models to ensure they're registered with SQLModel metadata
            verbose_log("Importing database models")
            from issue_tracker.adapters.db.models import (  # noqa: F401
                CommentModel,
                DependencyModel,
                EpicModel,
                IssueLabelModel,
                IssueModel,
                LabelModel,
            )

            # Use SQLModel to create all tables directly
            verbose_step("Creating tables using SQLModel metadata")
            from sqlmodel import SQLModel, create_engine

            connect_args = {"check_same_thread": False, "timeout": 30}
            engine = create_engine(db_url, echo=False, connect_args=connect_args)

            try:
                # Enable WAL mode for better concurrency
                with engine.begin() as conn:
                    conn.exec_driver_sql("PRAGMA journal_mode=WAL")
                    conn.exec_driver_sql("PRAGMA busy_timeout=30000")

                SQLModel.metadata.create_all(engine)
                verbose_success("Database schema created successfully")
            finally:
                # CRITICAL: Dispose engine to prevent memory leak
                # This is called by integration_cli_runner for every test
                # Without disposal, each test leaks 2-5MB of resources on Linux
                engine.dispose()

        except Exception as e:
            verbose_error("Schema creation error", error=e)
            typer.echo(f"Warning: Schema creation encountered an issue: {e}", err=True)
            # Create empty database file as fallback
            verbose_step("Creating empty database file as fallback")
            db_path.touch()
            verbose_success(f"Created empty database: {db_path}")

        # Create default configuration
        verbose_step("Creating default configuration")
        from issue_tracker.daemon.config import DaemonConfig

        config = DaemonConfig.default(Path.cwd())
        verbose_log(
            "Config settings",
            daemon_mode=config.daemon_mode,
            auto_start=config.auto_start_daemon,
            git_enabled=config.git_integration,
            sync_interval=config.sync_interval_seconds,
        )

        config.save(Path.cwd())
        verbose_success(f"Saved configuration to {config_path}")

        # Update or create AGENTS.md with issue CLI instructions
        verbose_step("Updating AGENTS.md with issue CLI instructions")
        agents_md_path = Path.cwd() / "AGENTS.md"
        _update_agents_md(agents_md_path)
        verbose_success("Updated AGENTS.md with issue tracker instructions")

        # Auto-start daemon if configured
        daemon_started = False
        if config.auto_start_daemon:
            verbose_step("Starting daemon (auto_start_daemon=true)")
            try:
                from issue_tracker.daemon.service import start_daemon

                start_daemon(Path.cwd(), detach=True)
                daemon_started = True
                verbose_success("Daemon started successfully")
            except Exception as e:  # noqa: S110
                verbose_error("Daemon start failed (non-fatal)", error=e)
                # Daemon start failure shouldn't block init
                pass
        else:
            verbose_log("Daemon auto-start disabled in configuration")

        verbose_section("Initialization Complete")

        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "status": "initialized",
                        "workspace": str(issues_dir),
                        "database": str(db_path),
                        "config": str(config_path),
                        "daemon_started": daemon_started,
                    }
                )
            )
        else:
            typer.echo(f"Initialized workspace in {issues_dir}")
            typer.echo(f"  Database: {db_path}")
            typer.echo(f"  Config: {config_path}")
            if daemon_started:
                typer.echo("  Daemon: started")
            typer.echo("\nNext steps:")
            typer.echo('  1. Create your first issue: issues create "My first issue"')
            typer.echo("  2. List issues: issues list")
    except typer.Exit:
        raise
    except Exception as e:
        verbose_error("Unexpected error during initialization", error=e)
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def sync(
    export_only: bool = typer.Option(False, "--export-only", "--export", help="Only export, don't import"),
    import_only: bool = typer.Option(False, "--import-only", "--import", help="Only import, don't export"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Manually trigger sync."""
    try:
        from pathlib import Path

        from issue_tracker.daemon.config import DaemonConfig
        from issue_tracker.daemon.ipc_server import IPCClient
        from issue_tracker.daemon.service import is_daemon_running, start_daemon

        workspace = Path.cwd()
        config = DaemonConfig.load(workspace)

        # Ensure daemon is running
        if not is_daemon_running(workspace):
            if config.auto_start_daemon:
                start_daemon(workspace, detach=True)
                import time

                time.sleep(0.5)  # Wait for daemon to start
            else:
                typer.echo("Error: Daemon not running. Start it with: issues daemons start", err=True)
                raise typer.Exit(1)

        # Trigger sync via IPC
        import asyncio

        client = IPCClient(config.get_socket_path())
        response = asyncio.run(client.send_request({"method": "sync"}))

        if "error" in response:
            typer.echo(f"Error: {response['error']}", err=True)
            raise typer.Exit(1)

        stats = response.get("stats", {})
        exported = stats.get("exported", 0)
        imported = stats.get("imported", 0)

        result = {
            "exported": 0 if import_only else exported,
            "imported": 0 if export_only else imported,
        }

        if json_output:
            typer.echo(json.dumps(result))
        else:
            typer.echo("Sync completed")
            if not import_only:
                typer.echo(f"  Exported: {result['exported']} issues")
            if not export_only:
                typer.echo(f"  Imported: {result['imported']} issues")
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Daemon subcommands
daemons_app = typer.Typer(help="Daemon management commands")
app.add_typer(daemons_app, name="daemons")


@daemons_app.command(name="list")
def list_daemons(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all daemons."""
    try:
        import glob
        from pathlib import Path

        from issue_tracker.daemon.config import DaemonConfig
        from issue_tracker.daemon.service import is_daemon_running

        daemons = []

        # Search for .issues directories with PID files
        for pid_file in glob.glob("**/.issues/daemon.pid", recursive=True):
            workspace = Path(pid_file).parent.parent
            if is_daemon_running(workspace):
                config = DaemonConfig.load(workspace)
                pid = int(config.get_pid_path().read_text())
                daemons.append(
                    {
                        "workspace": str(workspace.absolute()),
                        "pid": pid,
                        "socket": str(config.get_socket_path()),
                    }
                )

        if json_output:
            typer.echo(json.dumps(daemons))
        else:
            if not daemons:
                typer.echo("No daemons running")
            else:
                for daemon in daemons:
                    typer.echo(f"{daemon['workspace']} (PID: {daemon['pid']})")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@daemons_app.command()
def health(
    workspace: str | None = typer.Option(None, "--workspace", help="Specific workspace"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Check daemon health."""
    try:
        import asyncio
        from pathlib import Path

        from issue_tracker.daemon.config import DaemonConfig
        from issue_tracker.daemon.ipc_server import IPCClient
        from issue_tracker.daemon.service import is_daemon_running

        ws_path = Path(workspace) if workspace else Path.cwd()
        config = DaemonConfig.load(ws_path)

        if not is_daemon_running(ws_path):
            health_data = {"healthy": False, "error": "Daemon not running"}
        else:
            try:
                client = IPCClient(config.get_socket_path())
                health_data = asyncio.run(client.send_request({"method": "health"}))
            except Exception as e:
                health_data = {"healthy": False, "error": str(e)}

        if json_output:
            typer.echo(json.dumps(health_data))
        else:
            if health_data.get("healthy"):
                typer.echo("Daemon status: healthy")
                typer.echo(f"Uptime: {health_data.get('uptime_seconds', 0)}s")
                typer.echo(f"PID: {health_data.get('pid')}")
            else:
                typer.echo(f"Daemon status: unhealthy - {health_data.get('error', 'unknown')}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@daemons_app.command()
def stop(
    workspace: str | None = typer.Option(None, "--workspace", help="Specific workspace"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Stop daemon."""
    try:
        from pathlib import Path

        from issue_tracker.daemon.service import stop_daemon

        ws_path = Path(workspace) if workspace else Path.cwd()
        stopped = stop_daemon(ws_path)

        if json_output:
            typer.echo(json.dumps({"status": "stopped" if stopped else "not_running"}))
        else:
            if stopped:
                typer.echo("Daemon stopped")
            else:
                typer.echo("Daemon not running")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@daemons_app.command()
def restart(
    workspace: str | None = typer.Option(None, "--workspace", help="Specific workspace"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Restart daemon."""
    try:
        import time
        from pathlib import Path

        from issue_tracker.daemon.service import start_daemon, stop_daemon

        ws_path = Path(workspace) if workspace else Path.cwd()
        stop_daemon(ws_path)
        time.sleep(0.5)
        pid = start_daemon(ws_path, detach=True)

        if json_output:
            typer.echo(json.dumps({"status": "restarted", "pid": pid}))
        else:
            typer.echo(f"Daemon restarted (PID: {pid})")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@daemons_app.command()
def killall(
    force: bool = typer.Option(False, "--force", help="Force kill without confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Kill all daemons."""
    try:
        if not force:
            typer.echo("Error: --force flag required to kill all daemons", err=True)
            raise typer.Exit(1)

        import glob
        from pathlib import Path

        from issue_tracker.daemon.service import stop_daemon

        killed = 0
        for pid_file in glob.glob("**/.issues/daemon.pid", recursive=True):
            workspace = Path(pid_file).parent.parent
            if stop_daemon(workspace):
                killed += 1

        if json_output:
            typer.echo(json.dumps({"killed": killed}))
        else:
            typer.echo(f"Killed {killed} daemons")
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@daemons_app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    workspace: str | None = typer.Option(None, "--workspace", help="Specific workspace"),
):
    """View daemon logs."""
    try:
        import time
        from pathlib import Path

        from issue_tracker.daemon.config import DaemonConfig

        ws_path = Path(workspace) if workspace else Path.cwd()
        config = DaemonConfig.load(ws_path)
        log_path = config.get_log_path()

        if not log_path.exists():
            typer.echo("No log file found")
            return

        # Read last N lines
        with open(log_path, encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
            for line in recent_lines:
                typer.echo(line.rstrip())

        if follow:
            typer.echo("\n--- Following logs (Ctrl+C to exit) ---")
            with open(log_path, encoding="utf-8") as f:
                # Seek to end
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        typer.echo(line.rstrip())
                    else:
                        time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Export/Import commands
@app.command()
def export(
    output: str = typer.Option("./issues.jsonl", "-o", "--output", help="Output JSONL file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Export all issues to JSONL file."""
    try:
        from pathlib import Path

        service = get_issue_service()
        issues = service.list_issues()

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSONL (one JSON object per line)
        with open(output_path, "w", encoding="utf-8") as f:
            for issue in issues:
                issue_dict = {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description,
                    "status": issue.status.value if hasattr(issue.status, "value") else str(issue.status),
                    "priority": issue.priority.value if hasattr(issue.priority, "value") else int(issue.priority),
                    "type": issue.type.value if hasattr(issue.type, "value") else str(issue.type),
                    "assignee": issue.assignee,
                    "epic_id": issue.epic_id,
                    "labels": issue.labels,
                    "created_at": format_datetime_iso(issue.created_at),
                    "updated_at": format_datetime_iso(issue.updated_at),
                    "closed_at": format_datetime_iso(issue.closed_at),
                    "project_id": issue.project_id,
                }
                f.write(json.dumps(issue_dict) + "\n")

        if json_output:
            typer.echo(json.dumps({"exported": len(issues), "file": str(output_path)}))
        else:
            typer.echo(f"✓ Exported {len(issues)} issues to {output_path}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="import")
def import_issues(
    input: str = typer.Option(..., "-i", "--input", help="Input JSONL file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying"),
    dedupe_after: bool = typer.Option(False, "--dedupe-after", help="Detect duplicates after import"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Import issues from JSONL file."""
    try:
        from pathlib import Path

        service = get_issue_service()
        input_path = Path(input)

        if not input_path.exists():
            typer.echo(f"Error: File not found: {input_path}", err=True)
            raise typer.Exit(1)

        # Parse JSONL
        issues_data = []
        with open(input_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    issues_data.append(json.loads(line))

        new_count = 0
        updated_count = 0
        error_count = 0

        if dry_run:
            # Just analyze what would change
            for issue_data in issues_data:
                existing = service.get_issue(issue_data["id"])
                if existing:
                    updated_count += 1
                else:
                    new_count += 1

            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "dry_run": True,
                            "new": new_count,
                            "updated": updated_count,
                            "total": len(issues_data),
                        }
                    )
                )
            else:
                typer.echo(f"Dry run: Would import {len(issues_data)} issues")
                typer.echo(f"  New: {new_count}")
                typer.echo(f"  Updates: {updated_count}")
        else:
            # Actually import

            from issue_tracker.domain import IssuePriority, IssueStatus, IssueType

            for issue_data in issues_data:
                try:
                    # Convert string values back to enums
                    status_str = issue_data.get("status", "open")
                    status = IssueStatus[status_str.upper()] if isinstance(status_str, str) else status_str

                    priority_val = issue_data.get("priority", 2)
                    priority = IssuePriority(priority_val) if isinstance(priority_val, int) else priority_val

                    type_str = issue_data.get("type", "task")
                    issue_type = IssueType[type_str.upper()] if isinstance(type_str, str) else type_str

                    existing = service.get_issue(issue_data["id"])
                    if existing:
                        # Update existing
                        service.update_issue(
                            issue_data["id"],
                            title=issue_data.get("title"),
                            description=issue_data.get("description"),
                            priority=priority,
                            assignee=issue_data.get("assignee"),
                            epic_id=issue_data.get("epic_id"),
                        )
                        
                        # Update status if changed (requires transition)
                        if status != existing.status:
                            service.transition_issue(issue_data["id"], status)
                        
                        # Update labels if provided
                        if "labels" in issue_data:
                            updated_issue = service.get_issue(issue_data["id"])
                            if updated_issue:
                                # Remove labels not in new set
                                for label in updated_issue.labels:
                                    if label not in issue_data["labels"]:
                                        updated_issue = updated_issue.remove_label(label)
                                # Add labels from new set
                                for label in issue_data["labels"]:
                                    if label not in updated_issue.labels:
                                        updated_issue = updated_issue.add_label(label)
                                service.uow.issues.save(updated_issue)
                        
                        updated_count += 1
                    else:
                        # Create new with custom ID
                        service.create_issue(
                            title=issue_data["title"],
                            description=issue_data.get("description", ""),
                            priority=priority,
                            issue_type=issue_type,
                            assignee=issue_data.get("assignee"),
                            epic_id=issue_data.get("epic_id"),
                            labels=issue_data.get("labels", []),
                            custom_id=issue_data["id"],
                        )
                        new_count += 1
                except Exception as e:
                    typer.echo(f"Warning: Failed to import {issue_data.get('id', 'unknown')}: {e}", err=True)
                    error_count += 1
            
            # Commit all changes
            service.uow.session.commit()

            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "imported": new_count + updated_count,
                            "new": new_count,
                            "updated": updated_count,
                            "errors": error_count,
                        }
                    )
                )
            else:
                typer.echo(f"✓ Imported {new_count + updated_count} issues")
                typer.echo(f"  New: {new_count}")
                typer.echo(f"  Updated: {updated_count}")
                if error_count > 0:
                    typer.echo(f"  Errors: {error_count}")

            if dedupe_after:
                typer.echo("\nRunning duplicate detection...")
                # Would call duplicates detection here
                typer.echo("  (Duplicate detection not yet implemented)")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Cleanup command
@app.command()
def cleanup(
    older_than: int | None = typer.Option(None, "--older-than", help="Delete issues closed more than N days ago"),
    force: bool = typer.Option(False, "--force", help="Required to confirm deletion"),
    cascade: bool = typer.Option(False, "--cascade", help="Also delete dependent issues"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be deleted"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Delete closed issues."""
    try:
        if not force and not dry_run:
            typer.echo("Error: --force flag required for actual deletion", err=True)
            raise typer.Exit(1)

        from datetime import datetime, timedelta

        service = get_issue_service()
        issues = service.list_issues(status=IssueStatus.CLOSED)

        # Filter by age if specified
        if older_than:
            cutoff = datetime.now(UTC) - timedelta(days=older_than)
            issues = [i for i in issues if i.closed_at and i.closed_at < cutoff]

        if dry_run:
            if json_output:
                typer.echo(json.dumps({"dry_run": True, "would_delete": len(issues)}))
            else:
                typer.echo(f"Dry run: Would delete {len(issues)} closed issues")
                for issue in issues[:10]:  # Show first 10
                    typer.echo(f"  {issue.id}: {issue.title}")
                if len(issues) > 10:
                    typer.echo(f"  ... and {len(issues) - 10} more")
        else:
            deleted_count = 0
            for issue in issues:
                try:
                    service.delete_issue(issue.id)
                    deleted_count += 1
                except Exception as e:
                    typer.echo(f"Warning: Failed to delete {issue.id}: {e}", err=True)

            if json_output:
                typer.echo(json.dumps({"deleted": deleted_count}))
            else:
                typer.echo(f"✓ Deleted {deleted_count} closed issues")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Duplicate detection and merging
@app.command()
def duplicates(
    auto_merge: bool = typer.Option(False, "--auto-merge", help="Automatically merge all duplicates"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be merged"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Find and optionally merge duplicate issues."""
    try:
        import hashlib

        service = get_issue_service()
        all_issues = service.list_issues()

        # Group issues by content hash
        hash_groups: dict[str, list] = {}
        for issue in all_issues:
            # Hash based on title + description + status
            content = f"{issue.title}|{issue.description}|{issue.status.value if hasattr(issue.status, 'value') else str(issue.status)}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:12]

            if content_hash not in hash_groups:
                hash_groups[content_hash] = []
            hash_groups[content_hash].append(issue)

        # Find duplicates (groups with >1 issue)
        duplicate_groups = {k: v for k, v in hash_groups.items() if len(v) > 1}

        if not duplicate_groups:
            if json_output:
                typer.echo(json.dumps({"duplicates": 0, "groups": []}))
            else:
                typer.echo("No duplicates found")
            return

        if json_output:
            groups_data = []
            for hash_key, issues in duplicate_groups.items():
                group = {
                    "hash": hash_key,
                    "count": len(issues),
                    "issues": [{"id": i.id, "title": i.title} for i in issues],
                }
                groups_data.append(group)
            typer.echo(
                json.dumps({"duplicates": sum(len(v) - 1 for v in duplicate_groups.values()), "groups": groups_data})
            )
        else:
            typer.echo(f"Found {len(duplicate_groups)} duplicate group(s):\n")
            for hash_key, issues in duplicate_groups.items():
                typer.echo(f"Group (hash: {hash_key}):")
                for issue in issues:
                    typer.echo(f"  {issue.id}: {issue.title}")
                # Suggest merge command
                target = issues[0].id
                sources = [i.id for i in issues[1:]]
                typer.echo(f"  Suggested: issues merge {' '.join(sources)} --into {target}\n")

        if auto_merge and not dry_run:
            typer.echo("\n--auto-merge not yet implemented (use merge command manually)")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def merge(
    source_ids: list[str] = typer.Argument(..., help="Source issue IDs to merge"),
    into: str = typer.Option(..., "--into", help="Target issue ID to merge into"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview merge without applying"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Merge duplicate issues into a target issue."""
    try:
        service = get_issue_service()
        graph_service = get_graph_service()

        # Validate all issues exist
        target = service.get_issue(into)
        if not target:
            typer.echo(f"Error: Target issue not found: {into}", err=True)
            raise typer.Exit(1)

        sources = []
        for source_id in source_ids:
            if source_id == into:
                typer.echo(f"Error: Cannot merge issue into itself: {source_id}", err=True)
                raise typer.Exit(1)
            source = service.get_issue(source_id)
            if not source:
                typer.echo(f"Error: Source issue not found: {source_id}", err=True)
                raise typer.Exit(1)
            sources.append(source)

        if dry_run:
            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "dry_run": True,
                            "target": into,
                            "sources": source_ids,
                            "actions": [
                                "Close source issues",
                                "Migrate dependencies",
                                "Update text references",
                            ],
                        }
                    )
                )
            else:
                typer.echo(f"Dry run: Would merge {len(sources)} issue(s) into {into}")
                typer.echo("\nActions:")
                typer.echo(f"  1. Close {len(sources)} source issues")
                typer.echo(f"  2. Migrate dependencies to {into}")
                typer.echo("  3. Update text references")
        else:
            # Close source issues
            for source in sources:
                service.close_issue(source.id, reason=f"Merged into {into}")

            # Migrate dependencies
            for source in sources:
                # Get dependencies where source is involved
                deps = graph_service.get_dependencies(source.id)
                for dep in deps:
                    if dep.from_id == source.id:
                        # Redirect from source to target
                        graph_service.remove_dependency(source.id, dep.to_id)
                        graph_service.add_dependency(into, dep.to_id, dep.type)
                    else:
                        # Redirect to source to target
                        graph_service.remove_dependency(dep.from_id, source.id)
                        graph_service.add_dependency(dep.from_id, into, dep.type)

            if json_output:
                typer.echo(json.dumps({"merged": len(sources), "target": into}))
            else:
                typer.echo(f"✓ Merged {len(sources)} issue(s) into {into}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Rename prefix command
@app.command(name="rename-prefix")
def rename_prefix(
    new_prefix: str = typer.Argument(..., help="New prefix (e.g., 'kw-')"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Rename the issue prefix for all issues."""
    try:
        import re

        # Validate prefix format
        if not new_prefix:
            typer.echo("Error: Prefix cannot be empty", err=True)
            raise typer.Exit(1)

        if len(new_prefix) > 8:
            typer.echo("Error: Prefix too long (max 8 characters)", err=True)
            raise typer.Exit(1)

        if not re.match(r"^[a-z][a-z0-9-]*-?$", new_prefix):
            typer.echo(
                "Error: Invalid prefix format. Must start with letter, contain only lowercase letters/numbers/hyphens",
                err=True,
            )
            raise typer.Exit(1)

        # Ensure ends with hyphen
        if not new_prefix.endswith("-"):
            new_prefix += "-"

        service = get_issue_service()
        all_issues = service.list_issues()

        if not all_issues:
            typer.echo("No issues to rename")
            return

        # Detect current prefix from first issue
        first_id = all_issues[0].id
        current_prefix = first_id.rsplit("-", 1)[0] + "-" if "-" in first_id else ""

        if dry_run:
            renamed_count = len(all_issues)
            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "dry_run": True,
                            "current_prefix": current_prefix,
                            "new_prefix": new_prefix,
                            "affected": renamed_count,
                        }
                    )
                )
            else:
                typer.echo(f"Dry run: Would rename {renamed_count} issues")
                typer.echo(f"  From prefix: {current_prefix}")
                typer.echo(f"  To prefix: {new_prefix}")
                typer.echo("\nExamples:")
                for issue in all_issues[:5]:
                    old_id = issue.id
                    new_id = new_prefix + old_id.split("-", 1)[-1]
                    typer.echo(f"  {old_id} → {new_id}")
        else:
            typer.echo("Error: Rename prefix not yet fully implemented (too complex for initial version)", err=True)
            typer.echo("This operation requires:", err=True)
            typer.echo("  - Renaming all issue IDs in database", err=True)
            typer.echo("  - Updating all dependency references", err=True)
            typer.echo("  - Updating text references in descriptions/notes", err=True)
            typer.echo("  - Updating configuration", err=True)
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Edit command (HUMAN ONLY - NOT FOR MCP/AI AGENTS)
@app.command()
def edit(
    issue_id: str = typer.Argument(..., help="Issue ID to edit"),
    title: bool = typer.Option(False, "--title", help="Edit title"),
    design: bool = typer.Option(False, "--design", help="Edit design notes"),
    notes: bool = typer.Option(False, "--notes", help="Edit notes"),
    acceptance: bool = typer.Option(False, "--acceptance", help="Edit acceptance criteria"),
):
    """Edit issue fields in $EDITOR (HUMAN ONLY).

    WARNING: This command is for HUMAN use only and should NOT be exposed
    to AI agents or the MCP server. AI agents should use the update command
    with explicit field parameters instead.
    """
    try:
        import os
        import subprocess
        import tempfile

        service = get_issue_service()
        issue = service.get_issue(issue_id)
        if not issue:
            typer.echo(f"Error: Issue not found: {issue_id}", err=True)
            raise typer.Exit(1)

        # Determine what to edit
        if title:
            field_name = "title"
            current_content = issue.title
        elif design:
            field_name = "design"
            current_content = getattr(issue, "design", "")
        elif notes:
            field_name = "notes"
            current_content = getattr(issue, "notes", "")
        elif acceptance:
            field_name = "acceptance"
            current_content = getattr(issue, "acceptance", "")
        else:
            # Default to description
            field_name = "description"
            current_content = issue.description

        # Get editor from environment
        editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "notepad" if os.name == "nt" else "vi"))

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(current_content or "")
            temp_path = f.name

        try:
            # Open editor
            subprocess.run([editor, temp_path], check=True)  # noqa: S603

            # Read edited content
            with open(temp_path, encoding="utf-8") as f:
                new_content = f.read().strip()

            if new_content != current_content:
                # Update issue
                if field_name == "title":
                    service.update_issue(issue_id, title=new_content)
                elif field_name == "description":
                    service.update_issue(issue_id, description=new_content)
                else:
                    # For extended fields, would need service method support
                    typer.echo(f"Note: {field_name} editing not yet fully implemented", err=True)
                    return

                typer.echo(f"✓ Updated {field_name} for {issue_id}")
            else:
                typer.echo("No changes made")

        finally:
            # Clean up temp file
            os.unlink(temp_path)

    except subprocess.CalledProcessError:
        typer.echo("Editor exited with error", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Compact command (memory decay)
@app.command()
def compact(
    analyze: bool = typer.Option(False, "--analyze", help="Analyze and return candidates"),
    apply: bool = typer.Option(False, "--apply", help="Apply compaction"),
    issue_id: str | None = typer.Option(None, "--id", help="Issue ID to compact"),
    summary: str | None = typer.Option(None, "--summary", help="Summary file path (- for stdin)"),
    stats: bool = typer.Option(False, "--stats", help="Show compaction statistics"),
    tier: int | None = typer.Option(None, "--tier", help="Filter by tier (1=oldest/lowest priority)"),
    limit: int | None = typer.Option(None, "--limit", help="Limit number of candidates"),
    auto: bool = typer.Option(False, "--auto", help="AI-powered auto-compaction"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes"),
    all: bool = typer.Option(False, "--all", help="Process all candidates"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Compact/summarize old or low-priority issues (memory decay).

    Agent-driven workflow:
        1. issues compact --analyze --json  # Get candidates
        2. issues compact --apply --id <id> --summary summary.txt

    AI-powered workflow (requires ANTHROPIC_API_KEY):
        issues compact --auto --dry-run --all
    """
    try:
        if stats:
            # Show statistics
            service = get_issue_service()
            all_issues = service.list_issues()
            closed_count = len([i for i in all_issues if i.status == IssueStatus.CLOSED])

            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "total": len(all_issues),
                            "closed": closed_count,
                            "compacted": 0,  # Would track compacted issues
                        }
                    )
                )
            else:
                typer.echo("Issue statistics:")
                typer.echo(f"  Total: {len(all_issues)}")
                typer.echo(f"  Closed: {closed_count}")
                typer.echo("  Compacted: 0 (not yet tracked)")

        elif analyze:
            # Analyze and return candidates
            service = get_issue_service()
            all_issues = service.list_issues()

            # Simple tier logic: older + lower priority = higher tier
            from datetime import datetime

            now = datetime.now(UTC)
            candidates = []
            for issue in all_issues:
                if issue.status == IssueStatus.CLOSED:
                    days_old = (now - issue.updated_at).days if issue.updated_at else 0
                    priority_val = issue.priority.value if hasattr(issue.priority, "value") else int(issue.priority)

                    # Tier 1: >90 days old, P3-P4
                    # Tier 2: >60 days old, P2-P4
                    # Tier 3: >30 days old, any priority
                    issue_tier = 3
                    if days_old > 90 and priority_val >= 3:
                        issue_tier = 1
                    elif days_old > 60 and priority_val >= 2:
                        issue_tier = 2

                    if tier is None or issue_tier <= tier:
                        candidates.append(
                            {"id": issue.id, "title": issue.title, "tier": issue_tier, "days_old": days_old}
                        )

            # Apply limit
            if limit:
                candidates = candidates[:limit]

            if json_output:
                typer.echo(json.dumps({"candidates": len(candidates), "issues": candidates}))
            else:
                typer.echo(f"Found {len(candidates)} compaction candidates:\n")
                for c in candidates[:10]:
                    typer.echo(f"  {c['id']} (tier {c['tier']}, {c['days_old']} days old): {c['title']}")
                if len(candidates) > 10:
                    typer.echo(f"  ... and {len(candidates) - 10} more")

        elif apply:
            if not issue_id:
                typer.echo("Error: --id required for apply mode", err=True)
                raise typer.Exit(1)
            if not summary:
                typer.echo("Error: --summary required for apply mode", err=True)
                raise typer.Exit(1)

            # Read summary
            if summary == "-":
                import sys

                summary_text = sys.stdin.read()
            else:
                from pathlib import Path

                with open(Path(summary), encoding="utf-8") as f:
                    summary_text = f.read()

            if not dry_run:
                service = get_issue_service()
                # Update issue with summary (would replace description)
                service.update_issue(issue_id, description=f"[COMPACTED]\n\n{summary_text}")
                typer.echo(f"✓ Compacted {issue_id}")
            else:
                typer.echo(f"Dry run: Would compact {issue_id} with summary ({len(summary_text)} chars)")

        elif auto:
            typer.echo("Error: AI-powered auto-compaction requires ANTHROPIC_API_KEY", err=True)
            typer.echo("This feature is not yet implemented", err=True)
            raise typer.Exit(1)

        else:
            typer.echo("Error: Must specify --analyze, --apply, --stats, or --auto", err=True)
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Add cycles detection to dep subcommand


@app.command()
def template_save(
    name: str = typer.Argument(..., help="Template name"),
    title: str = typer.Option("", "--title", help="Default title pattern"),
    description: str = typer.Option("", "-d", "--description", help="Default description"),
    type: str = typer.Option("task", "-t", "--type", help="Default issue type"),
    priority: int = typer.Option(2, "-p", "--priority", help="Default priority"),
    labels: str | None = typer.Option(None, "-l", "--labels", help="Comma-separated labels"),
    assignee: str | None = typer.Option(None, "-a", "--assignee", help="Default assignee"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Save an issue template for reuse."""
    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_issues_folder
        from issue_tracker.templates import Template, TemplateManager

        # Get templates directory
        issues_folder = Path(get_issues_folder())
        templates_dir = issues_folder / "templates"
        manager = TemplateManager(templates_dir)

        # Create template
        label_list = [label.strip() for label in labels.split(",")] if labels else []
        template = Template(
            name=name,
            title=title,
            description=description,
            type=type,
            priority=priority,
            labels=label_list,
            assignee=assignee,
        )

        manager.save_template(template)

        if json_output:
            typer.echo(json.dumps(template.to_dict()))
        else:
            typer.echo(f"Template '{name}' saved")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def template_list(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all available templates."""
    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_issues_folder
        from issue_tracker.templates import TemplateManager

        issues_folder = Path(get_issues_folder())
        templates_dir = issues_folder / "templates"
        manager = TemplateManager(templates_dir)

        names = manager.list_templates()

        if json_output:
            typer.echo(json.dumps(names))
        else:
            if not names:
                typer.echo("No templates found")
            else:
                typer.echo("Available templates:")
                for name in names:
                    typer.echo(f"  - {name}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def template_show(
    name: str = typer.Argument(..., help="Template name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show details of a template."""
    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_issues_folder
        from issue_tracker.templates import TemplateManager

        issues_folder = Path(get_issues_folder())
        templates_dir = issues_folder / "templates"
        manager = TemplateManager(templates_dir)

        template = manager.load_template(name)
        if not template:
            typer.echo(f"Template '{name}' not found", err=True)
            raise typer.Exit(1)

        if json_output:
            typer.echo(json.dumps(template.to_dict()))
        else:
            typer.echo(f"Template: {template.name}")
            typer.echo(f"  Title: {template.title}")
            typer.echo(f"  Type: {template.type}")
            typer.echo(f"  Priority: {template.priority}")
            if template.labels:
                typer.echo(f"  Labels: {', '.join(template.labels)}")
            if template.assignee:
                typer.echo(f"  Assignee: {template.assignee}")
            if template.description:
                typer.echo(f"  Description: {template.description}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def template_delete(
    name: str = typer.Argument(..., help="Template name"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Delete a template."""
    try:
        from pathlib import Path

        from issue_tracker.cli.dependencies import get_issues_folder
        from issue_tracker.templates import TemplateManager

        issues_folder = Path(get_issues_folder())
        templates_dir = issues_folder / "templates"
        manager = TemplateManager(templates_dir)

        if not force:
            confirm = typer.confirm(f"Delete template '{name}'?")
            if not confirm:
                typer.echo("Cancelled")
                return

        deleted = manager.delete_template(name)

        if json_output:
            typer.echo(json.dumps({"deleted": deleted, "name": name}))
        else:
            if deleted:
                typer.echo(f"Template '{name}' deleted")
            else:
                typer.echo(f"Template '{name}' not found", err=True)
                raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Mount command subgroups
app.add_typer(comments_app, name="comments")
app.add_typer(dependencies_app, name="dependencies")
app.add_typer(epics_app, name="epics")
app.add_typer(instructions_app, name="instructions")
app.add_typer(labels_app, name="labels")


# Top-level bulk label commands for consistency with other bulk commands
@app.command(name="bulk-label-add")
def bulk_label_add_top(
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

    For consistency with other bulk commands (bulk-close, bulk-update).

    Examples:
        issues bulk-label-add urgent,backend issue-1 issue-2
        issues bulk-label-add needs-review --status open --type bug
    """
    from issue_tracker.cli.commands.labels import bulk_add

    # Call the labels bulk-add command
    bulk_add(labels, issue_ids, status, type, priority, assignee, label_filter, json_output)


@app.command(name="bulk-label-remove")
def bulk_label_remove_top(
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

    For consistency with other bulk commands (bulk-close, bulk-update).

    Examples:
        issues bulk-label-remove old-tag issue-1 issue-2
        issues bulk-label-remove wont-fix --status closed --type bug
    """
    from issue_tracker.cli.commands.labels import bulk_remove

    # Call the labels bulk-remove command
    bulk_remove(labels, issue_ids, status, type, priority, assignee, label_filter, json_output)


if __name__ == "__main__":
    app()

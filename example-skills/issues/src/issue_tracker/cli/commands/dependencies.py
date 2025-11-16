"""Dependency management commands."""

import json
from typing import Any

import typer

app = typer.Typer(name="dependencies", help="Manage issue dependencies and blocking relationships")


def get_issue_service():
    """Import and return issue service (avoids circular import)."""
    from issue_tracker.cli.app import get_issue_service as _get_issue_service

    return _get_issue_service()


def get_graph_service():
    """Import and return graph service (avoids circular import)."""
    from issue_tracker.cli.app import get_graph_service as _get_graph_service

    return _get_graph_service()


@app.command(name="add")
def add(
    from_id: str = typer.Argument(..., help="Source issue ID"),
    dep_type: str = typer.Argument(..., help="Dependency type (blocks, depends-on, related-to, discovered-from)"),
    to_id: str = typer.Argument(..., help="Target issue ID"),
    skip_cycle_check: bool = typer.Option(False, "--skip-cycle-check", help="Skip circular dependency check"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Add a dependency between two issues with full validation.

    Validates:
    - Both issues exist
    - Prevents self-dependencies
    - Checks for circular dependencies
    - Validates dependency type
    - Prevents duplicate dependencies

    Examples:
        issues dependencies add issue-1 blocks issue-2
        issues dependencies add issue-1 depends-on issue-2
        issues dependencies add issue-1 related-to issue-2 --skip-cycle-check
    """
    try:
        from issue_tracker.domain.entities.dependency import DependencyType

        graph_service = get_graph_service()
        service = get_issue_service()

        # 1. Validate dependency type
        try:
            dep_type_enum = DependencyType(dep_type)
        except ValueError:
            valid_types = ", ".join([t.value for t in DependencyType])
            typer.echo(f"Error: Invalid dependency type '{dep_type}'. Valid types: {valid_types}")
            raise typer.Exit(1)

        # 2. Prevent self-dependencies
        if from_id == to_id:
            typer.echo(f"Error: Cannot create self-dependency. Issue {from_id} cannot depend on itself.")
            raise typer.Exit(1)

        # 3. Check both issues exist
        try:
            from_issue = service.get_issue(from_id)
        except Exception:
            typer.echo(f"Error: Source issue '{from_id}' not found")
            raise typer.Exit(1)

        try:
            to_issue = service.get_issue(to_id)
        except Exception:
            typer.echo(f"Error: Target issue '{to_id}' not found")
            raise typer.Exit(1)

        # 4. Check for duplicate dependency
        existing_deps = graph_service.get_dependencies(from_id, dep_type_enum)
        for dep in existing_deps:
            if dep.to_issue_id == to_id:
                typer.echo(f"Error: Dependency already exists: {from_id} {dep_type} {to_id}")
                raise typer.Exit(1)

        # 5. Check for circular dependencies (unless skipped)
        if not skip_cycle_check:
            # Temporarily add the dependency to check for cycles
            # The service already does this, but we can provide a better error message
            pass  # Service will handle this

        # Add dependency (service will also validate)
        dependency = graph_service.add_dependency(from_id, to_id, dep_type_enum)

        dep_dict = {
            "from": dependency.from_issue_id,
            "from_title": from_issue.title,
            "type": dependency.dependency_type.value,
            "to": dependency.to_issue_id,
            "to_title": to_issue.title,
        }

        if json_output:
            typer.echo(json.dumps(dep_dict))
        else:
            typer.echo(
                f"✓ Added dependency: {from_id} ({from_issue.title[:30]}) {dep_type} {to_id} ({to_issue.title[:30]})"
            )
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="remove")
def remove(
    from_id: str = typer.Argument(..., help="Source issue ID"),
    dep_type_or_to: str = typer.Argument(..., help="Dependency type or target ID"),
    to_id: str | None = typer.Argument(None, help="Target issue ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Remove a dependency."""
    try:
        from issue_tracker.domain.entities.dependency import DependencyType

        graph_service = get_graph_service()

        # If to_id is None, dep_type_or_to is the target ID (remove any type)
        if to_id is None:
            target = dep_type_or_to
            # Remove all dependencies between from_id and target (no type specified)
            graph_service.remove_dependency(from_id, target, None)

            if json_output:
                typer.echo(json.dumps({"from": from_id, "to": target, "removed": True}))
            else:
                typer.echo(f"Removed dependency: {from_id} -> {target}")
        else:
            # Specific type removal
            dep_type = dep_type_or_to
            try:
                dep_type_enum = DependencyType(dep_type)
            except ValueError:
                typer.echo(f"Error: Invalid dependency type '{dep_type}'", err=True)
                raise typer.Exit(1)

            graph_service.remove_dependency(from_id, to_id, dep_type_enum)

            if json_output:
                typer.echo(json.dumps({"from": from_id, "type": dep_type, "to": to_id, "removed": True}))
            else:
                typer.echo(f"Removed dependency: {from_id} {dep_type} {to_id}")
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="list")
def list_deps(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    type: str | None = typer.Option(None, "--type", help="Filter by dependency type"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List dependencies."""
    try:
        from issue_tracker.domain.entities.dependency import DependencyType

        graph_service = get_graph_service()

        # Convert type filter if specified
        type_filter = None
        if type:
            try:
                type_filter = DependencyType(type)
            except ValueError:
                typer.echo(f"Error: Invalid dependency type '{type}'", err=True)
                raise typer.Exit(1)

        # Get both outgoing and incoming dependencies
        outgoing = graph_service.get_dependencies(issue_id, type_filter)
        incoming = graph_service.get_dependents(issue_id, type_filter)

        # Combine and convert to dicts
        deps = []
        for dep in outgoing:
            deps.append({"from": dep.from_issue_id, "type": dep.dependency_type.value, "to": dep.to_issue_id})
        for dep in incoming:
            deps.append({"from": dep.from_issue_id, "type": dep.dependency_type.value, "to": dep.to_issue_id})

        if json_output:
            typer.echo(json.dumps(deps))
        else:
            if not deps:
                typer.echo(f"No dependencies for {issue_id}")
            else:
                for dep in deps:
                    typer.echo(f"{dep['from']} {dep['type']} {dep['to']}")
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="list-all")
def list_all(
    type: str | None = typer.Option(None, "--type", help="Filter by dependency type"),
    from_issue: str | None = typer.Option(None, "--from", help="Filter by source issue"),
    to_issue: str | None = typer.Option(None, "--to", help="Filter by target issue"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all dependencies in the system with optional filtering.

    Shows global view of all dependency relationships.

    Examples:
        issues dependencies list-all                          # List all dependencies
        issues dependencies list-all --type blocks            # Only blocking dependencies
        issues dependencies list-all --from issue-123         # All deps from issue-123
        issues dependencies list-all --to issue-456           # All deps to issue-456
    """
    try:
        graph_service = get_graph_service()
        service = get_issue_service()

        # Get all issues to iterate through
        all_issues = service.list_issues()

        # Collect all dependencies
        all_deps = []
        seen = set()  # Track (from, to, type) tuples to avoid duplicates

        for issue in all_issues:
            # Get outgoing dependencies
            outgoing = graph_service.get_dependencies(issue.id, None)
            for dep in outgoing:
                dep_tuple = (dep.from_issue_id, dep.to_issue_id, dep.dependency_type.value)
                if dep_tuple not in seen:
                    seen.add(dep_tuple)
                    all_deps.append(dep)

        # Apply filters
        filtered_deps = []
        for dep in all_deps:
            # Type filter
            if type and dep.dependency_type.value != type:
                continue
            # From filter
            if from_issue and dep.from_issue_id != from_issue:
                continue
            # To filter
            if to_issue and dep.to_issue_id != to_issue:
                continue

            filtered_deps.append(dep)

        # Convert to output format
        if json_output:
            deps_data = []
            for dep in filtered_deps:
                # Get issue titles for context
                try:
                    from_title = service.get_issue(dep.from_issue_id).title
                except Exception:
                    from_title = "Unknown"
                try:
                    to_title = service.get_issue(dep.to_issue_id).title
                except Exception:
                    to_title = "Unknown"

                deps_data.append(
                    {
                        "from": dep.from_issue_id,
                        "from_title": from_title,
                        "type": dep.dependency_type.value,
                        "to": dep.to_issue_id,
                        "to_title": to_title,
                        "created_at": dep.created_at.isoformat() if hasattr(dep, "created_at") else None,
                    }
                )
            typer.echo(json.dumps(deps_data))
        else:
            if not filtered_deps:
                typer.echo("No dependencies found")
            else:
                typer.echo(f"Found {len(filtered_deps)} dependenc{'y' if len(filtered_deps) == 1 else 'ies'}:\n")

                # Group by type for better readability
                by_type: dict[str, list] = {}
                for dep in filtered_deps:
                    dep_type = dep.dependency_type.value
                    if dep_type not in by_type:
                        by_type[dep_type] = []
                    by_type[dep_type].append(dep)

                for dep_type, deps in by_type.items():
                    typer.echo(f"{dep_type.upper()} ({len(deps)}):")
                    for dep in deps:
                        # Get titles
                        try:
                            from_title = service.get_issue(dep.from_issue_id).title[:40]
                        except Exception:
                            from_title = "Unknown"
                        try:
                            to_title = service.get_issue(dep.to_issue_id).title[:40]
                        except Exception:
                            to_title = "Unknown"

                        typer.echo(f"  {dep.from_issue_id} ({from_title}) -> {dep.to_issue_id} ({to_title})")
                    typer.echo()
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="tree")
def tree(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    depth: int | None = typer.Option(None, "--depth", help="Maximum depth"),
    format: str = typer.Option("text", "--format", help="Output format: text, json, mermaid"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON (deprecated, use --format json)"),
):
    """Show dependency tree with multiple output formats.

    Examples:
        issues dependencies tree issue-123                    # ASCII tree (default)
        issues dependencies tree issue-123 --format json      # Enhanced JSON with full details
        issues dependencies tree issue-123 --format mermaid   # Mermaid diagram
        issues dependencies tree issue-123 --depth 2          # Limit tree depth
    """
    try:
        graph_service = get_graph_service()

        # Validate format
        valid_formats = ["text", "json", "mermaid"]
        if format not in valid_formats:
            typer.echo(f"Error: Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}", err=True)
            raise typer.Exit(1)

        # Build dependency tree using service
        tree_data = graph_service.build_dependency_tree(issue_id, max_depth=depth)

        # Handle deprecated --json flag
        if json_output:
            format = "json"

        if format == "json":
            # Enhanced JSON output with full issue details
            def convert_tree_to_dict(node: dict[str, Any]) -> dict[str, Any]:
                """Convert dependency tree node to dictionary format."""
                result = {
                    "issue_id": node["issue_id"],
                    "is_circular": node.get("is_circular", False),
                    "depth": node["depth"],
                }

                if node.get("issue"):
                    issue = node["issue"]
                    result["issue"] = {
                        "id": issue.id,
                        "title": issue.title,
                        "description": issue.description,
                        "status": issue.status.value,
                        "priority": issue.priority.value,
                        "type": issue.type.value,
                        "assignee": issue.assignee,
                        "labels": issue.labels,
                        "created_at": issue.created_at.isoformat().replace("+00:00", "Z"),
                        "updated_at": issue.updated_at.isoformat().replace("+00:00", "Z"),
                    }

                if node.get("dependency_type"):
                    result["dependency_type"] = node["dependency_type"]

                if node.get("dependencies"):
                    result["dependencies"] = [convert_tree_to_dict(child) for child in node["dependencies"]]

                return result

            typer.echo(json.dumps(convert_tree_to_dict(tree_data), indent=2))

        elif format == "mermaid":
            # Mermaid diagram format
            lines = ["graph TD"]
            visited = set()

            def add_mermaid_node(node: dict[str, Any], parent_id: str | None = None):
                """Add node to mermaid diagram."""
                node_id = node["issue_id"]

                if node_id not in visited:
                    visited.add(node_id)
                    # Add node with title and status
                    if node.get("issue"):
                        issue = node["issue"]
                        title = issue.title.replace('"', "'")  # Escape quotes
                        status = issue.status.value
                        # Use different shapes for different statuses
                        if status == "closed":
                            lines.append(f'    {node_id}["{title}<br/>[{status}]"]')
                        elif status == "in_progress":
                            lines.append(f'    {node_id}["{title}<br/>[{status}]"]')
                            lines.append(f"    style {node_id} fill:#ffeb3b")  # Yellow for in-progress
                        elif status == "blocked":
                            lines.append(f'    {node_id}["{title}<br/>[{status}]"]')
                            lines.append(f"    style {node_id} fill:#f44336")  # Red for blocked
                        else:
                            lines.append(f'    {node_id}["{title}<br/>[{status}]"]')
                    else:
                        lines.append(f'    {node_id}["{node_id}"]')

                if parent_id:
                    dep_type = node.get("dependency_type", "depends_on")
                    if node.get("is_circular"):
                        lines.append(f"    {parent_id} -.->|{dep_type} [CYCLE]| {node_id}")
                    else:
                        lines.append(f"    {parent_id} -->|{dep_type}| {node_id}")

                if node.get("dependencies") and not node.get("is_circular"):
                    for child in node["dependencies"]:
                        add_mermaid_node(child, node_id)

            add_mermaid_node(tree_data)
            typer.echo("\n".join(lines))

        else:  # text format (default)

            def print_tree(node: dict[str, Any], prefix: str = "", is_last: bool = True):
                """Print dependency tree in text format."""
                connector = "└── " if is_last else "├── "
                dep_type = f" ({node.get('dependency_type', '')})" if "dependency_type" in node else ""
                cycle_marker = " [CYCLE]" if node.get("is_circular") else ""

                # Enhanced text output with title and status
                if node.get("issue"):
                    issue = node["issue"]
                    title = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
                    status = issue.status.value
                    typer.echo(f"{prefix}{connector}{node['issue_id']}: {title} [{status}]{dep_type}{cycle_marker}")
                else:
                    typer.echo(f"{prefix}{connector}{node['issue_id']}{dep_type}{cycle_marker}")

                if node.get("dependencies"):
                    extension = "    " if is_last else "│   "
                    for i, child in enumerate(node["dependencies"]):
                        print_tree(child, prefix + extension, i == len(node["dependencies"]) - 1)

            typer.echo(f"Dependency tree for {issue_id}:")
            print_tree(tree_data)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="cycles")
def cycles(
    fix: bool = typer.Option(False, "--fix", help="Suggest dependency removals to break cycles"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Detect dependency cycles with detailed reporting.

    Shows cycle paths with issue titles, cycle length/severity, and optional
    suggestions for breaking cycles.

    Examples:
        issues dependencies cycles                    # Detect all cycles
        issues dependencies cycles --fix              # Show suggestions to break cycles
        issues dependencies cycles --json             # JSON output
    """
    try:
        graph_service = get_graph_service()
        service = get_issue_service()

        # Detect cycles using service
        cycles_found = graph_service.detect_cycles()

        if json_output:
            # Enhanced JSON with titles and metadata
            detailed_cycles = []
            for cycle in cycles_found:
                cycle_issues = []
                for issue_id in cycle:
                    try:
                        issue = service.get_issue(issue_id)
                        cycle_issues.append(
                            {
                                "id": issue.id,
                                "title": issue.title,
                                "status": issue.status.value,
                                "priority": int(issue.priority),
                            }
                        )
                    except Exception:
                        cycle_issues.append({"id": issue_id, "title": "Unknown"})

                detailed_cycles.append(
                    {
                        "cycle_length": len(cycle),
                        "severity": "high" if len(cycle) <= 3 else "medium" if len(cycle) <= 5 else "low",
                        "issues": cycle_issues,
                        "path": cycle,
                    }
                )

            typer.echo(json.dumps(detailed_cycles))
        else:
            if not cycles_found:
                typer.echo("No dependency cycles found")
            else:
                typer.echo(f"Found {len(cycles_found)} cycle(s):\n")
                for i, cycle in enumerate(cycles_found, 1):
                    cycle_length = len(cycle)
                    severity = "HIGH" if cycle_length <= 3 else "MEDIUM" if cycle_length <= 5 else "LOW"

                    typer.echo(f"Cycle {i} [Length: {cycle_length}, Severity: {severity}]:")

                    # Show detailed path with titles
                    for j, issue_id in enumerate(cycle):
                        try:
                            issue = service.get_issue(issue_id)
                            title = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
                            status = issue.status.value
                            typer.echo(f"  {j + 1}. {issue_id}: {title} [{status}]")
                        except Exception:
                            typer.echo(f"  {j + 1}. {issue_id}: (unknown)")

                    # Close the cycle
                    typer.echo(f"  └─> Back to {cycle[0]}")

                    # Suggest fixes
                    if fix:
                        typer.echo("\n  💡 Suggestion: Remove dependency between:")
                        # Suggest removing the last link in the cycle (easiest to break)
                        from_issue = cycle[-1]
                        to_issue = cycle[0]
                        typer.echo(f"     {from_issue} -> {to_issue}")
                        typer.echo(f"     Command: issues dependencies remove {from_issue} {to_issue}")

                    typer.echo()  # Blank line between cycles
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

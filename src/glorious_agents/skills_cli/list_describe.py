"""Skills list and describe commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from glorious_agents.core.registry import get_registry

console = Console()


def list_skills() -> None:
    """List all currently loaded skills."""
    registry = get_registry()
    skills = registry.list_all()

    if not skills:
        console.print("[yellow]No skills loaded.[/yellow]")
        return

    table = Table(title="Loaded Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Origin", style="green")
    table.add_column("Requires", style="yellow")

    for skill in skills:
        requires_str = ", ".join(skill.requires) if skill.requires else "-"
        table.add_row(skill.name, skill.version, skill.origin, requires_str)

    console.print(table)


def describe_skill(skill_name: str) -> None:
    """Describe a specific skill and display its detailed information."""
    from glorious_agents.core.db import get_connection

    registry = get_registry()
    manifest = registry.get_manifest(skill_name)

    if not manifest:
        console.print(f"[red]Skill '{skill_name}' not found.[/red]")
        return

    # Header
    console.print(f"[bold cyan]{manifest.name}[/bold cyan] v{manifest.version}")
    console.print(f"[dim]{manifest.description}[/dim]\n")

    # Origin
    console.print(f"[bold]Origin:[/bold] {manifest.origin}")

    # Dependencies
    if manifest.requires:
        requires_list = [f"[cyan]{req}[/cyan]" for req in manifest.requires]
        console.print(f"[bold]Requires skills:[/bold] {', '.join(requires_list)}")
    else:
        console.print("[bold]Requires skills:[/bold] None")

    # Find skills that depend on this skill
    all_skills = registry.list_all()
    dependents = [s.name for s in all_skills if skill_name in s.requires]
    if dependents:
        dependents_list = [f"[cyan]{dep}[/cyan]" for dep in dependents]
        console.print(f"[bold]Required by:[/bold] {', '.join(dependents_list)}")

    console.print()

    # Commands
    app = registry.get_app(skill_name)
    if app and hasattr(app, "registered_commands"):
        console.print("[bold]Commands:[/bold]")
        for cmd in app.registered_commands:
            cmd_name = cmd.name or cmd.callback.__name__
            cmd_help = cmd.help or cmd.callback.__doc__ or "No description"
            cmd_help_line = cmd_help.split("\n")[0].strip()
            console.print(f"  • [cyan]{cmd_name}[/cyan] - {cmd_help_line}")
        console.print()

    # Database info
    console.print(f"[bold]Database:[/bold] {'Yes' if manifest.requires_db else 'No'}")
    if manifest.requires_db:
        try:
            conn = get_connection()
            skill_table_prefix = skill_name.replace("-", "_")
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                (f"{skill_table_prefix}%",),
            )
            tables = [row[0] for row in cur.fetchall()]
            if tables:
                console.print(f"[bold]Tables:[/bold] {', '.join(tables)}")
            else:
                console.print("[yellow]No tables found (schema may not be initialized)[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not query database: {e}[/yellow]")
    console.print()

    # Configuration
    if manifest.config_schema:
        console.print("[bold]Configuration options:[/bold]")
        for key, schema in manifest.config_schema.items():
            cfg_type = schema.get("type", "str")
            default = schema.get("default", "N/A")
            choices = schema.get("choices")
            if choices:
                console.print(
                    f"  • [cyan]{key}[/cyan] ({cfg_type}) = {default} [choices: {choices}]"
                )
            else:
                console.print(f"  • [cyan]{key}[/cyan] ({cfg_type}) = {default}")
        console.print()

    # Documentation paths
    if manifest.path:
        console.print(f"[bold]Location:[/bold] {manifest.path}")
        if manifest.internal_doc:
            internal_path = Path(manifest.path) / manifest.internal_doc
            status = "✓" if internal_path.exists() else "✗"
            console.print(f"[bold]Internal docs:[/bold] {status} {manifest.internal_doc}")
        if manifest.external_doc:
            external_path = Path(manifest.path) / manifest.external_doc
            status = "✓" if external_path.exists() else "✗"
            console.print(f"[bold]External docs:[/bold] {status} {manifest.external_doc}")
        console.print()

    # Display usage documentation if available
    if manifest.external_doc and manifest.path:
        usage_path = Path(manifest.path) / manifest.external_doc
        if usage_path.exists():
            console.print("[bold]─── Usage Documentation ───[/bold]\n")
            console.print(usage_path.read_text())
        else:
            console.print(f"[yellow]Usage documentation not found at: {usage_path}[/yellow]")
    elif manifest.external_doc:
        console.print(f"[bold]External Docs:[/bold] {manifest.external_doc}")
    else:
        console.print("[dim]Tip: Add a usage.md file for user-friendly documentation.[/dim]")


def check_skill(skill_name: str) -> None:
    """Run health checks on a specific skill."""
    from glorious_agents.core.db import get_connection

    registry = get_registry()
    manifest = registry.get_manifest(skill_name)

    if not manifest:
        console.print(f"[red]✗ Skill '{skill_name}' not found[/red]")
        return

    issues = []
    warnings = []

    console.print(f"[cyan]Checking skill: {skill_name}[/cyan]")

    # Check required dependencies loaded
    if manifest.requires:
        for dep in manifest.requires:
            if not registry.get_manifest(dep):
                issues.append(f"Missing dependency: {dep}")

    # Check schema tables exist
    if manifest.requires_db and manifest.schema_file:
        try:
            conn = get_connection()
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                (f"{skill_name.replace('-', '_')}%",),
            )
            tables = cur.fetchall()
            if not tables:
                warnings.append(f"No schema tables found for {skill_name}")
        except Exception as e:
            issues.append(f"Database check failed: {e}")

    # Check entry point accessible
    try:
        app = registry.get_app(skill_name)
        if not app:
            issues.append("Entry point not loaded")
    except Exception as e:
        issues.append(f"Entry point error: {e}")

    # Check documentation files
    if manifest.path:
        skill_path = Path(manifest.path)
        if manifest.internal_doc:
            if not (skill_path / manifest.internal_doc).exists():
                warnings.append(f"Missing internal docs: {manifest.internal_doc}")
        if manifest.external_doc:
            if not (skill_path / manifest.external_doc).exists():
                warnings.append(f"Missing external docs: {manifest.external_doc}")

    # Display results
    if issues:
        console.print(f"[red]✗ {skill_name} - {len(issues)} issue(s) found[/red]")
        for issue in issues:
            console.print(f"  [red]✗[/red] {issue}")
    elif warnings:
        console.print(f"[yellow]⚠ {skill_name} - {len(warnings)} warning(s)[/yellow]")
        for warning in warnings:
            console.print(f"  [yellow]⚠[/yellow] {warning}")
    else:
        console.print(f"[green]✓ {skill_name} - All checks passed[/green]")


def doctor() -> None:
    """Run health checks on all loaded skills."""
    registry = get_registry()
    skills = registry.list_all()

    if not skills:
        console.print("[yellow]No skills loaded.[/yellow]")
        return

    console.print(f"[cyan]Running diagnostics on {len(skills)} skill(s)...[/cyan]\n")

    for manifest in skills:
        check_skill(manifest.name)

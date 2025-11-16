"""CLI commands for database migration management."""

import typer
from rich.console import Console
from rich.table import Table

from glorious_agents.core.migrations import (
    create_migration_file,
    get_current_version,
    get_migration_history,
    run_migrations,
)

app = typer.Typer(help="Database migration management")
console = Console()


@app.command()
def create(
    skill_name: str = typer.Argument(..., help="Skill name"),
    description: str = typer.Argument(..., help="Migration description"),
    migrations_dir: str = typer.Option("./migrations", "--dir", "-d", help="Migrations directory"),
) -> None:
    """Create a new migration file."""
    from pathlib import Path

    try:
        migration_path = create_migration_file(skill_name, Path(migrations_dir), description)
        console.print(f"[green]✓ Created migration:[/green] {migration_path}")
        console.print(f"[dim]Edit the file to add your SQL statements[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def run(
    skill_name: str = typer.Argument(..., help="Skill name"),
    migrations_dir: str = typer.Option("./migrations", "--dir", "-d", help="Migrations directory"),
) -> None:
    """Run pending migrations for a skill."""
    from pathlib import Path

    try:
        applied = run_migrations(skill_name, Path(migrations_dir))
        if applied:
            console.print(f"[green]✓ Applied {len(applied)} migration(s):[/green]")
            for version in applied:
                console.print(f"  - Version {version}")
        else:
            console.print("[yellow]No pending migrations[/yellow]")
    except Exception as e:
        console.print(f"[red]Migration failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def status(
    skill_name: str = typer.Option(None, "--skill", "-s", help="Filter by skill name"),
) -> None:
    """Show migration status."""
    from glorious_agents.core.db import get_connection

    try:
        if skill_name:
            # Show status for specific skill
            version = get_current_version(skill_name)
            console.print(f"[bold]{skill_name}[/bold]")
            console.print(f"  Current version: {version}")

            history = get_migration_history(skill_name)
            if history:
                console.print(f"  Applied migrations: {len(history)}")
        else:
            # Show all skills with migrations
            conn = get_connection()
            try:
                rows = conn.execute(
                    "SELECT DISTINCT skill_name FROM _migrations ORDER BY skill_name"
                ).fetchall()

                if not rows:
                    console.print("[yellow]No migrations found[/yellow]")
                    return

                table = Table(title="Migration Status")
                table.add_column("Skill", style="cyan")
                table.add_column("Version", style="green")
                table.add_column("Migrations", style="white")

                for (skill,) in rows:
                    version = get_current_version(skill)
                    history = get_migration_history(skill)
                    table.add_row(skill, str(version), str(len(history)))

                console.print(table)
            finally:
                conn.close()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def history(
    skill_name: str = typer.Option(None, "--skill", "-s", help="Filter by skill name"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records"),
) -> None:
    """Show migration history."""
    try:
        migrations = get_migration_history(skill_name)

        if not migrations:
            console.print("[yellow]No migration history found[/yellow]")
            return

        table = Table(title=f"Migration History{f' - {skill_name}' if skill_name else ''}")
        table.add_column("Skill", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("File", style="white")
        table.add_column("Applied", style="blue")

        for migration in migrations[-limit:]:
            table.add_row(
                migration["skill_name"],
                str(migration["version"]),
                migration["migration_file"],
                migration["applied_at"],
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

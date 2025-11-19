"""Migrate skill - universal export/import system.

Refactored to use service pattern while remaining
discoverable as a separate installable skill.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult

from .dependencies import get_migrate_service

app = typer.Typer(help="Data export/import and migration")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for migrate skill.

    Migrate skill is a utility and has no searchable content.

    Args:
        query: Search query string (unused)
        limit: Maximum number of results (unused)

    Returns:
        Empty list
    """
    return []


def get_db_path(db_path: str | None = None) -> Path:
    """Get database path from argument or config.

    Args:
        db_path: Optional explicit database path

    Returns:
        Path to database file
    """
    if db_path:
        return Path(db_path)

    from glorious_agents.config import config

    # Check for agent-specific DB first
    agent_db = Path(".agent/agents/default/agent.db")
    if agent_db.exists():
        return agent_db
    return config.get_shared_db_path()


@app.command()
def export(
    output: str = typer.Argument(..., help="Output directory"),
    db_path: str = typer.Option(None, "--db", help="Database path (default: system DB)"),
) -> None:
    """Export database to JSON files."""
    db = get_db_path(db_path)
    output_dir = Path(output)
    service = get_migrate_service()

    try:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        ) as progress:
            task = progress.add_task("Exporting database...", total=None)
            stats = service.export_database(db, output_dir)
            progress.update(task, completed=True)

        metadata = {
            "exported_at": datetime.now().isoformat(),
            "tables": stats,
            "total_rows": sum(stats.values()),
        }
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        console.print(f"[green]✓ Export complete:[/green] {output_dir}")
        console.print(f"  Tables: {len(stats)}")
        console.print(f"  Total rows: {metadata['total_rows']}")
    except Exception as e:
        console.print(f"[red]Export failed:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="import")
def import_cmd(
    input: str = typer.Argument(..., help="Input directory"),
    db_path: str = typer.Option(None, "--db", help="Database path (default: system DB)"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Backup existing DB"),
) -> None:
    """Import database from JSON files."""
    db = get_db_path(db_path)
    input_dir = Path(input)
    service = get_migrate_service()

    if not input_dir.exists():
        console.print(f"[red]Input directory not found:[/red] {input_dir}")
        raise typer.Exit(1)

    try:
        if backup and db.exists():
            backup_path = db.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            service.backup_database(db, backup_path)
            console.print(f"[blue]Backup created:[/blue] {backup_path}")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        ) as progress:
            task = progress.add_task("Importing database...", total=None)
            stats = service.import_database(db, input_dir)
            progress.update(task, completed=True)

        console.print("[green]✓ Import complete[/green]")
        console.print(f"  Tables: {len(stats)}")
        console.print(f"  Total rows: {sum(stats.values())}")
    except Exception as e:
        console.print(f"[red]Import failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def backup(
    output: str = typer.Argument(..., help="Backup file path"),
    db_path: str = typer.Option(None, "--db", help="Database path (default: system DB)"),
) -> None:
    """Create a backup copy of the database."""
    db = get_db_path(db_path)
    backup_path = Path(output)
    service = get_migrate_service()

    try:
        size = service.backup_database(db, backup_path)
        console.print(f"[green]✓ Backup created:[/green] {backup_path}")
        console.print(f"  Size: {size:,} bytes")
    except Exception as e:
        console.print(f"[red]Backup failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def restore(
    backup_file: str = typer.Argument(..., help="Backup file to restore"),
    db_path: str = typer.Option(None, "--db", help="Database path (default: system DB)"),
) -> None:
    """Restore database from backup."""
    db = get_db_path(db_path)
    backup_path = Path(backup_file)
    service = get_migrate_service()

    if not backup_path.exists():
        console.print(f"[red]Backup file not found:[/red] {backup_path}")
        raise typer.Exit(1)

    try:
        service.restore_database(backup_path, db)
        console.print(f"[green]✓ Restored from:[/green] {backup_path}")
    except Exception as e:
        console.print(f"[red]Restore failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    path: str = typer.Argument(..., help="Export directory or database file"),
) -> None:
    """Show information about export or database."""
    path_obj = Path(path)
    service = get_migrate_service()

    if path_obj.is_dir():
        metadata_file = path_obj / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
            console.print("[bold]Export Information[/bold]")
            console.print(f"  Exported: {metadata.get('exported_at', 'unknown')}")
            console.print(f"  Tables: {len(metadata.get('tables', {}))}")
            console.print(f"  Total rows: {metadata.get('total_rows', 0)}")
            console.print("\n[bold]Tables:[/bold]")
            for table, count in metadata.get("tables", {}).items():
                console.print(f"  {table}: {count} rows")
        else:
            console.print("[yellow]No metadata found in export directory[/yellow]")
    elif path_obj.suffix == ".db":
        info_dict = service.get_database_info(path_obj)
        console.print("[bold]Database Information[/bold]")
        console.print(f"  File: {info_dict['file']}")
        console.print(f"  Size: {info_dict['size']:,} bytes")
        console.print(f"  Tables: {info_dict['table_count']}")
        console.print("\n[bold]Tables:[/bold]")
        for table, count in info_dict["tables"].items():
            console.print(f"  {table}: {count} rows")
    else:
        console.print("[red]Path must be a directory or .db file[/red]")
        raise typer.Exit(1)

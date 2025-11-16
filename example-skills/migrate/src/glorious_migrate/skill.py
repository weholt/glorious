"""Migrate skill - universal export/import system."""

import base64
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from glorious_agents.core.context import SkillContext

app = typer.Typer(help="Data export/import and migration")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


def search(query: str, limit: int = 10) -> list["SearchResult"]:
    """Universal search API for migrate skill.
    
    Migrate skill is a utility and has no searchable content.
    
    Args:
        query: Search query string (unused)
        limit: Maximum number of results (unused)
        
    Returns:
        Empty list
    """
    return []


def export_table(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    """Export all rows from a table."""
    cursor = conn.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        row_dict = {}
        for col, val in zip(columns, row):
            # Convert bytes to base64 string for JSON serialization
            if isinstance(val, bytes):
                row_dict[col] = {"__type__": "bytes", "data": base64.b64encode(val).decode('utf-8')}
            else:
                row_dict[col] = val
        result.append(row_dict)
    return result


def import_table(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> int:
    """Import rows into a table."""
    if not rows:
        return 0

    columns = list(rows[0].keys())
    placeholders = ",".join(["?"] * len(columns))
    insert_sql = f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})"

    count = 0
    for row in rows:
        values = []
        for col in columns:
            val = row[col]
            # Convert base64-encoded bytes back to bytes
            if isinstance(val, dict) and val.get("__type__") == "bytes":
                values.append(base64.b64decode(val["data"]))
            else:
                values.append(val)
        conn.execute(insert_sql, values)
        count += 1

    conn.commit()
    return count


def export_database(db_path: Path, output_dir: Path) -> dict[str, int]:
    """Export entire database to JSON files."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    output_dir.mkdir(parents=True, exist_ok=True)
    stats = {}

    for table in tables:
        rows = export_table(conn, table)
        output_file = output_dir / f"{table}.json"
        with open(output_file, "w") as f:
            json.dump(rows, f, indent=2)
        stats[table] = len(rows)

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    schemas = [row[0] for row in cursor.fetchall() if row[0]]
    schema_file = output_dir / "schema.sql"
    with open(schema_file, "w") as f:
        f.write("\n\n".join(schemas))

    conn.close()
    return stats


def import_database(db_path: Path, input_dir: Path) -> dict[str, int]:
    """Import database from JSON files."""
    conn = sqlite3.connect(str(db_path))

    schema_file = input_dir / "schema.sql"
    if schema_file.exists():
        with open(schema_file) as f:
            schema_sql = f.read()
            for statement in schema_sql.split(";"):
                if statement.strip():
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError:
                        pass

    stats = {}
    for json_file in input_dir.glob("*.json"):
        if json_file.name == "metadata.json":
            continue

        table = json_file.stem
        with open(json_file) as f:
            rows = json.load(f)

        count = import_table(conn, table, rows)
        stats[table] = count

    conn.commit()
    conn.close()
    return stats


@app.command()
def export(
    output: str = typer.Argument(..., help="Output directory"),
    db_path: str = typer.Option(None, "--db", help="Database path (default: system DB)"),
) -> None:
    """Export database to JSON files."""
    assert _ctx is not None

    if db_path:
        db = Path(db_path)
    else:
        # Get DB path from config
        from glorious_agents.config import config
        # Check for agent-specific DB first
        agent_db = Path(".agent/agents/default/agent.db")
        if agent_db.exists():
            db = agent_db
        else:
            db = config.get_shared_db_path()
    output_dir = Path(output)

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Exporting database...", total=None)
            stats = export_database(db, output_dir)
            progress.update(task, completed=True)

        metadata = {"exported_at": datetime.now().isoformat(), "tables": stats, "total_rows": sum(stats.values())}
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        console.print(f"[green]✓ Export complete:[/green] {output_dir}")
        console.print(f"  Tables: {len(stats)}")
        console.print(f"  Total rows: {metadata['total_rows']}")
    except Exception as e:
        console.print(f"[red]Export failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def import_cmd(
    input: str = typer.Argument(..., help="Input directory"),
    db_path: str = typer.Option(None, "--db", help="Database path (default: system DB)"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Backup existing DB"),
) -> None:
    """Import database from JSON files."""
    assert _ctx is not None

    if db_path:
        db = Path(db_path)
    else:
        from glorious_agents.config import config
        agent_db = Path(".agent/agents/default/agent.db")
        if agent_db.exists():
            db = agent_db
        else:
            db = config.get_shared_db_path()
    input_dir = Path(input)

    if not input_dir.exists():
        console.print(f"[red]Input directory not found:[/red] {input_dir}")
        raise typer.Exit(1)

    try:
        if backup and db.exists():
            backup_path = db.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy2(db, backup_path)
            console.print(f"[blue]Backup created:[/blue] {backup_path}")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Importing database...", total=None)
            stats = import_database(db, input_dir)
            progress.update(task, completed=True)

        console.print(f"[green]✓ Import complete[/green]")
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
    assert _ctx is not None

    if db_path:
        db = Path(db_path)
    else:
        from glorious_agents.config import config
        agent_db = Path(".agent/agents/default/agent.db")
        if agent_db.exists():
            db = agent_db
        else:
            db = config.get_shared_db_path()
    backup_path = Path(output)

    try:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db, backup_path)
        size = backup_path.stat().st_size
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
    assert _ctx is not None

    if db_path:
        db = Path(db_path)
    else:
        from glorious_agents.config import config
        agent_db = Path(".agent/agents/default/agent.db")
        if agent_db.exists():
            db = agent_db
        else:
            db = config.get_shared_db_path()
    backup_path = Path(backup_file)

    if not backup_path.exists():
        console.print(f"[red]Backup file not found:[/red] {backup_path}")
        raise typer.Exit(1)

    try:
        current_backup = db.with_suffix(f".pre-restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(db, current_backup)
        console.print(f"[blue]Current DB backed up:[/blue] {current_backup}")

        shutil.copy2(backup_path, db)
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
        conn = sqlite3.connect(str(path_obj))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        console.print(f"[bold]Database Information[/bold]")
        console.print(f"  File: {path_obj}")
        console.print(f"  Size: {path_obj.stat().st_size:,} bytes")
        console.print(f"  Tables: {len(tables)}")

        console.print("\n[bold]Tables:[/bold]")
        for table in tables:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            console.print(f"  {table}: {count} rows")

        conn.close()
    else:
        console.print("[red]Path must be a directory or .db file[/red]")
        raise typer.Exit(1)

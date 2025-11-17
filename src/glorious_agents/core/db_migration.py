"""Database migration utilities for consolidating legacy databases."""

import shutil
import sqlite3
from pathlib import Path

from glorious_agents.config import config
from glorious_agents.core.db import get_agent_db_path, get_agent_folder


def migrate_from_legacy() -> None:
    """
    Migrate data from legacy database structure to unified database.

    Legacy structure:
    - ~/.glorious/agents/default/agent.db (main agent data)
    - ~/.glorious/master.db (agent registry)

    New structure:
    - <project>/.agent/glorious.db (unified database)
    """
    agent_folder = get_agent_folder()
    unified_db_path = get_agent_db_path()

    print(f"Migrating to unified database at: {unified_db_path}")
    print(f"Data folder: {agent_folder}")

    # Find legacy databases
    legacy_home = Path.home() / ".glorious"
    legacy_agent_db = legacy_home / "agents" / "default" / "agent.db"
    legacy_master_db = legacy_home / "master.db"

    migrated = False

    # Migrate main agent database
    if legacy_agent_db.exists():
        print(f"\nFound legacy agent database: {legacy_agent_db}")

        if unified_db_path.exists():
            backup_path = unified_db_path.with_suffix(".db.backup")
            print(f"Backing up current database to: {backup_path}")
            shutil.copy2(unified_db_path, backup_path)

        # Copy entire database as starting point
        print("Copying legacy database...")
        unified_db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_agent_db, unified_db_path)
        migrated = True
        print("✓ Migrated agent database")

    # Migrate master database tables
    if legacy_master_db.exists():
        print(f"\nFound legacy master database: {legacy_master_db}")

        try:
            legacy_conn = sqlite3.connect(str(legacy_master_db))
            unified_conn = sqlite3.connect(str(unified_db_path))

            # Create core_agents table if it doesn't exist
            unified_conn.execute("""
                CREATE TABLE IF NOT EXISTS core_agents (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT,
                    project_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migrate agents table
            try:
                cursor = legacy_conn.execute("SELECT * FROM agents")
                rows = cursor.fetchall()
                if rows:
                    unified_conn.executemany(
                        "INSERT OR REPLACE INTO core_agents VALUES (?, ?, ?, ?, ?)", rows
                    )
                    unified_conn.commit()
                    print(f"✓ Migrated {len(rows)} agents from master.db")
                    migrated = True
            except sqlite3.Error as e:
                print(f"Note: Could not migrate agents table: {e}")

            legacy_conn.close()
            unified_conn.close()
        except Exception as e:
            print(f"Warning: Error accessing master database: {e}")

    if migrated:
        print("\n✓ Migration complete!")
        print(f"  Unified database: {unified_db_path}")
        print("\nLegacy databases preserved at:")
        if legacy_agent_db.exists():
            print(f"  - {legacy_agent_db}")
        if legacy_master_db.exists():
            print(f"  - {legacy_master_db}")
    else:
        print("\nNo legacy databases found to migrate.")
        print("Starting fresh with new unified database structure.")


def show_migration_status() -> None:
    """Show current database locations and migration status."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Database Migration Status")
    table.add_column("Item", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Path", style="dim")

    # Current unified database
    unified_db = get_agent_db_path()
    if unified_db.exists():
        size = unified_db.stat().st_size / 1024
        table.add_row("Unified Database", f"✓ Active ({size:.1f} KB)", str(unified_db))
    else:
        table.add_row("Unified Database", "Not initialized", str(unified_db))

    # Legacy databases
    legacy_home = Path.home() / ".glorious"
    legacy_agent_db = legacy_home / "agents" / "default" / "agent.db"
    legacy_master_db = legacy_home / "master.db"

    if legacy_agent_db.exists():
        size = legacy_agent_db.stat().st_size / 1024
        table.add_row("Legacy Agent DB", f"⚠ Found ({size:.1f} KB)", str(legacy_agent_db))
    else:
        table.add_row("Legacy Agent DB", "Not found", str(legacy_agent_db))

    if legacy_master_db.exists():
        size = legacy_master_db.stat().st_size / 1024
        table.add_row("Legacy Master DB", f"⚠ Found ({size:.1f} KB)", str(legacy_master_db))
    else:
        table.add_row("Legacy Master DB", "Not found", str(legacy_master_db))

    console.print(table)

    # Show recommendation
    if legacy_agent_db.exists() or legacy_master_db.exists():
        console.print("\n[yellow]⚠ Legacy databases found![/yellow]")
        console.print("Run [bold]agent migrate[/bold] to consolidate into unified database.")

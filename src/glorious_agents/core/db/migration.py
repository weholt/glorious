"""Legacy database migration utilities."""

import sqlite3

from glorious_agents.config import get_config
from glorious_agents.core.db.connection import get_agent_db_path, get_connection, get_data_folder


def migrate_legacy_databases() -> None:
    """
    Migrate data from legacy database files to unified database.

    Looks for old database files and migrates them to the unified database.
    Legacy files: agent.db (in agents/default/), master.db, glorious_shared.db
    """
    config = get_config()
    data_folder = get_data_folder()
    unified_db = get_agent_db_path()

    # Check for legacy agent.db
    legacy_agent_db = data_folder / "agents" / "default" / "agent.db"
    if legacy_agent_db.exists() and not unified_db.exists():
        import shutil

        unified_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_agent_db, unified_db)
        print(f"Migrated legacy agent.db to {unified_db}")

    # Check for legacy master.db
    legacy_master_db = data_folder / config.DB_MASTER_NAME
    if legacy_master_db.exists():
        # Migrate agents table to core_agents
        try:
            legacy_conn = sqlite3.connect(str(legacy_master_db))
            unified_conn = get_connection()

            # Copy agents data
            cursor = legacy_conn.execute("SELECT * FROM agents")
            rows = cursor.fetchall()
            if rows:
                unified_conn.executemany(
                    "INSERT OR IGNORE INTO core_agents VALUES (?, ?, ?, ?, ?)", rows
                )
                unified_conn.commit()
                print(f"Migrated {len(rows)} agents from master.db")

            legacy_conn.close()
            unified_conn.close()
        except Exception as e:
            print(f"Warning: Could not migrate master.db: {e}")

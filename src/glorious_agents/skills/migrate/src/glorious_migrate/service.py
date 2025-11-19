"""Business logic for migrate skill."""

import base64
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class MigrateService:
    """Service layer for database migration utilities.

    Handles export/import operations for database migration
    without managing its own persistent data.
    """

    @staticmethod
    def export_table(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
        """Export all rows from a table.

        Args:
            conn: SQLite connection
            table: Table name

        Returns:
            List of row dictionaries
        """
        cursor = conn.execute(f"SELECT * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        result = []
        for row in rows:
            row_dict = {}
            for col, val in zip(columns, row):
                # Convert bytes to base64 string for JSON serialization
                if isinstance(val, bytes):
                    row_dict[col] = {
                        "__type__": "bytes",
                        "data": base64.b64encode(val).decode("utf-8"),
                    }
                else:
                    row_dict[col] = val
            result.append(row_dict)
        return result

    @staticmethod
    def import_table(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> int:
        """Import rows into a table.

        Args:
            conn: SQLite connection
            table: Table name
            rows: List of row dictionaries

        Returns:
            Number of rows imported
        """
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

    def export_database(self, db_path: Path, output_dir: Path) -> dict[str, int]:
        """Export entire database to JSON files.

        Args:
            db_path: Path to database file
            output_dir: Output directory for JSON files

        Returns:
            Dictionary mapping table names to row counts
        """
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        output_dir.mkdir(parents=True, exist_ok=True)
        stats = {}

        for table in tables:
            rows = self.export_table(conn, table)
            output_file = output_dir / f"{table}.json"
            with open(output_file, "w") as f:
                json.dump(rows, f, indent=2)
            stats[table] = len(rows)

        # Export schema
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        schemas = [row[0] for row in cursor.fetchall() if row[0]]
        schema_file = output_dir / "schema.sql"
        with open(schema_file, "w") as f:
            f.write("\n\n".join(schemas))

        conn.close()
        return stats

    def import_database(self, db_path: Path, input_dir: Path) -> dict[str, int]:
        """Import database from JSON files.

        Args:
            db_path: Path to database file
            input_dir: Input directory with JSON files

        Returns:
            Dictionary mapping table names to row counts
        """
        conn = sqlite3.connect(str(db_path))

        # Import schema
        schema_file = input_dir / "schema.sql"
        if schema_file.exists():
            with open(schema_file) as f:
                schema_sql = f.read()
                for statement in schema_sql.split(";"):
                    if statement.strip():
                        try:
                            conn.execute(statement)
                        except sqlite3.OperationalError:
                            pass  # Table might already exist

        # Import data
        stats = {}
        for json_file in input_dir.glob("*.json"):
            if json_file.name == "metadata.json":
                continue

            table = json_file.stem
            with open(json_file) as f:
                rows = json.load(f)

            count = self.import_table(conn, table, rows)
            stats[table] = count

        conn.commit()
        conn.close()
        return stats

    @staticmethod
    def backup_database(db_path: Path, backup_path: Path) -> int:
        """Create backup of database.

        Args:
            db_path: Source database path
            backup_path: Backup destination path

        Returns:
            Size of backup file in bytes
        """
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_path, backup_path)
        return backup_path.stat().st_size

    @staticmethod
    def restore_database(backup_path: Path, db_path: Path) -> None:
        """Restore database from backup.

        Args:
            backup_path: Backup file path
            db_path: Destination database path
        """
        # Create pre-restore backup
        if db_path.exists():
            pre_restore_backup = db_path.with_suffix(
                f".pre-restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            shutil.copy2(db_path, pre_restore_backup)

        # Restore from backup
        shutil.copy2(backup_path, db_path)

    @staticmethod
    def get_database_info(db_path: Path) -> dict[str, Any]:
        """Get information about a database.

        Args:
            db_path: Database file path

        Returns:
            Dictionary with database information
        """
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        table_info = {}
        for table in tables:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            table_info[table] = count

        conn.close()

        return {
            "file": str(db_path),
            "size": db_path.stat().st_size,
            "tables": table_info,
            "table_count": len(tables),
            "total_rows": sum(table_info.values()),
        }

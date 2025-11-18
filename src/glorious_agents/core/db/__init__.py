"""Database management for unified SQLite database.

This module provides database connection and initialization for the unified
glorious.db database that contains all agent data with prefixed tables.
"""

from glorious_agents.core.db.batch import batch_execute
from glorious_agents.core.db.connection import (
    get_agent_db_path,
    get_connection,
    get_data_folder,
    get_master_db_path,
)
from glorious_agents.core.db.migration import migrate_legacy_databases
from glorious_agents.core.db.optimization import optimize_database
from glorious_agents.core.db.schema import init_master_db, init_skill_schema

__all__ = [
    "batch_execute",
    "get_agent_db_path",
    "get_connection",
    "get_data_folder",
    "get_master_db_path",
    "init_master_db",
    "init_skill_schema",
    "migrate_legacy_databases",
    "optimize_database",
]

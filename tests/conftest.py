"""Pytest configuration and shared fixtures."""

import os
import sqlite3
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from glorious_agents.core.context import EventBus, SkillContext
from glorious_agents.core.runtime import reset_ctx


@pytest.fixture
def temp_db() -> Generator[sqlite3.Connection]:
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")

    yield conn

    conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus for testing."""
    return EventBus()


@pytest.fixture
def skill_context(temp_db: sqlite3.Connection, event_bus: EventBus) -> SkillContext:
    """Create a skill context for testing."""
    return SkillContext(temp_db, event_bus)


@pytest.fixture(autouse=True)
def _reset_runtime() -> Generator[None]:
    """Reset runtime context between tests."""
    yield
    reset_ctx()


@pytest.fixture
def temp_data_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary data folder and set environment variable."""
    data_folder = tmp_path / ".agent"
    data_folder.mkdir()
    # Use DATA_FOLDER which is what config actually reads
    monkeypatch.setenv("DATA_FOLDER", str(data_folder))

    # Reload config to pick up new environment variable
    import glorious_agents.config as config_module

    config_module.config = config_module.Config()

    # Also update the imported reference in db module
    import glorious_agents.core.db as db_module

    db_module.config = config_module.config

    return data_folder

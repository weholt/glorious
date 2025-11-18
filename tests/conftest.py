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
    """
    Create a temporary data folder, set DATA_FOLDER to its path, and reset the lazy-loaded config singleton.

    Parameters:
        tmp_path (Path): Base temporary directory provided by pytest.
        monkeypatch (pytest.MonkeyPatch): Pytest fixture used to set environment variables.

    Returns:
        Path: Path to the created data folder.
    """
    data_folder = tmp_path / ".agent"
    data_folder.mkdir()
    # Use DATA_FOLDER which is what config actually reads
    monkeypatch.setenv("DATA_FOLDER", str(data_folder))

    # Reset and reload config to pick up new environment variable
    from glorious_agents.config import reset_config

    reset_config()  # Reset the lazy-loaded singleton

    return data_folder

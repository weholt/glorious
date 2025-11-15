"""Pytest configuration and shared fixtures."""

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from glorious_agents.core.context import EventBus, SkillContext
from glorious_agents.core.runtime import reset_ctx


@pytest.fixture
def temp_db() -> Generator[sqlite3.Connection, None, None]:
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
def reset_runtime() -> Generator[None, None, None]:
    """Reset runtime context between tests."""
    yield
    reset_ctx()


@pytest.fixture
def temp_agent_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary agent folder and set environment variable."""
    agent_folder = tmp_path / ".agent"
    agent_folder.mkdir()
    monkeypatch.setenv("GLORIOUS_AGENT_FOLDER", str(agent_folder))
    
    # Reload config to pick up new environment variable
    import glorious_agents.config as config_module
    config_module.config = config_module.Config()
    
    # Also update the imported reference in db module
    import glorious_agents.core.db as db_module
    db_module.config = config_module.config
    
    return agent_folder

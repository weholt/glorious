"""Pytest configuration and shared fixtures."""

import os
import shutil
import sqlite3
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any, Optional

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
def skill_context(temp_db: sqlite3.Connection, event_bus: EventBus) -> Generator[SkillContext]:
    """Create a skill context for testing."""
    ctx = SkillContext(temp_db, event_bus)
    yield ctx
    ctx.close()


@pytest.fixture(autouse=True)
def _reset_runtime() -> Generator[None]:
    """Reset runtime context between tests."""
    yield
    reset_ctx()
    # Also cleanup any SQLAlchemy engines
    from glorious_agents.core.engine_registry import dispose_all_engines

    dispose_all_engines()
    # Also cleanup any SQLAlchemy engines
    from glorious_agents.core.engine_registry import dispose_all_engines

    dispose_all_engines()


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


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[dict[str, Any]]:
    """
    Create isolated environment for each test.

    This fixture creates a temporary directory structure and sets environment
    variables to ensure tests don't affect the current workspace.

    Yields:
        dict with keys: root, agent_folder, cwd, env
    """
    # Create temporary agent folder
    agent_folder = tmp_path / ".agent"
    agent_folder.mkdir()

    # Create temporary home directory for complete isolation
    temp_home = tmp_path / "home"
    temp_home.mkdir()

    # Set environment variables to use temp folders
    monkeypatch.setenv("GLORIOUS_DATA_FOLDER", str(agent_folder))
    monkeypatch.setenv("DATA_FOLDER", str(agent_folder))
    monkeypatch.setenv("HOME", str(temp_home))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))

    # Create tmp directory
    (tmp_path / "tmp").mkdir(exist_ok=True)

    # Reset config to pick up new environment
    from glorious_agents.config import reset_config

    reset_config()

    # Prepare environment dict for subprocess calls
    test_env = {
        "GLORIOUS_DATA_FOLDER": str(agent_folder),
        "DATA_FOLDER": str(agent_folder),
        "HOME": str(temp_home),
        "TMPDIR": str(tmp_path / "tmp"),
    }

    yield {"root": tmp_path, "agent_folder": agent_folder, "cwd": tmp_path, "env": test_env}

    # Cleanup is automatic with tmp_path
    # Reset config again after test
    reset_config()


def run_agent_cli(
    args: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    input_data: str | None = None,
    expect_failure: bool = False,
    isolated_env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run agent CLI command and capture output.

    Args:
        args: Command arguments (without 'uv run agent' prefix)
        cwd: Working directory for command
        env: Environment variables (will be merged with isolated_env if provided)
        input_data: Input to send to stdin
        expect_failure: Whether to expect command to fail
        isolated_env: Isolated environment dict from fixture (optional, for proper isolation)

    Returns:
        dict with keys: returncode, stdout, stderr, success, output
    """
    # Use python -m instead of uv run since uv may not be available
    cmd = ["python", "-m", "glorious_agents.cli"] + args

    # Start with a minimal environment to avoid leaking current workspace settings
    full_env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV", ""),
    }

    # Add isolated environment variables if provided
    if isolated_env and "env" in isolated_env:
        full_env.update(isolated_env["env"])

    # Add any additional environment variables
    if env:
        full_env.update(env)

    # Use cwd from isolated_env if not explicitly provided
    if cwd is None and isolated_env:
        cwd = isolated_env.get("cwd")

    result = subprocess.run(
        cmd, cwd=cwd, env=full_env, input=input_data, capture_output=True, text=True
    )

    success = (result.returncode == 0) if not expect_failure else (result.returncode != 0)

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": success,
        "output": result.stdout + result.stderr,
    }


# Make run_agent_cli available as a fixture too
@pytest.fixture
def run_cli():
    """Fixture that provides the run_agent_cli function."""
    return run_agent_cli


@pytest.fixture
def cli_runner(isolated_env):
    """
    Fixture that provides a pre-configured CLI runner for the isolated environment.

    This is a convenience wrapper that automatically uses the isolated environment.

    Usage:
        def test_example(cli_runner):
            result = cli_runner(['notes', 'add', 'Test'])
            assert result['success']
    """

    def runner(
        args: list[str], input_data: str | None = None, expect_failure: bool = False
    ) -> dict[str, Any]:
        """Run CLI command in isolated environment."""
        return run_agent_cli(
            args=args,
            input_data=input_data,
            expect_failure=expect_failure,
            isolated_env=isolated_env,
        )

    return runner

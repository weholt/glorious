"""Tests for CLI entry point."""

import os
from unittest.mock import patch

import pytest


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables."""
    monkeypatch.delenv("ISSUES_FOLDER", raising=False)
    monkeypatch.delenv("ISSUES_DB_PATH", raising=False)


def test_main_sets_default_issues_folder(clean_env, monkeypatch, tmp_path):
    """Test main sets ISSUES_FOLDER if not present."""
    monkeypatch.chdir(tmp_path)

    with patch("issue_tracker.cli.__main__.load_dotenv"):
        with patch("issue_tracker.cli.app.app"):
            from issue_tracker.cli.__main__ import main

            main()

            assert os.environ["ISSUES_FOLDER"] == "./.issues"
            assert os.environ["ISSUES_DB_PATH"] == "./.issues/issues.db"


def test_main_respects_existing_issues_folder(clean_env, monkeypatch, tmp_path):
    """Test main respects existing ISSUES_FOLDER."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ISSUES_FOLDER", "/custom/path")

    with patch("issue_tracker.cli.__main__.load_dotenv"):
        with patch("issue_tracker.cli.app.app"):
            from issue_tracker.cli.__main__ import main

            main()

            assert os.environ["ISSUES_FOLDER"] == "/custom/path"
            assert os.environ["ISSUES_DB_PATH"] == "/custom/path/issues.db"


def test_main_loads_env_file_if_exists(clean_env, monkeypatch, tmp_path):
    """Test main loads .env file if it exists."""
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("ISSUES_FOLDER=/from/env\n")

    with patch("issue_tracker.cli.__main__.load_dotenv") as mock_load:
        with patch("issue_tracker.cli.app.app"):
            from issue_tracker.cli.__main__ import main

            main()

            mock_load.assert_called_once_with(env_file)


def test_main_skips_dotenv_if_not_exists(clean_env, monkeypatch, tmp_path):
    """Test main skips .env loading if file doesn't exist."""
    monkeypatch.chdir(tmp_path)

    with patch("issue_tracker.cli.__main__.load_dotenv") as mock_load:
        with patch("issue_tracker.cli.app.app"):
            from issue_tracker.cli.__main__ import main

            main()

            mock_load.assert_not_called()


def test_main_calls_app(clean_env, monkeypatch, tmp_path):
    """Test main calls the Typer app."""
    monkeypatch.chdir(tmp_path)

    with patch("issue_tracker.cli.__main__.load_dotenv"):
        with patch("issue_tracker.cli.app.app") as mock_app:
            from issue_tracker.cli.__main__ import main

            main()

            mock_app.assert_called_once()

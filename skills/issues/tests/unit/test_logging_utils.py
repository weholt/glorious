"""Tests for logging utilities."""

from unittest.mock import patch

import pytest

from issue_tracker.cli.logging_utils import (
    is_verbose,
    set_verbose,
    verbose_error,
    verbose_log,
    verbose_section,
    verbose_step,
    verbose_success,
)


@pytest.fixture(autouse=True)
def reset_verbose():
    """Reset verbose mode before each test."""
    set_verbose(False)
    yield
    set_verbose(False)


def test_set_verbose():
    """Test setting verbose mode."""
    assert not is_verbose()
    set_verbose(True)
    assert is_verbose()
    set_verbose(False)
    assert not is_verbose()


def test_verbose_log_when_disabled():
    """Test verbose_log does nothing when disabled."""
    with patch("typer.echo") as mock_echo:
        verbose_log("test message")
        mock_echo.assert_not_called()


def test_verbose_log_when_enabled():
    """Test verbose_log outputs when enabled."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        verbose_log("test message")
        mock_echo.assert_called_once()
        call_args = mock_echo.call_args
        assert "test message" in call_args[0][0]
        assert call_args[1]["err"] is True


def test_verbose_log_with_kwargs():
    """Test verbose_log with extra key-value pairs."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        verbose_log("test", key1="value1", key2="value2")
        mock_echo.assert_called_once()
        call_args = mock_echo.call_args[0][0]
        assert "test" in call_args
        assert "key1=value1" in call_args
        assert "key2=value2" in call_args


def test_verbose_section_when_disabled():
    """Test verbose_section does nothing when disabled."""
    with patch("typer.echo") as mock_echo:
        verbose_section("Test Section")
        mock_echo.assert_not_called()


def test_verbose_section_when_enabled():
    """Test verbose_section outputs when enabled."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        verbose_section("Test Section")
        assert mock_echo.call_count == 4
        calls = [call[0][0] for call in mock_echo.call_args_list]
        assert any("Test Section" in call for call in calls)
        assert any("=" * 60 in call for call in calls)


def test_verbose_step_when_disabled():
    """Test verbose_step does nothing when disabled."""
    with patch("typer.echo") as mock_echo:
        verbose_step("step1", "detail1")
        mock_echo.assert_not_called()


def test_verbose_step_when_enabled():
    """Test verbose_step outputs when enabled."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        verbose_step("step1", "detail1")
        mock_echo.assert_called_once()
        call_args = mock_echo.call_args[0][0]
        assert "step1" in call_args
        assert "detail1" in call_args
        assert "→" in call_args


def test_verbose_step_without_detail():
    """Test verbose_step without detail."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        verbose_step("step1")
        mock_echo.assert_called_once()
        call_args = mock_echo.call_args[0][0]
        assert "step1" in call_args
        assert "→" in call_args


def test_verbose_error_when_disabled():
    """Test verbose_error does nothing when disabled."""
    with patch("typer.echo") as mock_echo:
        verbose_error("error message")
        mock_echo.assert_not_called()


def test_verbose_error_when_enabled():
    """Test verbose_error outputs when enabled."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        verbose_error("error message")
        mock_echo.assert_called_once()
        call_args = mock_echo.call_args[0][0]
        assert "error message" in call_args
        assert "ERROR" in call_args
        assert "✗" in call_args


def test_verbose_error_with_exception():
    """Test verbose_error with exception."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        error = ValueError("test error")
        verbose_error("error message", error)
        assert mock_echo.call_count == 2
        calls = [call[0][0] for call in mock_echo.call_args_list]
        assert any("error message" in call for call in calls)
        assert any("test error" in call for call in calls)


def test_verbose_success_when_disabled():
    """Test verbose_success does nothing when disabled."""
    with patch("typer.echo") as mock_echo:
        verbose_success("success message")
        mock_echo.assert_not_called()


def test_verbose_success_when_enabled():
    """Test verbose_success outputs when enabled."""
    set_verbose(True)
    with patch("typer.echo") as mock_echo:
        verbose_success("success message")
        mock_echo.assert_called_once()
        call_args = mock_echo.call_args[0][0]
        assert "success message" in call_args
        assert "✓" in call_args

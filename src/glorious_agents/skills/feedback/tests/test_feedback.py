"""Tests for feedback skill."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from glorious_feedback.skill import app, init_context, record_feedback


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_context():
    """Create mock SkillContext."""
    ctx = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 1
    ctx.conn = MagicMock()
    ctx.conn.execute = MagicMock(return_value=mock_cursor)
    ctx.conn.commit = MagicMock()
    return ctx


class TestRecordFeedbackFunction:
    """Tests for record_feedback callable function."""

    @patch("glorious_feedback.skill._ctx")
    def test_record_feedback_basic(self, mock_ctx):
        """Test recording basic feedback."""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_ctx.conn.execute.return_value = mock_cursor
        
        result = record_feedback("test-action", "success", "Test reason")
        assert result == 42
        mock_ctx.conn.execute.assert_called_once()
        mock_ctx.conn.commit.assert_called_once()

    def test_record_feedback_without_context(self):
        """Test record_feedback raises error without context."""
        import glorious_feedback.skill as skill_module
        skill_module._ctx = None
        
        with pytest.raises(RuntimeError, match="Context not initialized"):
            record_feedback("test", "success")

    @patch("glorious_feedback.skill._ctx")
    def test_record_feedback_with_meta(self, mock_ctx):
        """Test recording feedback with metadata."""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_ctx.conn.execute.return_value = mock_cursor
        
        meta = {"key": "value", "count": 5}
        result = record_feedback("action", "success", "reason", meta=meta)
        
        assert result == 1
        call_args = mock_ctx.conn.execute.call_args
        assert json.loads(call_args[0][1][4]) == meta


class TestRecordCommand:
    """Tests for record CLI command."""

    @patch("glorious_feedback.skill._ctx")
    def test_record_command_success(self, mock_ctx, runner):
        """Test record command with valid input."""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_ctx.conn.execute.return_value = mock_cursor
        
        result = runner.invoke(app, ["record", "my-action", "success", "--reason", "All good"])
        assert result.exit_code == 0
        assert "Feedback 1 recorded" in result.output

    @patch("glorious_feedback.skill._ctx")
    def test_record_command_minimal(self, mock_ctx, runner):
        """Test record command with minimal arguments."""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 5
        mock_ctx.conn.execute.return_value = mock_cursor
        
        result = runner.invoke(app, ["record", "action-id", "failed"])
        assert result.exit_code == 0
        assert "Feedback 5 recorded" in result.output


class TestListCommand:
    """Tests for list command."""

    def test_list_without_context(self, runner):
        """Test list command without context."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "not initialized" in result.output.lower()

    @patch("glorious_feedback.skill._ctx")
    def test_list_with_data(self, mock_ctx, runner):
        """Test list command displays feedback."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([
            (1, "action1", "success", "Good"),
            (2, "action2", "failed", "Bad"),
        ]))
        mock_ctx.conn.execute.return_value = mock_cursor
        
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Feedback" in result.output or "Recent" in result.output


class TestStatsCommand:
    """Tests for stats command."""

    def test_stats_without_context(self, runner):
        """Test stats command without context."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "not initialized" in result.output.lower() or "Statistics" in result.output


class TestInitContext:
    """Tests for init_context function."""

    def test_init_context(self, mock_context):
        """Test context initialization."""
        import glorious_feedback.skill as skill_module
        init_context(mock_context)
        assert skill_module._ctx == mock_context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

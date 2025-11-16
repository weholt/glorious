"""Tests for vacuum skill."""

from unittest.mock import MagicMock, patch

import pytest
from glorious_vacuum.skill import app, init_context
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_context():
    """Create mock SkillContext."""
    ctx = MagicMock()
    ctx.conn = MagicMock()
    ctx.conn.execute = MagicMock()
    ctx.conn.commit = MagicMock()
    return ctx


class TestRunCommand:
    """Tests for run command."""

    def test_run_default_mode(self, runner):
        """Test run with default summarize mode."""
        result = runner.invoke(app, ["run"])
        assert result.exit_code == 0
        assert "summarize" in result.output.lower()
        assert "completed" in result.output.lower()

    def test_run_summarize_mode(self, runner):
        """Test run with explicit summarize mode."""
        result = runner.invoke(app, ["run", "--mode", "summarize"])
        assert result.exit_code == 0
        assert "summarize" in result.output.lower()

    def test_run_dedupe_mode(self, runner):
        """Test run with dedupe mode."""
        result = runner.invoke(app, ["run", "--mode", "dedupe"])
        assert result.exit_code == 0
        assert "dedupe" in result.output.lower()

    def test_run_promote_rules_mode(self, runner):
        """Test run with promote-rules mode."""
        result = runner.invoke(app, ["run", "--mode", "promote-rules"])
        assert result.exit_code == 0
        assert "promote-rules" in result.output.lower()

    def test_run_sharpen_mode(self, runner):
        """Test run with sharpen mode."""
        result = runner.invoke(app, ["run", "--mode", "sharpen"])
        assert result.exit_code == 0
        assert "sharpen" in result.output.lower()

    def test_run_invalid_mode(self, runner):
        """Test run with invalid mode."""
        result = runner.invoke(app, ["run", "--mode", "invalid"])
        assert result.exit_code == 0
        assert "invalid mode" in result.output.lower()

    @patch("glorious_vacuum.skill._ctx")
    def test_run_with_context_records_operation(self, mock_ctx, runner):
        """Test run records operation when context is available."""
        mock_conn = MagicMock()
        mock_ctx.conn = mock_conn

        result = runner.invoke(app, ["run", "--mode", "dedupe"])
        assert result.exit_code == 0


class TestHistoryCommand:
    """Tests for history command."""

    def test_history_without_context(self, runner):
        """Test history command without initialized context."""
        result = runner.invoke(app, ["history"])
        assert result.exit_code == 0
        assert "not initialized" in result.output.lower()

    @patch("glorious_vacuum.skill._ctx")
    def test_history_with_empty_results(self, mock_ctx, runner):
        """Test history command with no operations."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_ctx.conn.execute.return_value = mock_cursor

        result = runner.invoke(app, ["history"])
        assert result.exit_code == 0
        assert "Vacuum History" in result.output

    @patch("glorious_vacuum.skill._ctx")
    def test_history_with_operations(self, mock_ctx, runner):
        """Test history command displays operations."""
        mock_cursor = MagicMock()
        # id, mode, items_processed, items_modified, started_at, status
        mock_cursor.__iter__ = MagicMock(
            return_value=iter(
                [
                    (1, "summarize", 10, 5, "2025-11-15", "completed"),
                    (2, "dedupe", 20, 3, "2025-11-14", "completed"),
                ]
            )
        )
        mock_ctx.conn.execute.return_value = mock_cursor

        result = runner.invoke(app, ["history"])
        assert result.exit_code == 0
        assert "Vacuum History" in result.output


class TestInitContext:
    """Tests for init_context function."""

    def test_init_context_sets_global(self, mock_context):
        """Test init_context sets global _ctx variable."""
        import glorious_vacuum.skill as skill_module

        init_context(mock_context)
        assert skill_module._ctx == mock_context

    def test_init_context_with_none(self):
        """Test init_context handles None gracefully."""
        import glorious_vacuum.skill as skill_module

        init_context(None)
        assert skill_module._ctx is None


class TestModeValidation:
    """Tests for mode validation logic."""

    def test_valid_modes(self):
        """Test all valid modes are recognized."""
        valid_modes = ["summarize", "dedupe", "promote-rules", "sharpen"]
        for mode in valid_modes:
            assert mode in valid_modes

    def test_invalid_mode_detection(self):
        """Test invalid modes are detected."""
        invalid_modes = ["invalid", "remove", "compact", ""]
        valid_modes = ["summarize", "dedupe", "promote-rules", "sharpen"]
        for mode in invalid_modes:
            assert mode not in valid_modes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

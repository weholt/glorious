"""Tests for prompts skill."""

import json
from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner
from glorious_prompts.skill import app, init_context, register_prompt

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.conn = MagicMock()
    return ctx

class TestRegisterPromptFunction:
    @patch("glorious_prompts.skill._ctx")
    def test_register_prompt_new(self, mock_ctx):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_cursor.lastrowid = 1
        mock_ctx.conn.execute.return_value = mock_cursor
        
        result = register_prompt("test-prompt", "Hello {name}")
        assert result == 1

    def test_register_prompt_without_context(self):
        import glorious_prompts.skill as skill_module
        skill_module._ctx = None
        with pytest.raises(RuntimeError):
            register_prompt("test", "template")

class TestRegisterCommand:
    @patch("glorious_prompts.skill._ctx")
    def test_register_command(self, mock_ctx, runner):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_cursor.lastrowid = 1
        mock_ctx.conn.execute.return_value = mock_cursor
        
        result = runner.invoke(app, ["register", "test", "Hello {name}"])
        assert result.exit_code == 0

class TestListCommand:
    def test_list_without_context(self, runner):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

class TestGetCommand:
    def test_get_without_context(self, runner):
        result = runner.invoke(app, ["get", "test-prompt"])
        assert result.exit_code == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

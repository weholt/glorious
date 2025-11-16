"""Tests for notes skill."""

import pytest
from glorious_skill_notes.skill import app
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


class TestAddCommand:
    def test_add_note(self, runner):
        result = runner.invoke(app, ["add", "test-note"])
        assert result.exit_code == 0


class TestListCommand:
    def test_list_notes(self, runner):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

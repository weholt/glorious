"""Tests for planner skill."""
from typer.testing import CliRunner
import pytest
from glorious_planner.skill import app

@pytest.fixture
def runner():
    return CliRunner()

class TestAddCommand:
    def test_add_task(self, runner):
        result = runner.invoke(app, ["add", "TEST-123"])
        assert result.exit_code == 0

class TestListCommand:
    def test_list_tasks(self, runner):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

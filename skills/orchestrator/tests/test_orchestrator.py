"""Tests for orchestrator skill."""
from typer.testing import CliRunner
import pytest
from glorious_orchestrator.skill import app

@pytest.fixture
def runner():
    return CliRunner()

class TestInfoCommand:
    def test_info_command(self, runner):
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "Orchestrator" in result.output or "placeholder" in result.output.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

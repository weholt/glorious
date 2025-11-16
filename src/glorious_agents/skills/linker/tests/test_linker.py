"""Tests for linker skill."""
from typer.testing import CliRunner
import pytest
from glorious_linker.skill import app

@pytest.fixture
def runner():
    return CliRunner()

class TestLinkCommand:
    def test_link_items(self, runner):
        result = runner.invoke(app, ["link", "src-id", "dst-id", "relates-to"])
        assert result.exit_code == 0

class TestListCommand:
    def test_list_links(self, runner):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

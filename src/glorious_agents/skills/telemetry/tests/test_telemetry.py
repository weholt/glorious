"""Tests for telemetry skill."""

import pytest
from glorious_telemetry.skill import app
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


class TestTrackCommand:
    def test_track_event(self, runner):
        result = runner.invoke(app, ["track", "test-event"])
        assert result.exit_code == 0


class TestStatsCommand:
    def test_get_stats(self, runner):
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

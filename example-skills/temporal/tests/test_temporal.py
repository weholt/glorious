"""Tests for temporal skill."""

import re
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from glorious_temporal.skill import app


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


class TestParseCommand:
    """Tests for parse command."""

    def test_parse_days(self, runner):
        """Test parsing days specification."""
        result = runner.invoke(app, ["parse", "7d"])
        assert result.exit_code == 0
        assert "7d" in result.output
        assert "Resolved to:" in result.output

    def test_parse_hours(self, runner):
        """Test parsing hours specification."""
        result = runner.invoke(app, ["parse", "3h"])
        assert result.exit_code == 0
        assert "3h" in result.output
        assert "Resolved to:" in result.output

    def test_parse_minutes(self, runner):
        """Test parsing minutes specification."""
        result = runner.invoke(app, ["parse", "30m"])
        assert result.exit_code == 0
        assert "30m" in result.output
        assert "Resolved to:" in result.output

    def test_parse_invalid_unit(self, runner):
        """Test parsing with invalid unit."""
        result = runner.invoke(app, ["parse", "5x"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output.lower()

    def test_parse_complex_spec(self, runner):
        """Test parsing complex time specification."""
        result = runner.invoke(app, ["parse", "last-week"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output.lower()

    def test_parse_date_format(self, runner):
        """Test parsing ISO date."""
        result = runner.invoke(app, ["parse", "2025-11-14"])
        assert result.exit_code == 0


class TestFilterSinceCommand:
    """Tests for filter_since command."""

    def test_filter_since_basic(self, runner):
        """Test filter_since command output."""
        result = runner.invoke(app, ["filter-since", "7d"])
        assert result.exit_code == 0
        assert "7d" in result.output
        assert "WHERE created_at >=" in result.output

    def test_filter_since_hours(self, runner):
        """Test filter_since with hours."""
        result = runner.invoke(app, ["filter-since", "3h"])
        assert result.exit_code == 0
        assert "3h" in result.output


class TestExamplesCommand:
    """Tests for examples command."""

    def test_examples_output(self, runner):
        """Test examples command shows help."""
        result = runner.invoke(app, ["examples"])
        assert result.exit_code == 0
        assert "--since 7d" in result.output
        assert "--since 3h" in result.output
        assert "--since 30m" in result.output
        assert "--until" in result.output

    def test_examples_has_description(self, runner):
        """Test examples has descriptions."""
        result = runner.invoke(app, ["examples"])
        assert "Last 7 days" in result.output
        assert "Last 3 hours" in result.output


class TestTimeSpecParsing:
    """Tests for time specification parsing logic."""

    def test_regex_pattern_days(self):
        """Test regex pattern matches days correctly."""
        pattern = r'(\d+)([dhm])'
        match = re.match(pattern, "7d")
        assert match is not None
        assert match.groups() == ("7", "d")

    def test_regex_pattern_hours(self):
        """Test regex pattern matches hours correctly."""
        pattern = r'(\d+)([dhm])'
        match = re.match(pattern, "3h")
        assert match is not None
        assert match.groups() == ("3", "h")

    def test_regex_pattern_minutes(self):
        """Test regex pattern matches minutes correctly."""
        pattern = r'(\d+)([dhm])'
        match = re.match(pattern, "30m")
        assert match is not None
        assert match.groups() == ("30", "m")

    def test_timedelta_calculation_days(self):
        """Test timedelta calculation for days."""
        delta = timedelta(days=7)
        assert delta.days == 7

    def test_timedelta_calculation_hours(self):
        """Test timedelta calculation for hours."""
        delta = timedelta(hours=3)
        assert delta.total_seconds() == 3 * 3600

    def test_timedelta_calculation_minutes(self):
        """Test timedelta calculation for minutes."""
        delta = timedelta(minutes=30)
        assert delta.total_seconds() == 30 * 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

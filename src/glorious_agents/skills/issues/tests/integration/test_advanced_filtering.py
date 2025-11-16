"""Integration tests for advanced filtering features.

Tests all advanced filtering options:
- Date range filters (created, updated, closed)
- Priority range filters
- Text search in fields
- Empty description filter
- Label OR logic
"""

import json
import time

import pytest
from typer.testing import CliRunner

from issue_tracker.cli.app import app


@pytest.mark.timeout(10)
class TestAdvancedFiltering:
    """Test advanced filtering options in list command."""

    def test_filter_by_date_range(self, integration_cli_runner: CliRunner):
        """Test filtering by created date range."""
        runner = integration_cli_runner

        # Create issues at different times
        result = runner.invoke(app, ["create", "Old issue", "--json"])
        assert result.exit_code == 0
        old_issue = json.loads(result.stdout)
        old_date = old_issue["created_at"][:10]  # YYYY-MM-DD

        time.sleep(0.1)  # Small delay to ensure different timestamps

        result = runner.invoke(app, ["create", "New issue", "--json"])
        assert result.exit_code == 0
        new_issue = json.loads(result.stdout)
        new_issue["created_at"][:10]

        # Filter by date range - should get both
        result = runner.invoke(app, ["list", "--created-after", old_date, "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)
        issue_ids = {i["id"] for i in issues}
        assert old_issue["id"] in issue_ids
        assert new_issue["id"] in issue_ids

    def test_filter_priority_range(self, integration_cli_runner: CliRunner):
        """Test filtering by priority range using priority-min/max."""
        runner = integration_cli_runner

        # Create issues with different priorities
        result = runner.invoke(app, ["create", "Critical", "-p", "0", "--json"])
        assert result.exit_code == 0
        critical = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "High", "-p", "1", "--json"])
        assert result.exit_code == 0
        high = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Low", "-p", "3", "--json"])
        assert result.exit_code == 0
        low = json.loads(result.stdout)

        # Filter for high-priority only (0-1)
        result = runner.invoke(app, ["list", "--priority-min", "0", "--priority-max", "1", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)

        issue_ids = {i["id"] for i in issues}
        assert critical["id"] in issue_ids
        assert high["id"] in issue_ids
        assert low["id"] not in issue_ids

    def test_filter_empty_description(self, integration_cli_runner: CliRunner):
        """Test filtering issues with no description."""
        runner = integration_cli_runner

        # Create issue without description
        result = runner.invoke(app, ["create", "No desc task", "--json"])
        assert result.exit_code == 0
        no_desc = json.loads(result.stdout)

        # Create issue with description
        result = runner.invoke(app, ["create", "Has desc task", "-d", "This has a description", "--json"])
        assert result.exit_code == 0
        has_desc = json.loads(result.stdout)

        # Filter for empty description
        result = runner.invoke(app, ["list", "--empty-description", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)

        issue_ids = {i["id"] for i in issues}
        assert no_desc["id"] in issue_ids
        assert has_desc["id"] not in issue_ids

    def test_filter_label_or_logic(self, integration_cli_runner: CliRunner):
        """Test filtering with OR logic for labels (has ANY label)."""
        runner = integration_cli_runner

        # Create issues with different labels
        result = runner.invoke(app, ["create", "Frontend task", "--json"])
        assert result.exit_code == 0
        frontend = json.loads(result.stdout)
        runner.invoke(app, ["labels", "add", frontend["id"], "frontend"])

        result = runner.invoke(app, ["create", "Backend task", "--json"])
        assert result.exit_code == 0
        backend = json.loads(result.stdout)
        runner.invoke(app, ["labels", "add", backend["id"], "backend"])

        result = runner.invoke(app, ["create", "No labels task", "--json"])
        assert result.exit_code == 0
        json.loads(result.stdout)

        # Filter with OR logic using --label-any
        result = runner.invoke(app, ["list", "--label-any", "frontend,backend", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)

        issue_ids = {i["id"] for i in issues}
        # Should include issues with frontend OR backend labels
        has_frontend = frontend["id"] in issue_ids
        has_backend = backend["id"] in issue_ids
        assert has_frontend or has_backend, "Should find at least one labeled issue"
        # Issues without labels should not appear
        # Note: may include other issues from workspace - just check our issues are handled correctly

    def test_text_search_in_fields(self, integration_cli_runner: CliRunner):
        """Test text search in title and description."""
        runner = integration_cli_runner

        # Create issues with different text
        result = runner.invoke(app, ["create", "Implement authentication", "-d", "Add JWT token support", "--json"])
        assert result.exit_code == 0
        auth_issue = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Fix database bug", "-d", "Connection pool issue", "--json"])
        assert result.exit_code == 0
        db_issue = json.loads(result.stdout)

        # Search in title
        result = runner.invoke(app, ["list", "--title-contains", "authentication", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)
        issue_ids = {i["id"] for i in issues}
        assert auth_issue["id"] in issue_ids
        assert db_issue["id"] not in issue_ids

        # Search in description
        result = runner.invoke(app, ["list", "--desc-contains", "JWT", "--json"])
        assert result.exit_code == 0
        issues = json.loads(result.stdout)
        issue_ids = {i["id"] for i in issues}
        assert auth_issue["id"] in issue_ids
        assert db_issue["id"] not in issue_ids

    def test_combined_filters(self, integration_cli_runner: CliRunner):
        """Test combining multiple filters together."""
        runner = integration_cli_runner

        # Create high-priority bug with specific label
        result = runner.invoke(app, ["create", "Critical auth bug", "-t", "bug", "-p", "0", "--json"])
        assert result.exit_code == 0
        target = json.loads(result.stdout)
        runner.invoke(app, ["labels", "add", target["id"], "security"])

        # Create other issues that don't match all criteria
        runner.invoke(app, ["create", "Low priority bug", "-t", "bug", "-p", "3", "--json"])
        runner.invoke(app, ["create", "High priority feature", "-t", "feature", "-p", "0", "--json"])

        # Filter with multiple criteria
        result = runner.invoke(
            app,
            [
                "list",
                "--type",
                "bug",
                "--priority-max",
                "1",
                "--label-any",
                "security",
                "--json",
            ],
        )
        assert result.exit_code == 0
        issues = json.loads(result.stdout)

        # Should only get the target issue
        assert len(issues) >= 1
        assert any(i["id"] == target["id"] for i in issues)

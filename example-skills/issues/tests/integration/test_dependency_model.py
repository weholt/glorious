"""Integration tests for dependency data model validation.

Tests that dependencies have all required fields and support all dependency types.
"""

import json

from typer.testing import CliRunner

from issue_tracker.cli.app import app


class TestDependencyDataModel:
    """Validate Dependency entity matches Beads schema."""

    def test_dependency_has_required_fields(self, integration_cli_runner: CliRunner):
        """Test dependency entity has from_issue_id, to_issue_id, type, created_at."""
        runner = integration_cli_runner

        # Create two issues
        result = runner.invoke(app, ["create", "Issue A", "--json"])
        assert result.exit_code == 0
        issue_a = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Issue B", "--json"])
        assert result.exit_code == 0
        issue_b = json.loads(result.stdout)

        # Add dependency
        result = runner.invoke(app, ["dependencies", "add", issue_a["id"], "blocks", issue_b["id"]])
        assert result.exit_code == 0

        # List all dependencies
        result = runner.invoke(app, ["dependencies", "list-all", "--json"])
        assert result.exit_code == 0
        deps = json.loads(result.stdout)

        assert len(deps) > 0
        dep = next(d for d in deps if d["from"] == issue_a["id"])

        # Verify required fields
        assert "from" in dep
        assert "to" in dep
        assert "type" in dep
        assert dep["from"] == issue_a["id"]
        assert dep["to"] == issue_b["id"]
        assert dep["type"] == "blocks"

    def test_dependency_types(self, integration_cli_runner: CliRunner):
        """Test all dependency types: blocks, depends-on, related-to, discovered-from."""
        runner = integration_cli_runner

        # Valid dependency types per DependencyType enum
        valid_types = ["blocks", "depends-on", "related-to", "discovered-from"]

        for dep_type in valid_types:
            # Create two new issues for each type
            result = runner.invoke(app, ["create", f"Issue from {dep_type}", "--json"])
            assert result.exit_code == 0
            from_issue = json.loads(result.stdout)

            result = runner.invoke(app, ["create", f"Issue to {dep_type}", "--json"])
            assert result.exit_code == 0
            to_issue = json.loads(result.stdout)

            # Add dependency with specific type
            result = runner.invoke(
                app, ["dependencies", "add", from_issue["id"], dep_type, to_issue["id"], "--json"]
            )
            assert result.exit_code == 0, f"Failed to add {dep_type} dependency"

            data = json.loads(result.stdout)
            assert data["from"] == from_issue["id"]
            assert data["to"] == to_issue["id"]
            assert data["type"] == dep_type

    def test_dependency_unique_constraint(self, integration_cli_runner: CliRunner):
        """Test no duplicate dependencies of same type between same issues."""
        runner = integration_cli_runner

        # Create two issues
        result = runner.invoke(app, ["create", "Issue 1", "--json"])
        assert result.exit_code == 0
        issue1 = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Issue 2", "--json"])
        assert result.exit_code == 0
        issue2 = json.loads(result.stdout)

        # Add dependency
        result = runner.invoke(app, ["dependencies", "add", issue1["id"], "blocks", issue2["id"]])
        assert result.exit_code == 0

        # Try to add same dependency again - should be rejected
        result = runner.invoke(app, ["dependencies", "add", issue1["id"], "blocks", issue2["id"]])
        # Should fail with error message about duplicate
        assert result.exit_code != 0
        assert "already exists" in result.stdout.lower() or "duplicate" in result.stdout.lower()

    def test_dependency_self_reference_prevention(self, integration_cli_runner: CliRunner):
        """Test that issues cannot depend on themselves."""
        runner = integration_cli_runner

        # Create issue
        result = runner.invoke(app, ["create", "Self-referencing issue", "--json"])
        assert result.exit_code == 0
        issue = json.loads(result.stdout)

        # Try to add self-dependency - should fail
        result = runner.invoke(app, ["dependencies", "add", issue["id"], "blocks", issue["id"]])
        assert result.exit_code != 0
        assert "itself" in result.stdout.lower() or "self" in result.stdout.lower()

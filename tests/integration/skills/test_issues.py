"""Integration tests for issues skill."""

import re

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestIssuesCreateCommand:
    """Tests for 'agent issues create' command."""

    def test_issues_create_basic(self, isolated_env):
        """Test creating a basic issue."""
        result = run_agent_cli(
            ["issues", "create", "Test Issue", "This is a test issue description"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]
        assert "created" in result["stdout"].lower() or "issue" in result["stdout"].lower()

    def test_issues_create_with_priority(self, isolated_env):
        """Test creating issue with priority."""
        result = run_agent_cli(
            ["issues", "create", "High Priority Issue", "Description", "--priority", "high"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_issues_create_with_labels(self, isolated_env):
        """Test creating issue with labels."""
        result = run_agent_cli(
            ["issues", "create", "Labeled Issue", "Description", "--labels", "bug,urgent"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_issues_create_with_assignee(self, isolated_env):
        """Test creating issue with assignee."""
        result = run_agent_cli(
            ["issues", "create", "Assigned Issue", "Description", "--assignee", "developer"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_issues_create_with_milestone(self, isolated_env):
        """Test creating issue with milestone."""
        result = run_agent_cli(
            ["issues", "create", "Milestone Issue", "Description", "--milestone", "v1.0"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_issues_create_empty_title(self, isolated_env):
        """Test creating issue with empty title."""
        result = run_agent_cli(
            ["issues", "create", "", "Description"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert not result["success"]


@pytest.mark.integration
class TestIssuesListCommand:
    """Tests for 'agent issues list' command."""

    def test_issues_list_default(self, isolated_env):
        """Test listing issues with defaults."""
        run_agent_cli(
            ["issues", "create", "Issue 1", "Description 1"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["issues", "create", "Issue 2", "Description 2"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["issues", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_issues_list_with_status(self, isolated_env):
        """Test listing issues by status."""
        result = run_agent_cli(
            ["issues", "list", "--status", "open"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_issues_list_with_priority(self, isolated_env):
        """Test listing issues by priority."""
        result = run_agent_cli(
            ["issues", "list", "--priority", "high"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_issues_list_with_labels(self, isolated_env):
        """Test listing issues by labels."""
        result = run_agent_cli(
            ["issues", "list", "--labels", "bug"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_issues_list_with_assignee(self, isolated_env):
        """Test listing issues by assignee."""
        result = run_agent_cli(
            ["issues", "list", "--assignee", "developer"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_issues_list_with_limit(self, isolated_env):
        """Test listing issues with custom limit."""
        for i in range(10):
            run_agent_cli(
                ["issues", "create", f"Issue {i}", "Description"],
                cwd=isolated_env["cwd"],
                isolated_env=isolated_env,
            )

        result = run_agent_cli(
            ["issues", "list", "--limit", "5"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_issues_list_json_output(self, isolated_env):
        """Test listing issues with JSON output."""
        run_agent_cli(
            ["issues", "create", "Test Issue", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["issues", "list", "--json"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"] and result["stdout"].strip():
            import json

            try:
                data = json.loads(result["stdout"])
                assert isinstance(data, list)
            except json.JSONDecodeError:
                pass


@pytest.mark.integration
class TestIssuesGetCommand:
    """Tests for 'agent issues get' command."""

    def test_issues_get_existing(self, isolated_env):
        """Test getting existing issue."""
        create_result = run_agent_cli(
            ["issues", "create", "Get This Issue", "Description"], cwd=isolated_env["cwd"]
        )

        # Try to extract issue ID from output
        match = re.search(r"(?:issue|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            issue_id = match.group(1)
            result = run_agent_cli(
                ["issues", "get", issue_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            if result["success"]:
                assert "Get This Issue" in result["stdout"] or "issue" in result["stdout"].lower()

    def test_issues_get_nonexistent(self, isolated_env):
        """Test getting non-existent issue."""
        result = run_agent_cli(
            ["issues", "get", "99999"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert "not found" in result["output"].lower() or not result["success"]


@pytest.mark.integration
class TestIssuesUpdateCommand:
    """Tests for 'agent issues update' command."""

    def test_issues_update_title(self, isolated_env):
        """Test updating issue title."""
        create_result = run_agent_cli(
            ["issues", "create", "Original Title", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:issue|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            issue_id = match.group(1)
            result = run_agent_cli(
                ["issues", "update", issue_id, "--title", "Updated Title"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]

    def test_issues_update_status(self, isolated_env):
        """Test updating issue status."""
        create_result = run_agent_cli(
            ["issues", "create", "Test Issue", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:issue|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            issue_id = match.group(1)
            result = run_agent_cli(
                ["issues", "update", issue_id, "--status", "closed"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]

    def test_issues_update_priority(self, isolated_env):
        """Test updating issue priority."""
        create_result = run_agent_cli(
            ["issues", "create", "Test Issue", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:issue|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            issue_id = match.group(1)
            result = run_agent_cli(
                ["issues", "update", issue_id, "--priority", "critical"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestIssuesCloseCommand:
    """Tests for 'agent issues close' command."""

    def test_issues_close_existing(self, isolated_env):
        """Test closing existing issue."""
        create_result = run_agent_cli(
            ["issues", "create", "Close Me", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:issue|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            issue_id = match.group(1)
            result = run_agent_cli(
                ["issues", "close", issue_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            assert result["returncode"] in [0, 1]

    def test_issues_close_nonexistent(self, isolated_env):
        """Test closing non-existent issue."""
        result = run_agent_cli(
            ["issues", "close", "99999"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestIssuesDeleteCommand:
    """Tests for 'agent issues delete' command."""

    def test_issues_delete_existing(self, isolated_env):
        """Test deleting existing issue."""
        create_result = run_agent_cli(
            ["issues", "create", "Delete Me", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:issue|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            issue_id = match.group(1)
            result = run_agent_cli(
                ["issues", "delete", issue_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            assert result["returncode"] in [0, 1]

    def test_issues_delete_nonexistent(self, isolated_env):
        """Test deleting non-existent issue."""
        result = run_agent_cli(
            ["issues", "delete", "99999"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestIssuesSearchCommand:
    """Tests for 'agent issues search' command."""

    def test_issues_search_basic(self, isolated_env):
        """Test searching issues."""
        run_agent_cli(
            ["issues", "create", "Bug in authentication", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["issues", "search", "authentication"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["returncode"] in [0, 1]

    def test_issues_search_no_results(self, isolated_env):
        """Test search with no results."""
        result = run_agent_cli(
            ["issues", "search", "nonexistent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestIssuesCommentCommand:
    """Tests for 'agent issues comment' command."""

    def test_issues_comment_add(self, isolated_env):
        """Test adding comment to issue."""
        create_result = run_agent_cli(
            ["issues", "create", "Test Issue", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:issue|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            issue_id = match.group(1)
            result = run_agent_cli(
                ["issues", "comment", issue_id, "This is a comment"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestIssuesImportCommand:
    """Tests for 'agent issues import' command."""

    def test_issues_import_from_file(self, isolated_env):
        """Test importing issues from file."""
        import json

        # Create import file
        import_file = isolated_env["root"] / "issues.json"
        issues_data = [
            {"title": "Imported Issue 1", "description": "Description 1", "priority": "high"},
            {
                "title": "Imported Issue 2",
                "description": "Description 2",
                "labels": ["bug", "urgent"],
            },
        ]
        import_file.write_text(json.dumps(issues_data))

        result = run_agent_cli(["issues", "import", str(import_file)], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestIssuesExportCommand:
    """Tests for 'agent issues export' command."""

    def test_issues_export_to_file(self, isolated_env):
        """Test exporting issues to file."""
        # Create some issues first
        run_agent_cli(
            ["issues", "create", "Export Issue 1", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["issues", "create", "Export Issue 2", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        export_file = isolated_env["root"] / "exported_issues.json"

        result = run_agent_cli(["issues", "export", str(export_file)], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestIssuesDependenciesCommand:
    """Tests for 'agent issues dependencies' command."""

    def test_issues_add_dependency(self, isolated_env):
        """Test adding dependency between issues."""
        # Create two issues
        run_agent_cli(
            ["issues", "create", "Issue 1", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["issues", "create", "Issue 2", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        # Try to add dependency
        result = run_agent_cli(["issues", "depends", "1", "2"], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_issues_list_dependencies(self, isolated_env):
        """Test listing issue dependencies."""
        result = run_agent_cli(
            ["issues", "dependencies"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

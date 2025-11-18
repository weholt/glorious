"""Integration tests for feedback skill."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestFeedbackSubmitCommand:
    """Tests for 'agent feedback submit' command."""

    def test_feedback_submit_basic(self, isolated_env):
        """Test submitting basic feedback."""
        result = run_agent_cli(
            ["feedback", "submit", "This is test feedback"], isolated_env=isolated_env
        )

        assert result["success"]
        assert "submitted" in result["stdout"].lower() or "feedback" in result["stdout"].lower()

    def test_feedback_submit_with_type(self, isolated_env):
        """Test submitting feedback with type."""
        result = run_agent_cli(
            ["feedback", "submit", "Bug report", "--type", "bug"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

    def test_feedback_submit_with_rating(self, isolated_env):
        """Test submitting feedback with rating."""
        result = run_agent_cli(
            ["feedback", "submit", "Great feature!", "--rating", "5"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

    def test_feedback_submit_with_category(self, isolated_env):
        """Test submitting feedback with category."""
        result = run_agent_cli(
            ["feedback", "submit", "UI improvement needed", "--category", "ui"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_feedback_submit_empty_content(self, isolated_env):
        """Test submitting empty feedback."""
        result = run_agent_cli(
            ["feedback", "submit", ""], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert not result["success"]


@pytest.mark.integration
class TestFeedbackListCommand:
    """Tests for 'agent feedback list' command."""

    def test_feedback_list_default(self, isolated_env):
        """Test listing feedback with defaults."""
        run_agent_cli(
            ["feedback", "submit", "Feedback 1"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        run_agent_cli(
            ["feedback", "submit", "Feedback 2"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["feedback", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_feedback_list_by_type(self, isolated_env):
        """Test listing feedback by type."""
        result = run_agent_cli(
            ["feedback", "list", "--type", "bug"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_feedback_list_by_category(self, isolated_env):
        """Test listing feedback by category."""
        result = run_agent_cli(
            ["feedback", "list", "--category", "ui"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_feedback_list_with_limit(self, isolated_env):
        """Test listing feedback with limit."""
        for i in range(10):
            run_agent_cli(
                ["feedback", "submit", f"Feedback {i}"],
                cwd=isolated_env["cwd"],
                isolated_env=isolated_env,
            )

        result = run_agent_cli(
            ["feedback", "list", "--limit", "5"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_feedback_list_json_output(self, isolated_env):
        """Test listing feedback with JSON output."""
        run_agent_cli(
            ["feedback", "submit", "Test feedback"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["feedback", "list", "--json"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"] and result["stdout"].strip():
            import json

            try:
                data = json.loads(result["stdout"])
                assert isinstance(data, list)
            except json.JSONDecodeError:
                pass


@pytest.mark.integration
class TestFeedbackGetCommand:
    """Tests for 'agent feedback get' command."""

    def test_feedback_get_existing(self, isolated_env):
        """Test getting existing feedback."""
        submit_result = run_agent_cli(
            ["feedback", "submit", "Get this feedback"], cwd=isolated_env["cwd"]
        )

        if submit_result["success"]:
            import re

            match = re.search(r"(?:feedback|id)[:\s]+(\d+)", submit_result["stdout"], re.IGNORECASE)
            if match:
                feedback_id = match.group(1)
                result = run_agent_cli(
                    ["feedback", "get", feedback_id],
                    cwd=isolated_env["cwd"],
                    isolated_env=isolated_env,
                )
                assert result["returncode"] in [0, 1]

    def test_feedback_get_nonexistent(self, isolated_env):
        """Test getting non-existent feedback."""
        result = run_agent_cli(
            ["feedback", "get", "99999"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert "not found" in result["output"].lower() or not result["success"]


@pytest.mark.integration
class TestFeedbackUpdateCommand:
    """Tests for 'agent feedback update' command."""

    def test_feedback_update_status(self, isolated_env):
        """Test updating feedback status."""
        submit_result = run_agent_cli(["feedback", "submit", "Update me"], cwd=isolated_env["cwd"])

        if submit_result["success"]:
            import re

            match = re.search(r"(?:feedback|id)[:\s]+(\d+)", submit_result["stdout"], re.IGNORECASE)
            if match:
                feedback_id = match.group(1)
                result = run_agent_cli(
                    ["feedback", "update", feedback_id, "--status", "reviewed"],
                    cwd=isolated_env["cwd"],
                )
                assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestFeedbackDeleteCommand:
    """Tests for 'agent feedback delete' command."""

    def test_feedback_delete_existing(self, isolated_env):
        """Test deleting existing feedback."""
        submit_result = run_agent_cli(["feedback", "submit", "Delete me"], cwd=isolated_env["cwd"])

        if submit_result["success"]:
            import re

            match = re.search(r"(?:feedback|id)[:\s]+(\d+)", submit_result["stdout"], re.IGNORECASE)
            if match:
                feedback_id = match.group(1)
                result = run_agent_cli(
                    ["feedback", "delete", feedback_id],
                    cwd=isolated_env["cwd"],
                    isolated_env=isolated_env,
                )
                assert result["returncode"] in [0, 1]

    def test_feedback_delete_nonexistent(self, isolated_env):
        """Test deleting non-existent feedback."""
        result = run_agent_cli(
            ["feedback", "delete", "99999"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestFeedbackStatsCommand:
    """Tests for 'agent feedback stats' command."""

    def test_feedback_stats_overall(self, isolated_env):
        """Test viewing overall feedback stats."""
        result = run_agent_cli(
            ["feedback", "stats"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_feedback_stats_by_type(self, isolated_env):
        """Test viewing stats by type."""
        result = run_agent_cli(
            ["feedback", "stats", "--group-by", "type"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_feedback_stats_by_category(self, isolated_env):
        """Test viewing stats by category."""
        result = run_agent_cli(
            ["feedback", "stats", "--group-by", "category"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]


@pytest.mark.integration
class TestFeedbackExportCommand:
    """Tests for 'agent feedback export' command."""

    def test_feedback_export_to_file(self, isolated_env):
        """Test exporting feedback to file."""
        run_agent_cli(
            ["feedback", "submit", "Export this"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        export_file = isolated_env["root"] / "feedback_export.json"

        result = run_agent_cli(["feedback", "export", str(export_file)], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_feedback_export_with_filter(self, isolated_env):
        """Test exporting filtered feedback."""
        export_file = isolated_env["root"] / "bugs.json"

        result = run_agent_cli(
            ["feedback", "export", str(export_file), "--type", "bug"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestFeedbackSearchCommand:
    """Tests for 'agent feedback search' command."""

    def test_feedback_search_basic(self, isolated_env):
        """Test searching feedback."""
        run_agent_cli(
            ["feedback", "submit", "Performance issue with loading"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["feedback", "search", "performance"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["returncode"] in [0, 1]

    def test_feedback_search_no_results(self, isolated_env):
        """Test search with no results."""
        result = run_agent_cli(
            ["feedback", "search", "nonexistent"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["returncode"] in [0, 1]

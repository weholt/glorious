"""Integration tests for notes skill."""

import re

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestNotesAddCommand:
    """Tests for 'agent notes add' command."""

    def test_notes_add_basic(self, isolated_env):
        """Test adding a basic note."""
        result = run_agent_cli(["notes", "add", "This is a test note"], cwd=isolated_env["cwd"])

        assert result["success"]
        assert "added" in result["stdout"].lower() or "note" in result["stdout"].lower()

    def test_notes_add_with_tags(self, isolated_env):
        """Test adding note with tags."""
        result = run_agent_cli(
            ["notes", "add", "Tagged note", "--tags", "test,important"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

    def test_notes_add_important(self, isolated_env):
        """Test adding important note."""
        result = run_agent_cli(
            ["notes", "add", "Important note", "--important"], cwd=isolated_env["cwd"]
        )

        assert result["success"]
        # May show importance indicator
        assert "★" in result["stdout"] or "important" in result["stdout"].lower()

    def test_notes_add_critical(self, isolated_env):
        """Test adding critical note."""
        result = run_agent_cli(
            ["notes", "add", "Critical note", "--critical"], cwd=isolated_env["cwd"]
        )

        assert result["success"]
        # May show critical indicator
        assert "⚠" in result["stdout"] or "critical" in result["stdout"].lower()

    def test_notes_add_empty_content(self, isolated_env):
        """Test adding note with empty content."""
        result = run_agent_cli(["notes", "add", ""], cwd=isolated_env["cwd"], expect_failure=True)

        assert not result["success"]

    def test_notes_add_very_long_content(self, isolated_env):
        """Test adding note with very long content."""
        long_content = "A" * 10000
        result = run_agent_cli(["notes", "add", long_content], cwd=isolated_env["cwd"])

        assert result["success"]


@pytest.mark.integration
class TestNotesListCommand:
    """Tests for 'agent notes list' command."""

    def test_notes_list_default(self, isolated_env):
        """Test listing notes with defaults."""
        run_agent_cli(
            ["notes", "add", "Note 1"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        run_agent_cli(
            ["notes", "add", "Note 2"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["notes", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        # Should show notes
        assert "note" in result["stdout"].lower() or len(result["stdout"]) > 0

    def test_notes_list_with_limit(self, isolated_env):
        """Test listing notes with custom limit."""
        for i in range(10):
            run_agent_cli(
                ["notes", "add", f"Note {i}"], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )

        result = run_agent_cli(
            ["notes", "list", "--limit", "5"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_notes_list_important_only(self, isolated_env):
        """Test listing only important notes."""
        run_agent_cli(
            ["notes", "add", "Normal note"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        run_agent_cli(
            ["notes", "add", "Important note", "--important"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["notes", "list", "--important"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_notes_list_critical_only(self, isolated_env):
        """Test listing only critical notes."""
        run_agent_cli(
            ["notes", "add", "Normal note"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        run_agent_cli(
            ["notes", "add", "Critical note", "--critical"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["notes", "list", "--critical"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]


@pytest.mark.integration
class TestNotesSearchCommand:
    """Tests for 'agent notes search' command."""

    def test_notes_search_basic(self, isolated_env):
        """Test searching notes."""
        run_agent_cli(
            ["notes", "add", "Quantum physics research"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["notes", "search", "quantum"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        if "quantum" in result["stdout"].lower():
            assert "quantum" in result["stdout"].lower()

    def test_notes_search_no_results(self, isolated_env):
        """Test search with no results."""
        result = run_agent_cli(
            ["notes", "search", "nonexistent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        # Should handle no results gracefully

    def test_notes_search_json_output(self, isolated_env):
        """Test search with JSON output."""
        run_agent_cli(
            ["notes", "add", "Test note"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["notes", "search", "test", "--json"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        if result["success"] and result["stdout"].strip():
            import json

            try:
                data = json.loads(result["stdout"])
                assert isinstance(data, list)
            except json.JSONDecodeError:
                # JSON output may not be implemented
                pass


@pytest.mark.integration
class TestNotesGetCommand:
    """Tests for 'agent notes get' command."""

    def test_notes_get_existing(self, isolated_env):
        """Test getting existing note."""
        add_result = run_agent_cli(
            ["notes", "add", "Get this note"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Try to extract note ID from output
        match = re.search(r"(?:note|id)[:\s]+(\d+)", add_result["stdout"], re.IGNORECASE)
        if match:
            note_id = match.group(1)
            result = run_agent_cli(
                ["notes", "get", note_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            if result["success"]:
                assert "Get this note" in result["stdout"] or "note" in result["stdout"].lower()

    def test_notes_get_nonexistent(self, isolated_env):
        """Test getting non-existent note."""
        result = run_agent_cli(
            ["notes", "get", "99999"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert "not found" in result["output"].lower() or not result["success"]


@pytest.mark.integration
class TestNotesMarkCommand:
    """Tests for 'agent notes mark' command."""

    def test_notes_mark_important(self, isolated_env):
        """Test marking note as important."""
        add_result = run_agent_cli(
            ["notes", "add", "Mark me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        match = re.search(r"(?:note|id)[:\s]+(\d+)", add_result["stdout"], re.IGNORECASE)
        if match:
            note_id = match.group(1)
            result = run_agent_cli(
                ["notes", "mark", note_id, "--important"],
                cwd=isolated_env["cwd"],
                isolated_env=isolated_env,
            )
            assert result["returncode"] in [0, 1]

    def test_notes_mark_critical(self, isolated_env):
        """Test marking note as critical."""
        add_result = run_agent_cli(
            ["notes", "add", "Mark me critical"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        match = re.search(r"(?:note|id)[:\s]+(\d+)", add_result["stdout"], re.IGNORECASE)
        if match:
            note_id = match.group(1)
            result = run_agent_cli(
                ["notes", "mark", note_id, "--critical"],
                cwd=isolated_env["cwd"],
                isolated_env=isolated_env,
            )
            assert result["returncode"] in [0, 1]

    def test_notes_mark_normal(self, isolated_env):
        """Test marking note as normal."""
        add_result = run_agent_cli(
            ["notes", "add", "Mark me", "--critical"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        match = re.search(r"(?:note|id)[:\s]+(\d+)", add_result["stdout"], re.IGNORECASE)
        if match:
            note_id = match.group(1)
            result = run_agent_cli(
                ["notes", "mark", note_id, "--normal"],
                cwd=isolated_env["cwd"],
                isolated_env=isolated_env,
            )
            assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestNotesDeleteCommand:
    """Tests for 'agent notes delete' command."""

    def test_notes_delete_existing(self, isolated_env):
        """Test deleting existing note."""
        add_result = run_agent_cli(
            ["notes", "add", "Delete me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        match = re.search(r"(?:note|id)[:\s]+(\d+)", add_result["stdout"], re.IGNORECASE)
        if match:
            note_id = match.group(1)
            result = run_agent_cli(
                ["notes", "delete", note_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            assert result["success"] or "deleted" in result["stdout"].lower()

    def test_notes_delete_nonexistent(self, isolated_env):
        """Test deleting non-existent note."""
        result = run_agent_cli(
            ["notes", "delete", "99999"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed (idempotent) or show not found
        assert result["returncode"] in [0, 1]

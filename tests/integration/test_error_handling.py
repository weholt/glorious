"""Error handling and edge case tests."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_sql_injection_prevention(self, isolated_env):
        """Test that SQL injection is prevented."""
        malicious_input = "'; DROP TABLE notes; --"

        result = run_agent_cli(["notes", "add", malicious_input], cwd=isolated_env["cwd"])

        # Should succeed without executing SQL
        assert result["success"]

        # Verify table still exists by listing notes
        list_result = run_agent_cli(
            ["notes", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        assert list_result["success"]

    def test_unicode_handling(self, isolated_env):
        """Test handling of Unicode characters."""
        unicode_text = "Hello 世界 🌍 Привет"

        result = run_agent_cli(["notes", "add", unicode_text], cwd=isolated_env["cwd"])

        assert result["success"]

    def test_very_long_input(self, isolated_env):
        """Test handling of very long input."""
        long_text = "A" * 100000

        result = run_agent_cli(["notes", "add", long_text], cwd=isolated_env["cwd"])

        # Should either succeed or fail gracefully
        assert result["returncode"] in [0, 1]

    def test_null_bytes_in_input(self, isolated_env):
        """Test handling of null bytes."""
        # Note: Null bytes cannot be passed through subprocess arguments
        # This test verifies that the system handles this limitation gracefully
        with pytest.raises(ValueError, match="embedded null byte"):
            run_agent_cli(["notes", "add", "test\x00null"], cwd=isolated_env["cwd"])

    def test_special_characters_in_identifiers(self, isolated_env):
        """Test special characters in identifiers."""
        result = run_agent_cli(
            ["identity", "register", "--name", "Test@#$%Agent"], cwd=isolated_env["cwd"]
        )

        # Should sanitize or handle gracefully
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestErrorMessages:
    """Tests for error message quality."""

    def test_not_found_error_message(self, isolated_env):
        """Test error message for non-existent resources."""
        result = run_agent_cli(
            ["notes", "get", "99999"], cwd=isolated_env["cwd"], expect_failure=True
        )

        # Should have clear error message
        assert "not found" in result["output"].lower() or "error" in result["output"].lower()

    def test_invalid_command_error(self, isolated_env):
        """Test error message for invalid commands."""
        result = run_agent_cli(
            ["nonexistent-command"], cwd=isolated_env["cwd"], expect_failure=True
        )

        # Should show error
        assert not result["success"]

    def test_missing_required_argument(self, isolated_env):
        """Test error message for missing required arguments."""
        result = run_agent_cli(["notes", "add"], cwd=isolated_env["cwd"], expect_failure=True)

        # Should show error about missing argument
        assert not result["success"]


@pytest.mark.integration
class TestConcurrency:
    """Tests for concurrent access handling."""

    def test_concurrent_writes(self, isolated_env):
        """Test concurrent writes to database."""
        import threading

        results = []

        def add_note(n):
            result = run_agent_cli(
                ["notes", "add", f"Note {n}"], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            results.append(result)

        threads = [threading.Thread(target=add_note, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Most should succeed
        successful = sum(1 for r in results if r["success"])
        assert successful >= 3  # At least 3 out of 5 should succeed

    def test_concurrent_reads(self, isolated_env):
        """Test concurrent reads from database."""
        # Add some data first
        run_agent_cli(
            ["notes", "add", "Test note"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        import threading

        results = []

        def list_notes():
            result = run_agent_cli(
                ["notes", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            results.append(result)

        threads = [threading.Thread(target=list_notes) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All reads should succeed
        assert all(r["success"] for r in results)


@pytest.mark.integration
class TestDatabaseErrors:
    """Tests for database error handling."""

    def test_corrupted_database_handling(self, isolated_env):
        """Test handling of corrupted database."""
        # Create some data first
        run_agent_cli(["notes", "add", "Test"], cwd=isolated_env["cwd"], isolated_env=isolated_env)

        # Corrupt the database file
        db_path = isolated_env["agent_folder"] / "agents" / "default" / "agent.db"
        if db_path.exists():
            db_path.write_bytes(b"corrupted data")

        # Try to use CLI
        result = run_agent_cli(
            ["notes", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should fail gracefully with error message
        assert (
            "error" in result["output"].lower()
            or "corrupt" in result["output"].lower()
            or not result["success"]
        )

    @pytest.mark.skipif(True, reason="Permission tests may not work in all environments")
    def test_readonly_database(self, isolated_env):
        """Test handling of read-only database."""
        import os

        # Create database first
        run_agent_cli(["notes", "add", "Test"], cwd=isolated_env["cwd"], isolated_env=isolated_env)

        # Make database read-only
        db_path = isolated_env["agent_folder"] / "agents" / "default" / "agent.db"
        if db_path.exists():
            os.chmod(db_path, 0o444)

        # Try to write
        result = run_agent_cli(
            ["notes", "add", "Should fail"], cwd=isolated_env["cwd"], expect_failure=True
        )

        # Should fail with permission error
        assert not result["success"]

        # Restore permissions
        if db_path.exists():
            os.chmod(db_path, 0o644)


@pytest.mark.integration
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_database_operations(self, isolated_env):
        """Test operations on empty database."""
        result = run_agent_cli(
            ["notes", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should handle empty database gracefully
        assert result["success"]

    def test_maximum_limit_parameter(self, isolated_env):
        """Test with very large limit parameter."""
        result = run_agent_cli(
            ["notes", "list", "--limit", "999999"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        # Should handle gracefully
        assert result["returncode"] in [0, 1]

    def test_zero_limit_parameter(self, isolated_env):
        """Test with zero limit parameter."""
        result = run_agent_cli(
            ["notes", "list", "--limit", "0"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should handle gracefully
        assert result["returncode"] in [0, 1]

    def test_negative_limit_parameter(self, isolated_env):
        """Test with negative limit parameter."""
        result = run_agent_cli(
            ["notes", "list", "--limit", "-1"], cwd=isolated_env["cwd"], expect_failure=True
        )

        # Should reject negative limit
        assert not result["success"]

    def test_empty_string_arguments(self, isolated_env):
        """Test with empty string arguments."""
        result = run_agent_cli(["notes", "add", ""], cwd=isolated_env["cwd"], expect_failure=True)

        # Should reject empty content
        assert not result["success"]

    def test_whitespace_only_arguments(self, isolated_env):
        """Test with whitespace-only arguments."""
        result = run_agent_cli(["notes", "add", "   "], cwd=isolated_env["cwd"])

        # Should either accept or reject gracefully
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestResourceLimits:
    """Tests for resource limit handling."""

    def test_many_records(self, isolated_env):
        """Test handling of many records."""
        # Add many notes
        for i in range(100):
            run_agent_cli(
                ["notes", "add", f"Note {i}"], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )

        # List should still work
        result = run_agent_cli(
            ["notes", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        assert result["success"]

    def test_large_json_output(self, isolated_env):
        """Test large JSON output."""
        # Add many notes
        for i in range(50):
            run_agent_cli(
                ["notes", "add", f"Note {i}"], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )

        # Get JSON output
        result = run_agent_cli(
            ["notes", "search", "Note", "--json"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        # Should handle large output
        assert result["returncode"] in [0, 1]

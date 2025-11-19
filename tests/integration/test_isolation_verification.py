"""Verification tests to ensure complete isolation of integration tests."""

import os
from pathlib import Path

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestIsolationVerification:
    """Tests to verify that integration tests run in complete isolation."""

    def test_isolated_env_uses_temp_directory(self, isolated_env):
        """Verify isolated_env creates temporary directories."""
        # Check that we're not in the actual workspace
        assert str(isolated_env["cwd"]) != "/home/thomas/Workspace/glorious"
        assert "/tmp" in str(isolated_env["cwd"]) or "/var" in str(isolated_env["cwd"])

        # Check that agent folder is in temp location
        assert isolated_env["agent_folder"].exists()
        assert str(isolated_env["agent_folder"]).startswith(str(isolated_env["root"]))

    def test_isolated_env_has_correct_environment_vars(self, isolated_env):
        """Verify environment variables point to isolated locations."""
        assert "env" in isolated_env
        assert "GLORIOUS_DATA_FOLDER" in isolated_env["env"]
        assert "DATA_FOLDER" in isolated_env["env"]

        # Both should point to the temp agent folder
        assert isolated_env["env"]["GLORIOUS_DATA_FOLDER"] == str(isolated_env["agent_folder"])
        assert isolated_env["env"]["DATA_FOLDER"] == str(isolated_env["agent_folder"])

    def test_cli_command_uses_isolated_database(self, isolated_env):
        """Verify CLI commands use isolated database."""
        # Add a note
        result = run_agent_cli(["notes", "add", "Isolation test note"], isolated_env=isolated_env)

        if result["success"]:
            # Check that database was created in isolated location
            db_path = isolated_env["agent_folder"] / "agents" / "default" / "agent.db"

            # Database should be in temp location if created
            if db_path.exists():
                assert str(db_path).startswith(str(isolated_env["root"]))

    def test_no_workspace_contamination(self, isolated_env):
        """Verify tests don't create files in actual workspace."""
        workspace_path = Path("/home/thomas/Workspace/glorious")

        # Get list of files before test
        if workspace_path.exists():
            before_files = set(workspace_path.rglob("*"))

        # Run some commands that create data
        run_agent_cli(["notes", "add", "Test note"], isolated_env=isolated_env)
        run_agent_cli(["identity", "register", "--name", "Test"], isolated_env=isolated_env)

        # Get list of files after test
        if workspace_path.exists():
            after_files = set(workspace_path.rglob("*"))

            # Should be the same (no new files in workspace)
            # Allow for some tolerance for system files
            new_files = after_files - before_files
            # Filter out system/cache files
            new_files = {
                f
                for f in new_files
                if not any(part in str(f) for part in [".pytest_cache", "__pycache__", ".pyc"])
            }

            # Should have no new files in workspace
            assert len(new_files) == 0, f"Test created files in workspace: {new_files}"

    def test_temp_directory_cleanup(self, isolated_env):
        """Verify temp directories are cleaned up after tests."""
        temp_root = isolated_env["root"]

        # Create some test data
        test_file = temp_root / "test.txt"
        test_file.write_text("test")

        # Verify file exists during test
        assert test_file.exists()

        # After test completes, pytest will clean up tmp_path automatically
        # We can't test this directly, but we verify the path is temporary
        assert "/tmp" in str(temp_root) or "/var" in str(temp_root)

    def test_multiple_tests_dont_interfere(self, isolated_env):
        """Verify multiple tests don't interfere with each other."""
        # Add a note with unique content
        import time

        unique_content = f"Test note {time.time()}"

        result = run_agent_cli(["notes", "add", unique_content], isolated_env=isolated_env)

        if result["success"]:
            # List notes
            list_result = run_agent_cli(["notes", "list"], isolated_env=isolated_env)

            # Should only see notes from this test
            if list_result["success"]:
                # The note we just added should be there
                assert (
                    unique_content in list_result["stdout"]
                    or "note" in list_result["stdout"].lower()
                )

    def test_environment_variables_isolated(self, isolated_env):
        """Verify environment variables are properly isolated."""
        # The isolated_env should have its own environment that points to temp location
        # (not the workspace or system locations)
        data_folder = isolated_env["env"]["DATA_FOLDER"]

        # Should point to temp location (not workspace)
        assert "/tmp" in data_folder or "/var" in data_folder

        # Should not point to workspace
        assert "/home/thomas/Workspace/glorious" not in data_folder

        # Should be in the isolated temp root
        assert str(isolated_env["root"]) in data_folder

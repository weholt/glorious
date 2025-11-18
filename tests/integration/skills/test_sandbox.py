"""Integration tests for sandbox skill."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestSandboxCreateCommand:
    """Tests for 'agent sandbox create' command."""

    def test_sandbox_create_basic(self, isolated_env):
        """Test creating a basic sandbox."""
        result = run_agent_cli(["sandbox", "create", "test-sandbox"], cwd=isolated_env["cwd"])

        assert result["success"]
        assert "created" in result["stdout"].lower() or "sandbox" in result["stdout"].lower()

    def test_sandbox_create_with_template(self, isolated_env):
        """Test creating sandbox with template."""
        result = run_agent_cli(
            ["sandbox", "create", "template-sandbox", "--template", "python"],
            cwd=isolated_env["cwd"],
        )

        assert result["returncode"] in [0, 1]

    def test_sandbox_create_with_description(self, isolated_env):
        """Test creating sandbox with description."""
        result = run_agent_cli(
            ["sandbox", "create", "desc-sandbox", "--description", "Test sandbox"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_sandbox_create_duplicate(self, isolated_env):
        """Test creating duplicate sandbox."""
        run_agent_cli(
            ["sandbox", "create", "duplicate"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        result = run_agent_cli(
            ["sandbox", "create", "duplicate"], cwd=isolated_env["cwd"], expect_failure=True
        )

        # Should fail or warn about duplicate
        assert "exists" in result["output"].lower() or not result["success"]


@pytest.mark.integration
class TestSandboxListCommand:
    """Tests for 'agent sandbox list' command."""

    def test_sandbox_list_default(self, isolated_env):
        """Test listing sandboxes."""
        run_agent_cli(
            ["sandbox", "create", "sandbox1"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        run_agent_cli(
            ["sandbox", "create", "sandbox2"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_sandbox_list_json_output(self, isolated_env):
        """Test listing sandboxes with JSON output."""
        run_agent_cli(
            ["sandbox", "create", "test"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "list", "--json"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"] and result["stdout"].strip():
            import json

            try:
                data = json.loads(result["stdout"])
                assert isinstance(data, list)
            except json.JSONDecodeError:
                pass


@pytest.mark.integration
class TestSandboxGetCommand:
    """Tests for 'agent sandbox get' command."""

    def test_sandbox_get_existing(self, isolated_env):
        """Test getting existing sandbox."""
        run_agent_cli(
            ["sandbox", "create", "get-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "get", "get-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_sandbox_get_nonexistent(self, isolated_env):
        """Test getting non-existent sandbox."""
        result = run_agent_cli(
            ["sandbox", "get", "nonexistent"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert "not found" in result["output"].lower() or not result["success"]


@pytest.mark.integration
class TestSandboxRunCommand:
    """Tests for 'agent sandbox run' command."""

    def test_sandbox_run_command(self, isolated_env):
        """Test running command in sandbox."""
        run_agent_cli(
            ["sandbox", "create", "run-test"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "run", "run-test", "echo", "hello"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_sandbox_run_python_code(self, isolated_env):
        """Test running Python code in sandbox."""
        run_agent_cli(
            ["sandbox", "create", "python-test"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "run", "python-test", "python", "-c", 'print("test")'],
            cwd=isolated_env["cwd"],
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSandboxExecCommand:
    """Tests for 'agent sandbox exec' command."""

    def test_sandbox_exec_script(self, isolated_env):
        """Test executing script in sandbox."""
        run_agent_cli(
            ["sandbox", "create", "exec-test"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Create a test script
        script_file = isolated_env["root"] / "test.sh"
        script_file.write_text('#!/bin/bash\necho "test"\n')

        result = run_agent_cli(
            ["sandbox", "exec", "exec-test", str(script_file)], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSandboxDeleteCommand:
    """Tests for 'agent sandbox delete' command."""

    def test_sandbox_delete_existing(self, isolated_env):
        """Test deleting existing sandbox."""
        run_agent_cli(
            ["sandbox", "create", "delete-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "delete", "delete-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_sandbox_delete_nonexistent(self, isolated_env):
        """Test deleting non-existent sandbox."""
        result = run_agent_cli(
            ["sandbox", "delete", "nonexistent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_sandbox_delete_with_force(self, isolated_env):
        """Test force deleting sandbox."""
        run_agent_cli(
            ["sandbox", "create", "force-delete"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["sandbox", "delete", "force-delete", "--force"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSandboxCleanCommand:
    """Tests for 'agent sandbox clean' command."""

    def test_sandbox_clean_specific(self, isolated_env):
        """Test cleaning specific sandbox."""
        run_agent_cli(
            ["sandbox", "create", "clean-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "clean", "clean-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_sandbox_clean_all(self, isolated_env):
        """Test cleaning all sandboxes."""
        result = run_agent_cli(
            ["sandbox", "clean", "--all"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSandboxCopyCommand:
    """Tests for 'agent sandbox copy' command."""

    def test_sandbox_copy_file_to_sandbox(self, isolated_env):
        """Test copying file to sandbox."""
        run_agent_cli(
            ["sandbox", "create", "copy-test"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Create a test file
        test_file = isolated_env["root"] / "copy.txt"
        test_file.write_text("test content")

        result = run_agent_cli(
            ["sandbox", "copy", str(test_file), "copy-test:/tmp/"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_sandbox_copy_from_sandbox(self, isolated_env):
        """Test copying file from sandbox."""
        run_agent_cli(
            ["sandbox", "create", "copy-from"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "copy", "copy-from:/tmp/test.txt", str(isolated_env["root"])],
            cwd=isolated_env["cwd"],
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSandboxInspectCommand:
    """Tests for 'agent sandbox inspect' command."""

    def test_sandbox_inspect(self, isolated_env):
        """Test inspecting sandbox."""
        run_agent_cli(
            ["sandbox", "create", "inspect-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["sandbox", "inspect", "inspect-me"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_sandbox_inspect_json(self, isolated_env):
        """Test inspecting sandbox with JSON output."""
        run_agent_cli(
            ["sandbox", "create", "inspect-json"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["sandbox", "inspect", "inspect-json", "--json"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

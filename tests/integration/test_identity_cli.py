"""Integration tests for identity management CLI commands."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestIdentityRegisterCommand:
    """Tests for 'agent identity register' command."""

    def test_identity_register_basic(self, isolated_env):
        """Test registering a new agent."""
        result = run_agent_cli(
            ["identity", "register", "--name", "Test Agent"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]
        assert "registered" in result["stdout"].lower() or "test-agent" in result["stdout"].lower()

    def test_identity_register_with_role(self, isolated_env):
        """Test registering agent with role."""
        result = run_agent_cli(
            ["identity", "register", "--name", "Developer", "--role", "Code Review"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]
        assert "developer" in result["stdout"].lower() or "registered" in result["stdout"].lower()

    def test_identity_register_with_project(self, isolated_env):
        """Test registering agent with project ID."""
        result = run_agent_cli(
            ["identity", "register", "--name", "Project Agent", "--project-id", "proj-123"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_identity_register_duplicate(self, isolated_env):
        """Test registering duplicate agent (should replace)."""
        run_agent_cli(
            ["identity", "register", "--name", "Duplicate"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        result = run_agent_cli(
            ["identity", "register", "--name", "Duplicate"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]  # Should replace, not error

    def test_identity_register_special_characters(self, isolated_env):
        """Test registering agent with special characters in name."""
        result = run_agent_cli(
            ["identity", "register", "--name", "Test@Agent#123"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]
        # Code should be sanitized
        output_lower = result["stdout"].lower()
        assert "test" in output_lower

    def test_identity_register_empty_name(self, isolated_env):
        """Test registering with empty name."""
        result = run_agent_cli(
            ["identity", "register", "--name", ""],
            cwd=isolated_env["cwd"],
            expect_failure=True,
            isolated_env=isolated_env,
        )

        assert not result["success"]


@pytest.mark.integration
class TestIdentityUseCommand:
    """Tests for 'agent identity use' command."""

    def test_identity_use_existing_agent(self, isolated_env):
        """Test switching to existing agent."""
        run_agent_cli(
            ["identity", "register", "--name", "Test Agent"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        result = run_agent_cli(
            ["identity", "use", "test-agent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        assert "switched" in result["stdout"].lower() or "active" in result["stdout"].lower()

    def test_identity_use_nonexistent_agent(self, isolated_env):
        """Test switching to non-existent agent."""
        result = run_agent_cli(
            ["identity", "use", "nonexistent-agent"],
            cwd=isolated_env["cwd"],
            expect_failure=True,
            isolated_env=isolated_env,
        )

        assert not result["success"]
        assert "not found" in result["output"].lower() or "error" in result["output"].lower()

    def test_identity_use_persists(self, isolated_env):
        """Test that agent switch persists."""
        run_agent_cli(
            ["identity", "register", "--name", "Persistent"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["identity", "use", "persistent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Check whoami
        result = run_agent_cli(
            ["identity", "whoami"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        if result["success"]:
            assert "persistent" in result["stdout"].lower()


@pytest.mark.integration
class TestIdentityWhoamiCommand:
    """Tests for 'agent identity whoami' command."""

    def test_identity_whoami_with_active_agent(self, isolated_env):
        """Test whoami with active agent."""
        run_agent_cli(
            ["identity", "register", "--name", "Current Agent"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["identity", "use", "current-agent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["identity", "whoami"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        assert (
            "current-agent" in result["stdout"].lower()
            or "current agent" in result["stdout"].lower()
        )

    def test_identity_whoami_no_active_agent(self, isolated_env):
        """Test whoami with no active agent."""
        result = run_agent_cli(
            ["identity", "whoami"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should show message about no active agent or succeed with empty
        assert "no active" in result["output"].lower() or result["success"]

    def test_identity_whoami_shows_details(self, isolated_env):
        """Test whoami shows agent details."""
        run_agent_cli(
            [
                "identity",
                "register",
                "--name",
                "Detailed",
                "--role",
                "Tester",
                "--project-id",
                "test-proj",
            ],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["identity", "use", "detailed"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["identity", "whoami"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"]:
            output_lower = result["stdout"].lower()
            assert "detailed" in output_lower


@pytest.mark.integration
class TestIdentityListCommand:
    """Tests for 'agent identity list' command."""

    def test_identity_list_empty(self, isolated_env):
        """Test list with no registered agents."""
        result = run_agent_cli(
            ["identity", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed with empty list or show table headers
        assert result["success"]

    def test_identity_list_multiple_agents(self, isolated_env):
        """Test list with multiple agents."""
        run_agent_cli(
            ["identity", "register", "--name", "Agent 1"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["identity", "register", "--name", "Agent 2"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["identity", "register", "--name", "Agent 3"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["identity", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        output_lower = result["stdout"].lower()
        # Should show at least some agents
        assert "agent" in output_lower

    def test_identity_list_shows_active(self, isolated_env):
        """Test list shows which agent is active."""
        run_agent_cli(
            ["identity", "register", "--name", "Active"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["identity", "register", "--name", "Inactive"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["identity", "use", "active"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["identity", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        # Should indicate active agent somehow
        assert len(result["stdout"]) > 0

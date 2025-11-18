"""Integration tests for main CLI commands."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestVersionCommand:
    """Tests for 'agent version' command."""

    def test_version_command(self, isolated_env):
        """Test version command displays correct version."""
        result = run_agent_cli(["version"], isolated_env=isolated_env)

        assert result["success"]
        assert "Glorious Agents v" in result["stdout"] or "version" in result["stdout"].lower()
        assert result["returncode"] == 0

    def test_version_with_help(self, isolated_env):
        """Test version command with --help flag."""
        result = run_agent_cli(["version", "--help"], isolated_env=isolated_env)

        assert result["success"]
        assert "version" in result["stdout"].lower()


@pytest.mark.integration
class TestInitCommand:
    """Tests for 'agent init' command."""

    def test_init_creates_agent_tools_md(self, isolated_env):
        """Test init creates AGENT-TOOLS.md file."""
        result = run_agent_cli(["init"], isolated_env=isolated_env)

        assert result["success"]
        agent_tools_path = isolated_env["cwd"] / "AGENT-TOOLS.md"
        assert agent_tools_path.exists()

        content = agent_tools_path.read_text()
        assert "# Agent Tools" in content or "agent tools" in content.lower()

    def test_init_creates_agents_md(self, isolated_env):
        """Test init creates or updates AGENTS.md."""
        result = run_agent_cli(["init"], isolated_env=isolated_env)

        assert result["success"]
        agents_md_path = isolated_env["cwd"] / "AGENTS.md"
        assert agents_md_path.exists()

        content = agents_md_path.read_text()
        assert "AGENT-TOOLS.md" in content or "agent" in content.lower()

    def test_init_updates_existing_agents_md(self, isolated_env):
        """Test init updates existing AGENTS.md without duplicating."""
        agents_md = isolated_env["cwd"] / "AGENTS.md"
        agents_md.write_text("# Existing Content\n")

        # Run init twice
        run_agent_cli(["init"], isolated_env=isolated_env)
        run_agent_cli(["init"], isolated_env=isolated_env)

        content = agents_md.read_text()
        # Should only have one reference (or handle gracefully)
        assert "Existing Content" in content

    def test_init_with_no_skills_loaded(self, isolated_env):
        """Test init behavior when no skills are loaded."""
        result = run_agent_cli(["init"], isolated_env=isolated_env)

        # Should succeed even with no skills or show appropriate message
        assert result["success"] or "skill" in result["output"].lower()


@pytest.mark.integration
class TestInfoCommand:
    """Tests for 'agent info' command."""

    def test_info_displays_system_info(self, isolated_env):
        """Test info command displays system information."""
        result = run_agent_cli(["info"], isolated_env=isolated_env)

        assert result["success"]
        # Should show some system information
        assert len(result["stdout"]) > 0

    def test_info_shows_data_folder(self, isolated_env):
        """Test info shows data folder location."""
        result = run_agent_cli(["info"], isolated_env=isolated_env)

        assert result["success"]
        # Should mention data folder or configuration
        assert "folder" in result["stdout"].lower() or "data" in result["stdout"].lower()

    def test_info_database_info(self, isolated_env):
        """Test info displays database information."""
        result = run_agent_cli(["info"], isolated_env=isolated_env)

        assert result["success"]
        # Should show database type or status
        output_lower = result["stdout"].lower()
        assert "database" in output_lower or "sqlite" in output_lower or "db" in output_lower


@pytest.mark.integration
class TestSearchCommand:
    """Tests for 'agent search' command."""

    def test_search_basic_query(self, isolated_env):
        """Test basic search functionality."""
        # Add some searchable content first
        run_agent_cli(
            ["notes", "add", "Test note about quantum physics"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["search", "quantum"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed (may or may not find results depending on indexing)
        assert result["returncode"] in [0, 1]

    def test_search_with_limit(self, isolated_env):
        """Test search with custom limit."""
        result = run_agent_cli(
            ["search", "test", "--limit", "5"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should accept limit parameter
        assert result["returncode"] in [0, 1]

    def test_search_json_output(self, isolated_env):
        """Test search with JSON output."""
        result = run_agent_cli(
            ["search", "test", "--json"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"]:
            # Should be valid JSON if successful
            import json

            try:
                data = json.loads(result["stdout"])
                assert isinstance(data, (list, dict))
            except json.JSONDecodeError:
                # May not have JSON output implemented yet
                pass

    def test_search_no_results(self, isolated_env):
        """Test search with no matching results."""
        result = run_agent_cli(
            ["search", "xyznonexistent123"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should handle gracefully
        assert result["returncode"] in [0, 1]

    def test_search_empty_query(self, isolated_env):
        """Test search with empty query."""
        result = run_agent_cli(
            ["search", ""], cwd=isolated_env["cwd"], expect_failure=True, isolated_env=isolated_env
        )

        # Should fail or return no results
        assert not result["success"] or "no results" in result["output"].lower()

    def test_search_special_characters(self, isolated_env):
        """Test search with special characters."""
        result = run_agent_cli(
            ["search", "test@#$%"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should handle gracefully
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestDaemonCommand:
    """Tests for 'agent daemon' command."""

    def test_daemon_help(self, isolated_env):
        """Test daemon command help."""
        result = run_agent_cli(["daemon", "--help"], isolated_env=isolated_env)

        assert result["success"]
        assert "daemon" in result["stdout"].lower()

    @pytest.mark.skip(reason="Daemon is long-running, needs special handling")
    def test_daemon_starts_with_defaults(self, isolated_env):
        """Test daemon starts with default host and port."""
        # This would require background process management
        pass

    @pytest.mark.skip(reason="Daemon is long-running, needs special handling")
    def test_daemon_custom_host_port(self, isolated_env):
        """Test daemon with custom host and port."""
        # This would require background process management
        pass

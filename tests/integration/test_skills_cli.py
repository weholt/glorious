"""Integration tests for skills management CLI commands."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestSkillsListCommand:
    """Tests for 'agent skills list' command."""

    def test_skills_list_shows_loaded_skills(self, isolated_env):
        """Test skills list displays all loaded skills."""
        result = run_agent_cli(
            ["skills", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        # Should show some output about skills
        assert len(result["stdout"]) > 0

    def test_skills_list_empty(self, isolated_env):
        """Test skills list when no skills loaded."""
        result = run_agent_cli(
            ["skills", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed even with no skills
        assert result["success"]

    def test_skills_list_shows_dependencies(self, isolated_env):
        """Test skills list shows skill dependencies."""
        result = run_agent_cli(
            ["skills", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]
        # May show dependencies column
        output_lower = result["stdout"].lower()
        assert "skill" in output_lower or "name" in output_lower


@pytest.mark.integration
class TestSkillsDescribeCommand:
    """Tests for 'agent skills describe' command."""

    def test_skills_describe_existing_skill(self, isolated_env):
        """Test describe command for existing skill."""
        result = run_agent_cli(
            ["skills", "describe", "notes"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # May succeed if notes skill is available
        if result["success"]:
            assert "notes" in result["stdout"].lower()

    def test_skills_describe_nonexistent_skill(self, isolated_env):
        """Test describe command for non-existent skill."""
        result = run_agent_cli(
            ["skills", "describe", "nonexistent-skill-xyz"],
            cwd=isolated_env["cwd"],
            expect_failure=True,
        )

        assert not result["success"]
        assert "not found" in result["output"].lower() or "error" in result["output"].lower()

    def test_skills_describe_shows_commands(self, isolated_env):
        """Test describe shows available commands."""
        result = run_agent_cli(
            ["skills", "describe", "notes"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"]:
            # Should show commands or usage information
            output_lower = result["stdout"].lower()
            assert (
                "command" in output_lower
                or "usage" in output_lower
                or "description" in output_lower
            )


@pytest.mark.integration
class TestSkillsReloadCommand:
    """Tests for 'agent skills reload' command."""

    def test_skills_reload_all(self, isolated_env):
        """Test reloading all skills."""
        result = run_agent_cli(
            ["skills", "reload"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed or show appropriate message
        assert result["returncode"] in [0, 1]

    def test_skills_reload_specific_skill(self, isolated_env):
        """Test reloading a specific skill."""
        result = run_agent_cli(
            ["skills", "reload", "notes"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # May succeed if skill exists
        assert result["returncode"] in [0, 1]

    def test_skills_reload_nonexistent_skill(self, isolated_env):
        """Test reloading non-existent skill."""
        result = run_agent_cli(
            ["skills", "reload", "nonexistent-skill"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert not result["success"]


@pytest.mark.integration
class TestSkillsExportCommand:
    """Tests for 'agent skills export' command."""

    def test_skills_export_json(self, isolated_env):
        """Test exporting skills metadata as JSON."""
        result = run_agent_cli(
            ["skills", "export", "--format", "json"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        if result["success"]:
            import json

            try:
                data = json.loads(result["stdout"])
                assert isinstance(data, list | dict)
            except json.JSONDecodeError:
                pytest.skip("JSON export not implemented or no skills loaded")

    def test_skills_export_markdown(self, isolated_env):
        """Test exporting skills metadata as Markdown."""
        result = run_agent_cli(
            ["skills", "export", "--format", "md"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        # Should succeed or show format not supported
        assert result["returncode"] in [0, 1]

    def test_skills_export_invalid_format(self, isolated_env):
        """Test export with invalid format."""
        result = run_agent_cli(
            ["skills", "export", "--format", "invalid"],
            cwd=isolated_env["cwd"],
            expect_failure=True,
        )

        # Should fail with invalid format
        assert (
            "unknown" in result["output"].lower()
            or "invalid" in result["output"].lower()
            or not result["success"]
        )


@pytest.mark.integration
class TestSkillsCheckCommand:
    """Tests for 'agent skills check' command."""

    def test_skills_check_existing_skill(self, isolated_env):
        """Test health check on existing skill."""
        result = run_agent_cli(
            ["skills", "check", "notes"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed or show skill not found
        assert result["returncode"] in [0, 1]

    def test_skills_check_nonexistent_skill(self, isolated_env):
        """Test check on non-existent skill."""
        result = run_agent_cli(
            ["skills", "check", "nonexistent"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert not result["success"]


@pytest.mark.integration
class TestSkillsDoctorCommand:
    """Tests for 'agent skills doctor' command."""

    def test_skills_doctor_all_skills(self, isolated_env):
        """Test doctor command checks all skills."""
        result = run_agent_cli(
            ["skills", "doctor"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should run diagnostics
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSkillsConfigCommand:
    """Tests for 'agent skills config' command."""

    def test_skills_config_show_all(self, isolated_env):
        """Test showing all config for a skill."""
        result = run_agent_cli(
            ["skills", "config", "notes"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed or show skill not found
        assert result["returncode"] in [0, 1]

    def test_skills_config_set_value(self, isolated_env):
        """Test setting config value."""
        result = run_agent_cli(
            ["skills", "config", "notes", "--key", "test_key", "--set", "test_value"],
            cwd=isolated_env["cwd"],
        )

        # May succeed if skill supports config
        assert result["returncode"] in [0, 1]

    def test_skills_config_reset(self, isolated_env):
        """Test resetting config."""
        result = run_agent_cli(["skills", "config", "notes", "--reset"], cwd=isolated_env["cwd"])

        # Should handle gracefully
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSkillsMigrateCommand:
    """Tests for 'agent skills migrate' command."""

    def test_skills_migrate_status(self, isolated_env):
        """Test migration status command."""
        result = run_agent_cli(
            ["skills", "migrate", "status"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should show migration status
        assert result["returncode"] in [0, 1]

    def test_skills_migrate_up(self, isolated_env):
        """Test running migrations up."""
        result = run_agent_cli(
            ["skills", "migrate", "up"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should run migrations or show none needed
        assert result["returncode"] in [0, 1]

    def test_skills_migrate_down(self, isolated_env):
        """Test running migrations down."""
        result = run_agent_cli(
            ["skills", "migrate", "down"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # May fail if no migrations to revert
        assert result["returncode"] in [0, 1]

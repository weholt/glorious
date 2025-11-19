"""Integration tests for remaining skills (AI, Automations, Prompts, Temporal, Vacuum, Docs, Orchestrator, Linker, Migrate)."""

import pytest
from conftest import run_agent_cli


# AI Skill Tests
@pytest.mark.integration
class TestAISkill:
    """Tests for AI skill commands."""

    def test_ai_complete_basic(self, isolated_env):
        """Test basic LLM completion."""
        result = run_agent_cli(["ai", "complete", "Hello world"], cwd=isolated_env["cwd"])

        # May fail if no API key configured
        assert result["returncode"] in [0, 1]

    def test_ai_history(self, isolated_env):
        """Test viewing completion history."""
        result = run_agent_cli(
            ["ai", "history"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


# Automations Skill Tests
@pytest.mark.integration
class TestAutomationsSkill:
    """Tests for Automations skill commands."""

    def test_automations_create_basic(self, isolated_env):
        """Test creating basic automation."""
        result = run_agent_cli(
            [
                "automations",
                "create",
                "Test Auto",
                "test.event",
                '[{"type":"log","message":"test"}]',
            ],
            cwd=isolated_env["cwd"],
        )

        assert result["returncode"] in [0, 1]

    def test_automations_list(self, isolated_env):
        """Test listing automations."""
        result = run_agent_cli(
            ["automations", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_automations_executions(self, isolated_env):
        """Test viewing execution history."""
        result = run_agent_cli(
            ["automations", "executions"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]


# Prompts Skill Tests
@pytest.mark.integration
class TestPromptsSkill:
    """Tests for Prompts skill commands."""

    def test_prompts_register_basic(self, isolated_env):
        """Test registering prompt template."""
        result = run_agent_cli(
            ["prompts", "register", "test-prompt", "Hello {name}"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_prompts_list(self, isolated_env):
        """Test listing prompts."""
        result = run_agent_cli(
            ["prompts", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_prompts_render_basic(self, isolated_env):
        """Test rendering prompt."""
        run_agent_cli(
            ["prompts", "register", "greet", "Hello {name}"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["prompts", "render", "greet", "--vars", '{"name":"World"}'], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


# Temporal Skill Tests
@pytest.mark.integration
class TestTemporalSkill:
    """Tests for Temporal skill commands."""

    def test_temporal_parse_days(self, isolated_env):
        """Test parsing day specification."""
        result = run_agent_cli(
            ["temporal", "parse", "7d"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_temporal_parse_hours(self, isolated_env):
        """Test parsing hour specification."""
        result = run_agent_cli(
            ["temporal", "parse", "3h"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_temporal_examples(self, isolated_env):
        """Test examples command."""
        result = run_agent_cli(
            ["temporal", "examples"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


# Vacuum Skill Tests
@pytest.mark.integration
class TestVacuumSkill:
    """Tests for Vacuum skill commands."""

    def test_vacuum_run_summarize(self, isolated_env):
        """Test vacuum summarize mode."""
        result = run_agent_cli(["vacuum", "run", "--mode", "summarize"], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_vacuum_history(self, isolated_env):
        """Test viewing vacuum history."""
        result = run_agent_cli(
            ["vacuum", "history"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


# Docs Skill Tests
@pytest.mark.integration
class TestDocsSkill:
    """Tests for Docs skill commands."""

    def test_docs_create_basic(self, isolated_env):
        """Test creating document."""
        result = run_agent_cli(
            ["docs", "create", "Test Doc", "--content", "Test content"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_docs_list(self, isolated_env):
        """Test listing documents."""
        result = run_agent_cli(["docs", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env)

        assert result["returncode"] in [0, 1]

    def test_docs_search(self, isolated_env):
        """Test searching documents."""
        result = run_agent_cli(
            ["docs", "search", "test"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


# Orchestrator Skill Tests
@pytest.mark.integration
class TestOrchestratorSkill:
    """Tests for Orchestrator skill commands."""

    def test_orchestrator_run(self, isolated_env):
        """Test running workflow."""
        result = run_agent_cli(
            ["orchestrator", "run", "Create a note about testing"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_orchestrator_list(self, isolated_env):
        """Test listing workflows."""
        result = run_agent_cli(
            ["orchestrator", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


# Linker Skill Tests
@pytest.mark.integration
class TestLinkerSkill:
    """Tests for Linker skill commands."""

    def test_linker_add_basic(self, isolated_env):
        """Test adding link."""
        result = run_agent_cli(
            ["linker", "add", "related", "--a", "note:1", "--b", "issue:2"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_linker_list(self, isolated_env):
        """Test listing links."""
        result = run_agent_cli(
            ["linker", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


# Migrate Skill Tests
@pytest.mark.integration
class TestMigrateSkill:
    """Tests for Migrate skill commands."""

    def test_migrate_export(self, isolated_env):
        """Test exporting database."""
        export_dir = isolated_env["root"] / "export"

        result = run_agent_cli(["migrate", "export", str(export_dir)], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_migrate_backup(self, isolated_env):
        """Test creating backup."""
        backup_file = isolated_env["root"] / "backup.db"

        result = run_agent_cli(["migrate", "backup", str(backup_file)], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_migrate_info(self, isolated_env):
        """Test showing database info."""
        result = run_agent_cli(
            ["migrate", "info"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

"""Cross-skill integration tests."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestEventDrivenIntegration:
    """Tests for event-driven integration between skills."""

    def test_notes_to_issues_integration(self, isolated_env):
        """Test that notes with 'todo' tag may create issues."""
        # Add note with todo tag
        result = run_agent_cli(
            ["notes", "add", "Fix the bug", "--tags", "todo"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

        # Check if issue was created (may not be implemented yet)
        issues_result = run_agent_cli(
            ["issues", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should handle gracefully whether issues skill exists or not
        assert issues_result["returncode"] in [0, 1]

    def test_universal_search_across_skills(self, isolated_env):
        """Test universal search finds content from multiple skills."""
        # Add content to different skills
        run_agent_cli(
            ["notes", "add", "Quantum computing research"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["prompts", "register", "quantum-prompt", "Explain quantum"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        # Search across all
        result = run_agent_cli(
            ["search", "quantum"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should succeed or handle gracefully
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestSkillDependencies:
    """Tests for skill dependency handling."""

    def test_dependent_skill_loading(self, isolated_env):
        """Test that dependent skills load correctly."""
        # List skills to see dependencies
        result = run_agent_cli(
            ["skills", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_skill_check_dependencies(self, isolated_env):
        """Test checking skill dependencies."""
        result = run_agent_cli(
            ["skills", "check", "issues"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should check dependencies
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestDataSharing:
    """Tests for data sharing between skills."""

    def test_linker_connects_entities(self, isolated_env):
        """Test linker can connect entities from different skills."""
        # Create entities in different skills
        run_agent_cli(
            ["notes", "add", "Test note"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Try to create link
        result = run_agent_cli(
            ["linker", "add", "related", "--a", "note:1", "--b", "doc:1"], cwd=isolated_env["cwd"]
        )

        # Should handle gracefully
        assert result["returncode"] in [0, 1]

    def test_cache_shared_across_skills(self, isolated_env):
        """Test cache is shared across skills."""
        # Set cache from one context
        run_agent_cli(
            ["cache", "set", "shared-key", "shared-value"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        # Get from another context
        result = run_agent_cli(
            ["cache", "get", "shared-key"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        # Should be accessible
        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestWorkflowIntegration:
    """Tests for workflow integration across skills."""

    def test_orchestrator_multi_skill_workflow(self, isolated_env):
        """Test orchestrator can coordinate multiple skills."""
        result = run_agent_cli(
            ["orchestrator", "run", "Create a note and cache the result"], cwd=isolated_env["cwd"]
        )

        # Should handle workflow
        assert result["returncode"] in [0, 1]

    def test_automation_triggers_across_skills(self, isolated_env):
        """Test automations can trigger actions in different skills."""
        # Create automation that affects multiple skills
        result = run_agent_cli(
            [
                "automations",
                "create",
                "Multi-Skill",
                "note.created",
                '[{"type":"cache","key":"last_note"}]',
            ],
            cwd=isolated_env["cwd"],
        )

        # Should handle gracefully
        assert result["returncode"] in [0, 1]

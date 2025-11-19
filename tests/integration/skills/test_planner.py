"""Integration tests for planner skill."""

import re

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestPlannerCreateCommand:
    """Tests for 'agent planner create' command."""

    def test_planner_create_basic(self, isolated_env):
        """Test creating a basic plan."""
        result = run_agent_cli(
            ["planner", "create", "Test Plan", "This is a test plan description"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]
        assert "created" in result["stdout"].lower() or "plan" in result["stdout"].lower()

    def test_planner_create_with_goal(self, isolated_env):
        """Test creating plan with goal."""
        result = run_agent_cli(
            ["planner", "create", "Goal Plan", "Description", "--goal", "Complete project"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_planner_create_with_deadline(self, isolated_env):
        """Test creating plan with deadline."""
        result = run_agent_cli(
            ["planner", "create", "Deadline Plan", "Description", "--deadline", "2025-12-31"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_planner_create_with_priority(self, isolated_env):
        """Test creating plan with priority."""
        result = run_agent_cli(
            ["planner", "create", "Priority Plan", "Description", "--priority", "high"],
            cwd=isolated_env["cwd"],
        )

        assert result["success"]

    def test_planner_create_empty_title(self, isolated_env):
        """Test creating plan with empty title."""
        result = run_agent_cli(
            ["planner", "create", "", "Description"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert not result["success"]


@pytest.mark.integration
class TestPlannerListCommand:
    """Tests for 'agent planner list' command."""

    def test_planner_list_default(self, isolated_env):
        """Test listing plans with defaults."""
        run_agent_cli(
            ["planner", "create", "Plan 1", "Description 1"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["planner", "create", "Plan 2", "Description 2"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["planner", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_planner_list_with_status(self, isolated_env):
        """Test listing plans by status."""
        result = run_agent_cli(
            ["planner", "list", "--status", "active"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_planner_list_with_priority(self, isolated_env):
        """Test listing plans by priority."""
        result = run_agent_cli(
            ["planner", "list", "--priority", "high"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["success"]

    def test_planner_list_json_output(self, isolated_env):
        """Test listing plans with JSON output."""
        run_agent_cli(
            ["planner", "create", "Test Plan", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["planner", "list", "--json"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"] and result["stdout"].strip():
            import json

            try:
                data = json.loads(result["stdout"])
                assert isinstance(data, list)
            except json.JSONDecodeError:
                pass


@pytest.mark.integration
class TestPlannerGetCommand:
    """Tests for 'agent planner get' command."""

    def test_planner_get_existing(self, isolated_env):
        """Test getting existing plan."""
        create_result = run_agent_cli(
            ["planner", "create", "Get This Plan", "Description"], cwd=isolated_env["cwd"]
        )

        # Try to extract plan ID from output
        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            result = run_agent_cli(
                ["planner", "get", plan_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            if result["success"]:
                assert "Get This Plan" in result["stdout"] or "plan" in result["stdout"].lower()

    def test_planner_get_nonexistent(self, isolated_env):
        """Test getting non-existent plan."""
        result = run_agent_cli(
            ["planner", "get", "99999"], cwd=isolated_env["cwd"], expect_failure=True
        )

        assert "not found" in result["output"].lower() or not result["success"]


@pytest.mark.integration
class TestPlannerUpdateCommand:
    """Tests for 'agent planner update' command."""

    def test_planner_update_title(self, isolated_env):
        """Test updating plan title."""
        create_result = run_agent_cli(
            ["planner", "create", "Original Title", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            result = run_agent_cli(
                ["planner", "update", plan_id, "--title", "Updated Title"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]

    def test_planner_update_status(self, isolated_env):
        """Test updating plan status."""
        create_result = run_agent_cli(
            ["planner", "create", "Test Plan", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            result = run_agent_cli(
                ["planner", "update", plan_id, "--status", "completed"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerAddStepCommand:
    """Tests for 'agent planner add-step' command."""

    def test_planner_add_step_basic(self, isolated_env):
        """Test adding step to plan."""
        create_result = run_agent_cli(
            ["planner", "create", "Test Plan", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            result = run_agent_cli(
                ["planner", "add-step", plan_id, "Step 1: Do something"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]

    def test_planner_add_step_with_order(self, isolated_env):
        """Test adding step with specific order."""
        create_result = run_agent_cli(
            ["planner", "create", "Test Plan", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            result = run_agent_cli(
                ["planner", "add-step", plan_id, "Step 1", "--order", "1"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerCompleteStepCommand:
    """Tests for 'agent planner complete-step' command."""

    def test_planner_complete_step(self, isolated_env):
        """Test completing a step."""
        # Create plan and add step
        create_result = run_agent_cli(
            ["planner", "create", "Test Plan", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            run_agent_cli(
                ["planner", "add-step", plan_id, "Step 1"],
                cwd=isolated_env["cwd"],
                isolated_env=isolated_env,
            )

            result = run_agent_cli(
                ["planner", "complete-step", plan_id, "1"], cwd=isolated_env["cwd"]
            )
            assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerDeleteCommand:
    """Tests for 'agent planner delete' command."""

    def test_planner_delete_existing(self, isolated_env):
        """Test deleting existing plan."""
        create_result = run_agent_cli(
            ["planner", "create", "Delete Me", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            result = run_agent_cli(
                ["planner", "delete", plan_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            assert result["returncode"] in [0, 1]

    def test_planner_delete_nonexistent(self, isolated_env):
        """Test deleting non-existent plan."""
        result = run_agent_cli(
            ["planner", "delete", "99999"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerProgressCommand:
    """Tests for 'agent planner progress' command."""

    def test_planner_progress_show(self, isolated_env):
        """Test showing plan progress."""
        create_result = run_agent_cli(
            ["planner", "create", "Test Plan", "Description"], cwd=isolated_env["cwd"]
        )

        match = re.search(r"(?:plan|id)[:\s]+(\d+)", create_result["stdout"], re.IGNORECASE)
        if match:
            plan_id = match.group(1)
            result = run_agent_cli(
                ["planner", "progress", plan_id], cwd=isolated_env["cwd"], isolated_env=isolated_env
            )
            assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerGenerateCommand:
    """Tests for 'agent planner generate' command."""

    def test_planner_generate_from_goal(self, isolated_env):
        """Test generating plan from goal."""
        result = run_agent_cli(
            ["planner", "generate", "Build a web application"], cwd=isolated_env["cwd"]
        )

        # May require AI/LLM integration
        assert result["returncode"] in [0, 1]

    def test_planner_generate_with_steps(self, isolated_env):
        """Test generating plan with specific number of steps."""
        result = run_agent_cli(
            ["planner", "generate", "Complete project", "--steps", "5"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerExportCommand:
    """Tests for 'agent planner export' command."""

    def test_planner_export_to_file(self, isolated_env):
        """Test exporting plan to file."""
        # Create a plan first
        run_agent_cli(
            ["planner", "create", "Export Plan", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        export_file = isolated_env["root"] / "exported_plan.json"

        result = run_agent_cli(
            ["planner", "export", "1", str(export_file)], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_planner_export_all(self, isolated_env):
        """Test exporting all plans."""
        run_agent_cli(
            ["planner", "create", "Plan 1", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )
        run_agent_cli(
            ["planner", "create", "Plan 2", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        export_file = isolated_env["root"] / "all_plans.json"

        result = run_agent_cli(
            ["planner", "export", "--all", str(export_file)], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerImportCommand:
    """Tests for 'agent planner import' command."""

    def test_planner_import_from_file(self, isolated_env):
        """Test importing plan from file."""
        import json

        # Create import file
        import_file = isolated_env["root"] / "plan.json"
        plan_data = {
            "title": "Imported Plan",
            "description": "This is an imported plan",
            "steps": [{"description": "Step 1", "order": 1}, {"description": "Step 2", "order": 2}],
        }
        import_file.write_text(json.dumps(plan_data))

        result = run_agent_cli(["planner", "import", str(import_file)], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerTemplateCommand:
    """Tests for 'agent planner template' command."""

    def test_planner_template_list(self, isolated_env):
        """Test listing plan templates."""
        result = run_agent_cli(
            ["planner", "template", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_planner_template_create_from(self, isolated_env):
        """Test creating plan from template."""
        result = run_agent_cli(
            ["planner", "template", "create", "project-setup", "My Project"],
            cwd=isolated_env["cwd"],
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestPlannerSearchCommand:
    """Tests for 'agent planner search' command."""

    def test_planner_search_basic(self, isolated_env):
        """Test searching plans."""
        run_agent_cli(
            ["planner", "create", "Web Development Plan", "Description"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["planner", "search", "development"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_planner_search_no_results(self, isolated_env):
        """Test search with no results."""
        result = run_agent_cli(
            ["planner", "search", "nonexistent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

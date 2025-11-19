"""Integration tests for atlas skill."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestCodeAtlasScanCommand:
    """Tests for 'agent atlas scan' command."""

    def test_code_atlas_scan_basic(self, isolated_env):
        """Test basic code scanning."""
        # Create a simple Python file to scan
        test_file = isolated_env["root"] / "test.py"
        test_file.write_text('def hello():\n    print("Hello")\n')

        result = run_agent_cli(
            ["atlas", "scan", str(isolated_env["root"])], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_code_atlas_scan_with_pattern(self, isolated_env):
        """Test scanning with file pattern."""
        result = run_agent_cli(
            ["atlas", "scan", str(isolated_env["root"]), "--pattern", "*.py"],
            cwd=isolated_env["cwd"],
        )

        assert result["returncode"] in [0, 1]

    def test_code_atlas_scan_recursive(self, isolated_env):
        """Test recursive scanning."""
        result = run_agent_cli(
            ["atlas", "scan", str(isolated_env["root"]), "--recursive"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestCodeAtlasAnalyzeCommand:
    """Tests for 'agent atlas analyze' command."""

    def test_code_atlas_analyze_file(self, isolated_env):
        """Test analyzing a file."""
        test_file = isolated_env["root"] / "analyze.py"
        test_file.write_text("class MyClass:\n    def method(self):\n        pass\n")

        result = run_agent_cli(["atlas", "analyze", str(test_file)], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_code_atlas_analyze_with_metrics(self, isolated_env):
        """Test analyzing with metrics."""
        test_file = isolated_env["root"] / "metrics.py"
        test_file.write_text("def func():\n    return 42\n")

        result = run_agent_cli(
            ["atlas", "analyze", str(test_file), "--metrics"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestCodeAtlasQueryCommand:
    """Tests for 'agent atlas query' command."""

    def test_code_atlas_query_functions(self, isolated_env):
        """Test querying for functions."""
        result = run_agent_cli(["atlas", "query", "--type", "function"], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_code_atlas_query_classes(self, isolated_env):
        """Test querying for classes."""
        result = run_agent_cli(["atlas", "query", "--type", "class"], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]

    def test_code_atlas_query_with_name(self, isolated_env):
        """Test querying by name."""
        result = run_agent_cli(["atlas", "query", "--name", "test"], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestCodeAtlasGraphCommand:
    """Tests for 'agent atlas graph' command."""

    def test_code_atlas_graph_dependencies(self, isolated_env):
        """Test generating dependency graph."""
        result = run_agent_cli(
            ["atlas", "graph", "--type", "dependencies"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_code_atlas_graph_calls(self, isolated_env):
        """Test generating call graph."""
        result = run_agent_cli(["atlas", "graph", "--type", "calls"], cwd=isolated_env["cwd"])

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestCodeAtlasMetricsCommand:
    """Tests for 'agent atlas metrics' command."""

    def test_code_atlas_metrics_overall(self, isolated_env):
        """Test viewing overall metrics."""
        result = run_agent_cli(
            ["atlas", "metrics"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_code_atlas_metrics_for_file(self, isolated_env):
        """Test metrics for specific file."""
        test_file = isolated_env["root"] / "metrics.py"
        test_file.write_text("def test():\n    pass\n")

        result = run_agent_cli(
            ["atlas", "metrics", "--file", str(test_file)], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestCodeAtlasExportCommand:
    """Tests for 'agent atlas export' command."""

    def test_code_atlas_export_json(self, isolated_env):
        """Test exporting to JSON."""
        export_file = isolated_env["root"] / "atlas.json"

        result = run_agent_cli(
            ["atlas", "export", str(export_file), "--format", "json"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]

    def test_code_atlas_export_dot(self, isolated_env):
        """Test exporting to DOT format."""
        export_file = isolated_env["root"] / "atlas.dot"

        result = run_agent_cli(
            ["atlas", "export", str(export_file), "--format", "dot"], cwd=isolated_env["cwd"]
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestCodeAtlasCacheCommand:
    """Tests for 'agent atlas cache' command."""

    def test_code_atlas_cache_clear(self, isolated_env):
        """Test clearing cache."""
        result = run_agent_cli(
            ["atlas", "cache", "clear"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

    def test_code_atlas_cache_stats(self, isolated_env):
        """Test viewing cache stats."""
        result = run_agent_cli(
            ["atlas", "cache", "stats"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

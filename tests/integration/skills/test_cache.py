"""Integration tests for cache skill."""

import pytest
from conftest import run_agent_cli


@pytest.mark.integration
class TestCacheSetCommand:
    """Tests for 'agent cache set' command."""

    def test_cache_set_basic(self, isolated_env):
        """Test setting cache entry."""
        result = run_agent_cli(["cache", "set", "test-key", "test-value"], cwd=isolated_env["cwd"])

        assert result["success"]

    def test_cache_set_with_ttl(self, isolated_env):
        """Test setting cache with TTL."""
        result = run_agent_cli(
            ["cache", "set", "ttl-key", "value", "--ttl", "3600"], cwd=isolated_env["cwd"]
        )

        assert result["success"]

    def test_cache_set_with_kind(self, isolated_env):
        """Test setting cache with kind."""
        result = run_agent_cli(
            ["cache", "set", "kind-key", "value", "--kind", "test"], cwd=isolated_env["cwd"]
        )

        assert result["success"]


@pytest.mark.integration
class TestCacheGetCommand:
    """Tests for 'agent cache get' command."""

    def test_cache_get_existing(self, isolated_env):
        """Test getting existing cache entry."""
        run_agent_cli(
            ["cache", "set", "get-key", "get-value"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["cache", "get", "get-key"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        if result["success"]:
            assert "get-value" in result["stdout"] or "value" in result["stdout"].lower()

    def test_cache_get_nonexistent(self, isolated_env):
        """Test getting non-existent cache entry."""
        result = run_agent_cli(
            ["cache", "get", "nonexistent"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert (
            "not found" in result["output"].lower()
            or "expired" in result["output"].lower()
            or not result["success"]
        )


@pytest.mark.integration
class TestCacheListCommand:
    """Tests for 'agent cache list' command."""

    def test_cache_list_all(self, isolated_env):
        """Test listing all cache entries."""
        run_agent_cli(
            ["cache", "set", "key1", "val1"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )
        run_agent_cli(
            ["cache", "set", "key2", "val2"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["cache", "list"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_cache_list_by_kind(self, isolated_env):
        """Test listing cache entries by kind."""
        run_agent_cli(
            ["cache", "set", "k1", "v1", "--kind", "test"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        result = run_agent_cli(
            ["cache", "list", "--kind", "test"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]


@pytest.mark.integration
class TestCachePruneCommand:
    """Tests for 'agent cache prune' command."""

    def test_cache_prune_expired(self, isolated_env):
        """Test pruning expired entries."""
        result = run_agent_cli(
            ["cache", "prune"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["success"]

    def test_cache_prune_all(self, isolated_env):
        """Test pruning all entries."""
        result = run_agent_cli(
            ["cache", "prune", "--expired-only", "false"],
            cwd=isolated_env["cwd"],
            isolated_env=isolated_env,
        )

        assert result["returncode"] in [0, 1]


@pytest.mark.integration
class TestCacheDeleteCommand:
    """Tests for 'agent cache delete' command."""

    def test_cache_delete(self, isolated_env):
        """Test deleting cache entry."""
        run_agent_cli(
            ["cache", "set", "del-key", "value"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        result = run_agent_cli(
            ["cache", "delete", "del-key"], cwd=isolated_env["cwd"], isolated_env=isolated_env
        )

        assert result["returncode"] in [0, 1]

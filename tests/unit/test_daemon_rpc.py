"""Unit tests for daemon RPC endpoints."""

import asyncio
import inspect
import sqlite3
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from glorious_agents.core.context import EventBus, SkillContext
from glorious_agents.core.daemon_rpc import (
    RPCRequest,
    call_skill_method,
    clear_cache,
    daemon_app,
    delete_cache,
    get_cache,
    health_check,
    list_skills,
    list_topics,
    publish_event,
    set_cache,
    verify_api_key,
)


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(daemon_app)


@pytest.fixture
def mock_registry() -> MagicMock:
    """Create a mock registry."""
    registry = MagicMock()
    return registry


@pytest.fixture
def mock_ctx(skill_context: SkillContext) -> SkillContext:
    """Create a mock context."""
    return skill_context


@pytest.fixture(autouse=True)
def reset_config_before_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset config before each test to control DAEMON_API_KEY."""
    from glorious_agents.config import reset_config

    reset_config()


# ============================================================================
# Authentication Tests (verify_api_key)
# ============================================================================


class TestAuthentication:
    """Test authentication mechanism."""

    def test_no_api_key_when_daemon_api_key_is_none(self, client: TestClient) -> None:
        """Test that requests are allowed when DAEMON_API_KEY is None via health endpoint."""
        # Health endpoint does not require auth
        response = client.get("/health")
        assert response.status_code == 200

    def test_api_key_required_when_daemon_api_key_is_set(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that 401 is returned when API key is required but missing."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "secret-key-123")

        from glorious_agents.config import reset_config

        reset_config()

        # Try to access a protected endpoint without API key
        response = client.get("/cache")
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]

    def test_invalid_api_key_returns_403(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that 403 is returned for invalid API key."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "correct-secret-key")

        from glorious_agents.config import reset_config

        reset_config()

        # Try with wrong API key
        response = client.get("/cache", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    def test_valid_api_key_allows_access(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that valid API key allows access."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "correct-secret-key")

        from glorious_agents.config import reset_config

        reset_config()

        # Try with correct API key - will get 200 but cache might be empty, that's ok
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_cache = MagicMock()
            mock_cache._cache = {}

            mock_ctx = MagicMock()
            mock_ctx._cache = mock_cache
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/cache", headers={"X-API-Key": "correct-secret-key"})
            assert response.status_code == 200


# ============================================================================
# Health Check Endpoint Tests
# ============================================================================


class TestHealthCheck:
    """Test /health endpoint."""

    def test_health_check_success(self, client: TestClient) -> None:
        """Test that health check endpoint returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "glorious-agents-daemon"

    def test_health_check_no_auth_required(self, client: TestClient) -> None:
        """Test that health check does not require authentication."""
        # Health check should work without API key even if required
        response = client.get("/health")
        assert response.status_code == 200


# ============================================================================
# Skills List Endpoint Tests
# ============================================================================


class TestListSkills:
    """Test /skills endpoint."""

    def test_list_skills_empty(self, client: TestClient) -> None:
        """Test listing skills when no skills are loaded."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.list_all.return_value = []
            mock_get_registry.return_value = mock_registry

            response = client.get("/skills")

            assert response.status_code == 200
            data = response.json()
            assert data == []

    def test_list_skills_with_skills(self, client: TestClient) -> None:
        """Test listing multiple skills."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            mock_skill1 = MagicMock()
            mock_skill1.name = "notes"
            mock_skill1.version = "1.0.0"
            mock_skill1.description = "Notes management"
            mock_skill1.origin = "builtin"
            mock_skill1.requires = []

            mock_skill2 = MagicMock()
            mock_skill2.name = "cache"
            mock_skill2.version = "1.1.0"
            mock_skill2.description = "Cache operations"
            mock_skill2.origin = "builtin"
            mock_skill2.requires = ["storage"]

            mock_registry = MagicMock()
            mock_registry.list_all.return_value = [mock_skill1, mock_skill2]
            mock_get_registry.return_value = mock_registry

            response = client.get("/skills")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "notes"
            assert data[0]["version"] == "1.0.0"
            assert data[1]["name"] == "cache"
            assert data[1]["requires"] == ["storage"]

    def test_list_skills_returns_correct_fields(self, client: TestClient) -> None:
        """Test that list skills returns all expected fields."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            mock_skill = MagicMock()
            mock_skill.name = "test-skill"
            mock_skill.version = "2.0.0"
            mock_skill.description = "Test skill"
            mock_skill.origin = "external"
            mock_skill.requires = ["dep1", "dep2"]

            mock_registry = MagicMock()
            mock_registry.list_all.return_value = [mock_skill]
            mock_get_registry.return_value = mock_registry

            response = client.get("/skills")

            assert response.status_code == 200
            data = response.json()
            skill = data[0]
            assert "name" in skill
            assert "version" in skill
            assert "description" in skill
            assert "origin" in skill
            assert "requires" in skill


# ============================================================================
# RPC Method Call Endpoint Tests
# ============================================================================


class TestCallSkillMethod:
    """Test /rpc/{skill}/{method} endpoint."""

    def test_rpc_call_sync_function_success(self, client: TestClient) -> None:
        """Test calling a synchronous function via RPC."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup mock manifest
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test_skill:main"

                # Setup mock registry
                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                # Setup mock module
                mock_module = MagicMock()

                def test_func(x: int, y: int) -> int:
                    return x + y

                mock_module.add = test_func
                mock_import.return_value = mock_module

                response = client.post(
                    "/rpc/test_skill/add",
                    json={"params": {"x": 5, "y": 3}},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["skill"] == "test_skill"
                assert data["method"] == "add"
                assert data["result"] == 8

    @pytest.mark.asyncio
    async def test_rpc_call_async_function_success(self, client: TestClient) -> None:
        """Test calling an asynchronous function via RPC."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup mock manifest
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test_skill:main"

                # Setup mock registry
                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                # Setup mock module with async function
                mock_module = MagicMock()

                async def async_func(x: int) -> int:
                    return x * 2

                mock_module.multiply = async_func
                mock_import.return_value = mock_module

                response = client.post(
                    "/rpc/test_skill/multiply",
                    json={"params": {"x": 5}},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["result"] == 10

    def test_rpc_skill_not_found(self, client: TestClient) -> None:
        """Test RPC call when skill is not found."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.get_manifest.return_value = None
            mock_get_registry.return_value = mock_registry

            response = client.post(
                "/rpc/nonexistent/method",
                json={"params": {}},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_rpc_method_not_found(self, client: TestClient) -> None:
        """Test RPC call when method is not found in skill."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup mock manifest
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test_skill:main"

                # Setup mock registry
                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                # Setup mock module without the method
                mock_module = MagicMock(spec=[])
                mock_import.return_value = mock_module

                response = client.post(
                    "/rpc/test_skill/nonexistent_method",
                    json={"params": {}},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_rpc_method_not_callable(self, client: TestClient) -> None:
        """Test RPC call when method is not callable."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup mock manifest
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test_skill:main"

                # Setup mock registry
                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                # Setup mock module with non-callable attribute
                mock_module = MagicMock()
                mock_module.not_callable = "just a string"
                mock_import.return_value = mock_module

                response = client.post(
                    "/rpc/test_skill/not_callable",
                    json={"params": {}},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 400
                assert "not callable" in response.json()["detail"]

    def test_rpc_invalid_parameters(self, client: TestClient) -> None:
        """Test RPC call with invalid parameters."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup mock manifest
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test_skill:main"

                # Setup mock registry
                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                # Setup mock module
                mock_module = MagicMock()

                def test_func(required_param: int) -> int:
                    return required_param * 2

                mock_module.test = test_func
                mock_import.return_value = mock_module

                response = client.post(
                    "/rpc/test_skill/test",
                    json={"params": {"wrong_param": 5}},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 400
                assert "Invalid parameters" in response.json()["detail"]

    def test_rpc_module_import_error(self, client: TestClient) -> None:
        """Test RPC call when skill module cannot be imported."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup mock manifest
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "nonexistent_skill:main"

                # Setup mock registry
                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                # Make import fail
                mock_import.side_effect = ImportError("Module not found")

                response = client.post(
                    "/rpc/test_skill/method",
                    json={"params": {}},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 500
                assert "Failed to load skill module" in response.json()["detail"]

    def test_rpc_requires_authentication(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that RPC endpoint requires authentication when API key is set."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "required-key")

        from glorious_agents.config import reset_config

        reset_config()

        response = client.post(
            "/rpc/test_skill/method",
            json={"params": {}},
        )

        assert response.status_code == 401

    def test_rpc_with_no_params(self, client: TestClient) -> None:
        """Test RPC call with default empty params."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup mock manifest
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test_skill:main"

                # Setup mock registry
                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                # Setup mock module
                mock_module = MagicMock()

                def test_func() -> str:
                    return "no params needed"

                mock_module.test = test_func
                mock_import.return_value = mock_module

                response = client.post(
                    "/rpc/test_skill/test",
                    json={},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["result"] == "no params needed"


# ============================================================================
# Event Publishing Endpoint Tests
# ============================================================================


class TestPublishEvent:
    """Test /events/{topic} endpoint."""

    def test_publish_event_success(self, client: TestClient) -> None:
        """Test successfully publishing an event."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            event_data = {"key": "value", "count": 42}

            response = client.post(
                "/events/test_topic",
                json=event_data,
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "published"
            assert data["topic"] == "test_topic"

            # Verify context.publish was called
            mock_ctx.publish.assert_called_once_with("test_topic", event_data)

    def test_publish_event_empty_data(self, client: TestClient) -> None:
        """Test publishing an event with empty data."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            response = client.post(
                "/events/test_topic",
                json={},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 200
            mock_ctx.publish.assert_called_once_with("test_topic", {})

    def test_publish_event_error_handling(self, client: TestClient) -> None:
        """Test error handling when event publishing fails."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.publish.side_effect = RuntimeError("Publish failed")
            mock_get_ctx.return_value = mock_ctx

            response = client.post(
                "/events/test_topic",
                json={"data": "test"},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 500
            assert "Failed to publish event" in response.json()["detail"]

    def test_publish_event_requires_authentication(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that publishing events requires authentication when API key is set."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "required-key")

        from glorious_agents.config import reset_config

        reset_config()

        response = client.post(
            "/events/test_topic",
            json={"data": "test"},
        )

        assert response.status_code == 401

    def test_publish_event_complex_data(self, client: TestClient) -> None:
        """Test publishing event with complex nested data."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            complex_data = {
                "nested": {
                    "level1": {
                        "level2": [1, 2, 3],
                    }
                },
                "array": [{"id": 1}, {"id": 2}],
            }

            response = client.post(
                "/events/complex_topic",
                json=complex_data,
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 200
            mock_ctx.publish.assert_called_once_with("complex_topic", complex_data)


# ============================================================================
# Event Topics Listing Endpoint Tests
# ============================================================================


class TestListTopics:
    """Test /events/topics endpoint."""

    def test_list_topics_empty(self, client: TestClient) -> None:
        """Test listing topics when no subscribers exist."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_event_bus = MagicMock()
            mock_event_bus._subscribers = {}

            mock_ctx = MagicMock()
            mock_ctx._event_bus = mock_event_bus
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/events/topics")

            assert response.status_code == 200
            data = response.json()
            assert data["topics"] == []

    def test_list_topics_with_subscribers(self, client: TestClient) -> None:
        """Test listing multiple topics with subscribers."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_event_bus = MagicMock()
            mock_event_bus._subscribers = {
                "topic1": [MagicMock(), MagicMock()],
                "topic2": [MagicMock()],
                "topic3": [MagicMock(), MagicMock(), MagicMock()],
            }

            mock_ctx = MagicMock()
            mock_ctx._event_bus = mock_event_bus
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/events/topics")

            assert response.status_code == 200
            data = response.json()
            assert len(data["topics"]) == 3
            assert set(data["topics"]) == {"topic1", "topic2", "topic3"}

    def test_list_topics_returns_list(self, client: TestClient) -> None:
        """Test that list_topics returns a dictionary with topics list."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_event_bus = MagicMock()
            mock_event_bus._subscribers = {"topic1": []}

            mock_ctx = MagicMock()
            mock_ctx._event_bus = mock_event_bus
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/events/topics")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert "topics" in data
            assert isinstance(data["topics"], list)


# ============================================================================
# Cache Get Endpoint Tests
# ============================================================================


class TestGetCache:
    """Test GET /cache/{key} endpoint."""

    def test_get_cache_key_exists(self, client: TestClient) -> None:
        """Test retrieving an existing cache key."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.cache_get.return_value = "cached_value"
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/cache/test_key", headers={"X-API-Key": ""})

            assert response.status_code == 200
            data = response.json()
            assert data["key"] == "test_key"
            assert data["value"] == "cached_value"

    def test_get_cache_key_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent cache key."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.cache_get.return_value = None
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/cache/nonexistent", headers={"X-API-Key": ""})

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_cache_returns_different_types(self, client: TestClient) -> None:
        """Test that cache can return different data types."""
        test_cases = [
            ("string_value", "test string"),
            ("int_value", 42),
            ("float_value", 3.14),
            ("bool_value", True),
            ("list_value", [1, 2, 3]),
            ("dict_value", {"nested": "dict"}),
        ]

        for key, value in test_cases:
            with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
                mock_ctx = MagicMock()
                mock_ctx.cache_get.return_value = value
                mock_get_ctx.return_value = mock_ctx

                response = client.get(f"/cache/{key}", headers={"X-API-Key": ""})

                assert response.status_code == 200
                data = response.json()
                assert data["value"] == value

    def test_get_cache_requires_authentication(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that cache get requires authentication when API key is set."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "required-key")

        from glorious_agents.config import reset_config

        reset_config()

        response = client.get("/cache/test_key")

        assert response.status_code == 401


# ============================================================================
# Cache Set Endpoint Tests
# ============================================================================


class TestSetCache:
    """Test PUT /cache/{key} endpoint."""

    def test_set_cache_success(self, client: TestClient) -> None:
        """Test successfully setting a cache value."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            response = client.put(
                "/cache/test_key",
                json={"value": "test_value"},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "stored"
            assert data["key"] == "test_key"

            # Verify context.cache_set was called with correct params
            mock_ctx.cache_set.assert_called_once_with("test_key", "test_value", ttl=None)

    def test_set_cache_with_ttl(self, client: TestClient) -> None:
        """Test setting cache value with TTL."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            response = client.put(
                "/cache/ttl_key",
                json={"value": "ttl_value", "ttl": 3600},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 200
            mock_ctx.cache_set.assert_called_once_with("ttl_key", "ttl_value", ttl=3600)

    def test_set_cache_missing_value(self, client: TestClient) -> None:
        """Test error when 'value' key is missing."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            response = client.put(
                "/cache/test_key",
                json={"ttl": 3600},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 400
            assert "Missing 'value'" in response.json()["detail"]

    def test_set_cache_invalid_ttl_non_integer(self, client: TestClient) -> None:
        """Test error when TTL is not an integer."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            response = client.put(
                "/cache/test_key",
                json={"value": "test", "ttl": "not_an_int"},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 400
            assert "positive integer" in response.json()["detail"]

    def test_set_cache_invalid_ttl_zero(self, client: TestClient) -> None:
        """Test error when TTL is zero."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            response = client.put(
                "/cache/test_key",
                json={"value": "test", "ttl": 0},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 400
            assert "positive integer" in response.json()["detail"]

    def test_set_cache_invalid_ttl_negative(self, client: TestClient) -> None:
        """Test error when TTL is negative."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            response = client.put(
                "/cache/test_key",
                json={"value": "test", "ttl": -100},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 400
            assert "positive integer" in response.json()["detail"]

    def test_set_cache_different_value_types(self, client: TestClient) -> None:
        """Test setting cache with different value types."""
        test_values = [
            "string",
            42,
            3.14,
            True,
            [1, 2, 3],
            {"key": "value"},
            None,
        ]

        for value in test_values:
            with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
                mock_ctx = MagicMock()
                mock_get_ctx.return_value = mock_ctx

                response = client.put(
                    f"/cache/key_{id(value)}",
                    json={"value": value},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 200

    def test_set_cache_requires_authentication(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that cache set requires authentication when API key is set."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "required-key")

        from glorious_agents.config import reset_config

        reset_config()

        response = client.put(
            "/cache/test_key",
            json={"value": "test"},
        )

        assert response.status_code == 401


# ============================================================================
# Cache Delete Single Key Endpoint Tests
# ============================================================================


class TestDeleteCache:
    """Test DELETE /cache/{key} endpoint."""

    def test_delete_cache_success(self, client: TestClient) -> None:
        """Test successfully deleting a cache key."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.cache_delete.return_value = True
            mock_get_ctx.return_value = mock_ctx

            response = client.delete("/cache/test_key", headers={"X-API-Key": ""})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            assert data["key"] == "test_key"

            mock_ctx.cache_delete.assert_called_once_with("test_key")

    def test_delete_cache_key_not_found(self, client: TestClient) -> None:
        """Test deleting a non-existent cache key."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.cache_delete.return_value = False
            mock_get_ctx.return_value = mock_ctx

            response = client.delete("/cache/nonexistent", headers={"X-API-Key": ""})

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_delete_cache_requires_authentication(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that cache delete requires authentication when API key is set."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "required-key")

        from glorious_agents.config import reset_config

        reset_config()

        response = client.delete("/cache/test_key")

        assert response.status_code == 401


# ============================================================================
# Cache Clear All Endpoint Tests
# ============================================================================


class TestClearCache:
    """Test DELETE /cache endpoint."""

    def test_clear_cache_success(self, client: TestClient) -> None:
        """Test successfully clearing all cache entries."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_cache = MagicMock()
            mock_cache._cache = {"key1": "value1", "key2": "value2", "key3": "value3"}

            mock_ctx = MagicMock()
            mock_ctx._cache = mock_cache
            mock_get_ctx.return_value = mock_ctx

            response = client.delete("/cache", headers={"X-API-Key": ""})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cleared"
            assert data["count"] == 3

            mock_cache.clear.assert_called_once()

    def test_clear_cache_empty(self, client: TestClient) -> None:
        """Test clearing an empty cache."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_cache = MagicMock()
            mock_cache._cache = {}

            mock_ctx = MagicMock()
            mock_ctx._cache = mock_cache
            mock_get_ctx.return_value = mock_ctx

            response = client.delete("/cache", headers={"X-API-Key": ""})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cleared"
            assert data["count"] == 0

    def test_clear_cache_requires_authentication(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that cache clear requires authentication when API key is set."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "required-key")

        from glorious_agents.config import reset_config

        reset_config()

        response = client.delete("/cache")

        assert response.status_code == 401


# ============================================================================
# Cache Stats Endpoint Tests
# ============================================================================


class TestCacheStats:
    """Test GET /cache endpoint for statistics."""

    def test_cache_stats_success(self, client: TestClient) -> None:
        """Test retrieving cache statistics."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_cache = MagicMock()
            mock_cache._cache = {
                "key1": "value1",
                "key2": "value2",
                "key3": {"nested": "value"},
            }

            mock_ctx = MagicMock()
            mock_ctx._cache = mock_cache
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/cache", headers={"X-API-Key": ""})

            assert response.status_code == 200
            data = response.json()
            assert data["size"] == 3
            assert len(data["keys"]) == 3
            assert set(data["keys"]) == {"key1", "key2", "key3"}

    def test_cache_stats_empty(self, client: TestClient) -> None:
        """Test cache stats when cache is empty."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_cache = MagicMock()
            mock_cache._cache = {}

            mock_ctx = MagicMock()
            mock_ctx._cache = mock_cache
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/cache", headers={"X-API-Key": ""})

            assert response.status_code == 200
            data = response.json()
            assert data["size"] == 0
            assert data["keys"] == []

    def test_cache_stats_requires_authentication(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that cache stats requires authentication when API key is set."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "required-key")

        from glorious_agents.config import reset_config

        reset_config()

        response = client.get("/cache")

        assert response.status_code == 401

    def test_cache_stats_returns_correct_structure(self, client: TestClient) -> None:
        """Test that cache stats returns correct response structure."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_cache = MagicMock()
            mock_cache._cache = {"test": "data"}

            mock_ctx = MagicMock()
            mock_ctx._cache = mock_cache
            mock_get_ctx.return_value = mock_ctx

            response = client.get("/cache", headers={"X-API-Key": ""})

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert "size" in data
            assert "keys" in data
            assert isinstance(data["size"], int)
            assert isinstance(data["keys"], list)


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests combining multiple endpoints."""

    def test_rpc_call_with_authentication_flow(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test complete RPC flow with authentication."""
        monkeypatch.setenv("GLORIOUS_DAEMON_API_KEY", "test-api-key-123")

        from glorious_agents.config import reset_config

        reset_config()

        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                # Setup
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test:main"

                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                mock_module = MagicMock()
                mock_module.test_func = lambda x: x * 2
                mock_import.return_value = mock_module

                # Without API key - should fail
                response = client.post(
                    "/rpc/test/test_func",
                    json={"params": {"x": 5}},
                )
                assert response.status_code == 401

                # With API key - should succeed
                response = client.post(
                    "/rpc/test/test_func",
                    json={"params": {"x": 5}},
                    headers={"X-API-Key": "test-api-key-123"},
                )
                assert response.status_code == 200

    def test_cache_workflow(self, client: TestClient) -> None:
        """Test complete cache workflow: set, get, delete, clear."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_cache = MagicMock()
            mock_cache._cache = {}

            mock_ctx = MagicMock()
            mock_ctx._cache = mock_cache
            mock_ctx.cache_get.return_value = None
            mock_ctx.cache_delete.return_value = False
            mock_get_ctx.return_value = mock_ctx

            # Set value
            response = client.put(
                "/cache/workflow_key",
                json={"value": "workflow_value"},
                headers={"X-API-Key": ""},
            )
            assert response.status_code == 200

            # Get value
            mock_ctx.cache_get.return_value = "workflow_value"
            response = client.get("/cache/workflow_key", headers={"X-API-Key": ""})
            assert response.status_code == 200
            assert response.json()["value"] == "workflow_value"

            # Delete value
            mock_ctx.cache_delete.return_value = True
            response = client.delete("/cache/workflow_key", headers={"X-API-Key": ""})
            assert response.status_code == 200

            # Clear all
            mock_cache._cache = {"key1": "v1", "key2": "v2"}
            response = client.delete("/cache", headers={"X-API-Key": ""})
            assert response.status_code == 200

    def test_event_workflow(self, client: TestClient) -> None:
        """Test complete event workflow: publish, list topics."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_event_bus = MagicMock()
            mock_event_bus._subscribers = {"test_topic": [MagicMock()]}

            mock_ctx = MagicMock()
            mock_ctx._event_bus = mock_event_bus
            mock_get_ctx.return_value = mock_ctx

            # Publish event
            response = client.post(
                "/events/test_topic",
                json={"data": "test"},
                headers={"X-API-Key": ""},
            )
            assert response.status_code == 200

            # List topics
            response = client.get("/events/topics")
            assert response.status_code == 200
            assert "test_topic" in response.json()["topics"]


# ============================================================================
# Model Tests
# ============================================================================


class TestRPCRequest:
    """Test RPCRequest Pydantic model."""

    def test_rpc_request_default_params(self) -> None:
        """Test RPCRequest with default parameters."""
        request = RPCRequest()
        assert request.params == {}

    def test_rpc_request_with_params(self) -> None:
        """Test RPCRequest with provided parameters."""
        request = RPCRequest(params={"key": "value", "count": 5})
        assert request.params == {"key": "value", "count": 5}

    def test_rpc_request_nested_params(self) -> None:
        """Test RPCRequest with nested parameters."""
        params = {
            "nested": {"level1": {"level2": "value"}},
            "array": [1, 2, 3],
        }
        request = RPCRequest(params=params)
        assert request.params == params


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_cache_key_special_characters(self, client: TestClient) -> None:
        """Test cache operations with special characters in keys."""
        special_keys = [
            "key-with-dashes",
            "key_with_underscores",
            "key.with.dots",
            "key/with/slashes",
            "key:with:colons",
        ]

        for key in special_keys:
            with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
                mock_ctx = MagicMock()
                mock_get_ctx.return_value = mock_ctx

                response = client.put(
                    f"/cache/{key}",
                    json={"value": f"value_for_{key}"},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 200

    def test_rpc_large_parameters(self, client: TestClient) -> None:
        """Test RPC with large parameter sets."""
        with patch("glorious_agents.core.daemon_rpc.get_registry") as mock_get_registry:
            with patch("glorious_agents.core.daemon_rpc.importlib.import_module") as mock_import:
                mock_manifest = MagicMock()
                mock_manifest.entry_point = "test:main"

                mock_registry = MagicMock()
                mock_registry.get_manifest.return_value = mock_manifest
                mock_get_registry.return_value = mock_registry

                mock_module = MagicMock()
                mock_module.echo = lambda **kwargs: kwargs
                mock_import.return_value = mock_module

                # Create large parameter set
                large_params = {f"param_{i}": f"value_{i}" for i in range(100)}

                response = client.post(
                    "/rpc/test/echo",
                    json={"params": large_params},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 200

    def test_topic_name_special_characters(self, client: TestClient) -> None:
        """Test event topics with special characters."""
        special_topics = [
            "topic-with-dashes",
            "topic_with_underscores",
            "topic.with.dots",
            "topic:separator",
        ]

        for topic in special_topics:
            with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
                mock_ctx = MagicMock()
                mock_get_ctx.return_value = mock_ctx

                response = client.post(
                    f"/events/{topic}",
                    json={"data": "test"},
                    headers={"X-API-Key": ""},
                )

                assert response.status_code == 200

    def test_cache_large_values(self, client: TestClient) -> None:
        """Test caching large values."""
        with patch("glorious_agents.core.daemon_rpc.get_ctx") as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_get_ctx.return_value = mock_ctx

            # Create large value
            large_value = "x" * 10000

            response = client.put(
                "/cache/large_key",
                json={"value": large_value},
                headers={"X-API-Key": ""},
            )

            assert response.status_code == 200

    def test_health_check_always_available(self, client: TestClient) -> None:
        """Test that health check is always available without authentication."""
        # Even with missing context, health check should work
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

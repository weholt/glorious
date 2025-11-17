"""Tests for runtime singleton."""

import sqlite3
import threading

import pytest

from glorious_agents.core.runtime import get_ctx, reset_ctx


class TestRuntime:
    def setup_method(self):
        """Reset context before each test."""
        reset_ctx()

    def teardown_method(self):
        """Clean up after each test."""
        reset_ctx()

    def test_get_ctx_creates_singleton(self):
        """Test that get_ctx creates a singleton context."""
        ctx1 = get_ctx()
        ctx2 = get_ctx()

        assert ctx1 is ctx2

    def test_get_ctx_returns_context(self):
        """Test that get_ctx returns a SkillContext."""
        ctx = get_ctx()

        assert ctx is not None
        assert hasattr(ctx, "conn")
        assert hasattr(ctx, "_event_bus")

    def test_reset_ctx_clears_singleton(self):
        """Test that reset_ctx clears the singleton."""
        ctx1 = get_ctx()
        reset_ctx()
        ctx2 = get_ctx()

        assert ctx1 is not ctx2

    def test_reset_ctx_closes_connection(self):
        """Test that reset_ctx closes the connection."""
        ctx = get_ctx()
        conn = ctx.conn

        reset_ctx()

        # Connection should be closed, attempts to use it should fail
        with pytest.raises(sqlite3.ProgrammingError, match="Cannot operate on a closed database"):
            conn.execute("SELECT 1")

    def test_thread_safety(self):
        """Test that get_ctx is thread-safe."""
        contexts = []

        def get_and_store():
            ctx = get_ctx()
            contexts.append(ctx)

        threads = [threading.Thread(target=get_and_store) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same context
        assert len({id(ctx) for ctx in contexts}) == 1

    def test_reset_ctx_when_none(self):
        """Test that reset_ctx works when context is None."""
        reset_ctx()  # First reset
        reset_ctx()  # Second reset should not fail

        # Should be able to create context after reset
        ctx = get_ctx()
        assert ctx is not None

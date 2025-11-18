"""Unit tests for SkillContext lifecycle management."""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from glorious_agents.core.context import EventBus, SkillContext


class TestSkillContextLifecycle:
    """Tests for SkillContext lifecycle management (context manager)."""

    def test_context_manager_enter_returns_self(self):
        """Test that __enter__ returns the context instance."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        
        result = ctx.__enter__()
        assert result is ctx

    def test_context_manager_exit_closes_connection(self):
        """Test that __exit__ closes the database connection."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        ctx.__exit__(None, None, None)
        
        mock_conn.close.assert_called_once()

    def test_can_use_with_statement(self):
        """Test that SkillContext can be used with 'with' statement."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        with SkillContext(mock_conn, mock_event_bus) as ctx:
            # Context should be available inside with block
            assert isinstance(ctx, SkillContext)
            assert ctx._closed is False
        
        # Connection should be closed after with block
        mock_conn.close.assert_called_once()

    def test_close_method_closes_connection(self):
        """Test that close() method closes the database connection."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        ctx.close()
        
        mock_conn.close.assert_called_once()
        assert ctx._closed is True

    def test_close_method_is_idempotent(self):
        """Test that close() can be called multiple times safely."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        ctx.close()
        ctx.close()
        ctx.close()
        
        # Should only close once
        mock_conn.close.assert_called_once()
        assert ctx._closed is True

    def test_close_ignores_connection_errors(self):
        """Test that close() handles connection errors gracefully."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock(side_effect=sqlite3.ProgrammingError("Cannot operate on closed database"))
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        
        # Should not raise exception
        ctx.close()
        assert ctx._closed is True

    def test_conn_property_raises_after_close(self):
        """Test that accessing conn property after close raises error."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        ctx.close()
        
        with pytest.raises(RuntimeError, match="Cannot use connection after context is closed"):
            _ = ctx.conn

    def test_conn_property_works_before_close(self):
        """Test that conn property returns connection before close."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        
        # Should return the connection
        assert ctx.conn is mock_conn

    def test_exit_with_exception_still_closes(self):
        """Test that __exit__ closes connection even when exception occurred."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        
        # Simulate exception in with block
        exc_type = ValueError
        exc_val = ValueError("test error")
        exc_tb = None
        
        ctx.__exit__(exc_type, exc_val, exc_tb)
        
        # Connection should still be closed
        mock_conn.close.assert_called_once()

    def test_context_usage_in_typical_workflow(self):
        """Test typical workflow with context manager."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_conn.execute = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        with SkillContext(mock_conn, mock_event_bus) as ctx:
            # Simulate typical operations
            conn = ctx.conn
            conn.execute("SELECT 1")
            
            # Register a skill
            mock_skill = Mock()
            ctx.register_skill("test_skill", mock_skill)
            
            # Check closed state
            assert not ctx._closed
        
        # After with block, should be closed
        assert ctx._closed
        mock_conn.close.assert_called_once()

    def test_manual_close_before_exit(self):
        """Test that manually closing before __exit__ is handled correctly."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        with SkillContext(mock_conn, mock_event_bus) as ctx:
            ctx.close()  # Manual close
            assert ctx._closed
        
        # __exit__ should handle already-closed state
        # close() should only be called once
        mock_conn.close.assert_called_once()

    def test_cache_operations_after_close(self):
        """Test that cache operations still work after close (if needed)."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        mock_event_bus = Mock(spec=EventBus)
        
        ctx = SkillContext(mock_conn, mock_event_bus)
        
        # Set cache value before close
        ctx.set_cache("key1", "value1")
        
        ctx.close()
        
        # Cache get should still work (doesn't require connection)
        result = ctx.get_cache("key1")
        assert result == "value1"
        
        # Cache set after close should also work
        ctx.set_cache("key2", "value2")
        result2 = ctx.get_cache("key2")
        assert result2 == "value2"

    def test_event_bus_operations_after_close(self):
        """Test that event bus operations work after close."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.close = Mock()
        event_bus = EventBus()  # Use real event bus
        
        ctx = SkillContext(mock_conn, event_bus)
        
        callback_called = []
        
        def callback(data):
            callback_called.append(data)
        
        event_bus.subscribe("test_topic", callback)
        ctx.close()
        
        # Event bus should still work after close
        event_bus.publish("test_topic", {"message": "test"})
        assert len(callback_called) == 1
        assert callback_called[0]["message"] == "test"
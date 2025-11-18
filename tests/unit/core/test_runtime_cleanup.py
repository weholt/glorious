"""Unit tests for runtime cleanup functionality."""

import atexit
import threading
from unittest.mock import Mock, patch, call

import pytest

from glorious_agents.core.runtime import get_ctx, reset_ctx, _cleanup_context


class TestRuntimeCleanup:
    """Tests for runtime cleanup functionality."""

    def setup_method(self):
        """Reset runtime before each test."""
        reset_ctx()

    def teardown_method(self):
        """Clean up after each test."""
        reset_ctx()

    def test_reset_ctx_closes_connection(self):
        """Test that reset_ctx closes the database connection."""
        mock_conn = Mock()
        mock_conn.close = Mock()
        mock_event_bus = Mock()
        
        with patch("glorious_agents.core.runtime.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus):
            
            # Get context to initialize it
            ctx = get_ctx()
            
            # Reset should close the connection
            reset_ctx()
            
            # Verify close was called
            assert ctx._closed

    def test_reset_ctx_is_idempotent(self):
        """Test that reset_ctx can be called multiple times safely."""
        mock_conn = Mock()
        mock_conn.close = Mock()
        mock_event_bus = Mock()
        
        with patch("glorious_agents.core.runtime.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus):
            
            get_ctx()
            
            # Multiple resets should not cause errors
            reset_ctx()
            reset_ctx()
            reset_ctx()

    def test_reset_ctx_with_no_context(self):
        """Test that reset_ctx works when no context exists."""
        # Should not raise error
        reset_ctx()

    def test_cleanup_context_function_exists(self):
        """Test that _cleanup_context function is defined."""
        # Function should exist and be callable
        assert callable(_cleanup_context)

    def test_cleanup_context_calls_reset(self):
        """Test that _cleanup_context calls reset_ctx."""
        with patch("glorious_agents.core.runtime.reset_ctx") as mock_reset:
            _cleanup_context()
            mock_reset.assert_called_once()

    def test_atexit_handler_registered(self):
        """Test that cleanup is registered with atexit."""
        # This is tricky to test directly, but we can verify the pattern
        # by checking that get_ctx registers the handler
        
        mock_conn = Mock()
        mock_event_bus = Mock()
        
        with patch("glorious_agents.core.runtime.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus), \
             patch("glorious_agents.core.runtime.atexit.register") as mock_atexit:
            
            # First call should register atexit
            get_ctx()
            
            # Verify atexit.register was called with _cleanup_context
            assert mock_atexit.called
            # Check if _cleanup_context was registered
            registered_funcs = [call[0][0] for call in mock_atexit.call_args_list]
            assert _cleanup_context in registered_funcs

    def test_thread_safety_of_reset(self):
        """Test that reset_ctx is thread-safe."""
        mock_conn = Mock()
        mock_event_bus = Mock()
        
        errors = []
        
        def reset_thread():
            try:
                reset_ctx()
            except Exception as e:
                errors.append(e)
        
        with patch("glorious_agents.core.runtime.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus):
            
            get_ctx()
            
            # Create multiple threads that reset
            threads = [threading.Thread(target=reset_thread) for _ in range(10)]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join()
            
            # No errors should have occurred
            assert len(errors) == 0

    def test_get_ctx_after_reset_creates_new_context(self):
        """Test that get_ctx creates new context after reset."""
        mock_conn1 = Mock()
        mock_conn2 = Mock()
        mock_event_bus = Mock()
        
        with patch("glorious_agents.core.runtime.get_connection", side_effect=[mock_conn1, mock_conn2]), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus):
            
            ctx1 = get_ctx()
            reset_ctx()
            ctx2 = get_ctx()
            
            # Should be different contexts
            assert ctx1 is not ctx2

    def test_reset_handles_connection_close_error(self):
        """Test that reset handles errors during connection close."""
        mock_conn = Mock()
        mock_conn.close = Mock(side_effect=Exception("Close failed"))
        mock_event_bus = Mock()
        
        with patch("glorious_agents.core.runtime.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus):
            
            get_ctx()
            
            # Reset should not raise error even if close fails
            reset_ctx()

    def test_context_state_after_reset(self):
        """Test that context is properly marked as closed after reset."""
        mock_conn = Mock()
        mock_conn.close = Mock()
        mock_event_bus = Mock()
        
        with patch("glorious_agents.core.runtime.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus):
            
            ctx = get_ctx()
            assert not ctx._closed
            
            reset_ctx()
            assert ctx._closed

    def test_using_context_after_reset_raises_error(self):
        """Test that using closed context after reset raises error."""
        mock_conn = Mock()
        mock_event_bus = Mock()
        
        with patch("glorious_agents.core.runtime.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.runtime.EventBus", return_value=mock_event_bus):
            
            ctx = get_ctx()
            reset_ctx()
            
            # Trying to access connection should raise error
            with pytest.raises(RuntimeError, match="Cannot use connection after context is closed"):
                _ = ctx.conn
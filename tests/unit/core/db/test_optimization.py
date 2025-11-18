"""Unit tests for database optimization."""

import sqlite3
from unittest.mock import Mock, patch, call

import pytest

from glorious_agents.core.db.optimization import optimize_database


class TestOptimizeDatabase:
    """Tests for optimize_database function."""

    def test_runs_analyze_command(self):
        """Test that ANALYZE is executed."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.optimization.get_connection", return_value=mock_conn):
            optimize_database()
        
        # Check that ANALYZE was called
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        assert any("ANALYZE" in call for call in execute_calls)
        
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called_once()

    def test_reindexes_database(self):
        """Test that REINDEX is executed."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.optimization.get_connection", return_value=mock_conn):
            optimize_database()
        
        # Check that REINDEX was called
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        assert any("REINDEX" in call for call in execute_calls)

    def test_optimizes_pragma_settings(self):
        """Test that optimization pragma settings are applied."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.optimization.get_connection", return_value=mock_conn):
            optimize_database()
        
        # Should have executed multiple optimization commands
        assert mock_conn.execute.call_count >= 2

    def test_closes_connection_on_error(self):
        """Test that connection is closed even if optimization fails."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock(side_effect=sqlite3.OperationalError("database locked"))
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.optimization.get_connection", return_value=mock_conn):
            with pytest.raises(sqlite3.OperationalError):
                optimize_database()
            
            mock_conn.close.assert_called_once()

    def test_idempotent_optimization(self):
        """Test that optimization can be run multiple times safely."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.optimization.get_connection", return_value=mock_conn):
            optimize_database()
            optimize_database()
        
        # Should have been called twice without issues
        assert mock_conn.close.call_count == 2

    def test_does_not_run_vacuum_by_default(self):
        """Test that VACUUM is not run (as it's expensive)."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.optimization.get_connection", return_value=mock_conn):
            optimize_database()
        
        # Check that VACUUM was NOT called
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        assert not any("VACUUM" in call.upper() for call in execute_calls)
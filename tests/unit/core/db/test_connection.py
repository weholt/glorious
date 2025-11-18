"""Unit tests for database connection management."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from glorious_agents.core.db.connection import (
    get_agent_db_path,
    get_connection,
    get_data_folder,
    get_master_db_path,
)


class TestGetDataFolder:
    """Tests for get_data_folder function."""

    def test_creates_folder_if_not_exists(self, tmp_path, monkeypatch):
        """Test that data folder is created if it doesn't exist."""
        test_folder = tmp_path / "test_data"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = test_folder
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            result = get_data_folder()
            
        assert result == test_folder
        assert test_folder.exists()
        assert test_folder.is_dir()

    def test_returns_existing_folder(self, tmp_path, monkeypatch):
        """Test that existing folder is returned without error."""
        test_folder = tmp_path / "existing_data"
        test_folder.mkdir(parents=True, exist_ok=True)
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = test_folder
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            result = get_data_folder()
            
        assert result == test_folder
        assert test_folder.exists()

    def test_creates_nested_folders(self, tmp_path, monkeypatch):
        """Test that nested folder structure is created."""
        test_folder = tmp_path / "level1" / "level2" / "level3"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = test_folder
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            result = get_data_folder()
            
        assert result == test_folder
        assert test_folder.exists()


class TestGetAgentDbPath:
    """Tests for get_agent_db_path function."""

    def test_returns_unified_db_path(self, tmp_path):
        """Test that unified database path is returned."""
        test_folder = tmp_path / "data"
        test_folder.mkdir()
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = test_folder
        mock_config.DB_NAME = "glorious.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            result = get_agent_db_path()
            
        expected = test_folder / "glorious.db"
        assert result == expected

    def test_agent_code_parameter_is_ignored(self, tmp_path):
        """Test that agent_code parameter is deprecated but doesn't break."""
        test_folder = tmp_path / "data"
        test_folder.mkdir()
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = test_folder
        mock_config.DB_NAME = "glorious.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            result = get_agent_db_path(agent_code="test_agent")
            
        expected = test_folder / "glorious.db"
        assert result == expected

    def test_uses_custom_db_name_from_config(self, tmp_path):
        """Test that custom database name from config is used."""
        test_folder = tmp_path / "data"
        test_folder.mkdir()
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = test_folder
        mock_config.DB_NAME = "custom.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            result = get_agent_db_path()
            
        expected = test_folder / "custom.db"
        assert result == expected


class TestGetMasterDbPath:
    """Tests for get_master_db_path function."""

    def test_returns_same_as_agent_db_path(self, tmp_path):
        """Test that master DB path is the same as unified DB path."""
        test_folder = tmp_path / "data"
        test_folder.mkdir()
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = test_folder
        mock_config.DB_NAME = "glorious.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            master_path = get_master_db_path()
            agent_path = get_agent_db_path()
            
        assert master_path == agent_path


class TestGetConnection:
    """Tests for get_connection function."""

    def test_creates_connection_with_default_settings(self, tmp_path):
        """Test that connection is created with performance optimizations."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn = get_connection()
            
        try:
            # Verify it's a connection
            assert isinstance(conn, sqlite3.Connection)
            
            # Verify WAL mode
            cursor = conn.execute("PRAGMA journal_mode")
            assert cursor.fetchone()[0].upper() == "WAL"
            
            # Verify foreign keys enabled
            cursor = conn.execute("PRAGMA foreign_keys")
            assert cursor.fetchone()[0] == 1
            
            # Verify busy timeout set
            cursor = conn.execute("PRAGMA busy_timeout")
            timeout = cursor.fetchone()[0]
            assert timeout == 5000
            
        finally:
            conn.close()

    def test_check_same_thread_parameter(self, tmp_path):
        """Test that check_same_thread parameter is respected."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            # Default (False)
            conn1 = get_connection()
            conn1.close()
            
            # Explicit True
            conn2 = get_connection(check_same_thread=True)
            conn2.close()
            
            # Explicit False
            conn3 = get_connection(check_same_thread=False)
            conn3.close()

    def test_multiple_connections_with_wal_mode(self, tmp_path):
        """Test that multiple connections work with WAL mode."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn1 = get_connection()
            conn2 = get_connection()
            
        try:
            # Create table in first connection
            conn1.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
            conn1.commit()
            
            # Read from second connection
            cursor = conn2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test'")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "test"
            
        finally:
            conn1.close()
            conn2.close()

    def test_connection_with_memory_mapped_io(self, tmp_path):
        """Test that memory-mapped I/O is configured."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn = get_connection()
            
        try:
            cursor = conn.execute("PRAGMA mmap_size")
            mmap_size = cursor.fetchone()[0]
            assert mmap_size == 268435456  # 256MB
        finally:
            conn.close()

    def test_connection_cache_size(self, tmp_path):
        """Test that cache size is configured correctly."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn = get_connection()
            
        try:
            cursor = conn.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]
            assert cache_size == -64000  # 64MB in KB
        finally:
            conn.close()

    def test_connection_temp_store_in_memory(self, tmp_path):
        """Test that temp tables are stored in memory."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn = get_connection()
            
        try:
            cursor = conn.execute("PRAGMA temp_store")
            temp_store = cursor.fetchone()[0]
            assert temp_store == 2  # MEMORY
        finally:
            conn.close()

    def test_connection_page_size(self, tmp_path):
        """Test that page size is set correctly."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn = get_connection()
            
        try:
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            assert page_size == 4096
        finally:
            conn.close()

    def test_synchronous_mode_normal(self, tmp_path):
        """Test that synchronous mode is set to NORMAL."""
        db_path = tmp_path / "test.db"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = tmp_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn = get_connection()
            
        try:
            cursor = conn.execute("PRAGMA synchronous")
            sync_mode = cursor.fetchone()[0]
            assert sync_mode == 1  # NORMAL
        finally:
            conn.close()


class TestConnectionEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_connection_to_nonexistent_directory(self, tmp_path):
        """Test that connection creates necessary directories."""
        nested_path = tmp_path / "level1" / "level2"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = nested_path
        mock_config.DB_NAME = "test.db"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            # get_connection calls get_data_folder which creates directories
            conn = get_connection()
            
        try:
            assert nested_path.exists()
            assert (nested_path / "test.db").exists()
        finally:
            conn.close()

    def test_connection_with_special_characters_in_path(self, tmp_path):
        """Test that paths with special characters work."""
        special_folder = tmp_path / "data with spaces & symbols!"
        
        mock_config = Mock()
        mock_config.DATA_FOLDER = special_folder
        mock_config.DB_NAME = "test-db.sqlite3"
        
        with patch("glorious_agents.core.db.connection.get_config", return_value=mock_config):
            conn = get_connection()
            
        try:
            # Should create and work with special character paths
            assert isinstance(conn, sqlite3.Connection)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()
        finally:
            conn.close()
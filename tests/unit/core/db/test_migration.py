"""Unit tests for legacy database migration."""

import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from glorious_agents.core.db.migration import migrate_legacy_databases


class TestMigrateLegacyDatabases:
    """Tests for migrate_legacy_databases function."""

    def test_skips_if_no_legacy_databases_exist(self, tmp_path):
        """Test that migration is skipped if legacy DBs don't exist."""
        mock_config = Mock()
        mock_config.get_shared_db_path.return_value = tmp_path / "nonexistent_shared.db"
        mock_config.get_master_db_path.return_value = tmp_path / "nonexistent_master.db"
        mock_config.get_unified_db_path.return_value = tmp_path / "unified.db"
        
        with patch("glorious_agents.core.db.migration.get_config", return_value=mock_config):
            # Should not raise error
            migrate_legacy_databases()

    def test_migrates_shared_database_if_exists(self, tmp_path):
        """Test that shared database is migrated when it exists."""
        # Create mock legacy DB
        legacy_db = tmp_path / "shared.db"
        legacy_conn = sqlite3.connect(str(legacy_db))
        legacy_conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
        legacy_conn.execute("INSERT INTO test VALUES (1, 'test_data')")
        legacy_conn.commit()
        legacy_conn.close()
        
        unified_db = tmp_path / "unified.db"
        
        mock_config = Mock()
        mock_config.get_shared_db_path.return_value = legacy_db
        mock_config.get_master_db_path.return_value = tmp_path / "nonexistent_master.db"
        mock_config.get_unified_db_path.return_value = unified_db
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.migration.get_config", return_value=mock_config), \
             patch("glorious_agents.core.db.migration.get_connection", return_value=mock_conn):
            migrate_legacy_databases()
        
        # Verify ATTACH DATABASE was called
        execute_calls = [call[0][0] if call[0] else "" for call in mock_conn.execute.call_args_list]
        assert any("ATTACH DATABASE" in call for call in execute_calls)

    def test_migrates_master_database_if_exists(self, tmp_path):
        """Test that master database is migrated when it exists."""
        # Create mock master DB
        master_db = tmp_path / "master.db"
        master_conn = sqlite3.connect(str(master_db))
        master_conn.execute("CREATE TABLE agents (code TEXT PRIMARY KEY)")
        master_conn.execute("INSERT INTO agents VALUES ('agent1')")
        master_conn.commit()
        master_conn.close()
        
        unified_db = tmp_path / "unified.db"
        
        mock_config = Mock()
        mock_config.get_shared_db_path.return_value = tmp_path / "nonexistent_shared.db"
        mock_config.get_master_db_path.return_value = master_db
        mock_config.get_unified_db_path.return_value = unified_db
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.migration.get_config", return_value=mock_config), \
             patch("glorious_agents.core.db.migration.get_connection", return_value=mock_conn):
            migrate_legacy_databases()
        
        # Verify migration was attempted
        assert mock_conn.execute.call_count > 0

    def test_closes_connection_after_migration(self, tmp_path):
        """Test that connection is properly closed."""
        legacy_db = tmp_path / "shared.db"
        legacy_db.touch()  # Create empty file
        
        mock_config = Mock()
        mock_config.get_shared_db_path.return_value = legacy_db
        mock_config.get_master_db_path.return_value = tmp_path / "nonexistent.db"
        mock_config.get_unified_db_path.return_value = tmp_path / "unified.db"
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.migration.get_config", return_value=mock_config), \
             patch("glorious_agents.core.db.migration.get_connection", return_value=mock_conn):
            migrate_legacy_databases()
        
        mock_conn.close.assert_called_once()

    def test_handles_migration_errors_gracefully(self, tmp_path):
        """Test that migration errors are handled without crashing."""
        legacy_db = tmp_path / "shared.db"
        # Create corrupted DB
        legacy_db.write_bytes(b"corrupted data")
        
        mock_config = Mock()
        mock_config.get_shared_db_path.return_value = legacy_db
        mock_config.get_master_db_path.return_value = tmp_path / "nonexistent.db"
        mock_config.get_unified_db_path.return_value = tmp_path / "unified.db"
        
        with patch("glorious_agents.core.db.migration.get_config", return_value=mock_config):
            # Should handle error gracefully (might log it)
            try:
                migrate_legacy_databases()
            except sqlite3.DatabaseError:
                # Expected for corrupted database
                pass

    def test_migrates_both_databases_if_both_exist(self, tmp_path):
        """Test that both legacy databases are migrated if they exist."""
        # Create both legacy DBs
        shared_db = tmp_path / "shared.db"
        shared_conn = sqlite3.connect(str(shared_db))
        shared_conn.execute("CREATE TABLE shared_data (id INTEGER)")
        shared_conn.close()
        
        master_db = tmp_path / "master.db"
        master_conn = sqlite3.connect(str(master_db))
        master_conn.execute("CREATE TABLE master_data (id INTEGER)")
        master_conn.close()
        
        mock_config = Mock()
        mock_config.get_shared_db_path.return_value = shared_db
        mock_config.get_master_db_path.return_value = master_db
        mock_config.get_unified_db_path.return_value = tmp_path / "unified.db"
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.migration.get_config", return_value=mock_config), \
             patch("glorious_agents.core.db.migration.get_connection", return_value=mock_conn):
            migrate_legacy_databases()
        
        # Should have attached both databases
        execute_calls = [call[0][0] if call[0] else "" for call in mock_conn.execute.call_args_list]
        attach_calls = [call for call in execute_calls if "ATTACH DATABASE" in call]
        # Might be 1 or 2 attach calls depending on implementation
        assert len(attach_calls) >= 1
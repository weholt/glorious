"""Unit tests for database schema initialization."""

import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from glorious_agents.core.db.schema import init_master_db, init_skill_schema


class TestInitSkillSchema:
    """Tests for init_skill_schema function."""

    def test_does_nothing_if_schema_file_not_exists(self, tmp_path):
        """Test that function returns early if schema file doesn't exist."""
        schema_path = tmp_path / "nonexistent_schema.sql"
        
        # Should not raise error
        init_skill_schema("test_skill", schema_path)

    def test_executes_schema_sql_for_simple_skill(self, tmp_path):
        """Test that schema SQL is executed for skills without migrations."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text(schema_sql)
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.executescript = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_skill_schema("test_skill", schema_path)
        
        # Verify schema was executed
        mock_conn.executescript.assert_called_once()
        call_args = mock_conn.executescript.call_args[0][0]
        assert "CREATE TABLE" in call_args
        assert "test_data" in call_args
        
        # Verify metadata table created
        assert mock_conn.execute.call_count >= 1
        execute_calls = [str(call) for call in mock_conn.execute.call_args_list]
        assert any("_skill_schemas" in str(call) for call in execute_calls)
        
        # Verify commits and close
        assert mock_conn.commit.call_count >= 2
        mock_conn.close.assert_called_once()

    def test_tracks_schema_application_in_metadata(self, tmp_path):
        """Test that schema application is tracked."""
        schema_sql = "CREATE TABLE test (id INTEGER);"
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text(schema_sql)
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.executescript = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_skill_schema("my_skill", schema_path)
        
        # Check that skill name was inserted into metadata
        execute_calls = [call[0][0] if call[0] else "" for call in mock_conn.execute.call_args_list]
        insert_call = [c for c in execute_calls if "INSERT" in c and "_skill_schemas" in c]
        assert len(insert_call) > 0

    def test_handles_skill_with_migrations_directory(self, tmp_path):
        """Test that skills with migrations use migration system."""
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text("CREATE TABLE test (id INTEGER);")
        
        # Create migrations directory
        migrations_dir = schema_path.parent / "migrations"
        migrations_dir.mkdir()
        
        mock_conn = Mock(spec=sqlite3.Connection)
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.db.schema.init_migrations_table") as mock_init_mig, \
             patch("glorious_agents.core.db.schema.get_current_version", return_value=0), \
             patch("glorious_agents.core.db.schema.run_migrations") as mock_run_mig:
            
            init_skill_schema("test_skill", schema_path)
            
            # Verify migration system was used
            mock_init_mig.assert_called_once()
            mock_run_mig.assert_called_once_with("test_skill", migrations_dir)

    def test_applies_base_schema_only_if_no_migrations_run(self, tmp_path):
        """Test that base schema is only applied if version is 0."""
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text("CREATE TABLE test (id INTEGER);")
        
        migrations_dir = schema_path.parent / "migrations"
        migrations_dir.mkdir()
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.executescript = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        # Test with version 0 (should apply schema)
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.db.schema.init_migrations_table"), \
             patch("glorious_agents.core.db.schema.get_current_version", return_value=0), \
             patch("glorious_agents.core.db.schema.run_migrations"):
            
            init_skill_schema("test_skill", schema_path)
            mock_conn.executescript.assert_called_once()
        
        # Reset mocks
        mock_conn.reset_mock()
        
        # Test with version > 0 (should not apply schema)
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn), \
             patch("glorious_agents.core.db.schema.init_migrations_table"), \
             patch("glorious_agents.core.db.schema.get_current_version", return_value=5), \
             patch("glorious_agents.core.db.schema.run_migrations"):
            
            init_skill_schema("test_skill", schema_path)
            mock_conn.executescript.assert_not_called()

    def test_closes_connection_even_on_error(self, tmp_path):
        """Test that connection is closed even if schema execution fails."""
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text("INVALID SQL;")
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.executescript = Mock(side_effect=sqlite3.OperationalError("syntax error"))
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            with pytest.raises(sqlite3.OperationalError):
                init_skill_schema("test_skill", schema_path)
            
            # Connection should still be closed
            mock_conn.close.assert_called_once()

    def test_handles_complex_schema_with_multiple_tables(self, tmp_path):
        """Test execution of complex schema with foreign keys."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_items_category ON items(category_id);
        """
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text(schema_sql)
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.executescript = Mock()
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_skill_schema("complex_skill", schema_path)
        
        # Verify schema was executed
        mock_conn.executescript.assert_called_once()
        executed_sql = mock_conn.executescript.call_args[0][0]
        assert "categories" in executed_sql
        assert "items" in executed_sql
        assert "FOREIGN KEY" in executed_sql


class TestInitMasterDb:
    """Tests for init_master_db function."""

    def test_creates_core_agents_table(self):
        """Test that core_agents table is created."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_master_db()
        
        # Verify table creation SQL was executed
        mock_conn.execute.assert_called_once()
        create_sql = mock_conn.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS core_agents" in create_sql
        assert "code TEXT PRIMARY KEY" in create_sql
        assert "name TEXT NOT NULL" in create_sql
        assert "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" in create_sql
        
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_idempotent_initialization(self):
        """Test that init_master_db can be called multiple times safely."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_master_db()
            init_master_db()
        
        # Should have been called twice without error
        assert mock_conn.execute.call_count == 2
        assert mock_conn.commit.call_count == 2

    def test_closes_connection_on_error(self):
        """Test that connection is closed even if initialization fails."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock(side_effect=sqlite3.OperationalError("disk full"))
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            with pytest.raises(sqlite3.OperationalError):
                init_master_db()
            
            mock_conn.close.assert_called_once()

    def test_table_schema_has_all_required_fields(self):
        """Test that all expected fields are in the schema."""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_master_db()
        
        create_sql = mock_conn.execute.call_args[0][0]
        
        # Verify all required fields
        required_fields = ["code", "name", "role", "project_id", "created_at"]
        for field in required_fields:
            assert field in create_sql


class TestSchemaEdgeCases:
    """Tests for edge cases in schema initialization."""

    def test_empty_schema_file(self, tmp_path):
        """Test handling of empty schema file."""
        schema_path = tmp_path / "empty_schema.sql"
        schema_path.write_text("")
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.executescript = Mock()
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            # Should not raise error
            init_skill_schema("test_skill", schema_path)
        
        # Should still attempt to execute (even if empty)
        mock_conn.executescript.assert_called_once()

    def test_schema_with_comments_only(self, tmp_path):
        """Test schema file with only SQL comments."""
        schema_sql = """
        -- This is a comment
        /* Multi-line
           comment */
        """
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text(schema_sql)
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.executescript = Mock()
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_skill_schema("test_skill", schema_path)
        
        # Should execute without error
        mock_conn.executescript.assert_called_once()

    def test_unicode_in_schema_file(self, tmp_path):
        """Test that Unicode characters in schema are handled correctly."""
        schema_sql = """
        CREATE TABLE test (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT  -- Can contain émojis 🎉 and ütf-8
        );
        """
        schema_path = tmp_path / "schema.sql"
        schema_path.write_text(schema_sql, encoding="utf-8")
        
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_conn.executescript = Mock()
        mock_conn.execute = Mock()
        mock_conn.commit = Mock()
        mock_conn.close = Mock()
        
        with patch("glorious_agents.core.db.schema.get_connection", return_value=mock_conn):
            init_skill_schema("test_skill", schema_path)
        
        mock_conn.executescript.assert_called_once()
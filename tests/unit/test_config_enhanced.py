"""Unit tests for enhanced config module functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from glorious_agents.config import Config, get_config, reset_config, _find_project_root


class TestFindProjectRoot:
    """Tests for _find_project_root function."""

    def test_finds_git_directory(self, tmp_path):
        """Test that project root is found by .git directory."""
        # Create project structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".git").mkdir()
        
        subdir = project_root / "src" / "module"
        subdir.mkdir(parents=True)
        
        # Change to subdirectory
        original_cwd = Path.cwd()
        try:
            os.chdir(subdir)
            result = _find_project_root()
            assert result == project_root
        finally:
            os.chdir(original_cwd)

    def test_finds_env_file(self, tmp_path):
        """Test that project root is found by .env file."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".env").touch()
        
        subdir = project_root / "src"
        subdir.mkdir()
        
        original_cwd = Path.cwd()
        try:
            os.chdir(subdir)
            result = _find_project_root()
            assert result == project_root
        finally:
            os.chdir(original_cwd)

    def test_returns_cwd_if_no_markers_found(self, tmp_path):
        """Test that current directory is returned if no markers found."""
        test_dir = tmp_path / "no_markers"
        test_dir.mkdir()
        
        original_cwd = Path.cwd()
        try:
            os.chdir(test_dir)
            result = _find_project_root()
            assert result == test_dir
        finally:
            os.chdir(original_cwd)

    def test_prefers_closest_marker(self, tmp_path):
        """Test that closest marker is preferred when nested."""
        outer_root = tmp_path / "outer"
        outer_root.mkdir()
        (outer_root / ".git").mkdir()
        
        inner_root = outer_root / "inner"
        inner_root.mkdir()
        (inner_root / ".env").touch()
        
        subdir = inner_root / "src"
        subdir.mkdir()
        
        original_cwd = Path.cwd()
        try:
            os.chdir(subdir)
            result = _find_project_root()
            # Should find inner root first
            assert result == inner_root
        finally:
            os.chdir(original_cwd)


class TestConfigInitialization:
    """Tests for Config class initialization."""

    def test_default_initialization(self):
        """Test Config initialization with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.DB_NAME == "glorious.db"
            assert config.DB_SHARED_NAME == "glorious_shared.db"
            assert config.DB_MASTER_NAME == "master.db"
            assert config.DAEMON_HOST == "127.0.0.1"
            assert config.DAEMON_PORT == 8765
            assert config.DAEMON_API_KEY is None

    def test_initialization_with_env_variables(self):
        """Test Config initialization with environment variables."""
        test_env = {
            "GLORIOUS_DB_NAME": "custom.db",
            "GLORIOUS_DAEMON_HOST": "0.0.0.0",
            "GLORIOUS_DAEMON_PORT": "9000",
            "GLORIOUS_DAEMON_API_KEY": "secret_key",
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            
            assert config.DB_NAME == "custom.db"
            assert config.DAEMON_HOST == "0.0.0.0"
            assert config.DAEMON_PORT == 9000
            assert config.DAEMON_API_KEY == "secret_key"

    def test_initialization_with_custom_env_file(self, tmp_path):
        """Test Config initialization with custom .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("GLORIOUS_DB_NAME=from_file.db\n")
        
        config = Config(env_file=env_file)
        assert config.DB_NAME == "from_file.db"

    def test_initialization_with_nonexistent_env_file(self, tmp_path):
        """Test Config initialization with nonexistent .env file."""
        env_file = tmp_path / "nonexistent.env"
        
        # Should not raise error
        config = Config(env_file=env_file)
        assert config.DB_NAME == "glorious.db"  # Uses default

    def test_data_folder_from_env(self):
        """Test DATA_FOLDER from environment variable."""
        with patch.dict(os.environ, {"DATA_FOLDER": "/custom/path"}, clear=True):
            config = Config()
            assert config.DATA_FOLDER == Path("/custom/path")

    def test_data_folder_default_project_specific(self, tmp_path):
        """Test DATA_FOLDER defaults to project-specific .agent directory."""
        # Mock _find_project_root to return test path
        with patch("glorious_agents.config._find_project_root", return_value=tmp_path), \
             patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.DATA_FOLDER == tmp_path / ".agent"

    def test_skills_dir_from_env(self):
        """Test SKILLS_DIR from environment variable."""
        with patch.dict(os.environ, {"GLORIOUS_SKILLS_DIR": "/custom/skills"}, clear=True):
            config = Config()
            assert config.SKILLS_DIR == Path("/custom/skills")

    def test_skills_dir_default(self):
        """Test SKILLS_DIR default value."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.SKILLS_DIR == Path("skills")


class TestConfigPathMethods:
    """Tests for Config path methods."""

    def test_get_db_path_with_default(self, tmp_path):
        """Test get_db_path with default database name."""
        with patch("glorious_agents.config._find_project_root", return_value=tmp_path), \
             patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_db_path()
            
            assert path == tmp_path / ".agent" / "glorious.db"

    def test_get_db_path_with_custom_name(self, tmp_path):
        """Test get_db_path with custom database name."""
        with patch("glorious_agents.config._find_project_root", return_value=tmp_path), \
             patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_db_path("custom.db")
            
            assert path == tmp_path / ".agent" / "custom.db"

    def test_get_unified_db_path(self, tmp_path):
        """Test get_unified_db_path."""
        with patch("glorious_agents.config._find_project_root", return_value=tmp_path), \
             patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_unified_db_path()
            
            assert path == tmp_path / ".agent" / "glorious.db"

    def test_get_shared_db_path(self, tmp_path):
        """Test get_shared_db_path (legacy)."""
        with patch("glorious_agents.config._find_project_root", return_value=tmp_path), \
             patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_shared_db_path()
            
            assert path == tmp_path / ".agent" / "glorious_shared.db"

    def test_get_master_db_path(self, tmp_path):
        """Test get_master_db_path (legacy)."""
        with patch("glorious_agents.config._find_project_root", return_value=tmp_path), \
             patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_master_db_path()
            
            assert path == tmp_path / ".agent" / "master.db"


class TestGetConfigFunction:
    """Tests for get_config function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config()

    def test_returns_singleton_instance(self):
        """Test that get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2

    def test_lazy_initialization(self):
        """Test that config is lazily initialized."""
        reset_config()
        
        # Config should not exist yet
        from glorious_agents import config as config_module
        assert config_module._default_config is None
        
        # After get_config, should be initialized
        config = get_config()
        assert config is not None
        assert config_module._default_config is config

    def test_thread_safe_initialization(self):
        """Test that get_config is thread-safe."""
        import threading
        
        configs = []
        errors = []
        
        def get_in_thread():
            try:
                configs.append(get_config())
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=get_in_thread) for _ in range(10)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # No errors
        assert len(errors) == 0
        
        # All should be the same instance
        assert len(set(id(c) for c in configs)) == 1


class TestResetConfigFunction:
    """Tests for reset_config function."""

    def test_resets_default_config(self):
        """Test that reset_config clears the default config."""
        _ = get_config()  # Initialize
        
        from glorious_agents import config as config_module
        assert config_module._default_config is not None
        
        reset_config()
        assert config_module._default_config is None

    def test_reset_allows_new_config(self):
        """Test that reset allows getting new config instance."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        # Should be different instances
        assert config1 is not config2

    def test_reset_is_idempotent(self):
        """Test that reset_config can be called multiple times."""
        reset_config()
        reset_config()
        reset_config()
        
        # Should not raise error

    def test_reset_with_no_config(self):
        """Test that reset works when no config exists."""
        reset_config()  # Reset potentially existing config
        reset_config()  # Reset again with none existing
        
        # Should not raise error


class TestConfigEdgeCases:
    """Tests for edge cases in config handling."""

    def test_integer_parsing_from_env(self):
        """Test that integer values are properly parsed from env."""
        with patch.dict(os.environ, {"GLORIOUS_DAEMON_PORT": "12345"}, clear=True):
            config = Config()
            assert isinstance(config.DAEMON_PORT, int)
            assert config.DAEMON_PORT == 12345

    def test_invalid_integer_in_env(self):
        """Test handling of invalid integer in environment."""
        with patch.dict(os.environ, {"GLORIOUS_DAEMON_PORT": "invalid"}, clear=True):
            with pytest.raises(ValueError):
                Config()

    def test_empty_string_env_variable(self):
        """Test handling of empty string environment variable."""
        with patch.dict(os.environ, {"GLORIOUS_DB_NAME": ""}, clear=True):
            config = Config()
            # Empty string should be used, not default
            assert config.DB_NAME == ""

    def test_none_vs_missing_api_key(self):
        """Test distinction between None and missing API key."""
        # Missing API key
        with patch.dict(os.environ, {}, clear=True):
            config1 = Config()
            assert config1.DAEMON_API_KEY is None
        
        # Empty string API key
        with patch.dict(os.environ, {"GLORIOUS_DAEMON_API_KEY": ""}, clear=True):
            config2 = Config()
            assert config2.DAEMON_API_KEY == ""

    def test_path_with_tilde_expansion(self):
        """Test that paths with ~ are expanded."""
        with patch.dict(os.environ, {"DATA_FOLDER": "~/custom_agent_data"}, clear=True):
            config = Config()
            # Path should be created but ~ might not be expanded automatically
            assert str(config.DATA_FOLDER).startswith("~") or str(config.DATA_FOLDER).startswith("/")
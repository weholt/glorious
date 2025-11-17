"""Tests for configuration."""

from pathlib import Path

import pytest

from glorious_agents.config import Config


class TestConfig:
    def test_default_values(self):
        """Test that config has default values."""
        config = Config()

        assert config.DATA_FOLDER is not None
        assert config.SKILLS_DIR is not None
        assert isinstance(config.DATA_FOLDER, Path)
        assert isinstance(config.SKILLS_DIR, Path)

    def test_shared_db_path_property(self):
        """Test get_shared_db_path."""
        config = Config()
        db_path = config.get_shared_db_path()

        assert db_path.name == "glorious_shared.db"
        assert isinstance(db_path, Path)

    def test_skills_dir_property(self):
        """Test SKILLS_DIR property."""
        config = Config()
        skills_dir = config.SKILLS_DIR

        assert skills_dir.name == "skills"

    def test_data_folder_property(self):
        """Test DATA_FOLDER property."""
        config = Config()
        data_folder = config.DATA_FOLDER

        assert data_folder is not None
        assert isinstance(data_folder, Path)

    def test_master_db_path(self):
        """Test get_master_db_path."""
        config = Config()
        db_path = config.get_master_db_path()

        assert db_path.name == "master.db"
        assert isinstance(db_path, Path)

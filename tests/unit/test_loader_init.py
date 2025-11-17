"""Tests for skill initialization."""

import tempfile
from pathlib import Path

import pytest

from glorious_agents.core.loader.initialization import init_schemas


class TestInitSchemas:
    def test_init_schemas_no_schema_file(self):
        """Test init_schemas when skills have no schema_file."""
        skills_data = {
            "skill1": {
                "name": "skill1",
                "version": "1.0.0",
                # No schema_file
            }
        }

        # Should not raise error
        init_schemas(["skill1"], skills_data)

    def test_init_schemas_no_path(self):
        """Test init_schemas when skill has no _path."""
        skills_data = {
            "skill1": {
                "name": "skill1",
                "version": "1.0.0",
                "schema_file": "schema.sql",
                # No _path
            }
        }

        # Should log warning and skip
        init_schemas(["skill1"], skills_data)

    def test_init_schemas_nonexistent_file(self):
        """Test init_schemas when schema file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skill1"
            skill_path.mkdir()

            skills_data = {
                "skill1": {
                    "name": "skill1",
                    "version": "1.0.0",
                    "schema_file": "nonexistent.sql",
                    "_path": skill_path,
                }
            }

            # Should log debug and skip
            init_schemas(["skill1"], skills_data)

    def test_init_schemas_with_valid_schema(self):
        """Test init_schemas with valid schema file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "skill1"
            skill_path.mkdir()

            schema_file = skill_path / "schema.sql"
            schema_file.write_text("CREATE TABLE test (id INTEGER PRIMARY KEY);")

            skills_data = {
                "skill1": {
                    "name": "skill1",
                    "version": "1.0.0",
                    "schema_file": "schema.sql",
                    "_path": skill_path,
                }
            }

            # Should execute without error
            init_schemas(["skill1"], skills_data)

    def test_init_schemas_multiple_skills(self):
        """Test init_schemas with multiple skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_data = {}

            for i in range(3):
                skill_path = Path(tmpdir) / f"skill{i}"
                skill_path.mkdir()

                if i == 0:
                    # First skill has schema
                    schema_file = skill_path / "schema.sql"
                    schema_file.write_text(f"CREATE TABLE IF NOT EXISTS test{i} (id INTEGER);")
                    skills_data[f"skill{i}"] = {
                        "name": f"skill{i}",
                        "schema_file": "schema.sql",
                        "_path": skill_path,
                    }
                else:
                    # Other skills have no schema
                    skills_data[f"skill{i}"] = {
                        "name": f"skill{i}",
                        "_path": skill_path,
                    }

            # Should handle mixed scenarios
            init_schemas(["skill0", "skill1", "skill2"], skills_data)

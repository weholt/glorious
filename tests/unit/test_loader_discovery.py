"""Tests for skill discovery."""

import json
import tempfile
from pathlib import Path

import pytest

from glorious_agents.core.loader.discovery import (
    discover_entrypoint_skills,
    discover_local_skills,
)


class TestDiscoverLocalSkills:
    def test_discover_no_skills_dir(self):
        """Test discovery when skills directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent"
            skills = discover_local_skills(nonexistent)
            assert skills == {}

    def test_discover_empty_skills_dir(self):
        """Test discovery with empty skills directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skills = discover_local_skills(skills_dir)
            assert skills == {}

    def test_discover_skill_without_manifest(self):
        """Test that skills without manifest are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "test_skill"
            skill_dir.mkdir()

            skills = discover_local_skills(skills_dir)
            assert skills == {}

    def test_discover_valid_skill(self):
        """Test discovering a valid skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "test_skill"
            skill_dir.mkdir()

            manifest = {
                "name": "test_skill",
                "version": "1.0.0",
                "description": "Test skill",
                "entry_point": "test_skill.skill:app",
            }
            (skill_dir / "skill.json").write_text(json.dumps(manifest))

            skills = discover_local_skills(skills_dir)

            assert "test_skill" in skills
            assert skills["test_skill"]["name"] == "test_skill"
            assert skills["test_skill"]["_origin"] == "local"

    def test_discover_skill_with_invalid_json(self):
        """Test that invalid JSON is skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "bad_skill"
            skill_dir.mkdir()

            (skill_dir / "skill.json").write_text("not json")

            skills = discover_local_skills(skills_dir)
            assert skills == {}

    def test_discover_skill_with_missing_required_field(self):
        """Test that manifests with missing required fields are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "incomplete_skill"
            skill_dir.mkdir()

            manifest = {
                "name": "incomplete_skill",
                # Missing version, description, entry_point
            }
            (skill_dir / "skill.json").write_text(json.dumps(manifest))

            skills = discover_local_skills(skills_dir)
            assert skills == {}

    def test_discover_skill_ignores_files(self):
        """Test that files in skills directory are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)

            # Create a file (not a directory)
            (skills_dir / "not_a_skill.txt").write_text("test")

            skills = discover_local_skills(skills_dir)
            assert skills == {}

    def test_discover_multiple_skills(self):
        """Test discovering multiple skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)

            for i in range(3):
                skill_dir = skills_dir / f"skill{i}"
                skill_dir.mkdir()
                manifest = {
                    "name": f"skill{i}",
                    "version": "1.0.0",
                    "description": f"Skill {i}",
                    "entry_point": f"skill{i}.skill:app",
                }
                (skill_dir / "skill.json").write_text(json.dumps(manifest))

            skills = discover_local_skills(skills_dir)

            assert len(skills) == 3
            assert "skill0" in skills
            assert "skill1" in skills
            assert "skill2" in skills


    def test_discover_skill_with_requires_dict(self):
        """Test discovering a skill with requires as dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "test_skill"
            skill_dir.mkdir()

            manifest = {
                "name": "test_skill",
                "version": "1.0.0",
                "description": "Test skill",
                "entry_point": "test_skill.skill:app",
                "requires": {"skill_a": ">=1.0.0", "skill_b": "^2.0.0"},
            }
            (skill_dir / "skill.json").write_text(json.dumps(manifest))

            skills = discover_local_skills(skills_dir)

            assert "test_skill" in skills
            assert isinstance(skills["test_skill"]["requires"], dict)

    def test_discover_skill_with_requires_list(self):
        """Test discovering a skill with requires as list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "test_skill"
            skill_dir.mkdir()

            manifest = {
                "name": "test_skill",
                "version": "1.0.0",
                "description": "Test skill",
                "entry_point": "test_skill.skill:app",
                "requires": ["skill_a", "skill_b"],
            }
            (skill_dir / "skill.json").write_text(json.dumps(manifest))

            skills = discover_local_skills(skills_dir)

            assert "test_skill" in skills
            assert isinstance(skills["test_skill"]["requires"], list)

    def test_discover_skill_with_config_schema(self):
        """Test discovering a skill with config_schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "test_skill"
            skill_dir.mkdir()

            manifest = {
                "name": "test_skill",
                "version": "1.0.0",
                "description": "Test skill",
                "entry_point": "test_skill.skill:app",
                "config_schema": {
                    "properties": {
                        "api_key": {"type": "string"},
                        "timeout": {"type": "integer"},
                    }
                },
            }
            (skill_dir / "skill.json").write_text(json.dumps(manifest))

            skills = discover_local_skills(skills_dir)

            assert "test_skill" in skills
            assert "config_schema" in skills["test_skill"]

    def test_discover_skill_with_all_optional_fields(self):
        """Test discovering a skill with all optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_dir = skills_dir / "test_skill"
            skill_dir.mkdir()

            manifest = {
                "name": "test_skill",
                "version": "1.0.0",
                "description": "Test skill",
                "entry_point": "test_skill.skill:app",
                "schema_file": "schema.sql",
                "requires": ["dep1"],
                "requires_db": False,
                "internal_doc": "internal.md",
                "external_doc": "external.md",
                "config_schema": {"key": {"type": "string"}},
            }
            (skill_dir / "skill.json").write_text(json.dumps(manifest))

            skills = discover_local_skills(skills_dir)

            assert "test_skill" in skills
            skill = skills["test_skill"]
            assert skill["schema_file"] == "schema.sql"
            assert skill["requires"] == ["dep1"]
            assert skill["requires_db"] is False
            assert skill["internal_doc"] == "internal.md"
            assert skill["external_doc"] == "external.md"


class TestDiscoverEntrypointSkills:
    def test_discover_entrypoint_skills_no_group(self):
        """Test discovering entry point skills with non-existent group."""
        skills = discover_entrypoint_skills(group="nonexistent.group")
        # Should return empty dict or handle gracefully
        assert isinstance(skills, dict)

    def test_discover_entrypoint_skills_default_group(self):
        """Test discovering entry point skills with default group."""
        # This will discover any installed entry points
        skills = discover_entrypoint_skills()

        # Should return a dict (may be empty if no skills installed)
        assert isinstance(skills, dict)

        # If skills are found, they should have required fields
        for skill_name, manifest in skills.items():
            assert "name" in manifest
            assert "entry_point" in manifest
            assert manifest["_origin"] == "entrypoint"

    def test_discover_entrypoint_skills_with_manifest(self):
        """Test discovering entry point skill that has skill.json."""
        from unittest.mock import MagicMock, patch

        # Mock entry point
        mock_ep = MagicMock()
        mock_ep.name = "test_skill"
        mock_ep.value = "test_module.skill:app"

        # Mock module with __file__
        mock_module = MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            module_dir = Path(tmpdir)
            mock_module.__file__ = str(module_dir / "skill.py")

            # Create skill.json in module directory
            manifest = {
                "version": "2.0.0",
                "description": "From manifest",
                "requires": ["dep1"],
            }
            (module_dir / "skill.json").write_text(json.dumps(manifest))

            with (
                patch("glorious_agents.core.loader.discovery.entry_points", return_value=[mock_ep]),
                patch("glorious_agents.core.loader.discovery.importlib.import_module", return_value=mock_module),
            ):
                skills = discover_entrypoint_skills()

                assert "test_skill" in skills
                assert skills["test_skill"]["version"] == "2.0.0"
                assert skills["test_skill"]["description"] == "From manifest"
                # Entry point value should be preserved
                assert skills["test_skill"]["entry_point"] == "test_module.skill:app"



    def test_discover_entrypoint_skills_validation_error(self):
        """Test discovering entry point skill with validation errors."""
        from unittest.mock import MagicMock, patch

        mock_ep = MagicMock()
        mock_ep.name = "test_skill"
        mock_ep.value = "test_module.skill:app"

        # Create mock entry point that will fail validation
        with (
            patch("glorious_agents.core.loader.discovery.entry_points", return_value=[mock_ep]),
            patch("glorious_agents.core.loader.discovery.SkillManifest", side_effect=ValueError("Invalid")),
        ):
            skills = discover_entrypoint_skills()

            # Should handle validation error and skip the skill
            assert len(skills) == 0 or "test_skill" not in skills

    def test_discover_entrypoint_skills_with_config_schema_properties(self):
        """Test discovering entry point skill with config_schema."""
        from unittest.mock import MagicMock, patch

        mock_ep = MagicMock()
        mock_ep.name = "test_skill"
        mock_ep.value = "test_module.skill:app"

        mock_module = MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            module_dir = Path(tmpdir)
            mock_module.__file__ = str(module_dir / "skill.py")

            manifest = {
                "version": "1.0.0",
                "description": "Test",
                "config_schema": {
                    "properties": {
                        "api_key": {"type": "string"}
                    }
                },
            }
            (module_dir / "skill.json").write_text(json.dumps(manifest))

            with (
                patch("glorious_agents.core.loader.discovery.entry_points", return_value=[mock_ep]),
                patch("glorious_agents.core.loader.discovery.importlib.import_module", return_value=mock_module),
            ):
                skills = discover_entrypoint_skills()

                assert "test_skill" in skills
                assert "config_schema" in skills["test_skill"]

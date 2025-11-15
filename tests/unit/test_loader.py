"""Unit tests for loader and dependency resolution."""

import json
from pathlib import Path

import pytest

from glorious_agents.core.loader import (
    discover_local_skills,
    resolve_dependencies,
)


@pytest.mark.logic
def test_discover_local_skills_empty(tmp_path: Path) -> None:
    """Test discovery with no skills directory."""
    skills = discover_local_skills(tmp_path / "nonexistent")
    assert len(skills) == 0


@pytest.mark.logic
def test_discover_local_skills(tmp_path: Path) -> None:
    """Test discovery of local skills."""
    # Create test skills
    skills_dir = tmp_path / "skills"
    
    skill1_dir = skills_dir / "skill1"
    skill1_dir.mkdir(parents=True)
    (skill1_dir / "skill.json").write_text(json.dumps({
        "name": "skill1",
        "version": "1.0.0",
        "entry_point": "skill1.skill:app",
        "requires": []
    }))
    
    skill2_dir = skills_dir / "skill2"
    skill2_dir.mkdir(parents=True)
    (skill2_dir / "skill.json").write_text(json.dumps({
        "name": "skill2",
        "version": "1.0.0",
        "entry_point": "skill2.skill:app",
        "requires": ["skill1"]
    }))
    
    skills = discover_local_skills(skills_dir)
    
    assert len(skills) == 2
    assert "skill1" in skills
    assert "skill2" in skills
    assert skills["skill1"]["_origin"] == "local"


@pytest.mark.logic
def test_resolve_dependencies_simple() -> None:
    """Test simple dependency resolution."""
    skills = {
        "a": {"name": "a", "requires": []},
        "b": {"name": "b", "requires": ["a"]},
        "c": {"name": "c", "requires": ["b"]},
    }
    
    order = resolve_dependencies(skills)
    
    # Dependencies should be loaded first
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


@pytest.mark.logic
def test_resolve_dependencies_missing() -> None:
    """Test error on missing dependency."""
    skills = {
        "a": {"name": "a", "requires": ["nonexistent"]},
    }
    
    with pytest.raises(ValueError, match="missing skill"):
        resolve_dependencies(skills)


@pytest.mark.logic
def test_resolve_dependencies_circular() -> None:
    """Test error on circular dependency."""
    skills = {
        "a": {"name": "a", "requires": ["b"]},
        "b": {"name": "b", "requires": ["a"]},
    }
    
    with pytest.raises(ValueError, match="Circular dependency"):
        resolve_dependencies(skills)


@pytest.mark.logic
def test_resolve_dependencies_complex() -> None:
    """Test complex dependency graph."""
    skills = {
        "a": {"name": "a", "requires": []},
        "b": {"name": "b", "requires": ["a"]},
        "c": {"name": "c", "requires": ["a"]},
        "d": {"name": "d", "requires": ["b", "c"]},
    }
    
    order = resolve_dependencies(skills)
    
    # Check all dependencies
    assert order.index("a") < order.index("b")
    assert order.index("a") < order.index("c")
    assert order.index("b") < order.index("d")
    assert order.index("c") < order.index("d")


@pytest.mark.logic
def test_discover_local_skills_invalid_json(tmp_path: Path) -> None:
    """Test handling of invalid JSON in skill manifest."""
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "bad_skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "skill.json").write_text("{ invalid json }")
    
    # Should skip invalid skills gracefully
    skills = discover_local_skills(skills_dir)
    assert len(skills) == 0


@pytest.mark.logic
def test_discover_local_skills_missing_fields(tmp_path: Path) -> None:
    """Test handling of manifest with missing required fields."""
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "incomplete_skill"
    skill_dir.mkdir(parents=True)
    
    # Missing required fields (should fail validation)
    (skill_dir / "skill.json").write_text(json.dumps({
        "name": "incomplete"
        # Missing version, entry_point, etc.
    }))
    
    skills = discover_local_skills(skills_dir)
    # Should be skipped due to validation failure
    assert len(skills) == 0


@pytest.mark.logic
def test_discover_local_skills_invalid_entry_point_format(tmp_path: Path) -> None:
    """Test validation of entry_point format."""
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "bad_entrypoint"
    skill_dir.mkdir(parents=True)
    
    # Invalid entry_point format (missing colon)
    (skill_dir / "skill.json").write_text(json.dumps({
        "name": "bad",
        "version": "1.0.0",
        "description": "Test",
        "entry_point": "invalid_format_no_colon",
        "requires": []
    }))
    
    skills = discover_local_skills(skills_dir)
    # Should fail Pydantic validation
    assert len(skills) == 0


@pytest.mark.logic
def test_discover_local_skills_invalid_version(tmp_path: Path) -> None:
    """Test validation of semantic version format."""
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "bad_version"
    skill_dir.mkdir(parents=True)
    
    # Invalid version format
    (skill_dir / "skill.json").write_text(json.dumps({
        "name": "bad",
        "version": "not-a-version",
        "description": "Test",
        "entry_point": "test:app",
        "requires": []
    }))
    
    skills = discover_local_skills(skills_dir)
    # Should fail Pydantic validation
    assert len(skills) == 0


@pytest.mark.logic
def test_resolve_dependencies_self_reference() -> None:
    """Test error when skill depends on itself."""
    skills = {
        "a": {"name": "a", "requires": ["a"]},
    }
    
    with pytest.raises(ValueError, match="Circular dependency"):
        resolve_dependencies(skills)


@pytest.mark.logic
def test_resolve_dependencies_empty() -> None:
    """Test resolving empty skill set."""
    skills = {}
    order = resolve_dependencies(skills)
    assert order == []


@pytest.mark.logic
def test_skill_init_function() -> None:
    """Test that skill init() function behavior is correct."""
    from unittest.mock import MagicMock, patch
    from glorious_agents.core.loader import _call_skill_init
    
    # Test skill with init() that succeeds
    mock_module_success = MagicMock()
    mock_module_success.init = MagicMock()
    
    with patch("importlib.import_module", return_value=mock_module_success):
        # Should call init() without raising
        _call_skill_init("test_skill", "test.module:app", False)
        mock_module_success.init.assert_called_once()
    
    # Test skill with init() that fails
    mock_module_fail = MagicMock()
    mock_module_fail.init = MagicMock(side_effect=RuntimeError("Required API key not found"))
    
    with patch("importlib.import_module", return_value=mock_module_fail):
        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="init\\(\\) failed"):
            _call_skill_init("test_skill", "test.module:app", False)
    
    # Test skill without init() function
    mock_module_no_init = MagicMock(spec=[])  # No init attribute
    
    with patch("importlib.import_module", return_value=mock_module_no_init):
        # Should complete without error
        _call_skill_init("test_skill", "test.module:app", False)

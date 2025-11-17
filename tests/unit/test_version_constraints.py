"""Tests for version constraint parsing and checking."""

import pytest

from glorious_agents.core.loader import check_version_constraint, parse_version


def test_parse_version_valid() -> None:
    """Test parsing valid semantic versions."""
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("0.0.1") == (0, 0, 1)
    assert parse_version("10.20.30") == (10, 20, 30)
    assert parse_version("1.2.3-alpha") == (1, 2, 3)  # Ignores pre-release
    assert parse_version("2.0.0-beta.1") == (2, 0, 0)


def test_parse_version_invalid() -> None:
    """Test parsing invalid version strings raises ValueError."""
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_version("1.2")
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_version("invalid")
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_version("1")


def test_check_version_constraint_exact() -> None:
    """Test exact version matching."""
    assert check_version_constraint("1.2.3", "1.2.3")
    assert check_version_constraint("1.2.3", "==1.2.3")
    assert not check_version_constraint("1.2.3", "1.2.4")
    assert not check_version_constraint("1.2.3", "==1.2.4")


def test_check_version_constraint_greater_equal() -> None:
    """Test >= constraint."""
    assert check_version_constraint("1.2.3", ">=1.2.3")
    assert check_version_constraint("1.2.4", ">=1.2.3")
    assert check_version_constraint("2.0.0", ">=1.2.3")
    assert not check_version_constraint("1.2.2", ">=1.2.3")
    assert not check_version_constraint("1.1.9", ">=1.2.3")


def test_check_version_constraint_less_equal() -> None:
    """Test <= constraint."""
    assert check_version_constraint("1.2.3", "<=1.2.3")
    assert check_version_constraint("1.2.2", "<=1.2.3")
    assert check_version_constraint("1.0.0", "<=1.2.3")
    assert not check_version_constraint("1.2.4", "<=1.2.3")
    assert not check_version_constraint("2.0.0", "<=1.2.3")


def test_check_version_constraint_greater() -> None:
    """Test > constraint."""
    assert check_version_constraint("1.2.4", ">1.2.3")
    assert check_version_constraint("2.0.0", ">1.2.3")
    assert not check_version_constraint("1.2.3", ">1.2.3")
    assert not check_version_constraint("1.2.2", ">1.2.3")


def test_check_version_constraint_less() -> None:
    """Test < constraint."""
    assert check_version_constraint("1.2.2", "<1.2.3")
    assert check_version_constraint("1.0.0", "<1.2.3")
    assert not check_version_constraint("1.2.3", "<1.2.3")
    assert not check_version_constraint("1.2.4", "<1.2.3")


def test_check_version_constraint_caret() -> None:
    """Test ^ (caret) constraint - allows changes that don't modify left-most non-zero."""
    # ^1.2.3 allows >=1.2.3 <2.0.0
    assert check_version_constraint("1.2.3", "^1.2.3")
    assert check_version_constraint("1.2.4", "^1.2.3")
    assert check_version_constraint("1.9.9", "^1.2.3")
    assert not check_version_constraint("2.0.0", "^1.2.3")
    assert not check_version_constraint("1.2.2", "^1.2.3")

    # ^0.2.3 allows >=0.2.3 <0.3.0
    assert check_version_constraint("0.2.3", "^0.2.3")
    assert check_version_constraint("0.2.4", "^0.2.3")
    assert not check_version_constraint("0.3.0", "^0.2.3")
    assert not check_version_constraint("0.2.2", "^0.2.3")

    # ^0.0.3 allows exactly 0.0.3
    assert check_version_constraint("0.0.3", "^0.0.3")
    assert not check_version_constraint("0.0.4", "^0.0.3")
    assert not check_version_constraint("0.0.2", "^0.0.3")


def test_check_version_constraint_tilde() -> None:
    """Test ~ (tilde) constraint - allows patch-level changes."""
    # ~1.2.3 allows >=1.2.3 <1.3.0
    assert check_version_constraint("1.2.3", "~1.2.3")
    assert check_version_constraint("1.2.4", "~1.2.3")
    assert check_version_constraint("1.2.9", "~1.2.3")
    assert not check_version_constraint("1.3.0", "~1.2.3")
    assert not check_version_constraint("1.2.2", "~1.2.3")
    assert not check_version_constraint("2.0.0", "~1.2.3")


def test_resolve_dependencies_with_version_constraints(tmp_path):
    """Test dependency resolution with version constraints."""
    from glorious_agents.core.loader import resolve_dependencies

    # Test with dict-style version constraints
    skills_data = {
        "skill_a": {"version": "1.0.0", "requires": {}},
        "skill_b": {"version": "2.5.0", "requires": {"skill_a": ">=1.0.0"}},
        "skill_c": {"version": "1.0.0", "requires": {"skill_b": "^2.0.0"}},
    }

    result = resolve_dependencies(skills_data)
    assert "skill_a" in result
    assert "skill_b" in result
    assert "skill_c" in result
    assert result.index("skill_a") < result.index("skill_b")
    assert result.index("skill_b") < result.index("skill_c")


def test_resolve_dependencies_version_mismatch(tmp_path):
    """Test dependency resolution fails on version mismatch."""
    from glorious_agents.core.loader import resolve_dependencies

    # skill_b requires skill_a >= 2.0.0 but only 1.0.0 is available
    skills_data = {
        "skill_a": {"version": "1.0.0", "requires": {}},
        "skill_b": {"version": "1.0.0", "requires": {"skill_a": ">=2.0.0"}},
    }

    with pytest.raises(ValueError, match="requires 'skill_a' >=2.0.0 but found 1.0.0"):
        resolve_dependencies(skills_data)


def test_resolve_dependencies_missing_with_version(tmp_path):
    """Test dependency resolution fails when versioned dependency is missing."""
    from glorious_agents.core.loader import resolve_dependencies

    skills_data = {
        "skill_b": {"version": "1.0.0", "requires": {"skill_a": ">=1.0.0"}},
    }

    with pytest.raises(ValueError, match="'skill_a' >=1.0.0 but 'skill_a' is not installed"):
        resolve_dependencies(skills_data)


def test_resolve_dependencies_mixed_constraints(tmp_path):
    """Test dependency resolution with mixed list and dict constraints."""
    from glorious_agents.core.loader import resolve_dependencies

    # Some skills use list, others use dict
    skills_data = {
        "skill_a": {"version": "1.0.0", "requires": []},
        "skill_b": {"version": "2.0.0", "requires": ["skill_a"]},  # List format
        "skill_c": {"version": "1.0.0", "requires": {"skill_b": "^2.0.0"}},  # Dict format
    }

    result = resolve_dependencies(skills_data)
    assert len(result) == 3
    assert result.index("skill_a") < result.index("skill_b")
    assert result.index("skill_b") < result.index("skill_c")

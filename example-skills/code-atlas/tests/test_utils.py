"""Tests for utility functions."""

from pathlib import Path

import pytest

from code_atlas.utils import (
    DEFAULT_IGNORE_PATTERNS,
    SafeExpressionEvaluator,
    find_test_file,
    get_avg_complexity,
)


def test_get_avg_complexity_with_data() -> None:
    """Test average complexity calculation with data."""
    file_data = {
        "complexity": [
            {"complexity": 5},
            {"complexity": 10},
            {"complexity": 15},
        ]
    }
    result = get_avg_complexity(file_data)
    assert result == 10.0


def test_get_avg_complexity_empty() -> None:
    """Test average complexity with no complexity data."""
    file_data = {"complexity": []}
    result = get_avg_complexity(file_data)
    assert result == 0.0


def test_get_avg_complexity_missing_key() -> None:
    """Test average complexity with missing complexity key."""
    file_data: dict = {}
    result = get_avg_complexity(file_data)
    assert result == 0.0


def test_safe_expression_evaluator_arithmetic() -> None:
    """Test safe evaluator with arithmetic operations."""
    context = {"x": 10, "y": 5}
    evaluator = SafeExpressionEvaluator(context)

    assert evaluator.eval("x + y") == 15
    assert evaluator.eval("x - y") == 5
    assert evaluator.eval("x * y") == 50
    assert evaluator.eval("x / y") == 2.0


def test_safe_expression_evaluator_comparisons() -> None:
    """Test safe evaluator with comparison operations."""
    context = {"x": 10, "y": 5}
    evaluator = SafeExpressionEvaluator(context)

    assert evaluator.eval("x > y") is True
    assert evaluator.eval("x < y") is False
    assert evaluator.eval("x >= 10") is True
    assert evaluator.eval("x <= 10") is True
    assert evaluator.eval("x == 10") is True
    assert evaluator.eval("x != y") is True


def test_safe_expression_evaluator_boolean_ops() -> None:
    """Test safe evaluator with boolean operations."""
    context = {"x": 10, "y": 5, "z": 15}
    evaluator = SafeExpressionEvaluator(context)

    assert evaluator.eval("x > y and y < z") is True
    assert evaluator.eval("x > y or y > z") is True
    assert evaluator.eval("not (x < y)") is True


def test_safe_expression_evaluator_invalid_variable() -> None:
    """Test safe evaluator with undefined variable."""
    context = {"x": 10}
    evaluator = SafeExpressionEvaluator(context)

    with pytest.raises(ValueError, match="Undefined variable"):
        evaluator.eval("y + 5")


def test_safe_expression_evaluator_invalid_syntax() -> None:
    """Test safe evaluator with invalid syntax."""
    context = {"x": 10}
    evaluator = SafeExpressionEvaluator(context)

    with pytest.raises(ValueError, match="Failed to evaluate"):
        evaluator.eval("x +")


def test_default_ignore_patterns_exists() -> None:
    """Test that default ignore patterns are defined."""
    assert isinstance(DEFAULT_IGNORE_PATTERNS, set)
    assert ".venv" in DEFAULT_IGNORE_PATTERNS
    assert "__pycache__" in DEFAULT_IGNORE_PATTERNS
    assert ".git" in DEFAULT_IGNORE_PATTERNS


def test_find_test_file_not_found(tmp_path: Path) -> None:
    """Test find_test_file when test doesn't exist."""
    source_file = tmp_path / "module.py"
    source_file.touch()

    result = find_test_file(source_file, tmp_path)
    assert result is False


def test_find_test_file_found_test_prefix(tmp_path: Path) -> None:
    """Test find_test_file with test_ prefix pattern."""
    source_file = tmp_path / "module.py"
    source_file.touch()

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_file = tests_dir / "test_module.py"
    test_file.touch()

    result = find_test_file(source_file, tmp_path)
    assert result is True


def test_find_test_file_found_test_suffix(tmp_path: Path) -> None:
    """Test find_test_file with _test suffix pattern."""
    source_file = tmp_path / "module.py"
    source_file.touch()

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_file = tests_dir / "module_test.py"
    test_file.touch()

    result = find_test_file(source_file, tmp_path)
    assert result is True


def test_find_test_file_src_structure(tmp_path: Path) -> None:
    """Test find_test_file with src/tests directory structure."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    source_file = src_dir / "module.py"
    source_file.touch()

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_file = tests_dir / "test_module.py"
    test_file.touch()

    result = find_test_file(source_file, tmp_path)
    assert result is True

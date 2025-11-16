"""Tests for scanner module."""

import tempfile
from pathlib import Path

from code_atlas.scanner import ASTScanner, scan_directory


def test_scan_file_basic() -> None:
    """Test scanning a simple Python file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text(
            '''def hello() -> str:
    """Say hello."""
    return "hello"

class Greeter:
    """A greeter class."""

    def greet(self, name: str) -> str:
        """Greet someone."""
        return f"Hello, {name}"
''',
            encoding="utf-8",
        )

        scanner = ASTScanner(tmppath)
        result = scanner.scan_file(test_file)

        assert "path" in result
        assert "entities" in result
        assert len(result["entities"]) >= 2


def test_scan_directory() -> None:
    """Test scanning a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        test_file = tmppath / "test.py"
        test_file.write_text("def foo() -> None:\n    pass\n", encoding="utf-8")

        output_file = tmppath / "index.json"
        scan_directory(tmppath, output_file)

        assert output_file.exists()


def test_scan_file_syntax_error() -> None:
    """Test scanning a file with syntax error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "bad.py"
        test_file.write_text("def broken(\n    pass", encoding="utf-8")

        scanner = ASTScanner(tmppath)
        result = scanner.scan_file(test_file)

        assert "error" in result
        assert "SyntaxError" in result["error"]
        assert result["entities"] == []


def test_scan_file_exception_handling() -> None:
    """Test scanning handles other exceptions gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("def foo(): pass", encoding="utf-8")

        scanner = ASTScanner(tmppath)
        # Create a non-existent file path
        result = scanner.scan_file(tmppath / "nonexistent.py")

        assert "error" in result or result["entities"] == []

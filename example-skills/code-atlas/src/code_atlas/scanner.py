"""AST-based code scanner for extracting structure and metrics."""

import ast
import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from code_atlas.ast_extractor import CallVisitor, extract_entities, extract_imports
from code_atlas.dependency_graph import build_dependency_graph
from code_atlas.git_analyzer import extract_git_metadata
from code_atlas.metrics import compute_metrics
from code_atlas.utils import DEFAULT_IGNORE_PATTERNS, find_test_file

# Import optional dependencies for deep analysis
try:
    import mypy.api

    MYPY_AVAILABLE = True
except ImportError:
    MYPY_AVAILABLE = False


class ASTScanner:
    """Handles the scanning process for Python files."""

    def __init__(self, root: Path, ignore_patterns: set[str] | None = None):
        """Initialize scanner with root directory.

        Args:
            root: Root directory to scan
            ignore_patterns: Set of directory/file patterns to ignore (uses defaults if None)
        """
        self.root = root
        self.ignore_patterns = ignore_patterns if ignore_patterns is not None else DEFAULT_IGNORE_PATTERNS

    def scan_file(self, path: Path) -> dict[str, Any]:
        """Scan a single Python file and extract structure and metrics.

        Args:
            path: Path to Python file to scan

        Returns:
            Dictionary containing file analysis data
        """
        try:
            with open(path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(path))
            entities = extract_entities(tree)
            imports = extract_imports(tree)
            complexity_data, raw = compute_metrics(source)
            git_meta = extract_git_metadata(path)

            # Calculate comment ratio
            comment_ratio = raw["comments"] / raw["loc"] if raw["loc"] > 0 else 0.0

            # Check for test file using improved detection
            has_tests = find_test_file(path, self.root)

            return {
                "path": str(path.relative_to(self.root) if path.is_relative_to(self.root) else path),
                "entities": entities,
                "imports": imports,
                "complexity": complexity_data,
                "raw": raw,
                "comment_ratio": round(comment_ratio, 3),
                "git": git_meta,
                "has_tests": has_tests,
            }
        except SyntaxError as e:
            return {
                "path": str(path.relative_to(self.root) if path.is_relative_to(self.root) else path),
                "entities": [],
                "imports": [],
                "complexity": [],
                "raw": {"loc": 0, "sloc": 0, "comments": 0, "multi": 0, "blank": 0},
                "comment_ratio": 0.0,
                "git": {"commits": 0, "last_author": "", "last_commit": ""},
                "has_tests": False,
                "error": f"SyntaxError: {e.msg} at line {e.lineno}",
            }
        except Exception as e:  # noqa: S112
            return {
                "path": str(path.relative_to(self.root) if path.is_relative_to(self.root) else path),
                "entities": [],
                "imports": [],
                "complexity": [],
                "raw": {"loc": 0, "sloc": 0, "comments": 0, "multi": 0, "blank": 0},
                "comment_ratio": 0.0,
                "git": {"commits": 0, "last_author": "", "last_commit": ""},
                "has_tests": False,
                "error": str(e),
            }

    def _deep_analysis(self, path: Path) -> dict[str, Any]:
        """Perform deep analysis on a Python file.

        Args:
            path: Path to Python file

        Returns:
            Deep analysis results including type coverage and call graph
        """
        result: dict[str, Any] = {
            "type_coverage": 0.0,
            "type_errors": 0,
            "call_graph": {},
        }

        # Type coverage analysis with mypy
        if MYPY_AVAILABLE:
            try:
                # Run mypy on single file
                stdout, stderr, exit_code = mypy.api.run([str(path), "--show-error-codes", "--no-error-summary"])

                # Count errors
                error_count = stdout.count("error:")

                # Estimate type coverage (rough heuristic)
                # If no errors and exit_code == 0, assume good coverage
                if exit_code == 0:
                    result["type_coverage"] = 1.0
                else:
                    # Estimate based on error density
                    source = path.read_text(encoding="utf-8")
                    loc = len([line for line in source.splitlines() if line.strip()])
                    if loc > 0:
                        error_ratio = min(error_count / loc, 1.0)
                        result["type_coverage"] = max(0.0, 1.0 - error_ratio)

                result["type_errors"] = error_count

            except Exception:  # noqa: S110, S112
                pass

        # Call graph analysis (simple version - track function calls)
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)

            visitor = CallVisitor()
            visitor.visit(tree)

            result["call_graph"] = visitor.calls

        except Exception:  # noqa: S110, S112
            pass

        return result

    def _collect_python_files(self) -> list[Path]:
        """Collect all Python files, skipping ignored patterns."""
        return [f for f in self.root.rglob("*.py") if not any(ignored in f.parts for ignored in self.ignore_patterns)]

    def _load_existing_index(self) -> dict[str, dict[str, Any]]:
        """Load existing index for incremental updates."""
        index_file = Path("code_index.json")
        if not index_file.exists():
            return {}

        try:
            existing_data = json.loads(index_file.read_text(encoding="utf-8"))
            return {f["path"]: f for f in existing_data.get("files", [])}
        except (json.JSONDecodeError, OSError):
            return {}

    def _process_file(
        self,
        py_file: Path,
        cache: Any,
        existing_files: dict[str, Any],
        deep: bool,
    ) -> tuple[dict[str, Any] | None, bool]:
        """Process a single file. Returns (file_data, was_cached)."""
        # Check if file is unchanged (incremental mode)
        if cache and cache.is_unchanged(py_file):
            rel_path = str(py_file.relative_to(self.root) if py_file.is_relative_to(self.root) else py_file)
            if rel_path in existing_files:
                return existing_files[rel_path], True

        file_data = self.scan_file(py_file)

        # Add deep analysis if requested
        if deep:
            file_data["deep"] = self._deep_analysis(py_file)

        # Update cache
        if cache:
            cache.update_file(py_file)

        return file_data, False

    def _build_symbol_index(self, files: list[dict[str, Any]]) -> dict[str, str]:
        """Build symbol-to-location index."""
        symbol_index: dict[str, str] = {}
        for file_data in files:
            for entity in file_data.get("entities", []):
                symbol_index[entity["name"]] = f"{file_data['path']}:{entity['lineno']}"
        return symbol_index

    def _process_all_files(
        self,
        all_py_files: list[Path],
        cache: Any,
        existing_files: dict[str, Any],
        deep: bool,
        progress_callback: Callable[[str, int, int], None] | None,
    ) -> list[dict[str, Any]]:
        """Process all Python files with progress tracking."""
        files: list[dict[str, Any]] = []
        total_files = len(all_py_files)

        for idx, py_file in enumerate(all_py_files, 1):
            try:
                if progress_callback:
                    rel_path = str(py_file.relative_to(self.root) if py_file.is_relative_to(self.root) else py_file)
                    progress_callback(rel_path, idx, total_files)

                file_data, _ = self._process_file(py_file, cache, existing_files, deep)
                if file_data:
                    files.append(file_data)
            except Exception:  # noqa: S112
                continue

        return files

    def _cleanup_cache(self, cache: Any) -> None:
        """Save and cleanup cache."""
        if cache:
            existing_paths = {str(py_file) for py_file in self.root.rglob("*.py")}
            cache.cleanup(existing_paths)
            cache.save()

    def scan_directory(
        self,
        incremental: bool = False,
        deep: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Scan all Python files in directory recursively.

        Args:
            incremental: Use incremental caching to skip unchanged files
            deep: Enable deep analysis (call graphs, type coverage)
            progress_callback: Optional callback(file_path, current, total) for progress updates

        Returns:
            Complete code_index dict
        """
        from code_atlas.cache import FileCache

        cache = FileCache() if incremental else None
        existing_files = self._load_existing_index() if incremental and cache else {}
        all_py_files = self._collect_python_files()

        files = self._process_all_files(all_py_files, cache, existing_files, deep, progress_callback)
        self._cleanup_cache(cache)

        dependencies = build_dependency_graph(files)
        symbol_index = self._build_symbol_index(files)

        return {
            "scanned_root": str(self.root),
            "scanned_at": datetime.now().isoformat(),
            "version": "0.1.0",
            "total_files": len(files),
            "files": files,
            "dependencies": dependencies,
            "symbol_index": symbol_index,
        }


def scan_directory(
    root_path: Path,
    output_path: Path,
    incremental: bool = False,
    deep: bool = False,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> None:
    """Scan a directory of Python files and write index.

    Args:
        root_path: Root directory to scan
        output_path: Path to write code_index.json
        incremental: Use incremental caching to skip unchanged files
        deep: Enable deep analysis (call graphs, type coverage)
        progress_callback: Optional callback(file_path, current, total) for progress updates

    Raises:
        FileNotFoundError: If root_path does not exist
        ValueError: If root_path is not a directory
    """
    if not root_path.exists():
        raise FileNotFoundError(f"Directory not found: {root_path}")

    if not root_path.is_dir():
        raise ValueError(f"Path is not a directory: {root_path}")

    scanner = ASTScanner(root_path)
    index = scanner.scan_directory(incremental=incremental, deep=deep, progress_callback=progress_callback)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

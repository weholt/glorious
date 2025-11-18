"""Data models for code-atlas skill.

These are simple data structures, not database models.
Code-atlas uses file-based storage (code_index.json) rather than a database.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Entity:
    """Represents a code entity (function, class, method)."""

    name: str
    type: str
    lineno: int
    docstring: str | None = None
    decorators: list[str] | None = None


@dataclass
class FileData:
    """Represents analyzed file data."""

    path: str
    entities: list[dict[str, Any]]
    imports: list[str]
    complexity: list[dict[str, Any]]
    raw: dict[str, int]
    comment_ratio: float
    git: dict[str, Any]
    has_tests: bool
    error: str | None = None
    deep: dict[str, Any] | None = None


@dataclass
class CodeIndexData:
    """Represents the complete code index."""

    scanned_root: str
    scanned_at: str
    version: str
    total_files: int
    files: list[dict[str, Any]]
    dependencies: dict[str, Any]
    symbol_index: dict[str, str]


@dataclass
class ComplexityResult:
    """Result for complexity queries."""

    file: str
    function: str
    complexity: int
    lineno: int


@dataclass
class DependencyResult:
    """Result for dependency queries."""

    imports: list[str]
    imported_by: list[str]

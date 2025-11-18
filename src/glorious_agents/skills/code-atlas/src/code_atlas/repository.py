"""Repository layer for code-atlas data access.

Handles file-based storage and querying of code index data.
"""

import json
from pathlib import Path
from typing import Any

from glorious_agents.core.search import SearchResult

from .models import ComplexityResult, DependencyResult


class CodeIndexRepository:
    """Repository for code index data access.

    Provides structured access to the code_index.json file with
    methods for querying entities, complexity, and dependencies.
    """

    def __init__(self, index_path: Path | str = "code_index.json") -> None:
        """Initialize repository with index file path.

        Args:
            index_path: Path to code_index.json file
        """
        self.index_path = Path(index_path)
        self._data: dict[str, Any] = {}
        self._entity_index: dict[str, dict[str, Any]] = {}

        if self.index_path.exists():
            self.load()

    def load(self) -> None:
        """Load code index from file and build internal indices.

        Raises:
            FileNotFoundError: If index file doesn't exist
            ValueError: If index file is not valid JSON
        """
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")

        with open(self.index_path, encoding="utf-8") as f:
            self._data = json.load(f)

        self._build_entity_index()

    def _build_entity_index(self) -> None:
        """Build in-memory entity index for O(1) lookups."""
        self._entity_index = {}

        for file_data in self._data.get("files", []):
            for entity in file_data.get("entities", []):
                key = entity["name"]
                self._entity_index[key] = {
                    "file": file_data["path"],
                    "type": entity["type"],
                    "meta": entity,
                }

    def save(self, data: dict[str, Any]) -> None:
        """Save code index to file.

        Args:
            data: Code index data to save
        """
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self._data = data
        self._build_entity_index()

    def get_data(self) -> dict[str, Any]:
        """Get raw code index data.

        Returns:
            Complete code index dictionary
        """
        return self._data

    def find_entity(self, name: str) -> dict[str, Any] | None:
        """Find entity by name.

        Args:
            name: Name of class or function to find

        Returns:
            Entity information or None if not found
        """
        return self._entity_index.get(name)

    def get_all_files(self) -> list[dict[str, Any]]:
        """Get all file data.

        Returns:
            List of file data dictionaries
        """
        return self._data.get("files", [])

    def get_file(self, file_path: str) -> dict[str, Any] | None:
        """Get file data by path.

        Args:
            file_path: Relative file path

        Returns:
            File data or None if not found
        """
        for file_data in self._data.get("files", []):
            if file_data.get("path") == file_path:
                return file_data
        return None

    def find_complex_functions(self, threshold: int = 10) -> list[ComplexityResult]:
        """Find functions exceeding complexity threshold.

        Args:
            threshold: Minimum complexity value

        Returns:
            List of complex functions
        """
        results: list[ComplexityResult] = []

        for file_data in self._data.get("files", []):
            for comp in file_data.get("complexity", []):
                if comp["complexity"] > threshold:
                    results.append(
                        ComplexityResult(
                            file=file_data["path"],
                            function=comp["function"],
                            complexity=comp["complexity"],
                            lineno=comp["lineno"],
                        )
                    )

        return results

    def get_top_complex(self, n: int = 10) -> list[ComplexityResult]:
        """Get top N most complex functions.

        Args:
            n: Number of results to return

        Returns:
            List of most complex functions sorted by complexity descending
        """
        all_complex: list[ComplexityResult] = []

        for file_data in self._data.get("files", []):
            for comp in file_data.get("complexity", []):
                all_complex.append(
                    ComplexityResult(
                        file=file_data["path"],
                        function=comp["function"],
                        complexity=comp["complexity"],
                        lineno=comp["lineno"],
                    )
                )

        # Sort by complexity descending
        all_complex.sort(key=lambda x: x.complexity, reverse=True)

        return all_complex[:n]

    def get_dependencies(self, file_path: str) -> DependencyResult:
        """Get dependencies for a file.

        Args:
            file_path: Path to file

        Returns:
            Dependency information with imports and imported_by lists
        """
        deps = self._data.get("dependencies", {}).get(file_path, {})
        return DependencyResult(
            imports=deps.get("imports", []),
            imported_by=deps.get("imported_by", []),
        )

    def search_entities(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search entities by name, docstring, or file path.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []
        query_lower = query.lower()

        for file_data in self._data.get("files", []):
            file_path = file_data["path"]

            # Check if file name matches
            if query_lower in file_path.lower():
                results.append(
                    SearchResult(
                        skill="atlas",
                        id=file_path,
                        type="file",
                        content=f"File: {file_path}",
                        metadata={"lines": file_data.get("raw", {}).get("loc", 0)},
                        score=0.6,
                    )
                )

            # Search entities (classes, functions)
            for entity in file_data.get("entities", []):
                score = 0.0
                matched = False

                # Name exact match
                if query_lower == entity["name"].lower():
                    score = 1.0
                    matched = True
                # Name contains query
                elif query_lower in entity["name"].lower():
                    score = 0.8
                    matched = True
                # Docstring match
                elif entity.get("docstring") and query_lower in entity["docstring"].lower():
                    score = 0.5
                    matched = True

                if matched:
                    results.append(
                        SearchResult(
                            skill="atlas",
                            id=f"{file_path}:{entity['name']}",
                            type=entity["type"],
                            content=f"{entity['type']}: {entity['name']} in {file_path}",
                            metadata={
                                "lineno": entity.get("lineno"),
                                "docstring": entity.get("docstring", "")[:100],
                            },
                            score=score,
                        )
                    )

        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def get_symbol_index(self) -> dict[str, str]:
        """Get symbol-to-location index.

        Returns:
            Dictionary mapping symbol names to file:line locations
        """
        return self._data.get("symbol_index", {})

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Dictionary with statistics about the code index
        """
        files = self._data.get("files", [])
        return {
            "total_files": len(files),
            "total_lines": sum(f.get("raw", {}).get("loc", 0) for f in files),
            "total_entities": sum(len(f.get("entities", [])) for f in files),
            "scanned_root": self._data.get("scanned_root", ""),
            "scanned_at": self._data.get("scanned_at", ""),
            "version": self._data.get("version", ""),
        }

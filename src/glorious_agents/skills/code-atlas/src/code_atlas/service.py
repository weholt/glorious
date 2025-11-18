"""Business logic for code-atlas skill."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from glorious_agents.core.search import SearchResult

from .cache import FileCache
from .models import ComplexityResult, DependencyResult
from .repository import CodeIndexRepository
from .scanner import ASTScanner


class CodeAtlasService:
    """Service layer for code analysis operations.

    Coordinates scanning, querying, and caching operations while
    delegating data access to the repository layer.
    """

    def __init__(
        self,
        index_path: Path | str = "code_index.json",
        cache_path: Path | str = ".code_atlas_cache.json",
    ) -> None:
        """Initialize service with dependencies.

        Args:
            index_path: Path to code index file
            cache_path: Path to cache file
        """
        self.index_path = Path(index_path)
        self.cache_path = Path(cache_path)
        self.repository = CodeIndexRepository(index_path)
        self._cache: FileCache | None = None

    def get_cache(self) -> FileCache:
        """Get or create file cache instance.

        Returns:
            FileCache instance
        """
        if self._cache is None:
            self._cache = FileCache(self.cache_path)
        return self._cache

    def scan_directory(
        self,
        root_path: Path,
        incremental: bool = False,
        deep: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Scan a directory and generate code index.

        Args:
            root_path: Root directory to scan
            incremental: Use incremental caching
            deep: Enable deep analysis (call graphs, type coverage)
            progress_callback: Optional progress callback

        Returns:
            Code index data

        Raises:
            FileNotFoundError: If root_path doesn't exist
            ValueError: If root_path is not a directory
        """
        if not root_path.exists():
            raise FileNotFoundError(f"Directory not found: {root_path}")

        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")

        scanner = ASTScanner(root_path)
        index_data = scanner.scan_directory(
            incremental=incremental,
            deep=deep,
            progress_callback=progress_callback,
        )

        # Save to repository
        self.repository.save(index_data)

        return index_data

    def find_entity(self, name: str) -> dict[str, Any] | None:
        """Find a code entity by name.

        Args:
            name: Entity name to search for

        Returns:
            Entity information or None if not found
        """
        return self.repository.find_entity(name)

    def get_file_data(self, file_path: str) -> dict[str, Any] | None:
        """Get data for a specific file.

        Args:
            file_path: Relative file path

        Returns:
            File data or None if not found
        """
        return self.repository.get_file(file_path)

    def get_all_files(self) -> list[dict[str, Any]]:
        """Get all file data from index.

        Returns:
            List of file data dictionaries
        """
        return self.repository.get_all_files()

    def find_complex_functions(self, threshold: int = 10) -> list[ComplexityResult]:
        """Find functions exceeding complexity threshold.

        Args:
            threshold: Minimum complexity value

        Returns:
            List of complex functions
        """
        return self.repository.find_complex_functions(threshold)

    def get_top_complex(self, n: int = 10) -> list[ComplexityResult]:
        """Get top N most complex functions.

        Args:
            n: Number of results to return

        Returns:
            List of most complex functions
        """
        return self.repository.get_top_complex(n)

    def get_dependencies(self, file_path: str) -> DependencyResult:
        """Get dependencies for a file.

        Args:
            file_path: Path to file

        Returns:
            Dependency information
        """
        return self.repository.get_dependencies(file_path)

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search code index for entities and files.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        return self.repository.search_entities(query, limit)

    def get_symbol_index(self) -> dict[str, str]:
        """Get symbol-to-location index.

        Returns:
            Dictionary mapping symbol names to locations
        """
        return self.repository.get_symbol_index()

    def get_stats(self) -> dict[str, Any]:
        """Get code index statistics.

        Returns:
            Dictionary with statistics
        """
        return self.repository.get_stats()

    def clear_cache(self) -> None:
        """Clear file cache."""
        cache = self.get_cache()
        cache.clear()
        cache.save()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        cache = self.get_cache()
        return {
            "entries": len(cache.cache),
            "file": str(self.cache_path),
        }

    def query_by_type(self, entity_type: str | None = None, name_filter: str | None = None) -> list[dict[str, Any]]:
        """Query entities by type and/or name filter.

        Args:
            entity_type: Entity type to filter (function, class, etc)
            name_filter: Name substring to filter

        Returns:
            List of matching entities with file information
        """
        results = []

        for file_data in self.repository.get_all_files():
            for entity in file_data.get("entities", []):
                # Filter by type if specified
                if entity_type and entity.get("type") != entity_type:
                    continue

                # Filter by name if specified
                if name_filter and name_filter.lower() not in entity.get("name", "").lower():
                    continue

                results.append(
                    {
                        "file": file_data.get("path"),
                        "name": entity.get("name"),
                        "type": entity.get("type"),
                        "lineno": entity.get("lineno"),
                        "docstring": entity.get("docstring"),
                    }
                )

        return results

    def get_metrics(self, file_path: str | None = None) -> dict[str, Any]:
        """Get code metrics for a file or entire codebase.

        Args:
            file_path: Optional specific file path

        Returns:
            Dictionary with metrics
        """
        if file_path:
            file_data = self.repository.get_file(file_path)
            if file_data:
                return {
                    "file": file_path,
                    "lines": file_data.get("raw", {}).get("loc", 0),
                    "entities": len(file_data.get("entities", [])),
                    "complexity": file_data.get("complexity", []),
                    "comment_ratio": file_data.get("comment_ratio", 0.0),
                }
            return {}

        # Return overall stats
        return self.get_stats()

    def build_graph_data(self, graph_type: str = "dependencies") -> dict[str, Any]:
        """Build graph representation of code structure.

        Args:
            graph_type: Type of graph (dependencies, calls)

        Returns:
            Graph data with nodes and edges
        """
        graph_data = {
            "type": graph_type,
            "nodes": [],
            "edges": [],
        }

        for file_data in self.repository.get_all_files():
            file_path = file_data.get("path", "")
            graph_data["nodes"].append(
                {
                    "id": file_path,
                    "label": Path(file_path).name,
                }
            )

            # Add dependency edges
            if graph_type == "dependencies":
                deps = self.repository.get_dependencies(file_path)
                for imported in deps.imports:
                    graph_data["edges"].append(
                        {
                            "from": file_path,
                            "to": imported,
                        }
                    )

        return graph_data

    def export_to_format(self, output_format: str = "json") -> str:
        """Export code index to different formats.

        Args:
            output_format: Export format (json, dot)

        Returns:
            Formatted string

        Raises:
            ValueError: If format is not supported
        """
        if output_format == "json":
            import json

            return json.dumps(self.repository.get_data(), indent=2)

        elif output_format == "dot":
            # Generate simple DOT format
            dot_content = "digraph CodeAtlas {\n"
            for file_data in self.repository.get_all_files():
                file_name = Path(file_data.get("path", "")).name
                dot_content += f'  "{file_name}";\n'
            dot_content += "}\n"
            return dot_content

        else:
            raise ValueError(f"Unsupported format: {output_format}")

"""Dependency graph building utilities."""

from pathlib import Path
from typing import Any


def _extract_module_name(file_path: str) -> str:
    """Extract module name from file path.

    Args:
        file_path: Path to Python file

    Returns:
        Module name (e.g., "code_atlas.scanner" from "src/code_atlas/scanner.py")
    """
    path_parts = Path(file_path).parts
    module_parts = []

    for part in path_parts:
        if part == "src":
            continue
        if part.endswith(".py"):
            module_parts.append(part[:-3])
        elif part not in {"."}:
            module_parts.append(part)

    return ".".join(module_parts)


def _register_module(module_name: str, file_path: str, module_to_file: dict[str, list[str]]) -> None:
    """Register module and its parent modules in the mapping.

    Args:
        module_name: Full module name
        file_path: File path to register
        module_to_file: Module to file mapping to update
    """
    if not module_name:
        return

    # Register the module itself
    if module_name not in module_to_file:
        module_to_file[module_name] = []
    module_to_file[module_name].append(file_path)

    # Register parent modules (e.g., "code_atlas" for "code_atlas.scanner")
    parts = module_name.split(".")
    for i in range(1, len(parts)):
        parent_module = ".".join(parts[:i])
        if parent_module not in module_to_file:
            module_to_file[parent_module] = []
        module_to_file[parent_module].append(file_path)


def _build_module_mapping(dependencies: dict[str, dict[str, list[str]]]) -> dict[str, list[str]]:
    """Build module-to-file mapping for O(1) lookups.

    Args:
        dependencies: Initial dependency structure

    Returns:
        Mapping from module names to file paths
    """
    module_to_file: dict[str, list[str]] = {}

    for file_path in dependencies:
        module_name = _extract_module_name(file_path)
        _register_module(module_name, file_path, module_to_file)

    return module_to_file


def _populate_imported_by(dependencies: dict[str, dict[str, list[str]]], module_to_file: dict[str, list[str]]) -> None:
    """Populate imported_by lists using module mapping.

    Args:
        dependencies: Dependency structure to update
        module_to_file: Module to file mapping
    """
    for file_path, file_deps in dependencies.items():
        for imported_module in file_deps["imports"]:
            if imported_module in module_to_file:
                for target_file in module_to_file[imported_module]:
                    if file_path not in dependencies[target_file]["imported_by"]:
                        dependencies[target_file]["imported_by"].append(file_path)


def build_dependency_graph(files_data: list[dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
    """Build dependency graph showing imports and imported_by relationships.

    Args:
        files_data: List of file analysis dicts (must include 'imports' field)

    Returns:
        Dict mapping file paths to their dependencies
    """
    # Initialize dependencies structure
    dependencies: dict[str, dict[str, list[str]]] = {}
    for file_data in files_data:
        dependencies[file_data["path"]] = {
            "imports": file_data.get("imports", []),
            "imported_by": [],
        }

    # Build module-to-file mapping and populate imported_by
    module_to_file = _build_module_mapping(dependencies)
    _populate_imported_by(dependencies, module_to_file)

    return dependencies

"""Dependency resolution and version constraint validation."""

import logging
from typing import Any

from glorious_agents.core.loader.versioning import check_version_constraint

logger = logging.getLogger(__name__)


def validate_version_constraints(
    name: str, requires: dict[str, str], skills: dict[str, dict[str, Any]]
) -> None:
    """Validate version constraints for skill dependencies."""
    for dep_name, constraint in requires.items():
        if dep_name not in skills:
            raise ValueError(
                f"Skill '{name}' requires '{dep_name}' {constraint} but '{dep_name}' is not installed"
            )

        dep_version = skills[dep_name].get("version", "0.0.0")
        if not check_version_constraint(dep_version, constraint):
            raise ValueError(
                f"Skill '{name}' requires '{dep_name}' {constraint} but found {dep_version}"
            )


def build_dependency_graph(
    skills: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Build dependency graph and in-degree mapping."""
    graph: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}

    for name, manifest in skills.items():
        requires = manifest.get("requires", [])

        if isinstance(requires, dict):
            # Version constraints specified
            graph[name] = list(requires.keys())
            validate_version_constraints(name, requires, skills)
        else:
            # Simple list of dependencies (no version constraints)
            graph[name] = requires if isinstance(requires, list) else list(requires)

        in_degree[name] = 0

    # Calculate in-degrees
    for name, deps in graph.items():
        for dep in deps:
            if dep not in skills:
                raise ValueError(f"Skill '{name}' requires missing skill '{dep}'")
            in_degree[dep] = in_degree.get(dep, 0) + 1

    return graph, in_degree


def find_dependency_cycle(graph: dict[str, list[str]], unresolved: list[str]) -> str | None:
    """Find and format a dependency cycle if one exists."""
    if not unresolved:
        return None

    visited = set()
    current = unresolved[0]
    cycle_path = []

    while current not in visited:
        cycle_path.append(current)
        visited.add(current)
        # Follow first dependency that's also unresolved
        deps = [d for d in graph.get(current, []) if d in unresolved]
        if deps:
            current = deps[0]
        else:
            break

    # If we found a cycle, format it
    if current in cycle_path:
        cycle_start = cycle_path.index(current)
        cycle = cycle_path[cycle_start:] + [current]
        return " -> ".join(cycle)

    return None


def resolve_dependencies(skills: dict[str, dict[str, Any]]) -> list[str]:
    """Resolve skill dependencies using topological sort."""
    # Build dependency graph and check version constraints
    graph, in_degree = build_dependency_graph(skills)

    # Topological sort using Kahn's algorithm
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        current = queue.pop(0)
        result.append(current)

        for dep in graph.get(current, []):
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    if len(result) != len(skills):
        # Find which skills form the cycle
        unresolved = [name for name in skills if name not in result]
        cycle_str = find_dependency_cycle(graph, unresolved)

        if cycle_str:
            raise ValueError(
                f"Circular dependency detected in skills: {cycle_str}\n"
                f"Unresolved skills: {', '.join(sorted(unresolved))}"
            )

        raise ValueError(
            f"Circular dependency detected in skills. Unresolved: {', '.join(sorted(unresolved))}"
        )

    # Reverse to get load order (dependencies first)
    return list(reversed(result))

"""Skill discovery, dependency resolution, and loading."""

import importlib
import json
import logging
import re
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any

from glorious_agents.config import config
from glorious_agents.core.db import init_skill_schema
from glorious_agents.core.registry import SkillManifest, get_registry
from glorious_agents.core.runtime import get_ctx

if TYPE_CHECKING:
    import typer

logger = logging.getLogger(__name__)


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse semantic version string to tuple of integers.

    Args:
        version: Semantic version string (e.g., '1.2.3', '1.0.0-alpha').

    Returns:
        Tuple of (major, minor, patch) as integers.

    Raises:
        ValueError: If version string is invalid.
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def check_version_constraint(installed: str, constraint: str) -> bool:
    """Check if installed version satisfies constraint.

    Args:
        installed: Installed version string (e.g., '1.2.3').
        constraint: Version constraint (e.g., '>=1.0.0', '^1.2.0', '~1.2.0').

    Returns:
        True if constraint is satisfied, False otherwise.
    """
    installed_ver = parse_version(installed)

    # Handle different constraint operators
    if constraint.startswith("^"):
        # Caret: Allow changes that do not modify left-most non-zero digit
        required_ver = parse_version(constraint[1:])
        if required_ver[0] > 0:
            # ^1.2.3 := >=1.2.3 <2.0.0
            return installed_ver >= required_ver and installed_ver[0] == required_ver[0]
        elif required_ver[1] > 0:
            # ^0.2.3 := >=0.2.3 <0.3.0
            return (
                installed_ver >= required_ver
                and installed_ver[0] == 0
                and installed_ver[1] == required_ver[1]
            )
        else:
            # ^0.0.3 := >=0.0.3 <0.0.4
            return installed_ver == required_ver

    elif constraint.startswith("~"):
        # Tilde: Allow patch-level changes
        required_ver = parse_version(constraint[1:])
        # ~1.2.3 := >=1.2.3 <1.3.0
        return (
            installed_ver >= required_ver
            and installed_ver[0] == required_ver[0]
            and installed_ver[1] == required_ver[1]
        )

    elif constraint.startswith(">="):
        required_ver = parse_version(constraint[2:])
        return installed_ver >= required_ver

    elif constraint.startswith("<="):
        required_ver = parse_version(constraint[2:])
        return installed_ver <= required_ver

    elif constraint.startswith(">"):
        required_ver = parse_version(constraint[1:])
        return installed_ver > required_ver

    elif constraint.startswith("<"):
        required_ver = parse_version(constraint[1:])
        return installed_ver < required_ver

    elif constraint.startswith("==") or constraint[0].isdigit():
        # Exact match
        required_ver = parse_version(constraint[2:] if constraint.startswith("==") else constraint)
        return installed_ver == required_ver

    else:
        logger.warning(f"Unknown version constraint format: {constraint}")
        return True  # Allow by default if constraint format unknown


def discover_local_skills(skills_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Discover skills from local skills/ directory.

    Args:
        skills_dir: Directory containing skill folders. Uses config.SKILLS_DIR if None.

    Returns:
        Dictionary mapping skill names to manifest data.
    """
    skills: dict[str, dict[str, Any]] = {}

    if skills_dir is None:
        skills_dir = config.SKILLS_DIR

    if not skills_dir.exists():
        return skills

    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue

        manifest_file = skill_path / "skill.json"
        if not manifest_file.exists():
            continue

        try:
            manifest_data = json.loads(manifest_file.read_text())
            manifest_data["_path"] = skill_path
            manifest_data["_origin"] = "local"

            # Validate manifest with Pydantic (will raise ValidationError if invalid)
            from pydantic import ValidationError

            try:
                schema_file_val = manifest_data.get("schema_file")
                internal_doc_val = manifest_data.get("internal_doc")
                external_doc_val = manifest_data.get("external_doc")
                requires_val = manifest_data.get("requires", [])
                config_schema_val = manifest_data.get("config_schema", None)

                # Create a temporary manifest to validate structure
                requires_validated: list[str] | dict[str, str]
                if isinstance(requires_val, dict):
                    requires_validated = {str(k): str(v) for k, v in requires_val.items()}
                elif isinstance(requires_val, list):
                    requires_validated = list(requires_val)
                else:
                    requires_validated = []

                SkillManifest(
                    name=str(manifest_data.get("name", "")),
                    version=str(manifest_data.get("version", "0.0.0")),
                    description=str(manifest_data.get("description", "")),
                    entry_point=str(manifest_data.get("entry_point", "")),
                    schema_file=str(schema_file_val) if schema_file_val else None,
                    requires=requires_validated,
                    requires_db=bool(manifest_data.get("requires_db", True)),
                    internal_doc=str(internal_doc_val) if internal_doc_val else None,
                    external_doc=str(external_doc_val) if external_doc_val else None,
                    config_schema=dict(config_schema_val) if config_schema_val else None,
                    origin="local",
                    path=str(skill_path),
                )
            except ValidationError as ve:
                logger.error(
                    f"Invalid manifest for {skill_path.name}: {ve.error_count()} validation errors"
                )
                for error in ve.errors():
                    logger.error(f"  - {error['loc']}: {error['msg']}")
                continue

            skills[manifest_data["name"]] = manifest_data
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.error(f"Error loading manifest for {skill_path.name}: {e}", exc_info=True)
        except Exception as e:
            logger.error(
                f"Unexpected error loading manifest for {skill_path.name}: {e}", exc_info=True
            )

    return skills


def discover_entrypoint_skills(group: str = "glorious_agents.skills") -> dict[str, dict[str, Any]]:
    """
    Discover skills from Python entry points.

    Args:
        group: Entry point group name.

    Returns:
        Dictionary mapping skill names to manifest data.
    """
    skills: dict[str, dict[str, Any]] = {}

    try:
        eps = entry_points(group=group)
        for ep in eps:
            # Try to load skill.json from the package
            manifest_data = {
                "name": ep.name,
                "entry_point": f"{ep.value}",  # Use entry point from setup, not skill.json
                "_origin": "entrypoint",
                "version": "unknown",
                "description": f"External skill: {ep.name}",
                "requires": [],
                "requires_db": True,
            }

            try:
                # Get the module path from entry point
                module_path = ep.value.split(":")[0]
                module = importlib.import_module(module_path.rsplit(".", 1)[0])
                if hasattr(module, "__file__") and module.__file__:
                    module_dir = Path(module.__file__).parent
                    manifest_data["_path"] = module_dir  # Store path for entry point skills
                    manifest_file = module_dir / "skill.json"
                    if manifest_file.exists():
                        file_manifest = json.loads(manifest_file.read_text())
                        # Preserve the entry_point from Python's entry_points, don't override it
                        entry_point_backup = manifest_data["entry_point"]
                        manifest_data.update(file_manifest)
                        manifest_data["entry_point"] = entry_point_backup
            except (ImportError, AttributeError, json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not load skill.json for {ep.name}: {e}")
            except Exception as e:
                logger.error(
                    f"Unexpected error loading skill.json for {ep.name}: {e}", exc_info=True
                )

            # Validate manifest structure
            from pydantic import ValidationError

            try:
                schema_file_val = manifest_data.get("schema_file")
                internal_doc_val = manifest_data.get("internal_doc")
                external_doc_val = manifest_data.get("external_doc")
                requires_val = manifest_data.get("requires", [])
                path_val = manifest_data.get("_path", "")
                config_schema_val = manifest_data.get("config_schema")

                requires_validated: list[str] | dict[str, str]
                if isinstance(requires_val, dict):
                    requires_validated = {str(k): str(v) for k, v in requires_val.items()}
                elif isinstance(requires_val, list):
                    requires_validated = list(requires_val)
                else:
                    requires_validated = []

                SkillManifest(
                    name=str(manifest_data.get("name", ep.name)),
                    version=str(manifest_data.get("version", "0.0.0")),
                    description=str(manifest_data.get("description", f"External skill: {ep.name}")),
                    entry_point=str(manifest_data["entry_point"]),
                    schema_file=str(schema_file_val) if schema_file_val else None,
                    requires=requires_validated,
                    requires_db=bool(manifest_data.get("requires_db", True)),
                    internal_doc=str(internal_doc_val) if internal_doc_val else None,
                    external_doc=str(external_doc_val) if external_doc_val else None,
                    config_schema=dict(config_schema_val)
                    if isinstance(config_schema_val, dict)
                    else None,
                    origin="entrypoint",
                    path=str(path_val) if path_val else None,
                )
            except ValidationError as ve:
                logger.error(
                    f"Invalid manifest for entry point {ep.name}: {ve.error_count()} validation errors"
                )
                for error in ve.errors():
                    logger.error(f"  - {error['loc']}: {error['msg']}")
                continue

            skills[ep.name] = manifest_data
    except (ImportError, AttributeError) as e:
        logger.error(f"Error discovering entry points: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error discovering entry points: {e}", exc_info=True)

    return skills


def _validate_version_constraints(
    name: str, requires: dict[str, str], skills: dict[str, dict[str, Any]]
) -> None:
    """Validate version constraints for skill dependencies.

    Raises:
        ValueError: If dependency not found or version constraint not satisfied.
    """
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


def _build_dependency_graph(
    skills: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Build dependency graph and in-degree mapping.

    Returns:
        Tuple of (adjacency graph, in-degree mapping)

    Raises:
        ValueError: If dependencies are missing or version constraints not satisfied.
    """
    graph: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}

    for name, manifest in skills.items():
        requires = manifest.get("requires", [])

        if isinstance(requires, dict):
            # Version constraints specified
            graph[name] = list(requires.keys())
            _validate_version_constraints(name, requires, skills)
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


def _find_dependency_cycle(graph: dict[str, list[str]], unresolved: list[str]) -> str | None:
    """Find and format a dependency cycle if one exists.

    Args:
        graph: Dependency adjacency graph
        unresolved: List of unresolved skill names

    Returns:
        Formatted cycle string or None if no clear cycle found
    """
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
    """
    Resolve skill dependencies using topological sort.

    Validates version constraints for dependencies.

    Args:
        skills: Dictionary of skill manifests.

    Returns:
        List of skill names in dependency order.

    Raises:
        ValueError: If dependencies are missing, circular, or version constraints not satisfied.
    """
    # Build dependency graph and check version constraints
    graph, in_degree = _build_dependency_graph(skills)

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
        cycle_str = _find_dependency_cycle(graph, unresolved)

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


def init_schemas(sorted_skills: list[str], skills_data: dict[str, dict[str, Any]]) -> None:
    """
    Initialize database schemas for all skills.

    Args:
        sorted_skills: Skills in dependency order.
        skills_data: Dictionary of skill manifest data.
    """
    for skill_name in sorted_skills:
        manifest = skills_data[skill_name]
        schema_file = manifest.get("schema_file")

        if not schema_file:
            continue

        # Resolve schema path - works for both local and entry point skills
        skill_path = manifest.get("_path")
        if not skill_path:
            logger.warning(f"Skill {skill_name} has no path information, skipping schema init")
            continue

        schema_path = skill_path / schema_file

        if schema_path.exists():
            init_skill_schema(skill_name, schema_path)
        else:
            logger.debug(f"Schema file {schema_path} not found for skill {skill_name}")


def load_skill_entry(entry_point: str, skill_name: str, is_local: bool = False) -> "typer.Typer":
    """
    Load a skill's Typer app from its entry point.

    Args:
        entry_point: Module path and attribute (e.g., "pkg.module:app").
        skill_name: Name of the skill.
        is_local: Whether this is a local skill (needs skills/ dir in path).

    Returns:
        The loaded Typer app.
    """
    module_path, attr = entry_point.split(":")

    # Add skills directory to path only for local skills
    skills_dir = config.SKILLS_DIR
    path_added = False
    if is_local and skills_dir.exists():
        sys.path.insert(0, str(skills_dir.absolute()))
        path_added = True

    try:
        module = importlib.import_module(module_path)
        app: typer.Typer = getattr(module, attr)

        # Call init_context if it exists
        if hasattr(module, "init_context"):
            init_context = module.init_context
            ctx = get_ctx()
            init_context(ctx)

        return app
    finally:
        # Remove from path if we added it
        if path_added and str(skills_dir.absolute()) in sys.path:
            sys.path.remove(str(skills_dir.absolute()))


def _call_skill_init(skill_name: str, entry_point: str, is_local: bool) -> None:
    """Call optional init() function on skill module if it exists.

    Args:
        skill_name: Name of the skill
        entry_point: Entry point in format 'module.path:attribute'
        is_local: Whether skill is loaded from local directory

    Raises:
        Exception: If init() raises an exception indicating skill cannot run
    """
    module_path = entry_point.split(":")[0]

    try:
        if is_local:
            # Local skills use relative imports
            spec = importlib.util.spec_from_file_location(
                f"skills.{skill_name}.skill",
                config.SKILLS_DIR / skill_name / "skill.py",
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                return
        else:
            # Entry point skills use regular imports
            module = importlib.import_module(module_path)

        # Check if module has init() function
        if hasattr(module, "init"):
            init_func = module.init
            if callable(init_func):
                logger.debug(f"Calling init() for skill '{skill_name}'")
                init_func()
                logger.debug(f"Skill '{skill_name}' init() completed successfully")
    except Exception as e:
        # Re-raise to let caller handle
        raise RuntimeError(f"Skill '{skill_name}' init() failed: {e}") from e


def load_all_skills() -> None:
    """Discover, resolve, initialize, and load all skills."""
    # Discover skills
    local_skills = discover_local_skills()
    ep_skills = discover_entrypoint_skills()

    # Merge (local wins)
    all_skills = {**ep_skills, **local_skills}

    if not all_skills:
        return

    # Resolve dependencies
    sorted_skills = resolve_dependencies(all_skills)

    # Initialize schemas
    init_schemas(sorted_skills, all_skills)

    # Load skills with error recovery
    registry = get_registry()
    ctx = get_ctx()
    loaded_skills: list[str] = []
    failed_skills: list[tuple[str, str]] = []

    for skill_name in sorted_skills:
        manifest_data = all_skills[skill_name]

        # Create manifest object
        config_schema_data = manifest_data.get("config_schema")
        manifest = SkillManifest(
            name=manifest_data["name"],
            version=manifest_data.get("version", "0.0.0"),
            description=manifest_data.get("description", ""),
            entry_point=manifest_data["entry_point"],
            schema_file=manifest_data.get("schema_file"),
            requires=manifest_data.get("requires", []),
            requires_db=manifest_data.get("requires_db", True),
            internal_doc=manifest_data.get("internal_doc"),
            external_doc=manifest_data.get("external_doc"),
            config_schema=dict(config_schema_data)
            if isinstance(config_schema_data, dict)
            else None,
            origin=manifest_data["_origin"],
            path=str(manifest_data["_path"]) if "_path" in manifest_data else None,
        )

        # Load app
        try:
            is_local = manifest_data["_origin"] == "local"
            app = load_skill_entry(manifest.entry_point, skill_name, is_local)

            # Call optional init() to verify skill can run
            try:
                _call_skill_init(skill_name, manifest.entry_point, is_local)
            except Exception as init_error:
                logger.error(
                    f"Skill '{skill_name}' failed initialization: {init_error}",
                    exc_info=True,
                )
                failed_skills.append((skill_name, str(init_error)))
                continue

            registry.add(manifest, app)
            ctx.register_skill(skill_name, app)
            loaded_skills.append(skill_name)
        except (ImportError, AttributeError, KeyError) as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(f"Error loading skill '{skill_name}': {error_msg}", exc_info=True)
            failed_skills.append((skill_name, error_msg))
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(
                f"Unexpected error loading skill '{skill_name}': {error_msg}", exc_info=True
            )
            failed_skills.append((skill_name, error_msg))

    # Log summary
    if loaded_skills or failed_skills:
        logger.info(
            f"Skill loading complete: {len(loaded_skills)} loaded, {len(failed_skills)} failed"
        )
        if failed_skills:
            logger.warning(f"Failed to load skills: {', '.join(name for name, _ in failed_skills)}")

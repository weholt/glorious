"""Skill initialization - schemas and module loading."""

import importlib
import importlib.util
import logging
import sys
from typing import TYPE_CHECKING, Any

from glorious_agents.config import config
from glorious_agents.core.db import init_skill_schema
from glorious_agents.core.runtime import get_ctx

if TYPE_CHECKING:
    import typer

logger = logging.getLogger(__name__)


def init_schemas(sorted_skills: list[str], skills_data: dict[str, dict[str, Any]]) -> None:
    """Initialize database schemas for all skills."""
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
    """Load a skill's Typer app from its entry point."""
    from glorious_agents.core.isolation import create_restricted_context

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

        # Call init_context if it exists - provide restricted context
        if hasattr(module, "init_context"):
            init_context = module.init_context
            ctx = get_ctx()
            restricted_ctx = create_restricted_context(ctx, skill_name)
            init_context(restricted_ctx)

        return app
    finally:
        # Remove from path if we added it
        if path_added and str(skills_dir.absolute()) in sys.path:
            sys.path.remove(str(skills_dir.absolute()))


def call_skill_init(skill_name: str, entry_point: str, is_local: bool) -> None:
    """Call optional init() function on skill module if it exists."""
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

"""Skill loading orchestration - main entry point."""

import logging
from typing import TYPE_CHECKING

from glorious_agents.core.loader.dependencies import resolve_dependencies
from glorious_agents.core.loader.discovery import (
    discover_entrypoint_skills,
    discover_local_skills,
)
from glorious_agents.core.loader.initialization import (
    call_skill_init,
    init_schemas,
    load_skill_entry,
)
from glorious_agents.core.loader.versioning import check_version_constraint, parse_version
from glorious_agents.core.registry import SkillManifest, get_registry
from glorious_agents.core.runtime import get_ctx

if TYPE_CHECKING:
    import typer

logger = logging.getLogger(__name__)

# Re-export public API
__all__ = [
    "discover_local_skills",
    "discover_entrypoint_skills",
    "resolve_dependencies",
    "init_schemas",
    "load_skill_entry",
    "load_all_skills",
    "parse_version",
    "check_version_constraint",
]


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
                call_skill_init(skill_name, manifest.entry_point, is_local)
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

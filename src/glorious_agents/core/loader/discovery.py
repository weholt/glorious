"""Skill discovery from local directories and entry points."""

import importlib
import json
import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from glorious_agents.config import config
from glorious_agents.core.registry import SkillManifest

logger = logging.getLogger(__name__)


def discover_local_skills(skills_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Discover skills from local skills/ directory."""
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

            # Validate manifest with Pydantic
            try:
                schema_file_val = manifest_data.get("schema_file")
                internal_doc_val = manifest_data.get("internal_doc")
                external_doc_val = manifest_data.get("external_doc")
                requires_val = manifest_data.get("requires", [])
                config_schema_val = manifest_data.get("config_schema", None)

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
    """Discover skills from Python entry points."""
    skills: dict[str, dict[str, Any]] = {}

    try:
        eps = entry_points(group=group)
        for ep in eps:
            manifest_data = {
                "name": ep.name,
                "entry_point": f"{ep.value}",
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
                    manifest_data["_path"] = module_dir
                    manifest_file = module_dir / "skill.json"
                    if manifest_file.exists():
                        file_manifest = json.loads(manifest_file.read_text())
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

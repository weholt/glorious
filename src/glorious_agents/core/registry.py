"""In-process registry for loaded skills."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class SkillManifest(BaseModel):
    """Skill manifest metadata with validation.

    Uses Pydantic for automatic validation of skill.json files.
    Ensures all required fields are present and have correct types.
    """

    name: str = Field(..., min_length=1, description="Skill name (must be non-empty)")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+.*$", description="Semantic version")
    description: str = Field(..., description="Brief description of the skill")
    entry_point: str = Field(
        ..., pattern=r"^[\w.]+:[\w]+$", description="Module path in format 'module:app'"
    )
    schema_file: str | None = Field(None, description="Path to SQL schema file")
    requires: list[str] | dict[str, str] = Field(
        default_factory=list,
        description="List of required skills or dict with version constraints",
    )
    requires_db: bool = Field(True, description="Whether skill requires database access")
    internal_doc: str | None = Field(None, description="Internal documentation file")
    external_doc: str | None = Field(None, description="User-facing documentation file")
    config_schema: dict[str, dict[str, Any]] | None = Field(
        None, description="Configuration schema with type and default values"
    )
    origin: Literal["local", "entrypoint"] = Field(
        ..., description="Origin of the skill (local or entrypoint)"
    )
    path: str | None = Field(None, description="Path to skill directory")


class SkillRegistry:
    """Registry for loaded skills and their manifests."""

    def __init__(self) -> None:
        self._manifests: dict[str, SkillManifest] = {}
        self._apps: dict[str, Any] = {}

    def add(self, manifest: SkillManifest, app: Any) -> None:
        """
        Add a skill to the registry.

        Args:
            manifest: Skill manifest.
            app: Loaded Typer app.
        """
        self._manifests[manifest.name] = manifest
        self._apps[manifest.name] = app

    def get_manifest(self, name: str) -> SkillManifest | None:
        """Get a skill manifest by name."""
        return self._manifests.get(name)

    def get_app(self, name: str) -> Any:
        """Get a skill app by name."""
        return self._apps.get(name)

    def list_all(self) -> list[SkillManifest]:
        """List all registered skills."""
        return list(self._manifests.values())

    def clear(self) -> None:
        """Clear the registry."""
        self._manifests.clear()
        self._apps.clear()


# Global registry instance
_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """Get the global skill registry."""
    return _registry

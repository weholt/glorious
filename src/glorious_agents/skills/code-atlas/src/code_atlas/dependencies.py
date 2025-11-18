"""Dependency injection for code-atlas skill.

Provides factory functions for creating service instances with proper dependencies.
"""

from pathlib import Path

from .service import CodeAtlasService

# Module-level service instance for reuse
_service_instance: CodeAtlasService | None = None


def get_atlas_service(
    index_path: Path | str = "code_index.json",
    cache_path: Path | str = ".code_atlas_cache.json",
) -> CodeAtlasService:
    """Get or create CodeAtlasService instance.

    Args:
        index_path: Path to code index file
        cache_path: Path to cache file

    Returns:
        CodeAtlasService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = CodeAtlasService(
            index_path=index_path,
            cache_path=cache_path,
        )

    return _service_instance


def reset_service() -> None:
    """Reset the service instance.

    Useful for testing or when changing configuration.
    """
    global _service_instance
    _service_instance = None

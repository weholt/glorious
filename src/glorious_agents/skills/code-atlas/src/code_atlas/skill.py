"""Code-atlas skill for Glorious Agents.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from code_atlas.cli import app
from code_atlas.dependencies import get_atlas_service

if TYPE_CHECKING:
    from glorious_agents.core.context import SkillContext
    from glorious_agents.core.search import SearchResult

# Export the existing Typer app
# Glorious will load this automatically

__all__ = ["app", "search", "init_context"]

_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context.

    Args:
        ctx: Skill context from the framework
    """
    global _ctx
    _ctx = ctx


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for code atlas.

    Searches across classes, functions, and file names using the service layer.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    from pathlib import Path

    # Get service instance
    index_path = Path.cwd() / "code_index.json"

    # Check if index exists
    if not index_path.exists():
        return []

    try:
        service = get_atlas_service(index_path=index_path)
        return service.search(query, limit)
    except Exception:
        return []

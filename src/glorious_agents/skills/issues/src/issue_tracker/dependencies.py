"""Dependency injection for issues skill - top-level API.

Provides unified interface following the new framework patterns while
delegating to the existing CLI dependencies module.
"""

from typing import Any

from issue_tracker.cli.dependencies import (
    dispose_all_engines,
    get_engine,
    get_issue_graph_service,
    get_issue_service,
    get_issue_stats_service,
    get_session,
)
from issue_tracker.services.search_service import SearchService

# Module-level service instances for reuse (used by get functions)
_services: dict[str, Any] = {}


def get_search_service() -> SearchService:
    """Get or create SearchService instance.

    Returns:
        SearchService instance
    """
    if "search" not in _services:
        session = get_session()
        _services["search"] = SearchService(session)

    return _services["search"]


def reset_services() -> None:
    """Reset all service instances.

    Useful for testing or when changing configuration.
    Also disposes all database engines to prevent leaks.
    """
    _services.clear()
    dispose_all_engines()


# Re-export factory functions for backward compatibility
__all__ = [
    "get_engine",
    "get_session",
    "get_issue_service",
    "get_issue_graph_service",
    "get_issue_stats_service",
    "get_search_service",
    "dispose_all_engines",
    "reset_services",
]

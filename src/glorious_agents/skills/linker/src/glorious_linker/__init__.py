"""Linker skill for Glorious Agents - semantic cross-references between entities.

Modern architecture with Repository/Service patterns.
"""

from .dependencies import get_linker_service
from .models import Link
from .repository import LinkerRepository
from .service import LinkerService
from .skill import add_link, app, get_context_bundle, init_context, search

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "add_link",
    "get_context_bundle",
    "search",
    # Modern components
    "Link",
    "LinkerRepository",
    "LinkerService",
    "get_linker_service",
]

"""Vacuum skill for Glorious Agents.

Modern architecture with Repository/Service patterns.
"""

from .dependencies import get_vacuum_service
from .models import VacuumOperation
from .repository import VacuumRepository
from .service import VacuumService
from .skill import app, init_context, search

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "search",
    # Modern components
    "VacuumOperation",
    "VacuumRepository",
    "VacuumService",
    "get_vacuum_service",
]

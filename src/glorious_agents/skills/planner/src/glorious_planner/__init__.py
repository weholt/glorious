"""Planner skill for Glorious Agents.

Modern architecture with Repository/Service patterns.
"""

from .dependencies import get_planner_service
from .models import PlannerTask
from .repository import PlannerRepository
from .service import PlannerService
from .skill import add_task, app, get_next_task, init_context, search

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "add_task",
    "get_next_task",
    "search",
    # Modern components
    "PlannerTask",
    "PlannerRepository",
    "PlannerService",
    "get_planner_service",
]

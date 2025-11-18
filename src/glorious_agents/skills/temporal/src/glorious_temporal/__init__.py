"""Temporal skill for Glorious Agents.

Modern architecture with Service patterns.
"""

from .dependencies import get_temporal_service
from .models import TimeFilter
from .service import TemporalService
from .skill import app, init_context, search

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "search",
    # Modern components
    "TimeFilter",
    "TemporalService",
    "get_temporal_service",
]

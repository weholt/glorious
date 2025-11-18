"""Telemetry skill for Glorious Agents.

Modern architecture with Repository/Service patterns.
"""

from .dependencies import get_telemetry_service
from .models import TelemetryEvent
from .repository import TelemetryRepository
from .service import TelemetryService
from .skill import app, init_context, log_event, search

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "log_event",
    "search",
    # Modern components
    "TelemetryEvent",
    "TelemetryRepository",
    "TelemetryService",
    "get_telemetry_service",
]

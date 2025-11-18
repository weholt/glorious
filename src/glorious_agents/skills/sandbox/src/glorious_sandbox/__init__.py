"""Sandbox skill for Glorious Agents.

Modern architecture with Repository/Service patterns.
"""

from .dependencies import get_sandbox_service
from .models import Sandbox
from .repository import SandboxRepository
from .service import SandboxService
from .skill import app, init_context, search

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "search",
    # Modern components
    "Sandbox",
    "SandboxRepository",
    "SandboxService",
    "get_sandbox_service",
]

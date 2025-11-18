"""Orchestrator skill for Glorious Agents."""

from .dependencies import get_orchestrator_service
from .models import Workflow
from .repository import WorkflowRepository
from .service import OrchestratorService

__version__ = "0.1.0"

__all__ = [
    "Workflow",
    "WorkflowRepository",
    "OrchestratorService",
    "get_orchestrator_service",
]

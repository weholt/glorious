"""Automations skill for Glorious Agents."""

from .dependencies import get_automation_service
from .models import Automation, AutomationExecution
from .repository import AutomationExecutionRepository, AutomationRepository
from .service import AutomationService

__version__ = "0.1.0"

__all__ = [
    "Automation",
    "AutomationExecution",
    "AutomationRepository",
    "AutomationExecutionRepository",
    "AutomationService",
    "get_automation_service",
]

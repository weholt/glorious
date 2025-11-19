"""Feedback skill for Glorious Agents.

Modern architecture with Repository/Service patterns.
"""

from .dependencies import get_feedback_service
from .models import Feedback
from .repository import FeedbackRepository
from .service import FeedbackService
from .skill import app, init_context, record_feedback, search

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "record_feedback",
    "search",
    # Modern components
    "Feedback",
    "FeedbackRepository",
    "FeedbackService",
    "get_feedback_service",
]

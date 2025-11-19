"""Prompts skill for Glorious Agents - template management and versioning.

Modern architecture with Repository/Service patterns.
"""

from .dependencies import get_prompts_service
from .models import Prompt
from .repository import PromptsRepository
from .service import PromptsService
from .skill import app, init_context, register_prompt, search

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "register_prompt",
    "search",
    # Modern components
    "Prompt",
    "PromptsRepository",
    "PromptsService",
    "get_prompts_service",
]

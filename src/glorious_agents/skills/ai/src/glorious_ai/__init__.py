"""AI skill for Glorious Agents."""

from .dependencies import get_ai_service
from .models import AICompletion, AIEmbedding
from .repository import AICompletionRepository, AIEmbeddingRepository
from .service import AIService

__version__ = "0.1.0"

__all__ = [
    "AICompletion",
    "AIEmbedding",
    "AICompletionRepository",
    "AIEmbeddingRepository",
    "AIService",
    "get_ai_service",
]

"""Documentation management skill for Glorious Agents."""

from .dependencies import get_docs_service
from .models import Document, DocumentVersion
from .repository import DocumentRepository, DocumentVersionRepository
from .service import DocsService

__version__ = "0.1.0"

__all__ = [
    "Document",
    "DocumentVersion",
    "DocumentRepository",
    "DocumentVersionRepository",
    "DocsService",
    "get_docs_service",
]

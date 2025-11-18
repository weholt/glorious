"""Notes skill for Glorious Agents - persistent notes with full-text search.

Modern architecture with Repository/Service patterns and FTS support.
"""

from .dependencies import get_notes_service
from .models import Note
from .repository import NotesRepository
from .service import NotesService
from .skill import add_note, app, init_context, search, search_notes

__version__ = "0.1.0"

__all__ = [
    # CLI
    "app",
    "init_context",
    # Public API
    "add_note",
    "search_notes",
    "search",
    # Modern components
    "Note",
    "NotesRepository",
    "NotesService",
    "get_notes_service",
]

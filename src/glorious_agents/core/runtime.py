"""Runtime singleton for skill context."""

import threading

from glorious_agents.core.context import EventBus, SkillContext
from glorious_agents.core.db import get_connection

_context: SkillContext | None = None
_lock = threading.Lock()


def get_ctx() -> SkillContext:
    """
    Get the singleton skill context.

    Thread-safe singleton initialization using double-checked locking pattern.
    The context is shared across all skills and provides access to the database
    connection and event bus.

    Returns:
        The shared SkillContext instance.
    """
    global _context
    # Double-checked locking for performance
    if _context is None:
        with _lock:
            # Check again inside lock to prevent race condition
            if _context is None:
                conn = get_connection(check_same_thread=False)
                event_bus = EventBus()
                _context = SkillContext(conn, event_bus)
    return _context


def reset_ctx() -> None:
    """
    Reset the context (useful for testing).

    Thread-safe cleanup of the singleton context. Closes the database connection
    and resets the global context to None.
    """
    global _context
    with _lock:
        if _context is not None:
            _context.conn.close()
        _context = None

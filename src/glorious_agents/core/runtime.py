"""Runtime singleton for skill context."""

import atexit
import threading

from glorious_agents.core.context import EventBus, SkillContext
from glorious_agents.core.db import get_connection

_context: SkillContext | None = None
_lock = threading.Lock()


def get_ctx() -> SkillContext:
    """
    Retrieve the global SkillContext singleton used by skills.
    
    Initializes and returns the shared SkillContext on first access; subsequent calls return the same instance.
    
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
                # Register cleanup on exit
                atexit.register(_cleanup_context)
    return _context


def reset_ctx() -> None:
    """
    Reset the module-level SkillContext singleton and release its resources.
    
    If a context exists, this function calls its close() method and sets the global context reference to None. The operation is performed under the module lock to be safe for concurrent use (commonly used in tests or shutdown handling).
    """
    global _context
    with _lock:
        if _context is not None:
            _context.close()
        _context = None


def _cleanup_context() -> None:
    """
    Ensure the module-level SkillContext is closed and cleared at program exit.
    
    Intended to be registered with program-exit handlers to release resources held by the singleton context.
    """
    reset_ctx()
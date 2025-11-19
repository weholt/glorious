"""Dependency injection for sandbox skill.

This module manages dependencies without creating coupling
from the skill to specific implementations.
"""

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from glorious_agents.core.context import EventBus
from glorious_agents.core.engine_registry import get_engine_for_agent_db
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Sandbox
from .service import SandboxService


def get_engine() -> Engine:
    """Get database engine for sandbox skill.

    Uses the agent database from configuration.
    No caching to avoid memory leaks.

    Returns:
        SQLAlchemy engine
    """
    return get_engine_for_agent_db()


def init_database(engine: Engine) -> None:
    """Initialize database tables.

    Args:
        engine: SQLAlchemy engine
    """
    SQLModel.metadata.create_all(engine)


def get_sandbox_service(
    engine: Engine | None = None, event_bus: EventBus | None = None
) -> SandboxService:
    """Get sandbox service with dependencies.

    Args:
        engine: Optional engine (defaults to agent DB)
        event_bus: Optional event bus for publishing events

    Returns:
        Configured SandboxService instance
    """
    if engine is None:
        engine = get_engine()

    # Ensure tables exist
    init_database(engine)

    # Create service with fresh session and UoW
    session = Session(engine)
    uow = UnitOfWork(session)
    return SandboxService(uow, event_bus)

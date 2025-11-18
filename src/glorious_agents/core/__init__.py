"""Core package for glorious agents.

This package provides the foundational infrastructure for building skills
with modern architecture patterns including:
- Type-safe ORM with SQLModel/SQLAlchemy
- Repository pattern for data access
- Unit of Work for transaction management
- Dependency injection via service factories
- Event bus for inter-skill communication
"""

from glorious_agents.core.context import EventBus, SkillContext
from glorious_agents.core.engine_registry import (
    dispose_all_engines,
    dispose_engine,
    get_active_engines,
    get_engine,
    get_engine_for_agent_db,
    has_engine,
)
from glorious_agents.core.repository import BaseRepository
from glorious_agents.core.service_factory import ServiceFactory
from glorious_agents.core.skill_base import BaseSkill
from glorious_agents.core.unit_of_work import UnitOfWork

__all__ = [
    # Context and Events
    "EventBus",
    "SkillContext",
    # Modern Architecture Components
    "BaseRepository",
    "BaseSkill",
    "ServiceFactory",
    "UnitOfWork",
    # Engine Registry
    "dispose_all_engines",
    "dispose_engine",
    "get_active_engines",
    "get_engine",
    "get_engine_for_agent_db",
    "has_engine",
]

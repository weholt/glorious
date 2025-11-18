"""Dependency injection for migrate skill.

This module manages dependencies without creating coupling
from the skill to specific implementations.
"""

from .service import MigrateService


def get_migrate_service() -> MigrateService:
    """Get migrate service.

    Migrate is a utility skill that doesn't manage its own database,
    so the service is stateless.

    Returns:
        MigrateService instance
    """
    return MigrateService()

"""Dependency injection for temporal skill.

This module provides service instances without database dependencies
since temporal is a utility skill.
"""

from .service import TemporalService


def get_temporal_service() -> TemporalService:
    """Get temporal service instance.

    Returns:
        TemporalService instance
    """
    return TemporalService()

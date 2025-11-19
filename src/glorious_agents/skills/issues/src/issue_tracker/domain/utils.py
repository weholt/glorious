"""Domain utilities."""

from datetime import UTC, datetime

__all__ = ["utcnow_naive"]


def utcnow_naive() -> datetime:
    """Return current UTC time as naive datetime.

    SQLAlchemy/SQLModel stores datetime as naive by default.
    This centralizes the conversion to avoid DRY violations.
    """
    return datetime.now(UTC).replace(tzinfo=None)

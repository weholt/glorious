"""Domain exceptions for issue tracking."""


class DomainError(Exception):
    """Base exception for all domain errors."""

    pass


class InvariantViolationError(DomainError):
    """Raised when a domain invariant is violated."""

    def __init__(self, message: str, entity_id: str | None = None):
        super().__init__(message)
        self.entity_id = entity_id


class InvalidTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        message: str,
        entity_id: str,
        current_state: str,
        target_state: str,
    ):
        super().__init__(message)
        self.entity_id = entity_id
        self.current_state = current_state
        self.target_state = target_state


class NotFoundError(DomainError):
    """Raised when an entity is not found."""

    def __init__(self, message: str, entity_id: str | None = None):
        super().__init__(message)
        self.entity_id = entity_id


class ValidationError(DomainError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class DatabaseError(DomainError):
    """Raised when database operations fail."""

    pass


class CycleDetectedError(DomainError):
    """Raised when a dependency cycle is detected."""

    def __init__(self, message: str, cycle_path: list[str] | None = None):
        super().__init__(message)
        self.cycle_path = cycle_path or []


__all__ = [
    "DomainError",
    "InvariantViolationError",
    "InvalidTransitionError",
    "NotFoundError",
    "ValidationError",
    "DatabaseError",
    "CycleDetectedError",
]

"""Tests for domain exceptions."""

from issue_tracker.domain.exceptions import (
    DomainError,
    InvalidTransitionError,
    InvariantViolationError,
    NotFoundError,
)


def test_domain_error():
    """Test DomainError base exception."""
    error = DomainError("test error")
    assert str(error) == "test error"
    assert isinstance(error, Exception)


def test_invariant_violation_error():
    """Test InvariantViolationError."""
    error = InvariantViolationError("Invalid state", entity_id="issue-123")
    assert str(error) == "Invalid state"
    assert error.entity_id == "issue-123"


def test_invariant_violation_error_without_id():
    """Test InvariantViolationError without entity_id."""
    error = InvariantViolationError("Invalid state")
    assert str(error) == "Invalid state"
    assert error.entity_id is None


def test_invalid_transition_error():
    """Test InvalidTransitionError."""
    error = InvalidTransitionError(
        "Cannot transition",
        entity_id="issue-123",
        current_state="open",
        target_state="invalid",
    )
    assert str(error) == "Cannot transition"
    assert error.entity_id == "issue-123"
    assert error.current_state == "open"
    assert error.target_state == "invalid"


def test_not_found_error():
    """Test NotFoundError."""
    error = NotFoundError("Issue not found", entity_id="issue-123")
    assert str(error) == "Issue not found"
    assert error.entity_id == "issue-123"


def test_not_found_error_without_id():
    """Test NotFoundError without entity_id."""
    error = NotFoundError("Issue not found")
    assert str(error) == "Issue not found"
    assert error.entity_id is None

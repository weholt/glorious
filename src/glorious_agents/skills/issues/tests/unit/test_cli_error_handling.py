"""Tests for CLI error handling utilities."""

from issue_tracker.cli.error_handling import format_error_message
from issue_tracker.domain import (
    CycleDetectedError,
    DatabaseError,
    DomainError,
    InvalidTransitionError,
    InvariantViolationError,
    NotFoundError,
    ValidationError,
)


class TestFormatErrorMessage:
    """Tests for format_error_message function."""

    def test_formats_not_found_error(self):
        """Test formatting of NotFoundError."""
        error = NotFoundError("Issue not found", entity_id="issue-123")
        result = format_error_message(error)
        assert "Not found" in result
        assert "issue-123" in result

    def test_formats_not_found_without_entity_id(self):
        """Test formatting of NotFoundError without entity_id."""
        error = NotFoundError("Resource not found")
        result = format_error_message(error)
        assert "Not found" in result
        assert "Resource not found" in result

    def test_formats_validation_error(self):
        """Test formatting of ValidationError."""
        error = ValidationError("Invalid input", field="title")
        result = format_error_message(error)
        assert "Validation failed" in result
        assert "title" in result

    def test_formats_validation_error_without_field(self):
        """Test formatting of ValidationError without field."""
        error = ValidationError("Invalid data")
        result = format_error_message(error)
        assert "Validation failed" in result
        assert "Invalid data" in result

    def test_formats_invalid_transition_error(self):
        """Test formatting of InvalidTransitionError."""
        error = InvalidTransitionError(
            "Cannot close resolved issue", entity_id="issue-123", current_state="resolved", target_state="closed"
        )
        result = format_error_message(error)
        assert "Cannot transition" in result
        assert "resolved" in result
        assert "closed" in result

    def test_formats_invariant_violation_error(self):
        """Test formatting of InvariantViolationError."""
        error = InvariantViolationError("Title cannot be empty", entity_id="issue-123")
        result = format_error_message(error)
        assert "Domain error" in result

    def test_formats_cycle_detected_error(self):
        """Test formatting of CycleDetectedError."""
        error = CycleDetectedError("Circular dependency detected", cycle_path=["A", "B", "C", "A"])
        result = format_error_message(error)
        assert "Domain error" in result

    def test_formats_database_error(self):
        """Test formatting of DatabaseError."""
        error = DatabaseError("Connection failed")
        result = format_error_message(error)
        assert "Domain error" in result

    def test_formats_generic_domain_error(self):
        """Test formatting of generic DomainError."""
        error = DomainError("Something went wrong")
        result = format_error_message(error)
        assert "Domain error" in result
        assert "Something went wrong" in result

    def test_formats_generic_exception(self):
        """Test formatting of non-domain exceptions."""
        error = ValueError("Invalid value")
        result = format_error_message(error)
        assert "Invalid value" in result


class TestNewExceptionTypes:
    """Tests for new exception types."""

    def test_validation_error_attributes(self):
        """Test ValidationError stores field attribute."""
        error = ValidationError("Invalid email", field="email")
        assert error.field == "email"
        assert str(error) == "Invalid email"

    def test_validation_error_without_field(self):
        """Test ValidationError without field."""
        error = ValidationError("Invalid data")
        assert error.field is None

    def test_database_error_creation(self):
        """Test DatabaseError can be created and raised."""
        error = DatabaseError("Connection timeout")
        assert str(error) == "Connection timeout"
        assert isinstance(error, DomainError)

    def test_cycle_detected_error_attributes(self):
        """Test CycleDetectedError stores cycle_path."""
        path = ["issue-1", "issue-2", "issue-3", "issue-1"]
        error = CycleDetectedError("Cycle detected", cycle_path=path)
        assert error.cycle_path == path
        assert str(error) == "Cycle detected"

    def test_cycle_detected_error_default_path(self):
        """Test CycleDetectedError with default empty path."""
        error = CycleDetectedError("Cycle detected")
        assert error.cycle_path == []

    def test_all_errors_are_domain_errors(self):
        """Test that all custom errors inherit from DomainError."""
        errors = [
            NotFoundError("test"),
            ValidationError("test"),
            InvalidTransitionError("test", "id", "open", "closed"),
            InvariantViolationError("test"),
            DatabaseError("test"),
            CycleDetectedError("test"),
        ]
        for error in errors:
            assert isinstance(error, DomainError)

    def test_errors_can_be_caught_as_domain_error(self):
        """Test that specific errors can be caught as DomainError."""
        try:
            raise ValidationError("Test error")
        except DomainError as e:
            assert isinstance(e, ValidationError)
            assert str(e) == "Test error"

    def test_not_found_error_preserves_entity_id(self):
        """Test NotFoundError preserves entity_id attribute."""
        error = NotFoundError("Entity not found", entity_id="test-123")
        assert error.entity_id == "test-123"

    def test_invalid_transition_error_preserves_states(self):
        """Test InvalidTransitionError preserves state information."""
        error = InvalidTransitionError(
            "Cannot transition", entity_id="id-1", current_state="open", target_state="archived"
        )
        assert error.entity_id == "id-1"
        assert error.current_state == "open"
        assert error.target_state == "archived"

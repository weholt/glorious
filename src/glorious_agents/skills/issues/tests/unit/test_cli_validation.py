"""Tests for CLI input validation."""

from datetime import datetime

import pytest

from issue_tracker.cli.validation import (
    validate_date_string,
    validate_issue_id,
    validate_issue_type,
    validate_labels,
    validate_positive_integer,
    validate_priority,
    validate_status,
    validate_title,
)
from issue_tracker.domain import IssuePriority, IssueStatus, IssueType, ValidationError


class TestValidateIssueId:
    """Tests for validate_issue_id function."""

    def test_valid_issue_id(self):
        """Test validation of valid issue ID."""
        result = validate_issue_id("issue-abc123")
        assert result == "issue-abc123"

    def test_empty_issue_id(self):
        """Test validation rejects empty issue ID."""
        with pytest.raises(ValidationError) as exc:
            validate_issue_id("")
        assert "cannot be empty" in str(exc.value)

    def test_invalid_format(self):
        """Test validation rejects invalid format."""
        with pytest.raises(ValidationError) as exc:
            validate_issue_id("invalid")
        assert "Invalid issue ID format" in str(exc.value)

    def test_missing_hyphen(self):
        """Test validation rejects ID without hyphen."""
        with pytest.raises(ValidationError):
            validate_issue_id("issueabc123")


class TestValidatePriority:
    """Tests for validate_priority function."""

    def test_valid_priority_int(self):
        """Test validation of valid priority integer."""
        result = validate_priority(1)
        assert result == IssuePriority.HIGH

    def test_valid_priority_string(self):
        """Test validation of priority as string."""
        result = validate_priority("2")
        assert result == IssuePriority.MEDIUM

    def test_priority_out_of_range(self):
        """Test validation rejects out of range priority."""
        with pytest.raises(ValidationError) as exc:
            validate_priority(5)
        assert "between 0" in str(exc.value)

    def test_negative_priority(self):
        """Test validation rejects negative priority."""
        with pytest.raises(ValidationError):
            validate_priority(-1)

    def test_invalid_priority_type(self):
        """Test validation rejects invalid type."""
        with pytest.raises(ValidationError):
            validate_priority("invalid")


class TestValidateStatus:
    """Tests for validate_status function."""

    def test_valid_status(self):
        """Test validation of valid status."""
        result = validate_status("open")
        assert result == IssueStatus.OPEN

    def test_invalid_status(self):
        """Test validation rejects invalid status."""
        with pytest.raises(ValidationError) as exc:
            validate_status("invalid")
        assert "Invalid status" in str(exc.value)

    def test_status_case_sensitive(self):
        """Test that status validation is case-sensitive."""
        with pytest.raises(ValidationError):
            validate_status("Open")


class TestValidateIssueType:
    """Tests for validate_issue_type function."""

    def test_valid_type(self):
        """Test validation of valid issue type."""
        result = validate_issue_type("bug")
        assert result == IssueType.BUG

    def test_invalid_type(self):
        """Test validation rejects invalid type."""
        with pytest.raises(ValidationError) as exc:
            validate_issue_type("invalid")
        assert "Invalid issue type" in str(exc.value)


class TestValidateDateString:
    """Tests for validate_date_string function."""

    def test_valid_date_only(self):
        """Test validation of date-only string."""
        result = validate_date_string("2025-01-15")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_valid_datetime_iso(self):
        """Test validation of ISO datetime string."""
        result = validate_date_string("2025-01-15T10:30:00")
        assert isinstance(result, datetime)
        assert result.hour == 10
        assert result.minute == 30

    def test_empty_date_string(self):
        """Test validation rejects empty date."""
        with pytest.raises(ValidationError) as exc:
            validate_date_string("")
        assert "cannot be empty" in str(exc.value)

    def test_invalid_date_format(self):
        """Test validation rejects invalid format."""
        with pytest.raises(ValidationError) as exc:
            validate_date_string("15-01-2025")
        assert "Invalid date format" in str(exc.value)


class TestValidateTitle:
    """Tests for validate_title function."""

    def test_valid_title(self):
        """Test validation of valid title."""
        result = validate_title("Test Issue")
        assert result == "Test Issue"

    def test_title_with_whitespace(self):
        """Test title with leading/trailing whitespace."""
        result = validate_title("  Test Issue  ")
        assert result == "Test Issue"

    def test_empty_title(self):
        """Test validation rejects empty title."""
        with pytest.raises(ValidationError) as exc:
            validate_title("")
        assert "cannot be empty" in str(exc.value)

    def test_whitespace_only_title(self):
        """Test validation rejects whitespace-only title."""
        with pytest.raises(ValidationError):
            validate_title("   ")

    def test_title_too_long(self):
        """Test validation rejects overly long title."""
        long_title = "x" * 201
        with pytest.raises(ValidationError) as exc:
            validate_title(long_title)
        assert "cannot exceed 200 characters" in str(exc.value)


class TestValidateLabels:
    """Tests for validate_labels function."""

    def test_valid_labels_string(self):
        """Test validation of comma-separated labels."""
        result = validate_labels("bug,urgent,backend")
        assert result == ["bug", "urgent", "backend"]

    def test_valid_labels_list(self):
        """Test validation of label list."""
        result = validate_labels(["bug", "urgent"])
        assert result == ["bug", "urgent"]

    def test_empty_labels_string(self):
        """Test empty labels string returns empty list."""
        result = validate_labels("")
        assert result == []

    def test_labels_with_whitespace(self):
        """Test labels with whitespace are trimmed."""
        result = validate_labels(" bug , urgent , backend ")
        assert result == ["bug", "urgent", "backend"]

    def test_label_too_long(self):
        """Test validation rejects overly long label."""
        long_label = "x" * 51
        with pytest.raises(ValidationError) as exc:
            validate_labels(long_label)
        assert "exceeds 50 character limit" in str(exc.value)

    def test_label_invalid_characters(self):
        """Test validation rejects labels with invalid characters."""
        with pytest.raises(ValidationError) as exc:
            validate_labels("bug@urgent")
        assert "invalid characters" in str(exc.value)


class TestValidatePositiveInteger:
    """Tests for validate_positive_integer function."""

    def test_valid_positive_integer(self):
        """Test validation of valid positive integer."""
        result = validate_positive_integer(5)
        assert result == 5

    def test_zero_with_min_zero(self):
        """Test zero is valid with min_value=0."""
        result = validate_positive_integer(0, min_value=0)
        assert result == 0

    def test_value_below_minimum(self):
        """Test validation rejects value below minimum."""
        with pytest.raises(ValidationError) as exc:
            validate_positive_integer(0, min_value=1)
        assert "must be at least 1" in str(exc.value)

    def test_negative_value(self):
        """Test validation rejects negative value."""
        with pytest.raises(ValidationError):
            validate_positive_integer(-5)

    def test_string_integer(self):
        """Test validation accepts string integer."""
        result = validate_positive_integer("10")
        assert result == 10

    def test_invalid_string(self):
        """Test validation rejects non-numeric string."""
        with pytest.raises(ValidationError) as exc:
            validate_positive_integer("abc")
        assert "Expected a positive integer" in str(exc.value)

"""Input validation utilities for CLI commands."""

import re
from datetime import datetime
from typing import Any

from issue_tracker.domain import IssuePriority, IssueStatus, IssueType, ValidationError

__all__ = [
    "validate_issue_id",
    "validate_priority",
    "validate_status",
    "validate_issue_type",
    "validate_date_string",
    "validate_title",
    "validate_labels",
    "validate_positive_integer",
]


def validate_issue_id(issue_id: str) -> str:
    """Validate issue ID format.

    Args:
        issue_id: Issue ID to validate

    Returns:
        Validated issue ID

    Raises:
        ValidationError: If issue ID format is invalid
    """
    if not issue_id:
        raise ValidationError("Issue ID cannot be empty", field="issue_id")

    # Expected format: prefix-hexstring (e.g., issue-abc123)
    pattern = r"^[a-z][a-z0-9-]+-[a-f0-9]{6}$"
    if not re.match(pattern, issue_id):
        raise ValidationError(
            f"Invalid issue ID format: {issue_id}. Expected format: prefix-hexstring (e.g., issue-abc123)",
            field="issue_id",
        )

    return issue_id


def validate_priority(priority: int | str) -> IssuePriority:
    """Validate priority value.

    Args:
        priority: Priority value (0-4 or IssuePriority enum)

    Returns:
        Validated IssuePriority enum

    Raises:
        ValidationError: If priority is invalid
    """
    try:
        if isinstance(priority, str):
            priority = int(priority)

        if not 0 <= priority <= 4:
            raise ValidationError(
                f"Priority must be between 0 (critical) and 4 (backlog), got: {priority}",
                field="priority",
            )

        return IssuePriority(priority)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid priority value: {priority}", field="priority") from e


def validate_status(status: str) -> IssueStatus:
    """Validate status value.

    Args:
        status: Status string

    Returns:
        Validated IssueStatus enum

    Raises:
        ValidationError: If status is invalid
    """
    valid_statuses = [s.value for s in IssueStatus]
    if status not in valid_statuses:
        raise ValidationError(
            f"Invalid status: {status}. Valid values: {', '.join(valid_statuses)}",
            field="status",
        )

    return IssueStatus(status)


def validate_issue_type(issue_type: str) -> IssueType:
    """Validate issue type value.

    Args:
        issue_type: Issue type string

    Returns:
        Validated IssueType enum

    Raises:
        ValidationError: If issue type is invalid
    """
    valid_types = [t.value for t in IssueType]
    if issue_type not in valid_types:
        raise ValidationError(
            f"Invalid issue type: {issue_type}. Valid values: {', '.join(valid_types)}",
            field="type",
        )

    return IssueType(issue_type)


def validate_date_string(date_str: str, field_name: str = "date") -> datetime:
    """Validate and parse date string.

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        field_name: Name of the field for error messages

    Returns:
        Parsed datetime object

    Raises:
        ValidationError: If date format is invalid
    """
    if not date_str:
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)

    try:
        # Try ISO format with time
        if "T" in date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # Try date only format
        else:
            return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValidationError(
            f"Invalid date format for {field_name}: {date_str}. Expected YYYY-MM-DD or ISO format",
            field=field_name,
        ) from e


def validate_title(title: str) -> str:
    """Validate issue title.

    Args:
        title: Issue title

    Returns:
        Validated title

    Raises:
        ValidationError: If title is invalid
    """
    if not title or not title.strip():
        raise ValidationError("Title cannot be empty", field="title")

    if len(title) > 200:
        raise ValidationError("Title cannot exceed 200 characters", field="title")

    return title.strip()


def validate_labels(labels: str | list[str]) -> list[str]:
    """Validate and parse labels.

    Args:
        labels: Comma-separated string or list of labels

    Returns:
        List of validated label strings

    Raises:
        ValidationError: If labels are invalid
    """
    if isinstance(labels, str):
        if not labels.strip():
            return []
        labels = [lbl.strip() for lbl in labels.split(",")]

    # Validate each label
    validated = []
    for label in labels:
        if not label:
            continue
        if len(label) > 50:
            raise ValidationError(f"Label '{label}' exceeds 50 character limit", field="labels")
        if not re.match(r"^[a-zA-Z0-9_-]+$", label):
            raise ValidationError(
                f"Label '{label}' contains invalid characters. Use only letters, numbers, hyphens, and underscores",
                field="labels",
            )
        validated.append(label)

    return validated


def validate_positive_integer(value: Any, field_name: str = "value", min_value: int = 1) -> int:
    """Validate positive integer value.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value (default: 1)

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is not a valid positive integer
    """
    try:
        int_value = int(value)
        if int_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}, got: {int_value}",
                field=field_name,
            )
        return int_value
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid {field_name}: {value}. Expected a positive integer", field=field_name) from e

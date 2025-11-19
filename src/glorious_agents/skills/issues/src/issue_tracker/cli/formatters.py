"""Output formatters for CLI commands."""

from datetime import datetime
from typing import Any

from issue_tracker.domain import Issue, IssuePriority

__all__ = ["format_datetime_iso", "format_priority_emoji", "issue_to_dict"]


def format_datetime_iso(dt: datetime | None) -> str | None:
    """Format datetime to ISO string with Z suffix."""
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def format_priority_emoji(priority: IssuePriority | int) -> str:
    """Format priority as emoji label."""
    priority_labels = {
        0: "🔴 Critical",
        1: "🟠 High",
        2: "🟡 Medium",
        3: "🟢 Low",
        4: "⚪ Backlog",
    }
    priority_val = int(priority) if isinstance(priority, IssuePriority) else priority
    return priority_labels.get(priority_val, "⚪ Unknown")


def issue_to_dict(issue: Issue) -> dict[str, Any]:
    """Convert issue entity to dictionary with formatted fields."""
    return {
        "id": issue.id,
        "project_id": issue.project_id,
        "title": issue.title,
        "description": issue.description,
        "type": issue.type.value,
        "priority": int(issue.priority),
        "status": issue.status.value,
        "assignee": issue.assignee,
        "labels": issue.labels,
        "created_at": format_datetime_iso(issue.created_at),
        "updated_at": format_datetime_iso(issue.updated_at),
        "closed_at": format_datetime_iso(issue.closed_at),
        "epic_id": issue.epic_id,
    }

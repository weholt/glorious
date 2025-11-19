"""Data models for issues skill - re-exports from domain layer.

The issues skill uses a domain-driven design with entities in domain/entities/.
This module provides a simplified interface to those domain models.
"""

# Re-export domain entities
# Re-export database models (for migrations)
from issue_tracker.adapters.db.models import (
    CommentModel,
    DependencyModel,
    EpicModel,
    IssueLabelModel,
    IssueModel,
    LabelModel,
)
from issue_tracker.domain.entities.comment import Comment
from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.entities.epic import Epic
from issue_tracker.domain.entities.issue import Issue, IssuePriority, IssueStatus, IssueType
from issue_tracker.domain.entities.label import Label

__all__ = [
    # Domain entities
    "Issue",
    "IssueStatus",
    "IssueType",
    "IssuePriority",
    "Comment",
    "Dependency",
    "DependencyType",
    "Epic",
    "Label",
    # Database models
    "IssueModel",
    "CommentModel",
    "DependencyModel",
    "EpicModel",
    "LabelModel",
    "IssueLabelModel",
]

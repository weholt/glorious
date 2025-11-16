"""SQLModel database models for issue tracking.

Maps domain entities to database tables with proper relationships and indexes.
"""

from datetime import datetime

from sqlmodel import Column, Field, Index, SQLModel, String


class IssueModel(SQLModel, table=True):
    """Issue table model.

    Maps to issue_tracker.domain.entities.issue.Issue
    """

    __tablename__ = "issues"
    __table_args__ = (
        # Composite index for common queries
        Index("ix_issues_status_priority", "status", "priority"),
        Index("ix_issues_project_status", "project_id", "status"),
        Index("ix_issues_assignee_status", "assignee", "status"),
        Index("ix_issues_created_status", "created_at", "status"),
    )

    id: str = Field(primary_key=True, max_length=50)
    project_id: str = Field(index=True, max_length=50)
    title: str = Field(max_length=500)
    description: str = Field(default="", sa_column=Column(String))
    status: str = Field(max_length=20, index=True)
    priority: int = Field(default=2, index=True)
    type: str = Field(max_length=20, index=True)
    assignee: str | None = Field(default=None, max_length=100, index=True)
    epic_id: str | None = Field(default=None, max_length=50, index=True)
    created_at: datetime = Field(index=True)
    updated_at: datetime = Field(index=True)
    closed_at: datetime | None = Field(default=None, index=True)


class LabelModel(SQLModel, table=True):
    """Label table model.

    Maps to issue_tracker.domain.entities.label.Label
    """

    __tablename__ = "labels"

    id: str = Field(primary_key=True, max_length=50)
    project_id: str = Field(index=True, max_length=50)
    name: str = Field(max_length=100, index=True)
    color: str | None = Field(default=None, max_length=7)  # Hex color
    created_at: datetime


class IssueLabelModel(SQLModel, table=True):
    """Junction table for issue-label many-to-many relationship."""

    __tablename__ = "issue_labels"

    issue_id: str = Field(foreign_key="issues.id", primary_key=True, max_length=50)
    label_name: str = Field(primary_key=True, max_length=100)
    created_at: datetime


class CommentModel(SQLModel, table=True):
    """Comment table model.

    Maps to issue_tracker.domain.entities.comment.Comment
    """

    __tablename__ = "comments"

    id: str = Field(primary_key=True, max_length=50)
    issue_id: str = Field(foreign_key="issues.id", index=True, max_length=50)
    author: str = Field(max_length=100, index=True)
    content: str = Field(sa_column=Column(String))
    created_at: datetime = Field(index=True)
    updated_at: datetime


class DependencyModel(SQLModel, table=True):
    """Dependency edge table for issue relationships.

    Maps to issue_tracker.domain.entities.dependency.Dependency
    """

    __tablename__ = "dependencies"
    __table_args__ = (
        # Composite index for dependency graph traversal
        Index("ix_dependencies_from_to", "from_issue_id", "to_issue_id"),
        Index("ix_dependencies_to_type", "to_issue_id", "type"),
    )

    id: str = Field(primary_key=True, max_length=50)
    from_issue_id: str = Field(foreign_key="issues.id", index=True, max_length=50)
    to_issue_id: str = Field(foreign_key="issues.id", index=True, max_length=50)
    type: str = Field(max_length=20, index=True)  # blocks, depends-on, related-to
    created_at: datetime


class EpicModel(SQLModel, table=True):
    """Epic table model.

    Maps to issue_tracker.domain.entities.epic.Epic
    Note: Epics are also stored in issues table with type='epic'
    This table stores epic-specific metadata.
    """

    __tablename__ = "epics"

    id: str = Field(foreign_key="issues.id", primary_key=True, max_length=50)
    project_id: str = Field(index=True, max_length=50)
    status: str = Field(max_length=20, index=True)
    progress: int = Field(default=0)  # 0-100
    parent_epic_id: str | None = Field(default=None, max_length=50, index=True)
    start_date: datetime | None = None
    target_date: datetime | None = None
    completed_date: datetime | None = None

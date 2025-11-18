"""Domain models for planner skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class PlannerTask(SQLModel, table=True):
    """Task in the planner queue.

    Represents an actionable task with priority, status tracking,
    and metadata for project management.
    """

    __tablename__ = "planner_queue"

    id: int | None = Field(default=None, primary_key=True)
    issue_id: str = Field(max_length=200, index=True)
    priority: int = Field(default=0, index=True)
    status: str = Field(default="queued", max_length=20, index=True)
    project_id: str = Field(default="", max_length=200, index=True)
    tags: str = Field(default="", max_length=500)
    important: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "issue_id": "PROJ-123",
                "priority": 10,
                "status": "queued",
                "project_id": "my-project",
                "important": True,
            }
        }

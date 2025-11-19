"""Domain models for sandbox skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Sandbox(SQLModel, table=True):
    """Sandbox container tracking.

    Represents a Docker-based isolated execution environment
    with status tracking and logging.
    """

    __tablename__ = "sandboxes"

    id: int | None = Field(default=None, primary_key=True)
    container_id: str = Field(max_length=200, unique=True, index=True)
    image: str = Field(max_length=200)
    status: str = Field(max_length=50, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = Field(default=None)
    exit_code: int | None = Field(default=None)
    logs: str = Field(default="")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "container_id": "abc123def456",
                "image": "python:3.12-slim",
                "status": "completed",
                "exit_code": 0,
            }
        }

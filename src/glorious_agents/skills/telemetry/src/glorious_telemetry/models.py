"""Domain models for telemetry skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class TelemetryEvent(SQLModel, table=True):
    """Telemetry event tracking.

    Represents logged events from agent actions with
    categorization, timing, and metadata.
    """

    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    category: str = Field(max_length=100, index=True)
    event: str = Field(max_length=500)
    project_id: str = Field(default="", max_length=200)
    skill: str = Field(default="", max_length=100, index=True)
    duration_ms: int = Field(default=0)
    status: str = Field(default="success", max_length=50)
    meta: str = Field(default="")  # JSON string

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "category": "task_execution",
                "event": "Task completed successfully",
                "skill": "planner",
                "duration_ms": 1500,
                "status": "success",
            }
        }

"""Domain models for orchestrator skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Workflow(SQLModel, table=True):
    """Workflow execution record.

    Represents a multi-step workflow with intent, steps,
    and execution status tracking.
    """

    __tablename__ = "workflows"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=500, index=True)
    intent: str | None = Field(default=None, max_length=2000)
    steps: str | None = Field(default=None)  # JSON string
    status: str = Field(default="pending", max_length=50, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "Deploy feature X",
                "intent": "Deploy new feature to production",
                "steps": '["build", "test", "deploy"]',
                "status": "pending",
            }
        }

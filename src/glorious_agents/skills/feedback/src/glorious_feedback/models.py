"""Domain models for feedback skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Feedback(SQLModel, table=True):
    """Action feedback tracking.

    Represents feedback records for actions with status,
    reason, and optional metadata.
    """

    __tablename__ = "feedback"

    id: int | None = Field(default=None, primary_key=True)
    action_id: str = Field(max_length=200, index=True)
    action_type: str = Field(default="", max_length=100, index=True)
    status: str = Field(max_length=50, index=True)
    reason: str = Field(default="", max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    meta: str = Field(default="")  # JSON string

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "action_id": "task-123",
                "action_type": "deployment",
                "status": "success",
                "reason": "Completed successfully",
            }
        }

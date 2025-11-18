"""Domain models for vacuum skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class VacuumOperation(SQLModel, table=True):
    """Vacuum operation tracking.

    Represents a knowledge distillation/optimization operation
    with metrics and status tracking.
    """

    __tablename__ = "vacuum_operations"

    id: int | None = Field(default=None, primary_key=True)
    mode: str = Field(max_length=50, index=True)
    items_processed: int = Field(default=0)
    items_modified: int = Field(default=0)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)
    status: str = Field(default="running", max_length=20, index=True)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "mode": "summarize",
                "items_processed": 100,
                "items_modified": 25,
                "status": "completed",
            }
        }

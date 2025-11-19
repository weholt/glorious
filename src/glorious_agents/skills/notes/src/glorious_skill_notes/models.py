"""Domain models for notes skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Note(SQLModel, table=True):
    """Note with full-text search support.

    Represents a persistable note with tags, timestamps,
    and importance levels for prioritization.
    """

    __tablename__ = "notes"

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(max_length=100000)
    tags: str = Field(default="", max_length=500, index=True)
    importance: int = Field(default=0, ge=0, le=2, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "content": "Remember to review the code changes",
                "tags": "todo,review",
                "importance": 1,
            }
        }

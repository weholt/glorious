"""Domain models for linker skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Link(SQLModel, table=True):
    """Link between two entities.

    Represents a semantic relationship between entities
    with type, weight, and bidirectional queries.
    """

    __tablename__ = "links"

    id: int | None = Field(default=None, primary_key=True)
    kind: str = Field(max_length=100, index=True)
    a_type: str = Field(max_length=50, index=True)
    a_id: str = Field(max_length=200, index=True)
    b_type: str = Field(max_length=50, index=True)
    b_id: str = Field(max_length=200, index=True)
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "kind": "related_to",
                "a_type": "issue",
                "a_id": "PROJ-123",
                "b_type": "note",
                "b_id": "456",
                "weight": 1.0,
            }
        }

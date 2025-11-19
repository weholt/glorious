"""Domain models for prompts skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Prompt(SQLModel, table=True):
    """Prompt template with versioning.

    Represents a versioned prompt template with metadata
    for template management and rendering.
    """

    __tablename__ = "prompts"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    version: int = Field(default=1, index=True)
    template: str = Field(max_length=100000)
    meta: str | None = Field(default=None)  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "system_prompt",
                "version": 1,
                "template": "You are a helpful assistant. Context: {context}",
            }
        }

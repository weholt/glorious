"""Domain models for docs skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    """Document with versioning support.

    Represents a document with title, content, and optional epic association.
    Supports versioning for tracking changes over time.
    """

    __tablename__ = "docs_documents"

    id: str = Field(primary_key=True, max_length=200)
    title: str = Field(max_length=500, index=True)
    content: str = Field()
    epic_id: str | None = Field(default=None, max_length=200, index=True)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "doc-abc123",
                "title": "API Documentation",
                "content": "# API Documentation\n\nThis is the API documentation...",
                "epic_id": "epic-1",
                "version": 1,
            }
        }


class DocumentVersion(SQLModel, table=True):
    """Document version history.

    Stores historical versions of document content for rollback and audit trail.
    """

    __tablename__ = "docs_versions"

    id: int | None = Field(default=None, primary_key=True)
    doc_id: str = Field(max_length=200, index=True, foreign_key="docs_documents.id")
    version: int = Field()
    content: str = Field()
    changed_by: str | None = Field(default=None, max_length=200)
    changed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "doc_id": "doc-abc123",
                "version": 2,
                "content": "Updated content...",
            }
        }

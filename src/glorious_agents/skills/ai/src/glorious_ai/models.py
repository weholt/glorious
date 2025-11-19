"""Domain models for ai skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class AIEmbedding(SQLModel, table=True):
    """AI embedding record.

    Stores embeddings for content with model metadata.
    The embedding is stored as a pickled blob.
    """

    __tablename__ = "ai_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field()
    embedding: bytes = Field()  # Pickled numpy array
    embedding_metadata: str | None = Field(default=None)  # JSON string
    model: str = Field(max_length=100, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "content": "Sample text for embedding",
                "model": "text-embedding-ada-002",
            }
        }


class AICompletion(SQLModel, table=True):
    """AI completion record.

    Stores LLM completion requests and responses with usage metadata.
    """

    __tablename__ = "ai_completions"

    id: int | None = Field(default=None, primary_key=True)
    prompt: str = Field()
    response: str = Field()
    model: str = Field(max_length=100, index=True)
    provider: str = Field(max_length=50)
    tokens_used: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "prompt": "What is Python?",
                "response": "Python is a programming language...",
                "model": "gpt-4",
                "provider": "openai",
                "tokens_used": 150,
            }
        }

"""Repository for AI data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import AICompletion, AIEmbedding


class AIEmbeddingRepository(BaseRepository[AIEmbedding]):
    """Repository for AI embeddings with domain-specific queries."""

    def get_by_model(self, model: str, limit: int = 100) -> list[AIEmbedding]:
        """Get embeddings by model.

        Args:
            model: Model name to filter by
            limit: Maximum number of embeddings

        Returns:
            List of embeddings for the specified model
        """
        statement = (
            select(AIEmbedding)
            .where(AIEmbedding.model == model)
            .order_by(AIEmbedding.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent(self, limit: int = 20) -> list[AIEmbedding]:
        """Get recent embeddings.

        Args:
            limit: Maximum number of embeddings

        Returns:
            List of recent embeddings
        """
        statement = select(AIEmbedding).order_by(AIEmbedding.created_at.desc()).limit(limit)
        return list(self.session.exec(statement))


class AICompletionRepository(BaseRepository[AICompletion]):
    """Repository for AI completions with domain-specific queries."""

    def get_by_model(self, model: str, limit: int = 100) -> list[AICompletion]:
        """Get completions by model.

        Args:
            model: Model name to filter by
            limit: Maximum number of completions

        Returns:
            List of completions for the specified model
        """
        statement = (
            select(AICompletion)
            .where(AICompletion.model == model)
            .order_by(AICompletion.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_by_provider(self, provider: str, limit: int = 100) -> list[AICompletion]:
        """Get completions by provider.

        Args:
            provider: Provider name to filter by
            limit: Maximum number of completions

        Returns:
            List of completions for the specified provider
        """
        statement = (
            select(AICompletion)
            .where(AICompletion.provider == provider)
            .order_by(AICompletion.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent(self, limit: int = 20) -> list[AICompletion]:
        """Get recent completions.

        Args:
            limit: Maximum number of completions

        Returns:
            List of recent completions
        """
        statement = select(AICompletion).order_by(AICompletion.created_at.desc()).limit(limit)
        return list(self.session.exec(statement))

    def search_completions(self, query: str, limit: int = 10) -> list[AICompletion]:
        """Search completions by prompt or response.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching completions
        """
        query_pattern = f"%{query}%"
        statement = (
            select(AICompletion)
            .where(
                (AICompletion.prompt.like(query_pattern))
                | (AICompletion.response.like(query_pattern))
            )
            .order_by(AICompletion.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

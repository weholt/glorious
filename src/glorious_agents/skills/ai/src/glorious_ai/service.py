"""Business logic for AI skill."""

import os
import pickle
from typing import Any

import numpy as np

from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import AICompletion, AIEmbedding
from .repository import AICompletionRepository, AIEmbeddingRepository


class AIService:
    """Service layer for AI operations.

    Handles LLM completions, embeddings, and semantic search
    while delegating data access to repositories.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize service with dependencies.

        Args:
            uow: Unit of Work for transaction management
        """
        self.uow = uow
        self.completion_repo = AICompletionRepository(uow.session, AICompletion)
        self.embedding_repo = AIEmbeddingRepository(uow.session, AIEmbedding)

    def complete(
        self, prompt: str, model: str = "gpt-4", provider: str = "openai", max_tokens: int = 1000
    ) -> dict[str, Any]:
        """Generate LLM completion.

        Args:
            prompt: The prompt text
            model: Model name
            provider: Provider name (openai/anthropic)
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with response and metadata

        Raises:
            ValueError: If API key is missing or provider is unknown
        """
        api_key = os.getenv(f"{provider.upper()}_API_KEY")
        if not api_key:
            raise ValueError(f"Missing API key for {provider}")

        if provider == "openai":
            try:
                from openai import OpenAI

                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                result = {
                    "response": response.choices[0].message.content,
                    "model": model,
                    "provider": provider,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                }
            except ImportError:
                raise ValueError("OpenAI library not installed")
        elif provider == "anthropic":
            try:
                from anthropic import Anthropic

                client = Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = {
                    "response": response.content[0].text,
                    "model": model,
                    "provider": provider,
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                }
            except ImportError:
                raise ValueError("Anthropic library not installed")
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Store completion
        completion = AICompletion(
            prompt=prompt,
            response=result["response"],
            model=model,
            provider=provider,
            tokens_used=result["tokens_used"],
        )
        self.completion_repo.add(completion)

        return result

    def embed(self, content: str, model: str = "text-embedding-ada-002") -> list[float]:
        """Generate embeddings for content.

        Args:
            content: Content to embed
            model: Embedding model name

        Returns:
            List of embedding values

        Raises:
            ValueError: If API key is missing
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY")

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(model=model, input=content)
            embedding = response.data[0].embedding

            # Store embedding
            embedding_blob = pickle.dumps(embedding)
            ai_embedding = AIEmbedding(
                content=content,
                embedding=embedding_blob,
                model=model,
            )
            self.embedding_repo.add(ai_embedding)

            return embedding
        except ImportError:
            raise ValueError("OpenAI library not installed")

    def semantic_search(
        self, query: str, model: str = "text-embedding-ada-002", top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Perform semantic search using embeddings.

        Args:
            query: Search query
            model: Embedding model name
            top_k: Number of results to return

        Returns:
            List of search results with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embed(query, model)
        query_vec = np.array(query_embedding, dtype=np.float32)

        # Get all embeddings for the model
        embeddings = self.embedding_repo.get_by_model(model, limit=1000)

        if not embeddings:
            return []

        similarities = []
        for embedding_record in embeddings:
            embedding = pickle.loads(embedding_record.embedding)
            doc_vec = np.array(embedding, dtype=np.float32)
            similarity = np.dot(query_vec, doc_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
            )
            similarities.append(
                {
                    "id": embedding_record.id,
                    "content": embedding_record.content,
                    "similarity": float(similarity),
                }
            )

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    def get_completion_history(self, limit: int = 10) -> list[AICompletion]:
        """Get completion history.

        Args:
            limit: Maximum number of completions

        Returns:
            List of recent completions
        """
        return self.completion_repo.get_recent(limit)

    def search_completions(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Universal search for completions.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        completions = self.completion_repo.search_completions(query, limit)

        results = []
        query_lower = query.lower()

        for completion in completions:
            score = 0.0

            # Score based on match quality
            if completion.prompt and query_lower in completion.prompt.lower():
                score += 0.8

            if completion.response and query_lower in completion.response.lower():
                score += 0.6

            # Ensure score is between 0 and 1
            score = min(1.0, max(0.0, score))

            # Create content preview
            prompt_preview = (
                completion.prompt[:100] + "..."
                if len(completion.prompt) > 100
                else completion.prompt
            )
            response_preview = (
                completion.response[:200] + "..."
                if len(completion.response) > 200
                else completion.response
            )
            content = f"{prompt_preview}\n\n{response_preview}"

            results.append(
                SearchResult(
                    skill="ai",
                    id=f"completion-{completion.id}",
                    type="completion",
                    content=content,
                    metadata={
                        "model": completion.model,
                        "provider": completion.provider,
                        "tokens": completion.tokens_used,
                    },
                    score=score,
                )
            )

        return results

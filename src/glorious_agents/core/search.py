"""Universal search protocol for skills."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class SearchResult:
    """Standard search result format for all skills.

    Attributes:
        skill: Name of the skill that returned this result
        id: Unique identifier within the skill (e.g., note_id, issue_id)
        type: Type of entity (e.g., 'note', 'issue', 'task', 'prompt')
        content: Main content/text of the result
        metadata: Additional contextual information (tags, dates, status, etc)
        score: Relevance score (0.0-1.0, higher is more relevant)
    """

    skill: str
    id: str | int
    type: str
    content: str
    metadata: dict[str, Any]
    score: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "skill": self.skill,
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
        }


class SearchableSkill(Protocol):
    """Protocol for skills that support search functionality.

    Skills should implement a search() function that returns SearchResult objects.
    The function should be exposed as a callable API (not just a CLI command).

    Example:
        def search(query: str, limit: int = 10) -> list[SearchResult]:
            results = []
            # Perform search logic
            for item in matching_items:
                results.append(SearchResult(
                    skill="notes",
                    id=item.id,
                    type="note",
                    content=item.content,
                    metadata={"tags": item.tags, "created_at": item.created_at},
                    score=item.relevance_score
                ))
            return results
    """

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for items matching the query.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects, ordered by relevance
        """
        ...


def search_all_skills(
    ctx: Any, query: str, limit_per_skill: int = 10, total_limit: int = 50
) -> list[SearchResult]:
    """Search across all registered skills that support search.

    Args:
        ctx: SkillContext instance with registered skills
        query: Search query string
        limit_per_skill: Max results per skill
        total_limit: Max total results across all skills

    Returns:
        Aggregated and sorted list of SearchResult objects
    """
    all_results: list[SearchResult] = []

    # Get all registered skills
    for skill_name in dir(ctx):
        skill = getattr(ctx, skill_name, None)
        if skill is None:
            continue

        # Check if skill has search method
        if hasattr(skill, "search") and callable(skill.search):
            try:
                results = skill.search(query, limit=limit_per_skill)
                all_results.extend(results)
            except Exception:
                # Skip skills that fail to search
                continue

    # Sort by score (descending) and limit
    all_results.sort(key=lambda r: r.score, reverse=True)
    return all_results[:total_limit]

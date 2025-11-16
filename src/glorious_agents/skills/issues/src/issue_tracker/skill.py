from __future__ import annotations

from typing import TYPE_CHECKING

from issue_tracker.cli.app import app

if TYPE_CHECKING:
    from glorious_agents.core.search import SearchResult

"""Issue-tracker skill for Glorious Agents."""

# Re-export existing app
__all__ = ["app", "search"]


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for issues using FTS5 full-text search.

    Searches across issue titles, descriptions, and comments using
    SQLite FTS5 for fast and relevant results.

    Args:
        query: Search query string (supports FTS5 syntax)
        limit: Maximum number of results

    Returns:
        List of SearchResult objects ordered by relevance
    """
    from glorious_agents.core.search import SearchResult

    from issue_tracker.cli.dependencies import get_issue_service
    from issue_tracker.services.search_service import SearchService

    try:
        from sqlmodel import Session

        from issue_tracker.cli.dependencies import get_engine
        from issue_tracker.services.search_service import SearchService

        engine = get_engine()
        session = Session(engine)

        try:
            search_service = SearchService(session)
            fts_results = search_service.search(query=query, limit=limit, include_closed=False)

            if not fts_results:
                return []

            # Get full issue details
            issue_service = get_issue_service()
            results = []

            for fts_result in fts_results:
                try:
                    issue = issue_service.get_issue(fts_result.issue_id)
                    if not issue:
                        continue

                    # Convert BM25 rank to 0-1 score (higher rank = more relevant, but negative)
                    # BM25 scores are typically negative, closer to 0 is better
                    score = max(0.0, min(1.0, 1.0 / (1.0 + abs(fts_result.rank))))

                    results.append(
                        SearchResult(
                            skill="issues",
                            id=issue.id,
                            type=issue.type.value,
                            content=fts_result.snippet
                            or f"{issue.title}\n{issue.description[:200] if issue.description else ''}",
                            metadata={
                                "status": issue.status.value,
                                "priority": issue.priority.value,
                                "labels": issue.labels,
                                "created_at": issue.created_at.isoformat(),
                                "fts_rank": fts_result.rank,
                            },
                            score=score,
                        )
                    )
                except Exception:
                    # Skip issues that fail to load
                    continue

            return results
        finally:
            session.close()

    except Exception:
        # Fallback to empty results if FTS5 fails
        return []

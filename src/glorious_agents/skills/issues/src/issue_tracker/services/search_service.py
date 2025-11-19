"""Full-text search service using SQLite FTS5."""

from dataclasses import dataclass

from sqlmodel import Session, text

__all__ = ["SearchService", "SearchResult"]


@dataclass
class SearchResult:
    """Search result with relevance ranking."""

    issue_id: str
    rank: float
    snippet: str


class SearchService:
    """Service for full-text search using FTS5."""

    def __init__(self, session: Session) -> None:
        """Initialize search service.

        Args:
            session: SQLModel session for database access
        """
        self.session = session

    def search(self, query: str, limit: int = 20, include_closed: bool = False) -> list[SearchResult]:
        """Search issues using FTS5 full-text search.

        Args:
            query: Search query (supports FTS5 syntax)
            limit: Maximum number of results
            include_closed: Whether to include closed issues

        Returns:
            List of SearchResult objects ordered by relevance

        Examples:
            >>> service.search("authentication bug")
            >>> service.search("title:login OR description:password")
            >>> service.search("memory NEAR/3 leak")
        """
        # Build FTS5 query
        sql = text("""
            SELECT
                fts.id as issue_id,
                bm25(issues_fts) as rank,
                snippet(issues_fts, 1, '<mark>', '</mark>', '...', 32) as snippet,
                i.status
            FROM issues_fts fts
            JOIN issues i ON fts.id = i.id
            WHERE issues_fts MATCH :query
        """)

        if not include_closed:
            sql = text(str(sql) + " AND i.status != 'closed'")

        sql = text(str(sql) + " ORDER BY rank LIMIT :limit")

        results = self.session.exec(sql, params={"query": query, "limit": limit})

        return [SearchResult(issue_id=row.issue_id, rank=float(row.rank), snippet=row.snippet) for row in results]

    def search_by_field(self, field: str, query: str, limit: int = 20) -> list[SearchResult]:
        """Search specific field using FTS5.

        Args:
            field: Field to search (title, description, labels)
            query: Search query
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        fts_query = f"{field}:{query}"
        return self.search(fts_query, limit=limit)

    def rebuild_index(self) -> int:
        """Rebuild the FTS5 index from scratch.

        Returns:
            Number of issues indexed
        """
        # Clear existing FTS data
        self.session.exec(text("DELETE FROM issues_fts;"))

        # Rebuild from issues table
        self.session.exec(
            text("""
            INSERT INTO issues_fts(rowid, id, title, description)
            SELECT rowid, id, title, COALESCE(description, '')
            FROM issues;
        """)
        )

        self.session.commit()

        # Count indexed issues
        count_result = self.session.exec(text("SELECT COUNT(*) as cnt FROM issues_fts;"))
        return count_result.first().cnt if count_result else 0

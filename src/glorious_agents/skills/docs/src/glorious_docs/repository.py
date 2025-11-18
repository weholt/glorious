"""Repository for docs data access."""

from sqlalchemy import text
from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import Document, DocumentVersion


class DocumentRepository(BaseRepository[Document]):
    """Repository for documents with domain-specific queries."""

    def get_by_epic(self, epic_id: str, limit: int = 100) -> list[Document]:
        """Get documents by epic ID.

        Args:
            epic_id: Epic identifier
            limit: Maximum number of documents

        Returns:
            List of documents for the epic
        """
        statement = (
            select(Document)
            .where(Document.epic_id == epic_id)
            .order_by(Document.updated_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_recent(self, limit: int = 100) -> list[Document]:
        """Get recent documents.

        Args:
            limit: Maximum number of documents

        Returns:
            List of recent documents
        """
        statement = select(Document).order_by(Document.updated_at.desc()).limit(limit)
        return list(self.session.exec(statement))

    def search_fts(self, query: str, limit: int = 10) -> list[tuple[str, str, str, float]]:
        """Search documents using FTS5.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of tuples (doc_id, title, snippet, score)
        """
        # Use raw SQL for FTS5 queries
        sql = text("""
            SELECT d.id, d.title,
                   snippet(docs_fts, 1, '<mark>', '</mark>', '...', 32) as snippet,
                   rank
            FROM docs_fts
            JOIN docs_documents d ON docs_fts.rowid = d.rowid
            WHERE docs_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """)

        result = self.session.exec(sql, {"query": query, "limit": limit})
        return [(row[0], row[1], row[2], row[3]) for row in result]


class DocumentVersionRepository(BaseRepository[DocumentVersion]):
    """Repository for document versions."""

    def get_by_document(self, doc_id: str, limit: int = 100) -> list[DocumentVersion]:
        """Get version history for a document.

        Args:
            doc_id: Document identifier
            limit: Maximum number of versions

        Returns:
            List of versions ordered by version number (newest first)
        """
        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.doc_id == doc_id)
            .order_by(DocumentVersion.version.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_version(self, doc_id: str, version: int) -> DocumentVersion | None:
        """Get specific version of a document.

        Args:
            doc_id: Document identifier
            version: Version number

        Returns:
            Document version or None if not found
        """
        statement = select(DocumentVersion).where(
            (DocumentVersion.doc_id == doc_id) & (DocumentVersion.version == version)
        )
        return self.session.exec(statement).first()

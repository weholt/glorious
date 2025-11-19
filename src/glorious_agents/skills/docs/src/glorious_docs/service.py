"""Business logic for docs skill."""

import hashlib
from datetime import datetime
from pathlib import Path

import frontmatter

from glorious_agents.core.search import SearchResult
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Document, DocumentVersion
from .repository import DocumentRepository, DocumentVersionRepository


def generate_doc_id(title: str) -> str:
    """Generate a unique document ID from title."""
    hash_obj = hashlib.sha256(title.encode())
    return f"doc-{hash_obj.hexdigest()[:8]}"


class DocsService:
    """Service layer for documentation management.

    Handles document versioning, FTS search, and frontmatter parsing
    while delegating data access to repositories.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize service with dependencies.

        Args:
            uow: Unit of Work for transaction management
        """
        self.uow = uow
        self.doc_repo = DocumentRepository(uow.session, Document)
        self.version_repo = DocumentVersionRepository(uow.session, DocumentVersion)

    def create_document(
        self,
        title: str,
        content: str = "",
        epic_id: str | None = None,
        custom_id: str | None = None,
    ) -> Document:
        """Create a new document.

        Args:
            title: Document title
            content: Document content
            epic_id: Optional epic association
            custom_id: Optional custom document ID

        Returns:
            Created document

        Raises:
            ValueError: If document ID already exists
        """
        doc_id = custom_id or generate_doc_id(title)

        # Check if document already exists
        existing = self.doc_repo.get(doc_id)
        if existing:
            raise ValueError(f"Document {doc_id} already exists")

        # Create document
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            epic_id=epic_id,
            version=1,
        )
        document = self.doc_repo.add(document)

        # Create first version
        version = DocumentVersion(
            doc_id=doc_id,
            version=1,
            content=content,
        )
        self.version_repo.add(version)

        return document

    def create_from_file(
        self,
        file_path: Path,
        title: str | None = None,
        epic_id: str | None = None,
        custom_id: str | None = None,
    ) -> Document:
        """Create document from file with frontmatter parsing.

        Args:
            file_path: Path to markdown file
            title: Optional title (extracted from file if not provided)
            epic_id: Optional epic association
            custom_id: Optional custom document ID

        Returns:
            Created document

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If title cannot be determined
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse frontmatter
        try:
            post = frontmatter.load(file_path)
            content = post.content
            metadata = post.metadata

            # Extract title from frontmatter if not provided
            if not title and metadata:
                title = metadata.get("title") or metadata.get("Title")

            # Extract epic from frontmatter if not provided
            if not epic_id and metadata:
                epic_id = metadata.get("epic") or metadata.get("Epic") or metadata.get("epic_id")

            # Extract custom_id from frontmatter if not provided
            if not custom_id and metadata:
                custom_id = metadata.get("id") or metadata.get("doc_id")
        except Exception:
            content = file_path.read_text()
            metadata = None

        # Auto-extract title from first # heading if still not provided
        if not title:
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            # Fallback to filename if no title found
            if not title:
                title = file_path.stem.replace("-", " ").replace("_", " ").title()

        if not title:
            raise ValueError("Title cannot be determined from file")

        return self.create_document(title, content, epic_id, custom_id)

    def get_document(self, doc_id: str) -> Document | None:
        """Get document by ID.

        Args:
            doc_id: Document identifier

        Returns:
            Document or None if not found
        """
        return self.doc_repo.get(doc_id)

    def update_document(
        self,
        doc_id: str,
        title: str | None = None,
        content: str | None = None,
        epic_id: str | None = None,
    ) -> Document | None:
        """Update a document.

        Args:
            doc_id: Document identifier
            title: New title (optional)
            content: New content (optional)
            epic_id: New epic ID (optional, use "" to clear)

        Returns:
            Updated document or None if not found
        """
        document = self.doc_repo.get(doc_id)
        if not document:
            return None

        # Update fields
        if title is not None:
            document.title = title
        if content is not None:
            document.content = content
            # Create new version when content changes
            document.version += 1
            version = DocumentVersion(
                doc_id=doc_id,
                version=document.version,
                content=content,
            )
            self.version_repo.add(version)
        if epic_id is not None:
            document.epic_id = epic_id if epic_id else None

        document.updated_at = datetime.utcnow()
        return self.doc_repo.update(document)

    def update_from_file(
        self, doc_id: str, file_path: Path, title: str | None = None, epic_id: str | None = None
    ) -> Document | None:
        """Update document from file with frontmatter parsing.

        Args:
            doc_id: Document identifier
            file_path: Path to markdown file
            title: Optional new title
            epic_id: Optional new epic ID

        Returns:
            Updated document or None if not found

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse frontmatter
        try:
            post = frontmatter.load(file_path)
            content = post.content
            metadata = post.metadata

            # Extract title from frontmatter if not provided via CLI
            if not title and metadata:
                title = metadata.get("title") or metadata.get("Title")

            # Extract epic from frontmatter if not provided via CLI
            if epic_id is None and metadata:
                epic_id = metadata.get("epic") or metadata.get("Epic") or metadata.get("epic_id")
        except Exception:
            content = file_path.read_text()

        return self.update_document(doc_id, title, content, epic_id)

    def list_documents(self, epic_id: str | None = None, limit: int = 100) -> list[Document]:
        """List documents.

        Args:
            epic_id: Optional epic ID filter
            limit: Maximum number of documents

        Returns:
            List of documents
        """
        if epic_id:
            return self.doc_repo.get_by_epic(epic_id, limit)
        return self.doc_repo.get_recent(limit)

    def get_version(self, doc_id: str, version: int) -> DocumentVersion | None:
        """Get specific version of a document.

        Args:
            doc_id: Document identifier
            version: Version number

        Returns:
            Document version or None if not found
        """
        return self.version_repo.get_version(doc_id, version)

    def get_versions(self, doc_id: str, limit: int = 100) -> list[DocumentVersion]:
        """Get version history for a document.

        Args:
            doc_id: Document identifier
            limit: Maximum number of versions

        Returns:
            List of versions
        """
        return self.version_repo.get_by_document(doc_id, limit)

    def search_documents(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search documents using FTS5.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        fts_results = self.doc_repo.search_fts(query, limit)

        results = []
        for doc_id, title, snippet, rank in fts_results:
            # Convert FTS5 rank to 0-1 score (rank is negative, closer to 0 is better)
            score = max(0.0, min(1.0, 1.0 + (rank / 10.0)))

            results.append(
                SearchResult(
                    skill="docs",
                    id=doc_id,
                    type="document",
                    content=f"{title}\n\n{snippet}",
                    metadata={"title": title},
                    score=score,
                )
            )

        return results

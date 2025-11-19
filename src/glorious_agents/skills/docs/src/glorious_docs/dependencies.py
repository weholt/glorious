"""Dependency injection for docs skill.

This module manages dependencies without creating coupling
from the skill to specific implementations.
"""

from sqlalchemy import Engine, event, text
from sqlmodel import Session, SQLModel

from glorious_agents.core.engine_registry import get_engine_for_agent_db
from glorious_agents.core.unit_of_work import UnitOfWork

from .models import Document, DocumentVersion
from .service import DocsService


def get_engine() -> Engine:
    """Get database engine for docs skill.

    Uses the agent database from configuration.
    No caching to avoid memory leaks.

    Returns:
        SQLAlchemy engine
    """
    return get_engine_for_agent_db()


def init_database(engine: Engine) -> None:
    """Initialize database tables including FTS5.

    Args:
        engine: SQLAlchemy engine
    """
    # Create base tables
    SQLModel.metadata.create_all(engine)

    # Create FTS5 virtual table and triggers using raw SQL
    with engine.connect() as conn:
        # Create FTS5 virtual table
        conn.execute(
            text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                title,
                content,
                content=docs_documents,
                content_rowid=rowid
            )
        """)
        )

        # Trigger to keep FTS in sync on insert
        conn.execute(
            text("""
            CREATE TRIGGER IF NOT EXISTS docs_fts_insert AFTER INSERT ON docs_documents BEGIN
                INSERT INTO docs_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
            END
        """)
        )

        # Trigger to keep FTS in sync on delete
        conn.execute(
            text("""
            CREATE TRIGGER IF NOT EXISTS docs_fts_delete AFTER DELETE ON docs_documents BEGIN
                DELETE FROM docs_fts WHERE rowid = OLD.rowid;
            END
        """)
        )

        # Trigger to keep FTS in sync on update
        conn.execute(
            text("""
            CREATE TRIGGER IF NOT EXISTS docs_fts_update AFTER UPDATE ON docs_documents BEGIN
                DELETE FROM docs_fts WHERE rowid = OLD.rowid;
                INSERT INTO docs_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
            END
        """)
        )

        conn.commit()


def get_docs_service(engine: Engine | None = None) -> DocsService:
    """Get docs service with dependencies.

    Args:
        engine: Optional engine (defaults to agent DB)

    Returns:
        Configured DocsService instance
    """
    if engine is None:
        engine = get_engine()

    # Ensure tables exist
    init_database(engine)

    # Create service with fresh session and UoW
    session = Session(engine)
    uow = UnitOfWork(session)
    return DocsService(uow)

"""Add FTS5 full-text search index

Revision ID: fts5_search_001
Revises: 8619a22eed23
Create Date: 2025-11-16 00:40:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fts5_search_001"
down_revision: str | Sequence[str] | None = "8619a22eed23"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add FTS5 virtual table and triggers."""

    # Create FTS5 virtual table for full-text search
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS issues_fts USING fts5(
            id UNINDEXED,
            title,
            description
        );
    """)

    # Populate FTS table with existing data
    op.execute("""
        INSERT INTO issues_fts(rowid, id, title, description)
        SELECT rowid, id, title, COALESCE(description, '')
        FROM issues;
    """)

    # Create trigger to keep FTS index in sync on INSERT
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS issues_fts_insert
        AFTER INSERT ON issues
        BEGIN
            INSERT INTO issues_fts(rowid, id, title, description)
            VALUES (NEW.rowid, NEW.id, NEW.title, COALESCE(NEW.description, ''));
        END;
    """)

    # Create trigger to keep FTS index in sync on UPDATE
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS issues_fts_update
        AFTER UPDATE ON issues
        BEGIN
            UPDATE issues_fts
            SET title = NEW.title,
                description = COALESCE(NEW.description, '')
            WHERE rowid = NEW.rowid;
        END;
    """)

    # Create trigger to keep FTS index in sync on DELETE
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS issues_fts_delete
        AFTER DELETE ON issues
        BEGIN
            DELETE FROM issues_fts WHERE rowid = OLD.rowid;
        END;
    """)


def downgrade() -> None:
    """Remove FTS5 virtual table and triggers."""

    op.execute("DROP TRIGGER IF EXISTS issues_fts_delete;")
    op.execute("DROP TRIGGER IF EXISTS issues_fts_update;")
    op.execute("DROP TRIGGER IF EXISTS issues_fts_insert;")
    op.execute("DROP TABLE IF EXISTS issues_fts;")

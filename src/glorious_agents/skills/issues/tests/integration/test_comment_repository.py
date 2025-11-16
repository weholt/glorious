"""Integration tests for CommentRepository."""

from datetime import UTC, datetime

from sqlmodel import Session

from issue_tracker.adapters.db.repositories.comment_repository import CommentRepository
from issue_tracker.domain.entities.comment import Comment


class TestCommentRepositoryCRUD:
    """Test CRUD operations for comments."""

    def test_get_comment(self, test_session: Session) -> None:
        """Test retrieving a comment by ID."""
        repo = CommentRepository(test_session)

        # Create and save comment
        comment = Comment(
            id="COM-001",
            issue_id="ISS-001",
            author="testuser",
            text="Test comment",
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        saved = repo.save(comment)
        test_session.commit()

        # Retrieve comment
        retrieved = repo.get(saved.id)

        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.text == "Test comment"
        assert retrieved.author == "testuser"

    def test_get_nonexistent_comment(self, test_session: Session) -> None:
        """Test retrieving a comment that doesn't exist."""
        repo = CommentRepository(test_session)
        result = repo.get("NONEXISTENT")
        assert result is None

    def test_delete_comment(self, test_session: Session) -> None:
        """Test deleting a comment."""
        repo = CommentRepository(test_session)

        # Create and save comment
        comment = Comment(
            id="COM-002",
            issue_id="ISS-001",
            author="testuser",
            text="To be deleted",
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        repo.save(comment)
        test_session.commit()

        # Delete comment
        result = repo.delete(comment.id)
        test_session.commit()

        assert result is True
        assert repo.get(comment.id) is None

    def test_delete_nonexistent_comment(self, test_session: Session) -> None:
        """Test deleting a comment that doesn't exist."""
        repo = CommentRepository(test_session)
        result = repo.delete("NONEXISTENT")
        assert result is False

    def test_list_by_author(self, test_session: Session) -> None:
        """Test listing comments by author."""
        repo = CommentRepository(test_session)

        # Create comments by different authors
        comment1 = Comment(
            id="COM-003",
            issue_id="ISS-001",
            author="alice",
            text="Alice's comment",
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        comment2 = Comment(
            id="COM-004",
            issue_id="ISS-002",
            author="alice",
            text="Alice's second comment",
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        comment3 = Comment(
            id="COM-005",
            issue_id="ISS-001",
            author="bob",
            text="Bob's comment",
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )

        repo.save(comment1)
        repo.save(comment2)
        repo.save(comment3)
        test_session.commit()

        # List Alice's comments
        alice_comments = repo.list_by_author("alice")
        assert len(alice_comments) == 2
        assert all(c.author == "alice" for c in alice_comments)

        # List Bob's comments
        bob_comments = repo.list_by_author("bob")
        assert len(bob_comments) == 1
        assert bob_comments[0].author == "bob"

"""Comment repository implementation with SQLModel."""

import logging

from sqlmodel import Session, select

from issue_tracker.adapters.db.models import CommentModel
from issue_tracker.domain.entities.comment import Comment

logger = logging.getLogger(__name__)

__all__ = ["CommentRepository"]


class CommentRepository:
    """Repository for Comment entities using SQLModel.

    Provides CRUD operations for issue comments.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def get(self, comment_id: str) -> Comment | None:
        """Retrieve comment by ID.

        Args:
            comment_id: Unique comment identifier

        Returns:
            Comment entity if found, None otherwise
        """
        model = self.session.get(CommentModel, comment_id)
        return self._model_to_entity(model) if model else None

    def save(self, comment: Comment) -> Comment:
        """Save or update comment.

        Args:
            comment: Comment entity to persist

        Returns:
            Saved comment with updated timestamps
        """
        logger.debug(
            "Repository: saving comment: id=%s, issue_id=%s, author=%s", comment.id, comment.issue_id, comment.author
        )
        model = self._entity_to_model(comment)
        merged = self.session.merge(model)
        self.session.flush()
        self.session.refresh(merged)
        saved_comment = self._model_to_entity(merged)
        logger.debug("Repository: comment saved: id=%s", saved_comment.id)
        return saved_comment

    def delete(self, comment_id: str) -> bool:
        """Delete comment by ID.

        Args:
            comment_id: Unique comment identifier

        Returns:
            True if comment was deleted, False if not found
        """
        logger.debug("Repository: deleting comment: id=%s", comment_id)
        model = self.session.get(CommentModel, comment_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            logger.info("Repository: comment deleted: id=%s", comment_id)
            return True
        logger.warning("Repository: comment not found for deletion: id=%s", comment_id)
        return False

    def list_by_issue(self, issue_id: str) -> list[Comment]:
        """List all comments for an issue.

        Args:
            issue_id: Issue identifier to get comments for

        Returns:
            List of comments ordered by creation time
        """
        logger.debug("Repository: listing comments for issue: id=%s", issue_id)
        statement = (
            select(CommentModel).where(CommentModel.issue_id == issue_id).order_by(CommentModel.created_at)  # type: ignore
        )
        models = self.session.exec(statement).all()
        logger.debug("Repository: found %d comments for issue: id=%s", len(models), issue_id)
        return [self._model_to_entity(model) for model in models]

    def list_by_author(self, author: str, limit: int = 100, offset: int = 0) -> list[Comment]:
        """List comments by author.

        Args:
            author: Author username to filter by
            limit: Maximum number of comments to return
            offset: Number of comments to skip

        Returns:
            List of comments by author
        """
        statement = (
            select(CommentModel)
            .where(CommentModel.author == author)
            .order_by(CommentModel.created_at.desc())  # type: ignore
            .limit(limit)
            .offset(offset)
        )
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def _entity_to_model(self, comment: Comment) -> CommentModel:
        """Convert Comment entity to database model.

        Args:
            comment: Comment entity to convert

        Returns:
            CommentModel for database persistence
        """
        return CommentModel(
            id=comment.id,
            issue_id=comment.issue_id,
            author=comment.author,
            content=comment.text,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    def _model_to_entity(self, model: CommentModel) -> Comment:
        """Convert database model to Comment entity.

        Args:
            model: CommentModel from database

        Returns:
            Comment domain entity
        """
        return Comment(
            id=model.id,
            issue_id=model.issue_id,
            author=model.author,
            text=model.content,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

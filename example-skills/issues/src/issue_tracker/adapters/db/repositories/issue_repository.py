"""Issue repository implementation with SQLModel."""

from collections.abc import Sequence

from sqlmodel import Session, select

from issue_tracker.adapters.db.models import IssueLabelModel, IssueModel
from issue_tracker.domain.entities.issue import Issue, IssuePriority, IssueStatus, IssueType
from issue_tracker.domain.utils import utcnow_naive


class IssueRepository:
    """Repository for Issue entities using SQLModel.

    Provides CRUD operations and advanced querying for issues.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def get(self, issue_id: str) -> Issue | None:
        """Retrieve issue by ID.

        Args:
            issue_id: Unique issue identifier

        Returns:
            Issue entity if found, None otherwise
        """
        model = self.session.get(IssueModel, issue_id)
        return self._model_to_entity(model) if model else None

    def save(self, issue: Issue) -> Issue:
        """Save or update issue.

        Args:
            issue: Issue entity to persist

        Returns:
            Saved issue with updated timestamps
        """
        model = self._entity_to_model(issue)
        merged = self.session.merge(model)
        self.session.flush()

        # Handle labels via junction table
        # First delete existing labels for this issue
        statement = select(IssueLabelModel).where(IssueLabelModel.issue_id == issue.id)
        existing_labels = self.session.exec(statement).all()
        for label_model in existing_labels:
            self.session.delete(label_model)
        self.session.flush()

        # Then add new labels
        now = utcnow_naive()
        for label_name in issue.labels:
            label_model = IssueLabelModel(
                issue_id=issue.id,
                label_name=label_name,
                created_at=now,
            )
            self.session.add(label_model)
        self.session.flush()

        self.session.refresh(merged)
        return self._model_to_entity(merged)

    def delete(self, issue_id: str) -> bool:
        """Delete issue by ID.

        Args:
            issue_id: Unique issue identifier

        Returns:
            True if issue was deleted, False if not found
        """
        model = self.session.get(IssueModel, issue_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List all issues with pagination.

        Args:
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issue entities
        """
        statement = select(IssueModel).limit(limit).offset(offset)
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_status(self, status: IssueStatus, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by status.

        Args:
            status: Issue status to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues matching status
        """
        statement = select(IssueModel).where(IssueModel.status == status.value).limit(limit).offset(offset)
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_priority(self, priority: IssuePriority, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by priority.

        Args:
            priority: Issue priority to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues matching priority
        """
        statement = select(IssueModel).where(IssueModel.priority == priority.value).limit(limit).offset(offset)
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_assignee(self, assignee: str, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by assignee.

        Args:
            assignee: Username to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues assigned to user
        """
        statement = select(IssueModel).where(IssueModel.assignee == assignee).limit(limit).offset(offset)
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_epic(self, epic_id: str, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues belonging to an epic.

        Args:
            epic_id: Epic identifier to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues in epic
        """
        statement = select(IssueModel).where(IssueModel.epic_id == epic_id).limit(limit).offset(offset)
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def list_by_type(self, issue_type: IssueType, limit: int = 100, offset: int = 0) -> list[Issue]:
        """List issues filtered by type.

        Args:
            issue_type: Issue type to filter by
            limit: Maximum number of issues to return
            offset: Number of issues to skip

        Returns:
            List of issues matching type
        """
        statement = select(IssueModel).where(IssueModel.type == issue_type.value).limit(limit).offset(offset)
        models = self.session.exec(statement).all()
        return self._models_to_entities(models)

    def _entity_to_model(self, issue: Issue) -> IssueModel:
        """Convert Issue entity to database model.

        Args:
            issue: Issue entity to convert

        Returns:
            IssueModel for database persistence
        """
        return IssueModel(
            id=issue.id,
            project_id=getattr(issue, "project_id", "default"),
            title=issue.title,
            description=issue.description or "",
            status=issue.status.value,
            priority=issue.priority.value,
            type=issue.type.value,
            assignee=issue.assignee,
            epic_id=issue.epic_id,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            closed_at=issue.closed_at,
        )

    def _model_to_entity(self, model: IssueModel) -> Issue:
        """Convert database model to Issue entity.

        Args:
            model: IssueModel from database

        Returns:
            Issue domain entity
        """
        # Load labels from junction table
        statement = select(IssueLabelModel).where(IssueLabelModel.issue_id == model.id)
        label_models = self.session.exec(statement).all()
        labels = [label_model.label_name for label_model in label_models]

        return Issue(
            id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description or "",
            status=IssueStatus(model.status),
            priority=IssuePriority(model.priority),
            type=IssueType(model.type),
            assignee=model.assignee,
            epic_id=model.epic_id,
            labels=labels,
            created_at=model.created_at,
            updated_at=model.updated_at,
            closed_at=model.closed_at,
        )

    def _models_to_entities(self, models: Sequence[IssueModel]) -> list[Issue]:
        """Convert multiple database models to Issue entities efficiently.

        Batch-loads labels to avoid N+1 queries.

        Args:
            models: Sequence of IssueModels from database

        Returns:
            List of Issue domain entities
        """
        if not models:
            return []

        # Batch-load all labels for these issues
        issue_ids: list[str] = [model.id for model in models]
        issue_id_col = IssueLabelModel.issue_id
        statement = select(IssueLabelModel).where(issue_id_col.in_(issue_ids))  # type: ignore[attr-defined]
        label_models = self.session.exec(statement).all()

        # Group labels by issue_id
        labels_by_issue: dict[str, list[str]] = {}
        for label_model in label_models:
            if label_model.issue_id not in labels_by_issue:
                labels_by_issue[label_model.issue_id] = []
            labels_by_issue[label_model.issue_id].append(label_model.label_name)

        # Convert models to entities with batched labels
        entities = []
        for model in models:
            labels = labels_by_issue.get(model.id, [])
            entity = Issue(
                id=model.id,
                project_id=model.project_id,
                title=model.title,
                description=model.description or "",
                status=IssueStatus(model.status),
                priority=IssuePriority(model.priority),
                type=IssueType(model.type),
                assignee=model.assignee,
                epic_id=model.epic_id,
                labels=labels,
                created_at=model.created_at,
                updated_at=model.updated_at,
                closed_at=model.closed_at,
            )
            entities.append(entity)

        return entities

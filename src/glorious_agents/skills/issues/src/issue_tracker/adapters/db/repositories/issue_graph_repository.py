"""Issue graph repository for dependency management."""

from sqlmodel import Session, or_, select

from issue_tracker.adapters.db.models import DependencyModel
from issue_tracker.domain.entities.dependency import Dependency, DependencyType

__all__ = ["IssueGraphRepository"]


class IssueGraphRepository:
    """Repository for issue dependency graph operations.

    Manages dependency edges between issues with cycle detection.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def add_dependency(self, dependency: Dependency) -> Dependency:
        """Add a dependency edge.

        Args:
            dependency: Dependency entity to persist

        Returns:
            Saved dependency with generated ID
        """
        model = self._entity_to_model(dependency)
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._model_to_entity(model)

    def remove_dependency(self, from_issue_id: str, to_issue_id: str, dependency_type: DependencyType) -> bool:
        """Remove a dependency edge.

        Args:
            from_issue_id: Source issue identifier
            to_issue_id: Target issue identifier
            dependency_type: Type of dependency relationship

        Returns:
            True if dependency was removed, False if not found
        """
        statement = select(DependencyModel).where(
            DependencyModel.from_issue_id == from_issue_id,
            DependencyModel.to_issue_id == to_issue_id,
            DependencyModel.type == dependency_type.value,
        )
        model = self.session.exec(statement).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def get_dependencies(self, issue_id: str) -> list[Dependency]:
        """Get all outgoing dependencies (this issue depends on...).

        Args:
            issue_id: Issue identifier

        Returns:
            List of outgoing dependency edges
        """
        statement = select(DependencyModel).where(DependencyModel.from_issue_id == issue_id)
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def get_dependents(self, issue_id: str) -> list[Dependency]:
        """Get all incoming dependencies (...depend on this issue).

        Args:
            issue_id: Issue identifier

        Returns:
            List of incoming dependency edges
        """
        statement = select(DependencyModel).where(DependencyModel.to_issue_id == issue_id)
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def get_blockers(self, issue_id: str) -> list[str]:
        """Get all issue IDs that block this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs blocking this issue
        """
        statement = select(DependencyModel).where(
            DependencyModel.to_issue_id == issue_id,
            DependencyModel.type == DependencyType.BLOCKS.value,
        )
        models = self.session.exec(statement).all()
        return [model.from_issue_id for model in models]

    def get_blocked_by(self, issue_id: str) -> list[str]:
        """Get all issue IDs blocked by this issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of issue IDs blocked by this issue
        """
        statement = select(DependencyModel).where(
            DependencyModel.from_issue_id == issue_id,
            DependencyModel.type == DependencyType.BLOCKS.value,
        )
        models = self.session.exec(statement).all()
        return [model.to_issue_id for model in models]

    def has_cycle(self, from_issue_id: str, to_issue_id: str) -> bool:
        """Check if adding edge would create cycle using DFS.

        Args:
            from_issue_id: Source issue identifier
            to_issue_id: Target issue identifier

        Returns:
            True if adding edge creates cycle, False otherwise
        """
        # Check if there's already a path from to_issue_id to from_issue_id
        visited: set[str] = set()

        def dfs(current: str) -> bool:
            """Depth-first search to detect cycles."""
            if current == from_issue_id:
                return True
            if current in visited:
                return False
            visited.add(current)

            # Get all dependencies of current issue
            statement = select(DependencyModel).where(DependencyModel.from_issue_id == current)  # type: ignore[attr-defined]
            models = self.session.exec(statement).all()

            for model in models:
                if dfs(model.to_issue_id):
                    return True

            return False

        return dfs(to_issue_id)

    def get_all_dependencies(self, issue_id: str) -> list[Dependency]:
        """Get all dependencies for an issue (both directions).

        Args:
            issue_id: Issue identifier

        Returns:
            List of all dependency edges involving this issue
        """
        statement = select(DependencyModel).where(
            or_(DependencyModel.from_issue_id == issue_id, DependencyModel.to_issue_id == issue_id)
        )
        models = self.session.exec(statement).all()
        return [self._model_to_entity(model) for model in models]

    def _entity_to_model(self, dependency: Dependency) -> DependencyModel:
        """Convert Dependency entity to database model.

        Args:
            dependency: Dependency entity to convert

        Returns:
            DependencyModel for database persistence
        """
        # Generate ID from issue IDs + type to allow multiple relationship types between same issues
        dep_id = (
            str(dependency.id)
            if dependency.id
            else f"{dependency.from_issue_id[:8]}{dependency.to_issue_id[:8]}{dependency.dependency_type.value[:5]}"
        )
        return DependencyModel(
            id=dep_id,
            from_issue_id=dependency.from_issue_id,
            to_issue_id=dependency.to_issue_id,
            type=dependency.dependency_type.value,
            created_at=dependency.created_at,
        )

    def _model_to_entity(self, model: DependencyModel) -> Dependency:
        """Convert database model to Dependency entity.

        Args:
            model: DependencyModel from database

        Returns:
            Dependency domain entity
        """
        return Dependency(
            from_issue_id=model.from_issue_id,
            to_issue_id=model.to_issue_id,
            dependency_type=DependencyType(model.type),
            id=None,  # Entity uses int, model uses string
            description=None,  # Not stored in DB currently
            created_at=model.created_at,
        )

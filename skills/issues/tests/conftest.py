"""Shared test fixtures and configuration for issue tracker tests."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def reset_services():
    """Reset service overrides before each test."""
    from issue_tracker.cli.app import set_service

    # Clear service overrides
    set_service("issue_service", None)
    set_service("graph_service", None)
    set_service("stats_service", None)
    yield
    set_service("issue_service", None)
    set_service("graph_service", None)
    set_service("stats_service", None)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture(autouse=True)
def inject_mock_service(reset_services, mock_service: MagicMock, mock_graph_service: MagicMock):
    """Automatically inject mock services into CLI for tests.

    Depends on reset_services to ensure it runs after the reset.
    """
    from issue_tracker.cli.app import set_service

    set_service("issue_service", mock_service)
    set_service("graph_service", mock_graph_service)
    yield


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def temp_issues_dir(temp_workspace: Path) -> Path:
    """Create a temporary .issues directory."""
    issues_dir = temp_workspace / ".issues"
    issues_dir.mkdir()
    return issues_dir


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock issue repository."""
    repo = MagicMock()
    repo.save = MagicMock()
    repo.get = MagicMock(return_value=None)
    repo.list = MagicMock(return_value=[])
    repo.delete = MagicMock()
    return repo


@pytest.fixture
def mock_service() -> MagicMock:
    """Create a mock issue service with proper return value wrapping and state tracking."""
    from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType, Comment
    from datetime import datetime, UTC

    service = MagicMock()

    # State tracking - track created issues and comments
    _issue_store: dict[str, Issue] = {}
    _comment_store: dict[str, Comment] = {}
    _comment_counter = [0]  # Use list to allow mutation in nested functions

    # Create wrapper functions that track state
    def create_issue_wrapper(**kwargs):
        """Wrapper for create_issue that tracks created issues."""
        result = service.create_issue.return_value

        # If dict, convert to Issue
        if isinstance(result, dict):
            issue = Issue(
                id=result.get("id", f"issue-{len(_issue_store) + 1}"),
                project_id=result.get("project_id", "default"),
                title=result.get("title", kwargs.get("title", "Test")),
                description=result.get("description", kwargs.get("description", "")),
                status=IssueStatus(result.get("status", "open")),
                priority=IssuePriority(result.get("priority", kwargs.get("priority", IssuePriority.MEDIUM))),
                type=IssueType(result.get("type", kwargs.get("issue_type", IssueType.TASK))),
                assignee=result.get("assignee", kwargs.get("assignee")),
                labels=result.get("labels", []),
                epic_id=result.get("epic_id"),
            )
        elif isinstance(result, Issue):
            issue = result
        else:
            # Create default from kwargs
            issue = Issue(
                id=f"issue-{len(_issue_store) + 1}",
                project_id="default",
                title=kwargs.get("title", "Test"),
                description=kwargs.get("description", ""),
                status=IssueStatus.OPEN,
                priority=kwargs.get("priority", IssuePriority.MEDIUM),
                type=kwargs.get("issue_type", IssueType.TASK),
                assignee=kwargs.get("assignee"),
                labels=kwargs.get("labels", []),
            )

        # Store for later retrieval
        _issue_store[issue.id] = issue
        return issue

    def get_issue_wrapper(issue_id: str):
        """Wrapper for get_issue that retrieves from store."""
        from issue_tracker.domain.exceptions import NotFoundError

        result = service.get_issue.return_value

        # If explicit return_value set, use it
        if isinstance(result, dict):
            return Issue(
                id=result.get("id", issue_id),
                project_id=result.get("project_id", "default"),
                title=result.get("title", "Test"),
                description=result.get("description", ""),
                status=IssueStatus(result.get("status", "open")),
                priority=IssuePriority(result.get("priority", 2)),
                type=IssueType(result.get("type", "task")),
                assignee=result.get("assignee"),
                labels=result.get("labels", []),
                epic_id=result.get("epic_id"),
            )
        if isinstance(result, Issue):
            return result

        # Check store first
        if issue_id in _issue_store:
            return _issue_store[issue_id]

        # Raise NotFoundError for nonexistent issues
        raise NotFoundError(f"Issue {issue_id} not found", entity_id=issue_id)

    def update_issue_wrapper(issue_id: str, **kwargs):
        """Wrapper for update_issue that updates store."""
        result = service.update_issue.return_value

        # Get existing issue or create default
        if issue_id not in _issue_store:
            _issue_store[issue_id] = Issue(
                id=issue_id,
                project_id="default",
                title="Test",
                description="",
                status=IssueStatus.OPEN,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
            )

        issue = _issue_store[issue_id]

        # If explicit return_value, use it
        if isinstance(result, dict):
            issue = Issue(
                id=result.get("id", issue_id),
                project_id=issue.project_id,
                title=result.get("title", issue.title),
                description=result.get("description", issue.description),
                status=IssueStatus(result.get("status", issue.status.value)),
                priority=IssuePriority(result.get("priority", issue.priority)),
                type=issue.type,
                assignee=result.get("assignee", issue.assignee),
                labels=result.get("labels", issue.labels),
                epic_id=result.get("epic_id", issue.epic_id),
            )
        elif isinstance(result, Issue):
            issue = result
        else:
            # Apply kwargs updates (only if not None)
            new_title = kwargs.get("title") if kwargs.get("title") is not None else issue.title
            new_desc = kwargs.get("description") if kwargs.get("description") is not None else issue.description
            new_status = kwargs.get("status") if kwargs.get("status") is not None else issue.status
            new_priority = kwargs.get("priority") if kwargs.get("priority") is not None else issue.priority
            new_assignee = kwargs.get("assignee") if kwargs.get("assignee") is not None else issue.assignee
            new_type = kwargs.get("issue_type") if kwargs.get("issue_type") is not None else issue.type
            new_epic = kwargs.get("epic_id") if kwargs.get("epic_id") is not None else issue.epic_id

            updated = Issue(
                id=issue.id,
                project_id=issue.project_id,
                title=new_title,
                description=new_desc,
                status=new_status
                if isinstance(new_status, IssueStatus)
                else (IssueStatus(new_status) if new_status else issue.status),
                priority=new_priority,
                type=new_type,
                assignee=new_assignee,
                labels=issue.labels,
                epic_id=new_epic,
                created_at=issue.created_at,
                updated_at=datetime.now(UTC),
                closed_at=issue.closed_at,
            )
            issue = updated

        _issue_store[issue.id] = issue
        return issue

    def close_issue_wrapper(issue_id: str):
        """Wrapper for close_issue."""
        # Get from store or create default
        if issue_id in _issue_store:
            issue = _issue_store[issue_id]
        else:
            # Create default issue for close operation
            issue = Issue(
                id=issue_id,
                project_id="default",
                title="Test Issue",
                description="",
                status=IssueStatus.OPEN,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
            )
            _issue_store[issue_id] = issue

        closed = Issue(
            id=issue.id,
            project_id=issue.project_id,
            title=issue.title,
            description=issue.description,
            status=IssueStatus.CLOSED,
            priority=issue.priority,
            type=issue.type,
            assignee=issue.assignee,
            labels=issue.labels,
            epic_id=issue.epic_id,
            created_at=issue.created_at,
            updated_at=datetime.now(UTC),
            closed_at=datetime.now(UTC),
        )
        _issue_store[issue_id] = closed
        return closed

    def reopen_issue_wrapper(issue_id: str):
        """Wrapper for reopen_issue."""
        # Get from store or create default
        if issue_id in _issue_store:
            issue = _issue_store[issue_id]
        else:
            # Create default issue for reopen operation
            issue = Issue(
                id=issue_id,
                project_id="default",
                title="Test Issue",
                description="",
                status=IssueStatus.CLOSED,
                priority=IssuePriority.MEDIUM,
                type=IssueType.TASK,
                closed_at=datetime.now(UTC),
            )
            _issue_store[issue_id] = issue

        reopened = Issue(
            id=issue.id,
            project_id=issue.project_id,
            title=issue.title,
            description=issue.description,
            status=IssueStatus.OPEN,
            priority=issue.priority,
            type=issue.type,
            assignee=issue.assignee,
            labels=issue.labels,
            epic_id=issue.epic_id,
            created_at=issue.created_at,
            updated_at=datetime.now(UTC),
            closed_at=None,
        )
        _issue_store[issue_id] = reopened
        return reopened

    def add_comment_wrapper(issue_id: str, text: str, author: str | None = None):
        """Wrapper for add_comment that tracks comments."""
        _comment_counter[0] += 1
        comment = Comment(
            id=f"comment-{_comment_counter[0]}",
            issue_id=issue_id,
            text=text,
            author=author,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        _comment_store[comment.id] = comment
        return comment

    def list_comments_wrapper(issue_id: str):
        """Wrapper for list_comments that returns comments for an issue."""
        # If return_value is explicitly set (not MagicMock), use it
        result = service.list_comments.return_value
        if not isinstance(result, MagicMock) and result is not None and result != []:
            # Convert dicts to Comment objects if needed
            if result and isinstance(result[0], dict):
                from datetime import datetime

                return [
                    Comment(
                        id=c.get("id", f"comment-{i}"),
                        issue_id=c.get("issue_id", issue_id),
                        text=c.get("text", ""),
                        author=c.get("author", ""),
                        created_at=datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                        if c.get("created_at")
                        else datetime.now(UTC),
                        updated_at=datetime.fromisoformat(c["updated_at"].replace("Z", "+00:00"))
                        if c.get("updated_at")
                        else datetime.now(UTC),
                    )
                    for i, c in enumerate(result)
                ]
            return result
        # Otherwise use store
        return [c for c in _comment_store.values() if c.issue_id == issue_id]

    def delete_comment_wrapper(comment_id: str):
        """Wrapper for delete_comment that removes from store."""
        if comment_id in _comment_store:
            del _comment_store[comment_id]
        return None

    def add_label_wrapper(issue_id: str, label: str):
        """Wrapper for add_label_to_issue that updates issue in store."""
        if issue_id in _issue_store:
            issue = _issue_store[issue_id]
            if label not in issue.labels:
                updated = Issue(
                    id=issue.id,
                    project_id=issue.project_id,
                    title=issue.title,
                    description=issue.description,
                    status=issue.status,
                    priority=issue.priority,
                    type=issue.type,
                    assignee=issue.assignee,
                    labels=issue.labels + [label],
                    epic_id=issue.epic_id,
                    created_at=issue.created_at,
                    updated_at=datetime.now(UTC),
                )
                _issue_store[issue_id] = updated
        return None

    def remove_label_wrapper(issue_id: str, label: str):
        """Wrapper for remove_label_from_issue that updates issue in store."""
        if issue_id in _issue_store:
            issue = _issue_store[issue_id]
            if label in issue.labels:
                updated = Issue(
                    id=issue.id,
                    project_id=issue.project_id,
                    title=issue.title,
                    description=issue.description,
                    status=issue.status,
                    priority=issue.priority,
                    type=issue.type,
                    assignee=issue.assignee,
                    labels=[l for l in issue.labels if l != label],
                    epic_id=issue.epic_id,
                    created_at=issue.created_at,
                    updated_at=datetime.now(UTC),
                )
                _issue_store[issue_id] = updated
        return None

    def set_epic_wrapper(issue_id: str, epic_id: str):
        """Wrapper for set_epic that updates issue in store."""
        if issue_id in _issue_store:
            issue = _issue_store[issue_id]
            updated = Issue(
                id=issue.id,
                project_id=issue.project_id,
                title=issue.title,
                description=issue.description,
                status=issue.status,
                priority=issue.priority,
                type=issue.type,
                assignee=issue.assignee,
                labels=issue.labels,
                epic_id=epic_id,
                created_at=issue.created_at,
                updated_at=datetime.now(UTC),
            )
            _issue_store[issue_id] = updated
        return None

    def clear_epic_wrapper(issue_id: str):
        """Wrapper for clear_epic that updates issue in store."""
        if issue_id in _issue_store:
            issue = _issue_store[issue_id]
            updated = Issue(
                id=issue.id,
                project_id=issue.project_id,
                title=issue.title,
                description=issue.description,
                status=issue.status,
                priority=issue.priority,
                type=issue.type,
                assignee=issue.assignee,
                labels=issue.labels,
                epic_id=None,
                created_at=issue.created_at,
                updated_at=datetime.now(UTC),
            )
            _issue_store[issue_id] = updated
        return None

    def list_issues_wrapper(**kwargs):
        """Wrapper for list_issues that returns issues from store."""
        issues = list(_issue_store.values())

        # Apply filters
        if "status" in kwargs and kwargs["status"]:
            issues = [i for i in issues if i.status == kwargs["status"]]
        if "priority" in kwargs and kwargs["priority"] is not None:
            issues = [i for i in issues if i.priority == kwargs["priority"]]
        if "assignee" in kwargs and kwargs["assignee"]:
            issues = [i for i in issues if i.assignee == kwargs["assignee"]]
        if "issue_type" in kwargs and kwargs["issue_type"]:
            issues = [i for i in issues if i.type == kwargs["issue_type"]]
        if "epic_id" in kwargs and kwargs["epic_id"]:
            issues = [i for i in issues if i.epic_id == kwargs["epic_id"]]

        return issues

    def transition_issue_wrapper(issue_id: str, new_status: IssueStatus):
        """Wrapper for transition_issue that updates status in store."""
        if issue_id in _issue_store:
            issue = _issue_store[issue_id]
            # If already at target status, return as-is (idempotent)
            if issue.status == new_status:
                return issue
            # Use the entity's transition method for proper validation
            updated = issue.transition(new_status)
            _issue_store[issue_id] = updated
            return updated
        return None

    # Configure side_effects with state tracking
    service.create_issue.side_effect = create_issue_wrapper
    service.get_issue.side_effect = get_issue_wrapper
    service.update_issue.side_effect = update_issue_wrapper
    service.transition_issue.side_effect = transition_issue_wrapper
    service.close_issue.side_effect = close_issue_wrapper
    service.reopen_issue.side_effect = reopen_issue_wrapper
    service.list_issues.side_effect = list_issues_wrapper
    service.delete_issue.return_value = None
    service.add_label_to_issue.side_effect = add_label_wrapper
    service.remove_label_from_issue.side_effect = remove_label_wrapper
    service.add_comment.side_effect = add_comment_wrapper
    service.list_comments.side_effect = list_comments_wrapper
    service.delete_comment.side_effect = delete_comment_wrapper
    service.set_epic.side_effect = set_epic_wrapper
    service.clear_epic.side_effect = clear_epic_wrapper

    # Add mock UnitOfWork with session
    mock_uow = MagicMock()
    mock_session = MagicMock()
    mock_session.commit = MagicMock()
    mock_uow.session = mock_session
    service.uow = mock_uow

    return service


@pytest.fixture
def mock_graph_service() -> MagicMock:
    """Create a mock graph service with state tracking for dependencies."""
    from issue_tracker.domain import Dependency
    from issue_tracker.domain.entities.dependency import DependencyType
    from datetime import datetime, UTC

    service = MagicMock()

    # State tracking - track dependencies
    _dependency_store: dict[str, Dependency] = {}
    _dependency_counter = [0]

    def add_dependency_wrapper(from_issue_id: str, to_issue_id: str, dependency_type: str | DependencyType):
        """Wrapper for add_dependency that tracks dependencies."""
        _dependency_counter[0] += 1
        dep_type = dependency_type if isinstance(dependency_type, DependencyType) else DependencyType(dependency_type)
        dep_id = f"{from_issue_id}:{to_issue_id}:{dep_type.value}"

        dependency = Dependency(
            id=dep_id,
            from_issue_id=from_issue_id,
            to_issue_id=to_issue_id,
            dependency_type=dep_type,
            created_at=datetime.now(UTC),
        )
        _dependency_store[dep_id] = dependency
        return dependency

    def remove_dependency_wrapper(from_issue_id: str, to_issue_id: str, dependency_type: str | DependencyType = None):
        """Wrapper for remove_dependency that removes from store."""
        dep_type = (
            dependency_type
            if isinstance(dependency_type, DependencyType)
            else DependencyType(dependency_type)
            if dependency_type
            else None
        )
        if dep_type:
            dep_id = f"{from_issue_id}:{to_issue_id}:{dep_type.value}"
            if dep_id in _dependency_store:
                del _dependency_store[dep_id]
        else:
            # Remove all dependencies between these issues
            to_remove = [k for k in _dependency_store.keys() if k.startswith(f"{from_issue_id}:{to_issue_id}:")]
            for k in to_remove:
                del _dependency_store[k]
        return None

    def get_dependencies_wrapper(issue_id: str, dependency_type: str | DependencyType = None):
        """Wrapper for get_dependencies that retrieves from store."""
        deps = [d for d in _dependency_store.values() if d.from_issue_id == issue_id]
        if dependency_type:
            dep_type = (
                dependency_type if isinstance(dependency_type, DependencyType) else DependencyType(dependency_type)
            )
            deps = [d for d in deps if d.dependency_type == dep_type]
        return deps

    def get_dependents_wrapper(issue_id: str, dependency_type: str | DependencyType = None):
        """Wrapper for get_dependents that retrieves from store."""
        deps = [d for d in _dependency_store.values() if d.to_issue_id == issue_id]
        if dependency_type:
            dep_type = (
                dependency_type if isinstance(dependency_type, DependencyType) else DependencyType(dependency_type)
            )
            deps = [d for d in deps if d.dependency_type == dep_type]
        return deps

    def build_dependency_tree_wrapper(issue_id: str, reverse: bool = False, max_depth: int | None = None):
        """Build dependency tree recursively."""
        from issue_tracker.domain import Issue, IssueStatus, IssuePriority, IssueType

        def build_tree(node_id: str, current_depth: int = 0, visited: set | None = None) -> dict:
            if visited is None:
                visited = set()

            if node_id in visited:
                return {
                    "issue_id": node_id,
                    "issue": None,
                    "is_circular": True,
                    "depth": current_depth,
                    "dependencies": [],
                }

            visited.add(node_id)

            if max_depth is not None and current_depth >= max_depth:
                # Create minimal issue for leaf nodes
                return {
                    "issue_id": node_id,
                    "issue": Issue(
                        id=node_id,
                        project_id="default",
                        title=f"Issue {node_id}",
                        description="",
                        status=IssueStatus.OPEN,
                        priority=IssuePriority.MEDIUM,
                        type=IssueType.TASK,
                    ),
                    "is_circular": False,
                    "depth": current_depth,
                    "dependencies": [],
                }

            # Get outgoing dependencies
            children = []
            for dep in _dependency_store.values():
                if dep.from_issue_id == node_id:
                    child_tree = build_tree(dep.to_issue_id, current_depth + 1, visited.copy())
                    child_tree["dependency_type"] = dep.dependency_type.value
                    children.append(child_tree)

            # Create minimal issue
            return {
                "issue_id": node_id,
                "issue": Issue(
                    id=node_id,
                    project_id="default",
                    title=f"Issue {node_id}",
                    description="",
                    status=IssueStatus.OPEN,
                    priority=IssuePriority.MEDIUM,
                    type=IssueType.TASK,
                ),
                "is_circular": False,
                "depth": current_depth,
                "dependencies": children,
            }

        return build_tree(issue_id)

    def detect_cycles_wrapper():
        """Detect dependency cycles using DFS."""
        # Build adjacency list
        graph = {}
        for dep in _dependency_store.values():
            if dep.from_issue_id not in graph:
                graph[dep.from_issue_id] = []
            graph[dep.from_issue_id].append(dep.to_issue_id)

        cycles_found = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles_found.append(cycle)
                        return True

            path.pop()
            rec_stack.remove(node)
            return False

        # Check all nodes
        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles_found

    def get_ready_queue_wrapper(status_filter=None):
        """Get issues ready to work (no open blockers)."""
        # Simplified mock - returns empty list
        # Tests that need this should provide specific mock behavior
        return []

    # Configure service
    service.add_dependency.side_effect = add_dependency_wrapper
    service.remove_dependency.side_effect = remove_dependency_wrapper
    service.get_dependencies.side_effect = get_dependencies_wrapper
    service.get_dependents.side_effect = get_dependents_wrapper
    service.build_dependency_tree.side_effect = build_dependency_tree_wrapper
    service.detect_cycles.side_effect = detect_cycles_wrapper
    service.get_ready_queue.side_effect = get_ready_queue_wrapper

    return service


@pytest.fixture
def mock_daemon_client() -> MagicMock:
    """Create a mock daemon client."""
    client = MagicMock()
    client.is_running = MagicMock(return_value=False)
    client.start = MagicMock()
    client.stop = MagicMock()
    client.health = MagicMock(return_value={"status": "healthy"})
    return client


@pytest.fixture
def sample_issue() -> dict[str, Any]:
    """Create a sample issue data structure."""
    return {
        "id": "issue-abc123",
        "title": "Sample issue",
        "type": "task",
        "priority": 2,
        "status": "open",
        "description": "Sample description",
        "assignee": None,
        "labels": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_issues() -> list[dict[str, Any]]:
    """Create a list of sample issues."""
    return [
        {
            "id": "issue-001",
            "title": "Critical bug",
            "type": "bug",
            "priority": 0,
            "status": "open",
            "labels": ["critical", "security"],
        },
        {
            "id": "issue-002",
            "title": "Feature request",
            "type": "feature",
            "priority": 2,
            "status": "in_progress",
            "assignee": "alice",
        },
        {
            "id": "issue-003",
            "title": "Epic task",
            "type": "epic",
            "priority": 1,
            "status": "open",
            "labels": ["milestone"],
        },
    ]


@pytest.fixture
def sample_epic() -> dict[str, Any]:
    """Create a sample epic."""
    return {
        "id": "issue-epic001",
        "title": "Q4 Release",
        "type": "epic",
        "priority": 1,
        "status": "in_progress",
        "description": "Major release epic",
    }


@pytest.fixture
def sample_comment() -> dict[str, Any]:
    """Create a sample comment."""
    return {
        "id": "comment-xyz789",
        "issue_id": "issue-abc123",
        "author": "bob",
        "text": "This is a comment",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_dependency() -> dict[str, Any]:
    """Create a sample dependency."""
    return {
        "from_id": "issue-001",
        "to_id": "issue-002",
        "type": "blocks",
    }


@pytest.fixture
def integration_cli_runner(tmp_path: Path) -> CliRunner:
    """Create a CLI runner for integration tests with real database.

    This fixture creates a temporary workspace with a real SQLite database
    for integration testing. Unlike the cli_runner fixture, this does NOT
    inject mocks - it uses real services.
    """
    import os
    from typer.testing import CliRunner

    # Create workspace
    workspace = tmp_path / "integration_workspace"
    workspace.mkdir()

    # Change to workspace directory
    old_cwd = os.getcwd()
    os.chdir(workspace)

    # CRITICAL: Disable daemon auto-start for tests to prevent hangs
    old_daemon_env = os.environ.get("ISSUES_AUTO_START_DAEMON")
    os.environ["ISSUES_AUTO_START_DAEMON"] = "false"

    try:
        # Don't inject mocks for integration tests
        from issue_tracker.cli.app import set_service

        set_service("issue_service", None)
        set_service("graph_service", None)
        set_service("stats_service", None)

        # Initialize the workspace using the CLI
        runner = CliRunner()
        from issue_tracker.cli.app import app

        init_result = runner.invoke(app, ["init"])
        if init_result.exit_code != 0:
            raise RuntimeError(f"Failed to initialize workspace: {init_result.stdout}")

        yield runner

    finally:
        # Cleanup
        os.chdir(old_cwd)
        set_service("issue_service", None)
        set_service("graph_service", None)
        set_service("stats_service", None)

        # Restore daemon env var
        if old_daemon_env is None:
            os.environ.pop("ISSUES_AUTO_START_DAEMON", None)
        else:
            os.environ["ISSUES_AUTO_START_DAEMON"] = old_daemon_env

        # CRITICAL: Dispose ALL cached engines to prevent memory leak
        # Each test creates a new workspace with different DB path
        # Without this, engines accumulate: 29 tests = 145MB leaked on Linux
        from issue_tracker.cli.dependencies import dispose_all_engines, get_db_url, get_issues_folder

        # Dispose all engines in registry (not just current one)
        dispose_all_engines()

        # Clear path caches
        get_db_url.cache_clear()
        get_issues_folder.cache_clear()

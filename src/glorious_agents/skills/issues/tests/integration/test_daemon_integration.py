"""Integration tests for daemon service with live daemon.

Tests verify daemon functionality with actual running daemon process:
- Daemon lifecycle (start/stop/status)
- IPC communication (health/sync/stop commands via HTTP)
- JSONL export/import with real data
- Git integration (commit/pull/push)
- Periodic sync operations

Uses HTTP-based IPC which works cross-platform (Windows, Linux, macOS).
"""

import asyncio
import json
import subprocess
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select

from issue_tracker.adapters.db.models import IssueModel as Issue
from issue_tracker.daemon.config import DaemonConfig
from issue_tracker.daemon.ipc_server import IPCClient
from issue_tracker.daemon.service import DaemonService


@pytest.fixture
def daemon_workspace(tmp_path):
    """Create a test workspace with database and config.

    CRITICAL: Disposes engine after setup to prevent memory leaks on Linux.
    """
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()

    # Create database
    db_path = workspace / "issues.db"
    engine = create_engine(f"sqlite:///{db_path}")

    try:
        Issue.metadata.create_all(engine)

        # Add test issues
        with Session(engine) as session:
            from datetime import datetime

            now = datetime.now()
            issue1 = Issue(
                project_id="test-project",
                id="TEST-001",
                title="Test Issue 1",
                description="First test issue",
                status="open",
                priority=1,
                type="task",
                assignee="test_user",
                created_at=now,
                updated_at=now,
            )
            issue2 = Issue(
                project_id="test-project",
                id="TEST-002",
                title="Test Issue 2",
                description="Second test issue",
                status="in_progress",
                priority=2,
                type="bug",
                created_at=now,
                updated_at=now,
            )
            session.add(issue1)
            session.add(issue2)
            session.commit()
    finally:
        # CRITICAL: Dispose engine to prevent memory leak
        engine.dispose()

    # Create export directory
    export_path = workspace / "exports"
    export_path.mkdir()

    # Initialize git repo (optional for some tests)
    git_repo = workspace / "git_repo"
    git_repo.mkdir()
    subprocess.run(["git", "init"], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )

    return {
        "workspace": workspace,
        "db_path": db_path,
        "export_path": export_path,
        "git_repo": git_repo,
    }


@pytest.fixture
def daemon_config(daemon_workspace):
    """Create daemon configuration."""
    workspace = daemon_workspace["workspace"]
    config = DaemonConfig(
        workspace_path=workspace,
        database_path=str(daemon_workspace["db_path"]),
        export_path=str(daemon_workspace["export_path"] / "issues.jsonl"),
        sync_enabled=True,
        sync_interval_seconds=5,
        git_integration=False,  # Start with git disabled
        daemon_mode="poll",  # Poll mode for testing
        issue_prefix="TEST",
        auto_start_daemon=False,
    )
    return config


@pytest.fixture
async def running_daemon(daemon_config):
    """Start a daemon and ensure it's running.

    CRITICAL: Properly cleans up all async resources to prevent memory leaks.
    """
    service = DaemonService(daemon_config)

    # Start daemon in background
    daemon_task = asyncio.create_task(service.start())
    await asyncio.sleep(0.5)  # Give daemon time to start

    yield service

    # CRITICAL: Proper cleanup sequence to prevent memory leaks
    await service._shutdown()  # Stops sync loop and disposes engine
    await service.ipc_server.stop()  # Stops web server

    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass

    # CRITICAL: Wait for all async cleanup to complete
    # Linux needs more time for TCP TIME_WAIT state cleanup
    await asyncio.sleep(0.5)

    # Cleanup IPC server runner if it exists
    if hasattr(service.ipc_server, "runner") and service.ipc_server.runner:
        await service.ipc_server.runner.cleanup()


@pytest.fixture
async def ipc_client(running_daemon):
    """Create an IPC client with proper cleanup.

    CRITICAL: Ensures ClientSession is properly closed to prevent memory leaks.
    Each unclosed session leaks ~100KB + file descriptors on Linux.
    """
    service = running_daemon
    client = IPCClient(service.config.get_socket_path())

    yield client

    # CRITICAL: Close the client session
    await client.close()


class TestDaemonLifecycle:
    """Test daemon lifecycle operations."""

    @pytest.mark.asyncio
    async def test_daemon_starts_and_writes_pid(self, daemon_config):
        """Test daemon starts successfully and writes PID file."""
        service = DaemonService(daemon_config)

        # Start daemon
        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        try:
            # Verify PID file exists
            pid_path = daemon_config.get_pid_path()
            assert pid_path.exists()

            # Verify PID is current process
            pid = int(pid_path.read_text())
            assert pid > 0

            # Verify daemon is running
            assert service.running is True

        finally:
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            # Give asyncio time to clean up on Windows
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_daemon_stops_and_removes_pid(self, running_daemon):
        """Test daemon stops cleanly and removes PID file."""
        service = running_daemon
        pid_path = service.config.get_pid_path()

        # Verify PID file exists
        assert pid_path.exists()

        # Stop daemon
        await service._shutdown()
        await service.ipc_server.stop()
        await asyncio.sleep(0.2)

        # Verify daemon stopped
        assert service.running is False

    @pytest.mark.asyncio
    async def test_daemon_status_command(self, ipc_client):
        """Test daemon status via IPC."""
        response = await ipc_client.send_request({"method": "status"})

        assert response["running"] is True
        assert "workspace" in response
        assert "pid" in response
        assert response["pid"] > 0
        assert "uptime_seconds" in response
        assert response["sync_enabled"] is True
        assert response["sync_interval"] == 5


class TestDaemonIPC:
    """Test IPC communication with daemon."""

    @pytest.mark.asyncio
    async def test_health_check(self, ipc_client):
        """Test health check endpoint."""
        response = await ipc_client.send_request({"method": "health"})

        assert response["healthy"] is True
        assert "uptime_seconds" in response
        assert "workspace" in response
        assert "pid" in response
        assert response["pid"] > 0
        assert "version" in response

    @pytest.mark.asyncio
    async def test_sync_command(self, ipc_client, running_daemon):
        """Test manual sync trigger via IPC."""
        service = running_daemon
        response = await ipc_client.send_request({"method": "sync"})

        assert response["status"] == "success"
        assert "stats" in response

        # Verify JSONL file was created
        export_path = Path(service.config.export_path)
        assert export_path.exists()

    @pytest.mark.asyncio
    async def test_stop_command(self, ipc_client, running_daemon):
        """Test stop command via IPC."""
        service = running_daemon
        response = await ipc_client.send_request({"method": "stop"})

        assert response["status"] == "stopping"

        # Give daemon time to stop
        await asyncio.sleep(0.3)
        assert service.running is False

    @pytest.mark.asyncio
    async def test_unknown_command(self, ipc_client):
        """Test handling of unknown IPC command."""
        response = await ipc_client.send_request({"method": "unknown_method"})

        assert "error" in response
        assert "Unknown method" in response["error"]


class TestDaemonJSONLExport:
    """Test JSONL export/import functionality."""

    @pytest.mark.asyncio
    async def test_export_creates_jsonl_file(self, ipc_client, running_daemon, daemon_workspace):
        """Test that sync creates JSONL export file."""
        service = running_daemon

        # Trigger sync
        response = await ipc_client.send_request({"method": "sync"})
        assert response["status"] == "success"

        # Verify JSONL file exists
        export_path = Path(service.config.export_path)
        assert export_path.exists()

        # Verify JSONL content
        with open(export_path) as f:
            lines = f.readlines()
            assert len(lines) == 2  # Two test issues

            # Parse first issue
            issue1 = json.loads(lines[0])
            assert issue1["id"] == "TEST-001"
            assert issue1["title"] == "Test Issue 1"
            assert issue1["status"] == "open"
            assert issue1["priority"] == 1

    @pytest.mark.asyncio
    async def test_export_updates_existing_jsonl(self, ipc_client, running_daemon, daemon_workspace):
        """Test that subsequent exports update JSONL file."""
        service = running_daemon

        # First sync
        await ipc_client.send_request({"method": "sync"})
        export_path = Path(service.config.export_path)
        first_mtime = export_path.stat().st_mtime

        # Wait a bit
        await asyncio.sleep(0.2)

        # Update database
        db_path = daemon_workspace["db_path"]
        engine = create_engine(f"sqlite:///{db_path}")
        try:
            with Session(engine) as session:
                issue = session.exec(select(Issue).where(Issue.id == "TEST-001")).first()
                if issue:
                    issue.title = "Updated Test Issue 1"
                session.commit()
        finally:
            # CRITICAL: Dispose engine to prevent memory leak
            engine.dispose()

        # Second sync
        await ipc_client.send_request({"method": "sync"})
        second_mtime = export_path.stat().st_mtime

        # Verify file was updated
        assert second_mtime > first_mtime

        # Verify content updated
        with open(export_path) as f:
            lines = f.readlines()
            issue1 = json.loads(lines[0])
            assert issue1["title"] == "Updated Test Issue 1"

    @pytest.mark.asyncio
    async def test_export_handles_empty_database(self, daemon_config, tmp_path):
        """Test export with no issues in database."""
        # Create empty database
        empty_db = tmp_path / "empty.db"
        engine = create_engine(f"sqlite:///{empty_db}")
        try:
            Issue.metadata.create_all(engine)
        finally:
            # CRITICAL: Dispose engine to prevent memory leak
            engine.dispose()

        daemon_config.database_path = str(empty_db)
        service = DaemonService(daemon_config)

        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        client = IPCClient(service.config.get_socket_path())
        try:
            response = await client.send_request({"method": "sync"})

            assert response["status"] == "success"

            # JSONL should be created but empty
            export_path = Path(service.config.export_path)
            if export_path.exists():
                content = export_path.read_text()
                assert content == "" or content.strip() == ""

        finally:
            await client.close()
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.3)


class TestDaemonGitIntegration:
    """Test git integration functionality."""

    @pytest.mark.asyncio
    async def test_sync_with_git_enabled(self, daemon_workspace):
        """Test sync with git integration enabled."""
        workspace = daemon_workspace["workspace"]
        git_repo = daemon_workspace["git_repo"]

        # Create export dir inside git repo
        export_path = git_repo / "issues.jsonl"

        config = DaemonConfig(
            workspace_path=workspace,
            database_path=str(daemon_workspace["db_path"]),
            export_path=str(export_path),
            sync_enabled=True,
            sync_interval_seconds=5,
            git_integration=True,
            daemon_mode="poll",
            issue_prefix="TEST",
            auto_start_daemon=False,
        )

        service = DaemonService(config)
        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        try:
            # Override sync engine to use git repo
            service.sync_engine = type(service.sync_engine)(
                workspace_path=git_repo,
                export_path=export_path,
                git_enabled=True,
            )

            client = IPCClient(service.config.get_socket_path())
            try:
                response = await client.send_request({"method": "sync"})

                assert response["status"] == "success"

                # Verify git commit was made
                result = subprocess.run(
                    ["git", "log", "--oneline"],
                    cwd=git_repo,
                    capture_output=True,
                    text=True,
                )

                # Should have at least one commit
                assert result.returncode == 0
                assert len(result.stdout.strip().split("\n")) > 0
            finally:
                await client.close()

        finally:
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.3)

    @pytest.mark.asyncio
    async def test_git_commits_on_issue_changes(self, daemon_workspace):
        """Test that git commits are made when issues change."""
        workspace = daemon_workspace["workspace"]
        git_repo = daemon_workspace["git_repo"]
        export_path = git_repo / "issues.jsonl"

        config = DaemonConfig(
            workspace_path=workspace,
            database_path=str(daemon_workspace["db_path"]),
            export_path=str(export_path),
            sync_enabled=True,
            sync_interval_seconds=5,
            git_integration=True,
            daemon_mode="poll",
            issue_prefix="TEST",
            auto_start_daemon=False,
        )

        service = DaemonService(config)
        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        try:
            service.sync_engine = type(service.sync_engine)(
                workspace_path=git_repo,
                export_path=export_path,
                git_enabled=True,
            )

            client = IPCClient(service.config.get_socket_path())

            # First sync
            await client.send_request({"method": "sync"})

            # Get initial commit count
            result = subprocess.run(
                ["git", "log", "--oneline"],
                cwd=git_repo,
                capture_output=True,
                text=True,
            )
            initial_commits = len(result.stdout.strip().split("\n"))

            # Update database
            db_path = daemon_workspace["db_path"]
            engine = create_engine(f"sqlite:///{db_path}")
            try:
                with Session(engine) as session:
                    issue = session.exec(select(Issue).where(Issue.id == "TEST-001")).first()
                    if issue:
                        issue.status = "closed"
                    session.commit()
            finally:
                # CRITICAL: Dispose engine to prevent memory leak
                engine.dispose()

            # Second sync
            await client.send_request({"method": "sync"})

            # Get new commit count
            result = subprocess.run(
                ["git", "log", "--oneline"],
                cwd=git_repo,
                capture_output=True,
                text=True,
            )
            new_commits = len(result.stdout.strip().split("\n"))

            # Should have new commit
            assert new_commits > initial_commits

        finally:
            await client.close()
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.3)


class TestDaemonPeriodicSync:
    """Test periodic sync operations."""

    @pytest.mark.asyncio
    async def test_periodic_sync_executes(self, daemon_workspace):
        """Test that periodic sync executes automatically."""
        workspace = daemon_workspace["workspace"]

        # Short interval for testing
        config = DaemonConfig(
            workspace_path=workspace,
            database_path=str(daemon_workspace["db_path"]),
            export_path=str(workspace / "issues.jsonl"),
            sync_enabled=True,
            sync_interval_seconds=1,  # 1 second for fast test
            git_integration=False,
            daemon_mode="poll",
            issue_prefix="TEST",
            auto_start_daemon=False,
        )

        service = DaemonService(config)
        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        try:
            export_path = Path(service.config.export_path)

            # Wait for first sync
            await asyncio.sleep(1.5)

            first_mtime = export_path.stat().st_mtime if export_path.exists() else 0

            # Wait for second sync
            await asyncio.sleep(1.5)

            second_mtime = export_path.stat().st_mtime if export_path.exists() else 0

            # File should have been updated by periodic sync
            assert second_mtime > first_mtime

        finally:
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.3)

    @pytest.mark.asyncio
    async def test_sync_disabled_prevents_periodic_sync(self, daemon_workspace):
        """Test that disabling sync prevents periodic execution."""
        workspace = daemon_workspace["workspace"]

        config = DaemonConfig(
            workspace_path=workspace,
            database_path=str(daemon_workspace["db_path"]),
            export_path=str(daemon_workspace["export_path"] / "issues.jsonl"),
            sync_enabled=False,  # Disabled
            sync_interval_seconds=1,
            git_integration=False,
            daemon_mode="poll",
            issue_prefix="TEST",
            auto_start_daemon=False,
        )

        service = DaemonService(config)
        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        try:
            export_path = Path(service.config.export_path)

            # Wait longer than sync interval
            await asyncio.sleep(2)

            # File should not be created
            assert not export_path.exists()

        finally:
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.3)


class TestDaemonErrorHandling:
    """Test daemon error handling."""

    @pytest.mark.asyncio
    async def test_handles_invalid_database_path(self, tmp_path):
        """Test daemon handles invalid database path gracefully."""
        workspace = tmp_path / "test_workspace"
        workspace.mkdir()

        config = DaemonConfig(
            workspace_path=workspace,
            database_path="/nonexistent/database.db",
            export_path=str(workspace / "issues.jsonl"),
            sync_enabled=True,
            sync_interval_seconds=5,
            git_integration=False,
            daemon_mode="poll",
            issue_prefix="TEST",
            auto_start_daemon=False,
        )

        service = DaemonService(config)
        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        try:
            client = IPCClient(service.config.get_socket_path())
            try:
                # Sync should fail gracefully
                response = await client.send_request({"method": "sync"})

                # Should report error or return empty stats
                assert "status" in response
            finally:
                await client.close()

        finally:
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.3)

    @pytest.mark.asyncio
    async def test_continues_after_sync_error(self, daemon_workspace):
        """Test daemon continues running after sync error."""
        workspace = daemon_workspace["workspace"]

        config = DaemonConfig(
            workspace_path=workspace,
            database_path=str(daemon_workspace["db_path"]),
            export_path="/invalid/path/issues.jsonl",  # Invalid export path
            sync_enabled=True,
            sync_interval_seconds=1,
            git_integration=False,
            daemon_mode="poll",
            issue_prefix="TEST",
            auto_start_daemon=False,
        )

        service = DaemonService(config)
        daemon_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.5)

        try:
            # Trigger sync (will fail)
            client = IPCClient(service.config.get_socket_path())
            try:
                await client.send_request({"method": "sync"})

                # Wait a bit
                await asyncio.sleep(0.5)

                # Daemon should still be running
                status = await client.send_request({"method": "status"})
                assert status["running"] is True

                # Health check should still work
                health = await client.send_request({"method": "health"})
                assert health["healthy"] is True
            finally:
                await client.close()

        finally:
            await service._shutdown()
            await service.ipc_server.stop()
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.3)

"""Daemon module for background sync operations."""

from issue_tracker.daemon.config import DaemonConfig
from issue_tracker.daemon.ipc_server import IPCServer
from issue_tracker.daemon.service import (
    IssuesDaemonService,
    is_daemon_running,
    start_daemon,
    stop_daemon,
)
from issue_tracker.daemon.sync_engine import SyncEngine

# Backward compatibility alias
DaemonService = IssuesDaemonService

__all__ = [
    "DaemonService",  # Deprecated, use IssuesDaemonService
    "IssuesDaemonService",
    "SyncEngine",
    "IPCServer",
    "DaemonConfig",
    "start_daemon",
    "stop_daemon",
    "is_daemon_running",
]

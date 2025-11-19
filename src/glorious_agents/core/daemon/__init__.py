"""Daemon infrastructure for background services.

Provides reusable components for creating background daemons:
- BaseDaemonService: Core lifecycle management
- IPCServer/IPCClient: HTTP-based inter-process communication
- PIDFileManager: Process tracking and cleanup
- BaseWatcher: File system monitoring
- PeriodicTask: Background task scheduling
- DaemonConfig: Configuration management
- DaemonRegistry: Registry for tracking all running daemons
"""

from glorious_agents.core.daemon.base import BaseDaemonService
from glorious_agents.core.daemon.config import DaemonConfig
from glorious_agents.core.daemon.ipc import IPCClient, IPCServer
from glorious_agents.core.daemon.lifecycle import is_daemon_running, start_daemon, stop_daemon
from glorious_agents.core.daemon.pid import PIDFileManager
from glorious_agents.core.daemon.registry import DaemonInfo, DaemonRegistry, get_registry
from glorious_agents.core.daemon.tasks import PeriodicTask
from glorious_agents.core.daemon.watcher import BaseWatcher

# Re-export run_daemon from daemon_rpc for backward compatibility
from glorious_agents.core.daemon_rpc import run_daemon

__all__ = [
    "BaseDaemonService",
    "DaemonConfig",
    "IPCServer",
    "IPCClient",
    "PIDFileManager",
    "PeriodicTask",
    "BaseWatcher",
    "DaemonRegistry",
    "DaemonInfo",
    "get_registry",
    "start_daemon",
    "stop_daemon",
    "is_daemon_running",
    "run_daemon",  # For backward compatibility
]

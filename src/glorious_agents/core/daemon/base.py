"""Base daemon service with lifecycle management."""

import asyncio
import logging
import os
import signal
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from glorious_agents.core.daemon.config import DaemonConfig
from glorious_agents.core.daemon.ipc import IPCServer
from glorious_agents.core.daemon.pid import PIDFileManager

logger = logging.getLogger(__name__)


class BaseDaemonService(ABC):
    """Base class for all daemon services with lifecycle management.

    Provides common daemon functionality:
    - PID file management
    - IPC server for communication
    - Signal handling for graceful shutdown
    - Health checks
    - Logging setup

    Subclasses implement:
    - on_startup(): Initialize daemon-specific resources
    - on_shutdown(): Cleanup daemon-specific resources
    - get_health_info(): Return daemon-specific health data
    - handle_command(): Handle daemon-specific IPC commands
    """

    def __init__(self, config: DaemonConfig) -> None:
        """Initialize daemon service.

        Args:
            config: Daemon configuration
        """
        self.config = config
        self.workspace_path = config.workspace_path
        self.running = False
        self.start_time = datetime.now()

        # Core components
        self.pid_manager = PIDFileManager(config.get_pid_path())
        self.ipc_server = IPCServer(config.get_socket_path(), self._handle_ipc_request)

        # Background tasks managed by subclass
        self._tasks: list[asyncio.Task[Any]] = []
        self._loop: asyncio.AbstractEventLoop | None = None

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup file-based logging for daemon."""
        log_path = self.config.get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, self.config.log_level))
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.setLevel(getattr(logging, self.config.log_level))

        logger.info(f"Logging initialized: {log_path}")

    def _handle_ipc_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle IPC requests with standard commands.

        Args:
            request: Request dictionary with 'method' key

        Returns:
            Response dictionary
        """
        method = request.get("method", "")

        # Standard commands handled by base class
        if method == "health":
            return self._get_health()
        elif method == "status":
            return self._get_status()
        elif method == "stop":
            # Schedule shutdown in event loop
            if self._loop:
                self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self._shutdown()))
            return {"status": "stopping"}
        else:
            # Delegate to subclass for custom commands
            return self.handle_command(request)

    def _get_health(self) -> dict[str, Any]:
        """Get health check information.

        Returns:
            Health status dictionary
        """
        uptime = int((datetime.now() - self.start_time).total_seconds())

        health = {
            "healthy": self.running,
            "uptime_seconds": uptime,
            "workspace": str(self.workspace_path),
            "pid": os.getpid(),
        }

        # Add subclass-specific health info
        try:
            health.update(self.get_health_info())
        except Exception as e:
            logger.error(f"Error getting health info: {e}", exc_info=True)
            health["health_check_error"] = str(e)

        return health

    def _get_status(self) -> dict[str, Any]:
        """Get detailed status information.

        Returns:
            Status dictionary
        """
        return {
            "running": self.running,
            "workspace": str(self.workspace_path),
            "pid": os.getpid(),
            "uptime_seconds": int((datetime.now() - self.start_time).total_seconds()),
            "daemon_mode": self.config.daemon_mode,
            "config": self.config.to_dict(),
        }

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown signal handlers."""

        def signal_handler(sig: int) -> None:
            logger.info(f"Received signal {sig}, initiating shutdown")
            if self._loop:
                self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self._shutdown()))

        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s))
            signal.signal(signal.SIGINT, lambda s, f: signal_handler(s))

    async def start(self) -> None:
        """Start the daemon service."""
        logger.info(f"Starting daemon for {self.workspace_path}")

        self.running = True
        self._loop = asyncio.get_running_loop()

        # Write PID file
        self.pid_manager.write()

        # Start IPC server
        await self.ipc_server.start()

        # Setup signal handlers
        self._setup_signal_handlers()

        # Call subclass startup
        try:
            await self.on_startup()
        except Exception as e:
            logger.error(f"Error in on_startup: {e}", exc_info=True)
            await self._shutdown()
            raise

        logger.info("Daemon started successfully")

    async def _shutdown(self) -> None:
        """Shutdown the daemon gracefully."""
        if not self.running:
            return

        logger.info("Initiating daemon shutdown")
        self.running = False

        # Call subclass shutdown
        try:
            await self.on_shutdown()
        except Exception as e:
            logger.error(f"Error in on_shutdown: {e}", exc_info=True)

        # Cancel all background tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Stop IPC server
        await self.ipc_server.stop()

        # Remove PID file
        self.pid_manager.remove()

        # Clear event loop reference
        self._loop = None

        logger.info("Daemon shutdown complete")

    async def run(self) -> None:
        """Run the daemon (blocking).

        This is the main entry point for daemon execution.
        It starts the daemon and runs until shutdown is triggered.
        """
        await self.start()

        # Keep running until shutdown
        while self.running:
            await asyncio.sleep(1)

        await self._shutdown()

    @abstractmethod
    async def on_startup(self) -> None:
        """Called when daemon starts.

        Subclasses should initialize their specific resources here
        (e.g., start periodic tasks, open database connections).
        """
        pass

    @abstractmethod
    async def on_shutdown(self) -> None:
        """Called when daemon shuts down.

        Subclasses should cleanup their specific resources here
        (e.g., stop periodic tasks, close database connections).
        """
        pass

    @abstractmethod
    def get_health_info(self) -> dict[str, Any]:
        """Get daemon-specific health information.

        Returns:
            Dictionary with health metrics specific to this daemon
        """
        pass

    def handle_command(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle daemon-specific IPC commands.

        Override this to add custom commands beyond the standard ones
        (health, status, stop).

        Args:
            request: Request dictionary

        Returns:
            Response dictionary
        """
        return {"error": f"Unknown command: {request.get('method')}"}

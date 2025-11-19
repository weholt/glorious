"""Code-atlas daemon service using new infrastructure.

Refactored daemon that uses the new BaseDaemonService and BaseWatcher
infrastructure while maintaining existing functionality.
"""

import asyncio
from pathlib import Path
from typing import Any

from glorious_agents.core.daemon.base import BaseDaemonService
from glorious_agents.core.daemon.config import DaemonConfig
from glorious_agents.core.daemon.tasks import PeriodicTask
from glorious_agents.core.daemon.watcher import BaseWatcher

from .repository import CodeIndexRepository
from .scanner import ASTScanner


class CodeAtlasWatcher(BaseWatcher):
    """File system watcher for code-atlas daemon."""

    def __init__(self, watch_paths: list[Path], **kwargs: Any) -> None:
        """Initialize watcher with paths to monitor.

        Args:
            watch_paths: List of paths to monitor for changes
            **kwargs: Additional keyword arguments passed to BaseWatcher
        """
        super().__init__(**kwargs)
        self.watch_paths = watch_paths
        self._scanner = ASTScanner()

    def on_file_change(self, file_path: Path) -> None:
        """Handle file change event.

        Args:
            file_path: Path to the changed file
        """
        # Only handle Python files
        if not file_path.suffix == ".py":
            return

        self.logger.info(f"File changed: {file_path}")

    def on_directory_change(self, dir_path: Path) -> None:
        """Handle directory change event.

        Args:
            dir_path: Path to the changed directory
        """
        self.logger.debug(f"Directory changed: {dir_path}")


class CodeAtlasDaemonService(BaseDaemonService):
    """Daemon service for code-atlas scanning operations.

    Monitors file system for changes and triggers code rescanning.
    """

    def __init__(self, config: DaemonConfig, **kwargs: Any) -> None:
        """Initialize daemon service.

        Args:
            config: Daemon configuration
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.watch_paths: list[Path] = []
        self.repository: CodeIndexRepository | None = None
        self._scan_task: PeriodicTask | None = None

    async def start(self) -> None:
        """Start the daemon service."""
        await super().start()

        # Initialize repository and scanner
        index_path = self.config.data_dir / "code_index.json"
        self.repository = CodeIndexRepository(index_path)

        # Setup watchers
        await self._setup_watchers()

        # Setup periodic tasks
        await self._setup_tasks()

        # Perform initial scan
        await self._perform_scan("initial")

        self.logger.info("Code-atlas daemon started")

    async def stop(self) -> None:
        """Stop the daemon service."""
        self.logger.info("Stopping code-atlas daemon")

        if self._scan_task:
            await self._scan_task.stop()

        await super().stop()

    async def _setup_watchers(self) -> None:
        """Setup file system watchers."""
        # Get paths to watch from config or default to current directory
        if self.watch_paths:
            watch_dirs = self.watch_paths
        else:
            watch_dirs = [Path.cwd()]

        # Create watcher
        watcher = CodeAtlasWatcher(
            watch_paths=watch_dirs,
            recursive=True,
            debounce_interval=2.0,  # 2 second debounce
        )

        # Start watcher
        await self.add_watcher(watcher)

    async def _setup_tasks(self) -> None:
        """Setup periodic background tasks."""

        # Periodic full rescan (every 10 minutes)
        async def periodic_scan() -> None:
            await self._perform_scan("periodic")

        self._scan_task = PeriodicTask(
            func=periodic_scan,
            interval_seconds=600.0,  # 10 minutes
            name="periodic_scan",
        )

        await self.add_task(self._scan_task)

    async def _perform_scan(self, trigger: str) -> None:
        """Perform code scanning and update index.

        Args:
            trigger: Reason for the scan ("initial", "periodic", "watch")
        """
        try:
            self.logger.info(f"Starting scan (trigger: {trigger})")

            if not self.repository:
                self.logger.error("Repository not initialized")
                return

            # Perform scan using AST scanner
            scanner = ASTScanner()

            # Scan all watch paths
            all_entities = []
            for watch_path in self.watch_paths if self.watch_paths else [Path.cwd()]:
                if watch_path.exists():
                    entities = await asyncio.to_thread(scanner.scan_directory, watch_path)
                    all_entities.extend(entities)

            # Update repository
            if all_entities:
                self.repository.update_entities(all_entities)
                await asyncio.to_thread(self.repository.save)
                self.logger.info(f"Scan complete: {len(all_entities)} entities indexed")
            else:
                self.logger.info("Scan complete: no entities found")

        except Exception as e:
            self.logger.error(f"Scan failed: {e}")

    async def handle_scan_request(self, path: Path | None = None) -> dict[str, Any]:
        """Handle manual scan request via RPC.

        Args:
            path: Optional path to scan (defaults to watch paths)

        Returns:
            Dict with scan results
        """
        if path:
            self.watch_paths = [path]

        await self._perform_scan("manual")

        return {
            "status": "success",
            "message": "Scan completed",
            "watch_paths": [str(p) for p in self.watch_paths],
        }


def create_daemon_service(config_data: dict[str, Any]) -> CodeAtlasDaemonService:
    """Create and configure code-atlas daemon service.

    Args:
        config_data: Configuration dictionary

    Returns:
        Configured daemon service instance
    """
    config = DaemonConfig.from_dict(config_data)
    return CodeAtlasDaemonService(config)


async def main() -> None:
    """Main entry point for daemon service."""
    # Load configuration
    config_data = {
        "daemon_name": "code-atlas",
        "data_dir": Path.home() / ".cache" / "code-atlas",
        "log_level": "INFO",
        "port": 8765,  # Different port from other services
    }

    # Create service
    service = create_daemon_service(config_data)

    # Run service
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())

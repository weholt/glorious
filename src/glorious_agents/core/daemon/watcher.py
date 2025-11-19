"""File system monitoring for daemon services."""

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Watchdog is optional - gracefully handle if not installed
try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    # Provide stub types when watchdog not available
    WATCHDOG_AVAILABLE = False

    class FileSystemEvent:  # type: ignore[no-redef]
        src_path: str
        is_directory: bool

    class FileSystemEventHandler:  # type: ignore[no-redef]
        pass

    class Observer:  # type: ignore[no-redef]
        pass


class BaseWatcher(ABC):
    """Base class for file system watchers.

    Provides cross-platform file system monitoring using watchdog
    with debouncing and pattern matching.
    """

    def __init__(
        self,
        watch_path: Path,
        patterns: list[str] | None = None,
        debounce_seconds: float = 2.0,
    ) -> None:
        """Initialize watcher.

        Args:
            watch_path: Path to watch for changes
            patterns: File patterns to monitor (e.g., ['*.py', '*.md'])
            debounce_seconds: Minimum seconds between change notifications
        """
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog package required for file system monitoring")

        self.watch_path = watch_path
        self.patterns = patterns or ["*"]
        self.debounce_seconds = debounce_seconds
        self._observer: Any = None  # Observer type from watchdog
        self._pending_changes: set[Path] = set()
        self._debounce_task: asyncio.Task[None] | None = None
        self._last_notification = 0.0

    def _matches_pattern(self, path: str) -> bool:
        """Check if path matches any of the watch patterns.

        Args:
            path: File path to check

        Returns:
            True if path matches any pattern
        """
        if "*" in self.patterns:
            return True

        path_obj = Path(path)
        for pattern in self.patterns:
            if path_obj.match(pattern):
                return True
        return False

    def _create_event_handler(self) -> FileSystemEventHandler:
        """Create watchdog event handler.

        Returns:
            Event handler that triggers on_change callback
        """
        watcher = self

        class EventHandler(FileSystemEventHandler):
            def on_any_event(self, event: FileSystemEvent) -> None:
                if event.is_directory:
                    return

                # Explicitly convert to string for type safety
                src_path_str: str = str(event.src_path)
                if watcher._matches_pattern(src_path_str):
                    watcher._pending_changes.add(Path(src_path_str))
                    watcher._schedule_notification()

        return EventHandler()

    def _schedule_notification(self) -> None:
        """Schedule debounced notification."""
        import time

        # Cancel existing debounce task
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        async def debounced_notify() -> None:
            await asyncio.sleep(self.debounce_seconds)

            if self._pending_changes:
                changes = list(self._pending_changes)
                self._pending_changes.clear()
                self._last_notification = time.time()

                try:
                    await self.on_change(changes)
                except Exception as e:
                    logger.error(f"Error in on_change handler: {e}", exc_info=True)

        # Schedule new debounce task
        self._debounce_task = asyncio.create_task(debounced_notify())

    @abstractmethod
    async def on_change(self, paths: list[Path]) -> None:
        """Handle file system changes.

        Called after debounce period when files have changed.

        Args:
            paths: List of changed file paths
        """
        pass

    async def start(self) -> None:
        """Start watching for file changes.

        Raises:
            FileNotFoundError: If watch_path doesn't exist
        """
        if not self.watch_path.exists():
            raise FileNotFoundError(f"Watch path not found: {self.watch_path}")

        if not self.watch_path.is_dir():
            raise ValueError(f"Watch path is not a directory: {self.watch_path}")

        self._observer = Observer()
        handler = self._create_event_handler()
        self._observer.schedule(handler, str(self.watch_path), recursive=True)
        self._observer.start()

        logger.info(f"Watching {self.watch_path} for patterns: {self.patterns}")

    async def stop(self) -> None:
        """Stop watching for file changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
            try:
                await self._debounce_task
            except asyncio.CancelledError:
                pass

        logger.info("File watcher stopped")

    @property
    def is_running(self) -> bool:
        """Check if watcher is active.

        Returns:
            True if watching for changes
        """
        return self._observer is not None and self._observer.is_alive()

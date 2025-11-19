"""Periodic task scheduling for background operations."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class PeriodicTask:
    """Executes tasks at regular intervals with error recovery.

    Handles both sync and async callbacks, automatic error recovery,
    and graceful cancellation.
    """

    def __init__(
        self,
        interval: float,
        callback: Callable[[], Any] | Callable[[], Coroutine[Any, Any, Any]],
        name: str | None = None,
    ) -> None:
        """Initialize periodic task.

        Args:
            interval: Seconds between executions
            callback: Function to call periodically (sync or async)
            name: Optional task name for logging
        """
        self.interval = interval
        self.callback = callback
        self.name = name or callback.__name__
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def _run_loop(self) -> None:
        """Main task loop with error recovery."""
        logger.info(f"Starting periodic task '{self.name}' (interval: {self.interval}s)")

        while not self._stop_event.is_set():
            try:
                # Execute callback
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback()
                else:
                    # Run sync callback in executor
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, self.callback)

            except Exception as e:
                logger.error(f"Error in periodic task '{self.name}': {e}", exc_info=True)
                # Continue running despite errors

            # Wait for interval or stop event
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
            except TimeoutError:
                # Timeout is normal - interval elapsed
                pass

    async def start(self) -> None:
        """Start the periodic task.

        Raises:
            RuntimeError: If task is already running
        """
        if self._task is not None and not self._task.done():
            raise RuntimeError(f"Task '{self.name}' is already running")

        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Periodic task '{self.name}' started")

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the periodic task gracefully.

        Args:
            timeout: Maximum seconds to wait for task to finish
        """
        if self._task is None:
            return

        logger.info(f"Stopping periodic task '{self.name}'")
        self._stop_event.set()

        try:
            await asyncio.wait_for(self._task, timeout=timeout)
        except TimeoutError:
            logger.warning(f"Task '{self.name}' didn't stop within {timeout}s, cancelling")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            pass

        self._task = None
        logger.info(f"Periodic task '{self.name}' stopped")

    @property
    def is_running(self) -> bool:
        """Check if task is currently running.

        Returns:
            True if task is active
        """
        return self._task is not None and not self._task.done()

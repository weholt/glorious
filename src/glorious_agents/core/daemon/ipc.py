"""HTTP-based inter-process communication for daemons.

Provides aiohttp-based IPC server and client for daemon communication.
Uses HTTP over a dynamically assigned port to avoid socket file issues.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, ClientTimeout, web

logger = logging.getLogger(__name__)


class IPCServer:
    """HTTP-based IPC server using aiohttp.

    Runs on a random available port and writes the port number to a file
    for client discovery. This avoids Unix socket limitations on Windows.
    """

    def __init__(
        self, socket_path: Path, handler: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> None:
        """Initialize IPC server.

        Args:
            socket_path: Path to write port number (not an actual socket)
            handler: Synchronous function to handle requests
        """
        self.socket_path = socket_path
        self.handler = handler
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self.port: int | None = None

        # Setup routes
        self.app.router.add_post("/", self._handle_request)

    async def _handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming HTTP request.

        Args:
            request: aiohttp request object

        Returns:
            JSON response
        """
        try:
            data = await request.json()

            # Run synchronous handler in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, self.handler, data)

            return web.json_response(response)
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)

    async def start(self) -> None:
        """Start the IPC server on a random available port."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # Bind to random port (port=0 means any available)
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()

        # Get actual port and write to file
        # Access underlying server to get the actual port
        assert self.site._server is not None
        self.port = self.site._server.sockets[0].getsockname()[1]  # type: ignore[attr-defined]

        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        self.socket_path.write_text(str(self.port))

        logger.info(f"IPC server started on port {self.port}")

    async def stop(self) -> None:
        """Stop the IPC server and cleanup resources."""
        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        if self.socket_path.exists():
            self.socket_path.unlink()

        logger.info("IPC server stopped")


class IPCClient:
    """HTTP-based IPC client for daemon communication.

    Discovers daemon port from file and sends requests over HTTP.
    """

    def __init__(self, socket_path: Path) -> None:
        """Initialize IPC client.

        Args:
            socket_path: Path to port file
        """
        self.socket_path = socket_path
        self._session: ClientSession | None = None

    async def _get_session(self) -> ClientSession:
        """Get or create a reusable ClientSession.

        Returns:
            ClientSession instance
        """
        if self._session is None:
            self._session = ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the client session and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None

    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send request to daemon and return response.

        Args:
            request: Request dictionary

        Returns:
            Response dictionary from daemon

        Raises:
            ConnectionError: If cannot connect to daemon
        """
        if not self.socket_path.exists():
            raise ConnectionError(f"Daemon not running (no port file at {self.socket_path})")

        try:
            port = int(self.socket_path.read_text().strip())
            url = f"http://127.0.0.1:{port}/"

            session = await self._get_session()
            async with session.post(url, json=request, timeout=ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ConnectionError(f"Daemon returned error {resp.status}: {error_text}")

                result: dict[str, Any] = await resp.json()
                return result

        except ValueError as e:
            raise ConnectionError(f"Invalid port file: {e}") from e
        except TimeoutError as e:
            raise ConnectionError("Request to daemon timed out") from e
        except Exception as e:
            raise ConnectionError(f"Failed to connect to daemon: {e}") from e

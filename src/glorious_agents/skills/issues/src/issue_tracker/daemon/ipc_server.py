"""IPC server for daemon communication using HTTP (cross-platform)."""

import asyncio
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, ClientTimeout, web

__all__ = ["IPCServer", "IPCClient"]

logger = logging.getLogger(__name__)


class IPCServer:
    """IPC server using HTTP on localhost (cross-platform)."""

    def __init__(self, socket_path: Path, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        """Initialize IPC server.

        Args:
            socket_path: Path to file storing port number
            handler: Request handler function
        """
        self.socket_path = socket_path
        self.handler = handler
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self.port: int = 0

        # Add route for JSON-RPC style requests
        self.app.router.add_post("/rpc", self._handle_request)

    async def _handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming HTTP request."""
        try:
            data = await request.json()
            logger.debug(f"Received request: {data}")

            # Run synchronous handler in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, self.handler, data)
            return web.json_response(response)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return web.json_response({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Request handler error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def start(self) -> None:
        """Start the IPC server on a random available port.

        Listens on localhost and writes the assigned port to socket_path file.
        """
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # Use port 0 to get a random available port
        self.site = web.TCPSite(self.runner, "localhost", 0)
        await self.site.start()

        # Get the actual port assigned
        self.port = self.site._server.sockets[0].getsockname()[1]  # type: ignore

        # Write port to file for client to discover
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        self.socket_path.write_text(str(self.port))

        logger.info(f"IPC server listening on http://localhost:{self.port}")

    async def stop(self) -> None:
        """Stop the IPC server.

        Cleans up resources and removes the port file.
        """
        if self.runner:
            await self.runner.cleanup()

        if self.socket_path.exists():
            self.socket_path.unlink()


class IPCClient:
    """IPC client for communicating with daemon via HTTP."""

    def __init__(self, socket_path: Path) -> None:
        """Initialize IPC client.

        Args:
            socket_path: Path to file containing server port number
        """
        self.socket_path = socket_path
        self._session: ClientSession | None = None

    async def _get_session(self) -> ClientSession:
        """Get or create a reusable ClientSession.

        Returns:
            Active ClientSession instance
        """
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the client session and cleanup resources.

        CRITICAL: Must be called to prevent memory leaks on Linux.
        Each unclosed session leaks file descriptors and TCP connections.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send request to daemon and return response.

        Args:
            request: Request dictionary (method + params)

        Returns:
            Response dictionary

        Raises:
            ConnectionError: If cannot connect to daemon
        """
        if not self.socket_path.exists():
            raise ConnectionError(f"Daemon not running (no port file at {self.socket_path})")

        try:
            # Read port from file
            port = int(self.socket_path.read_text().strip())
            url = f"http://localhost:{port}/rpc"

            session = await self._get_session()
            async with session.post(url, json=request, timeout=ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ConnectionError(f"Daemon returned error {resp.status}: {error_text}")

                result: dict[str, Any] = await resp.json()
                return result

        except (FileNotFoundError, ValueError) as e:
            raise ConnectionError(f"Invalid port file: {e}")
        except TimeoutError:
            raise ConnectionError("Request to daemon timed out")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to daemon: {e}")

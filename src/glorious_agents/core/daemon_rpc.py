"""FastAPI daemon for RPC access to skills."""

import importlib
import inspect
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from glorious_agents.config import config
from glorious_agents.core.loader import load_all_skills
from glorious_agents.core.registry import get_registry
from glorious_agents.core.runtime import get_ctx, reset_ctx

logger = logging.getLogger(__name__)


def verify_api_key(x_api_key: str | None = Header(None)) -> None:
    """Verify API key if authentication is enabled.

    Raises:
        HTTPException: If API key is required but missing or invalid.
    """
    # Get fresh config to support dynamic config changes in tests
    from glorious_agents.config import get_config
    
    current_config = get_config()
    
    # If no API key is configured, allow all requests
    if current_config.DAEMON_API_KEY is None:
        logger.debug("API key authentication disabled")
        return

    # If API key is configured, require it
    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key required. Set X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if x_api_key != current_config.DAEMON_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    logger.debug("API key verified")


class RPCRequest(BaseModel):
    """Request model for RPC calls with validation."""

    params: dict[str, Any] = Field(default_factory=dict, description="Method parameters")

    class Config:
        json_schema_extra = {"example": {"params": {"key": "value", "count": 5}}}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """
    Lifespan context manager for daemon startup and shutdown.

    Handles:
    - Loading all skills on startup
    - Initializing shared context
    - Cleaning up resources on shutdown
    """
    # Startup
    logger.info("Starting Glorious Agents daemon...")
    try:
        load_all_skills()
        get_ctx()  # Initialize shared context
        logger.info("Daemon startup complete")
    except Exception as e:
        logger.error(f"Error during daemon startup: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Glorious Agents daemon...")
    try:
        reset_ctx()
        logger.info("Daemon shutdown complete")
    except Exception as e:
        logger.error(f"Error during daemon shutdown: {e}", exc_info=True)


daemon_app = FastAPI(title="Glorious Agents Daemon", lifespan=lifespan)


@daemon_app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint (no authentication required)."""
    return {"status": "healthy", "service": "glorious-agents-daemon"}


@daemon_app.get("/skills")
async def list_skills() -> list[dict[str, Any]]:
    """List all loaded skills."""
    registry = get_registry()
    skills = registry.list_all()

    return [
        {
            "name": s.name,
            "version": s.version,
            "description": s.description,
            "origin": s.origin,
            "requires": s.requires,
        }
        for s in skills
    ]


@daemon_app.post("/rpc/{skill}/{method}")
async def call_skill_method(
    skill: str,
    method: str,
    request: RPCRequest = RPCRequest(),
    _auth: None = Depends(verify_api_key),
) -> dict[str, Any]:
    """
    Call a skill method via RPC.

    Dynamically invokes a callable function from a skill module. The method must
    be a module-level function (not a Typer command) and must be callable.

    Args:
        skill: Skill name.
        method: Method name to call.
        request: Validated RPC request with parameters.

    Returns:
        Result dictionary with status and data.

    Raises:
        HTTPException: If skill not found, method not found, or call fails.
    """
    registry = get_registry()
    manifest = registry.get_manifest(skill)

    if not manifest:
        raise HTTPException(status_code=404, detail=f"Skill '{skill}' not found")

    # Get the skill module
    try:
        module_path = manifest.entry_point.split(":")[0]
        module = importlib.import_module(module_path)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import skill module {skill}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load skill module: {e}") from e

    # Get the method from the module
    if not hasattr(module, method):
        raise HTTPException(
            status_code=404,
            detail=f"Method '{method}' not found in skill '{skill}'",
        )

    func = getattr(module, method)

    # Verify it's callable
    if not callable(func):
        raise HTTPException(
            status_code=400,
            detail=f"'{method}' in skill '{skill}' is not callable",
        )

    # Call the function
    try:
        # Handle both sync and async functions
        if inspect.iscoroutinefunction(func):
            result = await func(**request.params)
        else:
            result = func(**request.params)

        return {
            "status": "success",
            "skill": skill,
            "method": method,
            "result": result,
        }
    except TypeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameters for method '{method}': {e}",
        ) from e
    except Exception as e:
        logger.error(f"Error calling {skill}.{method}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Method execution failed: {e}") from e


@daemon_app.post("/events/{topic}")
async def publish_event(
    topic: str,
    data: dict[str, Any],
    _auth: None = Depends(verify_api_key),
) -> dict[str, str]:
    """
    Publish an event to the event bus.

    Args:
        topic: Event topic name.
        data: Event data dictionary.

    Returns:
        Status message.
    """
    ctx = get_ctx()
    try:
        ctx.publish(topic, data)
        return {"status": "published", "topic": topic}
    except Exception as e:
        logger.error(f"Error publishing event to {topic}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {e}") from e


@daemon_app.get("/events/topics")
async def list_topics() -> dict[str, list[str]]:
    """
    List all active event topics with subscribers.

    Returns:
        Dictionary with topics list.
    """
    ctx = get_ctx()
    # Access the event bus's subscriber dictionary
    topics = list(ctx._event_bus._subscribers.keys())
    return {"topics": topics}


@daemon_app.get("/cache/{key:path}")
async def get_cache(key: str, _auth: None = Depends(verify_api_key)) -> dict[str, Any]:
    """
    Retrieve a value from the cache.

    Args:
        key: Cache key.

    Returns:
        Cached value or error.

    Raises:
        HTTPException: If key not found.
    """
    ctx = get_ctx()
    value = ctx.cache_get(key)

    if value is None:
        raise HTTPException(status_code=404, detail=f"Cache key '{key}' not found")

    return {"key": key, "value": value}


@daemon_app.put("/cache/{key:path}")
async def set_cache(
    key: str,
    data: dict[str, Any],
    _auth: None = Depends(verify_api_key),
) -> dict[str, str]:
    """
    Store a value in the cache with optional TTL.

    Args:
        key: Cache key.
        data: Dictionary containing 'value' key and optional 'ttl' (seconds).

    Returns:
        Status message.
    """
    ctx = get_ctx()

    if "value" not in data:
        raise HTTPException(status_code=400, detail="Missing 'value' in request body")

    ttl = data.get("ttl")
    if ttl is not None and (not isinstance(ttl, int) or ttl <= 0):
        raise HTTPException(status_code=400, detail="'ttl' must be a positive integer")

    ctx.cache_set(key, data["value"], ttl=ttl)
    return {"status": "stored", "key": key}


@daemon_app.delete("/cache/{key:path}")
async def delete_cache(key: str, _auth: None = Depends(verify_api_key)) -> dict[str, str]:
    """
    Delete a value from the cache.

    Args:
        key: Cache key.

    Returns:
        Status message.
    """
    ctx = get_ctx()

    # Use the new cache_delete method
    if not ctx.cache_delete(key):
        raise HTTPException(status_code=404, detail=f"Cache key '{key}' not found")

    return {"status": "deleted", "key": key}


@daemon_app.delete("/cache")
async def clear_cache(_auth: None = Depends(verify_api_key)) -> dict[str, Any]:
    """
    Clear all cache entries.

    Returns:
        Status message with count of cleared entries.
    """
    ctx = get_ctx()
    count = len(ctx._cache._cache)
    ctx._cache.clear()
    return {"status": "cleared", "count": count}


@daemon_app.get("/cache")
async def cache_stats(_auth: None = Depends(verify_api_key)) -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Cache statistics including size and keys.
    """
    ctx = get_ctx()
    return {
        "size": len(ctx._cache._cache),
        "keys": list(ctx._cache._cache.keys()),
    }


def run_daemon(host: str | None = None, port: int | None = None) -> None:
    """
    Run the FastAPI daemon.

    Args:
        host: Host to bind to. Uses config.DAEMON_HOST if None.
        port: Port to bind to. Uses config.DAEMON_PORT if None.
    """
    if host is None:
        host = config.DAEMON_HOST
    if port is None:
        port = config.DAEMON_PORT
    uvicorn.run(daemon_app, host=host, port=port)

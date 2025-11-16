from __future__ import annotations

"""Cache skill - short-term ephemeral storage with TTL."""

import json
from datetime import datetime, timedelta
from typing import Any

import typer
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, ValidationException, validate_input

app = typer.Typer(help="Cache management with TTL")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx


class SetCacheInput(SkillInput):
    """Input validation for setting cache values."""

    key: str = Field(..., min_length=1, max_length=500, description="Cache key")
    value: str = Field(..., min_length=1, max_length=1000000, description="Cache value")
    ttl_seconds: int | None = Field(None, ge=1, description="TTL in seconds")
    kind: str = Field("general", max_length=100, description="Cache kind")


class GetCacheInput(SkillInput):
    """Input validation for getting cache values."""

    key: str = Field(..., min_length=1, max_length=500, description="Cache key")


@validate_input
def set_cache(key: str, value: str, ttl_seconds: int | None = None, kind: str = "general") -> None:
    """
    Set a cache entry with optional TTL (callable API).

    Args:
        key: Cache key (1-500 chars).
        value: Value to cache (1-1,000,000 chars).
        ttl_seconds: Time-to-live in seconds (optional, >= 1).
        kind: Cache kind for organization.

    Raises:
        ValidationException: If input validation fails.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    # Convert value to bytes for BLOB storage
    value_bytes = value.encode("utf-8")

    _ctx.conn.execute(
        """
        INSERT OR REPLACE INTO cache_entries (key, value, kind, created_at, ttl_seconds)
        VALUES (?, ?, ?, ?, ?)
    """,
        (key, value_bytes, kind, datetime.utcnow().isoformat(), ttl_seconds),
    )
    _ctx.conn.commit()


@validate_input
def get_cache(key: str) -> str | None:
    """
    Get a cache entry (callable API).

    Args:
        key: Cache key (1-500 chars).

    Returns:
        Cached value or None if not found or expired.

    Raises:
        ValidationException: If input validation fails.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute(
        """
        SELECT value, created_at, ttl_seconds
        FROM cache_entries
        WHERE key = ?
    """,
        (key,),
    )

    row = cur.fetchone()
    if not row:
        return None

    value_bytes, created_at, ttl_seconds = row

    # Check if expired
    if ttl_seconds is not None:
        created = datetime.fromisoformat(created_at)
        expiry = created + timedelta(seconds=ttl_seconds)
        if datetime.utcnow() > expiry:
            # Delete expired entry
            _ctx.conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            _ctx.conn.commit()
            return None

    return value_bytes.decode("utf-8")


def prune_expired() -> int:
    """
    Remove expired cache entries.

    Returns:
        Number of entries deleted.
    """
    if _ctx is None:
        raise RuntimeError("Context not initialized")

    cur = _ctx.conn.execute("""
        SELECT key, created_at, ttl_seconds
        FROM cache_entries
        WHERE ttl_seconds IS NOT NULL
    """)

    expired_keys = []
    now = datetime.utcnow()

    for row in cur:
        key, created_at, ttl_seconds = row
        created = datetime.fromisoformat(created_at)
        expiry = created + timedelta(seconds=ttl_seconds)
        if now > expiry:
            expired_keys.append(key)

    if expired_keys:
        placeholders = ",".join("?" * len(expired_keys))
        _ctx.conn.execute(f"DELETE FROM cache_entries WHERE key IN ({placeholders})", expired_keys)
        _ctx.conn.commit()

    return len(expired_keys)


@app.command()
def set(
    key: str,
    value: str,
    ttl: int | None = typer.Option(None, help="TTL in seconds"),
    kind: str = typer.Option("general", help="Cache kind"),
) -> None:
    """Set a cache entry with optional TTL."""
    try:
        set_cache(key, value, ttl, kind)
        ttl_msg = f" (TTL: {ttl}s)" if ttl else ""
        console.print(f"[green]Cache entry '{key}' set{ttl_msg}[/green]")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def get(key: str) -> None:
    """Get a cache entry."""
    try:
        value = get_cache(key)
        if value is None:
            console.print(f"[yellow]Cache key '{key}' not found or expired[/yellow]")
        else:
            console.print(f"[cyan]{key}:[/cyan] {value}")
    except ValidationException as e:
        console.print(f"[red]{e.message}[/red]")


@app.command()
def list(kind: str | None = typer.Option(None, help="Filter by kind")) -> None:
    """List all cache entries."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    query = "SELECT key, kind, created_at, ttl_seconds FROM cache_entries"
    params: tuple[Any, ...] = ()

    if kind:
        query += " WHERE kind = ?"
        params = (kind,)

    query += " ORDER BY created_at DESC"

    cur = _ctx.conn.execute(query, params)

    table = Table(title="Cache Entries")
    table.add_column("Key", style="cyan")
    table.add_column("Kind", style="yellow")
    table.add_column("Created", style="dim")
    table.add_column("TTL", style="magenta")
    table.add_column("Status", style="green")

    now = datetime.utcnow()
    for row in cur:
        key_val, kind_val, created_at, ttl_seconds = row
        status = "✓ Valid"

        if ttl_seconds is not None:
            created = datetime.fromisoformat(created_at)
            expiry = created + timedelta(seconds=ttl_seconds)
            remaining = (expiry - now).total_seconds()

            if remaining <= 0:
                status = "✗ Expired"
                ttl_display = f"{ttl_seconds}s (expired)"
            else:
                ttl_display = f"{ttl_seconds}s ({int(remaining)}s left)"
        else:
            ttl_display = "∞ No expiry"

        table.add_row(key_val, kind_val or "-", created_at, ttl_display, status)

    console.print(table)


@app.command()
def prune(expired_only: bool = typer.Option(True, help="Only remove expired entries")) -> None:
    """Remove expired or all cache entries."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    if expired_only:
        deleted = prune_expired()
        console.print(f"[green]Pruned {deleted} expired cache entries[/green]")
    else:
        cur = _ctx.conn.execute("SELECT COUNT(*) FROM cache_entries")
        count = cur.fetchone()[0]

        _ctx.conn.execute("DELETE FROM cache_entries")
        _ctx.conn.commit()

        console.print(f"[green]Cleared all {count} cache entries[/green]")


@app.command()
def warmup(
    project_id: str = typer.Option(..., help="Project ID to warmup"),
    kinds: str = typer.Option("ast,symbols,deps", help="Comma-separated cache kinds"),
) -> None:
    """Warmup cache with project-specific data."""
    console.print(f"[yellow]Warmup for project '{project_id}' with kinds: {kinds}[/yellow]")

    kind_list = [k.strip() for k in kinds.split(",")]

    # Placeholder implementation - in real usage, this would populate cache
    # with actual project data (AST, symbols, dependencies, etc.)
    for kind in kind_list:
        key = f"{kind}:{project_id}"
        value = json.dumps({"project_id": project_id, "kind": kind, "status": "warmed_up"})

        try:
            set_cache(key, value, ttl_seconds=3600, kind=kind)
            console.print(f"[green]✓[/green] Warmed up {kind} cache")
        except ValidationException as e:
            console.print(f"[red]✗ Failed to warm up {kind}: {e.message}[/red]")

    console.print(f"[green]Cache warmup completed for project '{project_id}'[/green]")


@app.command()
def delete(key: str) -> None:
    """Delete a cache entry."""
    if _ctx is None:
        console.print("[red]Context not initialized[/red]")
        return

    cur = _ctx.conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
    _ctx.conn.commit()

    if cur.rowcount > 0:
        console.print(f"[green]Cache entry '{key}' deleted[/green]")
    else:
        console.print(f"[yellow]Cache key '{key}' not found[/yellow]")


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for cache entries."""
    from glorious_agents.core.search import SearchResult

    if _ctx is None:
        return []

    query_lower = query.lower()
    cur = _ctx.conn.execute(
        """
        SELECT key, value, expires_at
        FROM cache_entries
        WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
    """,
        (f"%{query_lower}%", f"%{query_lower}%", limit),
    )

    results = []
    for row in cur:
        results.append(
            SearchResult(
                skill="cache",
                id=row[0],
                type="cache_entry",
                content=f"{row[0]}: {row[1][:50]}...",
                metadata={"expires_at": row[2]},
                score=0.7,
            )
        )
    return results

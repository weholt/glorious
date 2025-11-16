"""Daemon process management utilities."""

import os
import subprocess
import sys
import time
from pathlib import Path

import typer

# Optional psutil for process checking
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def check_existing_daemon(pid_path: Path) -> bool:
    """Check if daemon is already running. Returns True if running."""
    if not pid_path.exists():
        return False

    try:
        existing_pid = int(pid_path.read_text().strip())
        if PSUTIL_AVAILABLE:
            if psutil.pid_exists(existing_pid):
                typer.echo(f"Watch daemon already running (PID: {existing_pid})")
                typer.echo(f"PID file: {pid_path}")
                return True
        else:
            if time.time() - pid_path.stat().st_mtime < 3600:
                typer.echo(f"Watch daemon may already be running (PID: {existing_pid})")
                typer.echo(f"Delete {pid_path} if daemon is not running")
                return True
    except (ValueError, OSError):
        pass
    return False


def build_daemon_command(
    path: str, output: str, debounce: float, pid_file: str, incremental: bool, deep: bool
) -> list[str]:
    """Build command line for daemon subprocess."""
    cmd = [
        sys.executable,
        "-m",
        "code_atlas.cli",
        "watch",
        str(path),
        "--output",
        str(output),
        "--debounce",
        str(debounce),
        "--pid-file",
        str(pid_file),
    ]
    if incremental:
        cmd.append("--incremental")
    else:
        cmd.append("--no-incremental")
    if deep:
        cmd.append("--deep")
    cmd.append("--_daemon-child")
    return cmd


def spawn_windows_daemon(cmd: list[str], log_path: Path, pid_path: Path) -> None:
    """Spawn daemon process on Windows."""
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200

    with open(log_path, "a", encoding="utf-8") as log_file:
        proc = subprocess.Popen(  # noqa: S603
            cmd,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )

    pid_path.write_text(str(proc.pid))
    typer.echo(f"✅ Watch daemon started (PID: {proc.pid})")
    typer.echo(f"   PID file: {pid_path}")
    typer.echo(f"   Logs: {log_path}")
    typer.echo("\nUse 'uv run code-atlas watch-status' to check status")
    typer.echo("Use 'uv run code-atlas stop-watch' to stop")


def spawn_unix_daemon(pid_path: Path, log_path: Path, root_path: Path, output_path: Path, debounce: float) -> None:
    """Spawn daemon process on Unix using double fork."""
    try:
        pid = os.fork()
        if pid > 0:
            typer.echo("✅ Watch daemon starting...")
            typer.echo(f"   PID file: {pid_path}")
            typer.echo(f"   Logs: {log_path}")
            typer.echo("\nUse 'uv run code-atlas watch-status' to check status")
            typer.echo("Use 'uv run code-atlas stop-watch' to stop")
            sys.exit(0)
    except OSError as e:
        typer.echo(f"Fork failed: {e}")
        raise typer.Exit(1) from e

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    os.chdir("/")
    os.umask(0)

    with open(log_path, "a", encoding="utf-8") as log_file:
        os.dup2(log_file.fileno(), sys.stdout.fileno())
        os.dup2(log_file.fileno(), sys.stderr.fileno())

    sys.stdin.close()
    pid_path.write_text(str(os.getpid()))

    print(f"\n{'=' * 80}")
    print(f"Watch daemon started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"PID: {os.getpid()}")
    print(f"Watching: {root_path}")
    print(f"Output: {output_path}")
    print(f"Debounce: {debounce}s")
    print(f"{'=' * 80}\n")


def setup_daemon_logging(output_path: Path, pid_path: Path, root_path: Path, debounce: float) -> None:
    """Setup logging for daemon child process."""
    log_path = output_path.parent / f"{output_path.stem}_watch.log"
    pid_path.write_text(str(os.getpid()))

    log_file = open(log_path, "a", encoding="utf-8")  # noqa: SIM115
    sys.stdout = log_file
    sys.stderr = log_file

    print(f"\n{'=' * 80}")
    print(f"Watch daemon started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"PID: {os.getpid()}")
    print(f"Watching: {root_path}")
    print(f"Output: {output_path}")
    print(f"Debounce: {debounce}s")
    print(f"{'=' * 80}\n")

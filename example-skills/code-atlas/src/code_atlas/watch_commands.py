"""Watch mode commands for CodeAtlas."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import typer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from code_atlas.daemon_utils import (
    build_daemon_command,
    check_existing_daemon,
    setup_daemon_logging,
    spawn_unix_daemon,
    spawn_windows_daemon,
)
from code_atlas.scanner import scan_directory


class _PythonFileHandler(FileSystemEventHandler):
    """Handle Python file change events."""

    def __init__(self) -> None:
        """Initialize handler with pending rescan flag."""
        super().__init__()
        self.pending_rescan = False

    def on_modified(self, event: object) -> None:
        """Handle file modification."""
        if not event.is_directory and event.src_path.endswith(".py"):  # type: ignore
            typer.echo(f"Detected change: {event.src_path}")  # type: ignore
            self.pending_rescan = True

    def on_created(self, event: object) -> None:
        """Handle file creation."""
        if not event.is_directory and event.src_path.endswith(".py"):  # type: ignore
            typer.echo(f"Detected new file: {event.src_path}")  # type: ignore
            self.pending_rescan = True

    def on_deleted(self, event: object) -> None:
        """Handle file deletion."""
        if not event.is_directory and event.src_path.endswith(".py"):  # type: ignore
            typer.echo(f"Detected deletion: {event.src_path}")  # type: ignore
            self.pending_rescan = True


def _log_message(message: str, is_daemon: bool) -> None:
    """Log message using appropriate output method.

    Args:
        message: Message to log
        is_daemon: Whether running as daemon
    """
    if is_daemon:
        print(message)
    else:
        typer.echo(message)


def _perform_initial_scan(root_path: Path, output_path: Path, incremental: bool, deep: bool, daemon: bool) -> float:
    """Perform initial scan and return timestamp.

    Args:
        root_path: Root directory to scan
        output_path: Output file path
        incremental: Use incremental caching
        deep: Enable deep analysis
        daemon: Running as daemon

    Returns:
        Timestamp of scan completion
    """
    if not daemon:
        typer.echo(f"Performing initial scan of {root_path}...")
        if incremental:
            typer.echo("Incremental mode: enabled")
        if deep:
            typer.echo("Deep analysis: enabled")

    scan_directory(root_path, output_path, incremental=incremental, deep=deep)

    if not daemon:
        typer.echo(f"Index written to {output_path}")

    return time.time()


def _handle_rescan(
    root_path: Path, output_path: Path, incremental: bool, deep: bool, is_daemon: bool
) -> None:
    """Handle rescanning the codebase.

    Args:
        root_path: Root directory
        output_path: Output file path
        incremental: Use incremental caching
        deep: Enable deep analysis
        is_daemon: Whether running as daemon
    """
    _log_message(f"\nRescanning codebase at {time.strftime('%H:%M:%S')}...", is_daemon)
    scan_directory(root_path, output_path, incremental=incremental, deep=deep)
    _log_message(f"Index updated at {output_path}", is_daemon)


def _cleanup_daemon(pid_path: Path) -> None:
    """Clean up daemon resources.

    Args:
        pid_path: Path to PID file
    """
    print(f"Watch daemon stopped at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if pid_path.exists():
        pid_path.unlink()
        print(f"Removed PID file: {pid_path}")


def _run_watch_loop(
    root_path: Path,
    output_path: Path,
    pid_path: Path,
    debounce: float,
    incremental: bool,
    deep: bool,
    daemon: bool,
    _daemon_child: bool,
) -> None:
    """Run the main watch loop."""
    is_daemon = daemon or _daemon_child

    # Initial scan
    last_scan_time = _perform_initial_scan(root_path, output_path, incremental, deep, daemon)

    # Setup watchdog observer
    event_handler = _PythonFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(root_path), recursive=True)
    observer.start()

    typer.echo(f"\nWatching {root_path} for changes (Ctrl+C to stop)...")
    typer.echo(f"Debounce delay: {debounce}s\n")

    try:
        while True:
            time.sleep(0.5)

            # Check if rescan needed and debounce period passed
            if event_handler.pending_rescan and (time.time() - last_scan_time >= debounce):
                _handle_rescan(root_path, output_path, incremental, deep, is_daemon)
                event_handler.pending_rescan = False
                last_scan_time = time.time()

    except KeyboardInterrupt:
        _log_message("\n\nReceived shutdown signal..." if _daemon_child else "\n\nStopping watch mode...", is_daemon)
        observer.stop()

    observer.join()

    # Cleanup in daemon mode
    if _daemon_child:
        _cleanup_daemon(pid_path)
    else:
        typer.echo("Watch mode stopped.")


def watch(
    path: str = typer.Argument(".", help="Path to watch"),
    output: str = typer.Option("code_index.json", help="Output file path"),
    debounce: float = typer.Option(2.0, help="Debounce delay in seconds"),
    daemon: bool = typer.Option(False, "--daemon", help="Run in background as daemon"),
    pid_file: str = typer.Option(".code_atlas_watch.pid", help="PID file for daemon mode"),
    incremental: bool = typer.Option(True, "--incremental/--no-incremental", help="Use incremental caching"),
    deep: bool = typer.Option(False, "--deep", help="Enable deep analysis"),
    _daemon_child: bool = typer.Option(False, "--_daemon-child", hidden=True, help="Internal: daemon child process"),
) -> None:
    """Watch directory for Python file changes and update index."""
    root_path = Path(path).resolve()
    output_path = Path(output).resolve()
    pid_path = Path(pid_file).resolve()

    # Handle daemon mode - spawn subprocess and exit
    if daemon:
        if check_existing_daemon(pid_path):
            raise typer.Exit(1)

        log_path = output_path.parent / f"{output_path.stem}_watch.log"
        cmd = build_daemon_command(path, output, debounce, pid_file, incremental, deep)

        if sys.platform == "win32":
            spawn_windows_daemon(cmd, log_path, pid_path)
            return
        else:
            spawn_unix_daemon(pid_path, log_path, root_path, output_path, debounce)

    # If we're the daemon child process, set up logging
    if _daemon_child:
        setup_daemon_logging(output_path, pid_path, root_path, debounce)

    # Run the watch loop
    _run_watch_loop(root_path, output_path, pid_path, debounce, incremental, deep, daemon, _daemon_child)


def _check_pid_file_exists(pid_path: Path, log_path: Path) -> int:
    """Check if PID file exists and read PID.

    Args:
        pid_path: Path to PID file
        log_path: Path to log file

    Returns:
        PID from file

    Raises:
        typer.Exit: If PID file missing or invalid
    """
    if not pid_path.exists():
        typer.echo("❌ Watch daemon is NOT running")
        typer.echo(f"   PID file not found: {pid_path}")
        if log_path.exists():
            typer.echo(f"\n📄 Last log activity: {log_path}")
            typer.echo(f"   Modified: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log_path.stat().st_mtime))}")
        raise typer.Exit(1)

    try:
        return int(pid_path.read_text().strip())
    except (ValueError, OSError) as e:
        typer.echo(f"❌ Invalid PID file: {e}")
        raise typer.Exit(1) from None


def _check_process_with_psutil(pid: int) -> bool:
    """Check if process is running using psutil.

    Args:
        pid: Process ID

    Returns:
        True if running
    """
    import psutil

    if psutil.pid_exists(pid):
        proc = psutil.Process(pid)
        typer.echo("✅ Watch daemon is RUNNING")
        typer.echo(f"   PID: {pid}")
        typer.echo(f"   Status: {proc.status()}")
        typer.echo(f"   CPU: {proc.cpu_percent(interval=0.1):.1f}%")
        typer.echo(f"   Memory: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
        typer.echo(f"   Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc.create_time()))}")
        return True
    return False


def _check_process_fallback(pid: int, pid_path: Path) -> bool:
    """Check if process is running without psutil.

    Args:
        pid: Process ID
        pid_path: Path to PID file

    Returns:
        True if running (or likely running)
    """
    try:
        os.kill(pid, 0)  # Check if process exists (Unix)
        typer.echo("✅ Watch daemon appears to be running")
        typer.echo(f"   PID: {pid}")
        return True
    except (OSError, AttributeError):
        # On Windows without psutil, check PID file age
        file_age = time.time() - pid_path.stat().st_mtime
        if file_age < 300:  # Less than 5 minutes old
            typer.echo("⚠️  Watch daemon status unknown (install psutil for accurate status)")
            typer.echo(f"   PID: {pid}")
            typer.echo(f"   PID file age: {file_age:.0f}s")
            return True
    return False


def _verify_process_running(pid: int, pid_path: Path) -> None:
    """Verify process is running, exit if not.

    Args:
        pid: Process ID
        pid_path: Path to PID file

    Raises:
        typer.Exit: If process not running
    """
    is_running = False

    try:
        is_running = _check_process_with_psutil(pid)
    except ImportError:
        is_running = _check_process_fallback(pid, pid_path)

    if not is_running:
        typer.echo("❌ Watch daemon NOT running (stale PID file)")
        typer.echo(f"   PID {pid} not found")
        typer.echo("   Run 'uv run code-atlas stop-watch' to cleanup")
        raise typer.Exit(1)


def _show_file_info(pid_path: Path, log_path: Path, output_path: Path) -> None:
    """Display file information.

    Args:
        pid_path: Path to PID file
        log_path: Path to log file
        output_path: Path to output file
    """
    typer.echo("\n📁 Files:")
    typer.echo(f"   PID file: {pid_path}")
    typer.echo(f"   Log file: {log_path}")
    if output_path.exists():
        typer.echo(f"   Index: {output_path}")
        typer.echo(
            f"   Index updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(output_path.stat().st_mtime))}"
        )


def _show_recent_logs(log_path: Path, log_lines: int) -> None:
    """Display recent log lines.

    Args:
        log_path: Path to log file
        log_lines: Number of lines to show
    """
    if log_path.exists() and log_lines > 0:
        typer.echo(f"\n📋 Recent log activity (last {log_lines} lines):")
        typer.echo("   " + "─" * 60)
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()
            for line in lines[-log_lines:]:
                typer.echo(f"   {line}")
        except OSError as e:
            typer.echo(f"   Error reading log: {e}")


def watch_status(
    pid_file: str = typer.Option(".code_atlas_watch.pid", help="PID file for daemon"),
    output: str = typer.Option("code_index.json", help="Output file path"),
    log_lines: int = typer.Option(20, help="Number of recent log lines to show"),
) -> None:
    """Check watch daemon status and show recent activity."""
    pid_path = Path(pid_file).resolve()
    output_path = Path(output).resolve()
    log_path = output_path.parent / f"{output_path.stem}_watch.log"

    pid = _check_pid_file_exists(pid_path, log_path)
    _verify_process_running(pid, pid_path)
    _show_file_info(pid_path, log_path, output_path)
    _show_recent_logs(log_path, log_lines)


def stop_watch(
    pid_file: str = typer.Option(".code_atlas_watch.pid", help="PID file for daemon"),
) -> None:
    """Stop the watch daemon."""
    pid_path = Path(pid_file).resolve()

    if not pid_path.exists():
        typer.echo("No watch daemon running (PID file not found)")
        typer.echo(f"Expected: {pid_path}")
        raise typer.Exit(1)

    try:
        pid = int(pid_path.read_text().strip())
        typer.echo(f"Stopping watch daemon (PID: {pid})...")

        # Send SIGTERM (or CTRL_BREAK_EVENT on Windows)
        try:
            if sys.platform == "win32":
                # On Windows, use taskkill
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, check=False)  # noqa: S603, S607
            else:
                os.kill(pid, signal.SIGTERM)

            # Wait a moment and check if PID file was cleaned up
            time.sleep(1)

            if pid_path.exists():
                # Force remove if daemon didn't cleanup
                pid_path.unlink()

            typer.echo("Watch daemon stopped successfully")

        except ProcessLookupError:
            typer.echo(f"Process {pid} not found (daemon may have already stopped)")
            pid_path.unlink()

    except (ValueError, OSError) as e:
        typer.echo(f"Error stopping daemon: {e}")
        raise typer.Exit(1) from e

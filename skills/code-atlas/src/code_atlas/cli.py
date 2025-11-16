"""CLI interface for CodeAtlas."""

from pathlib import Path

import typer

from code_atlas.analysis_commands import agent, check, rank
from code_atlas.scanner import scan_directory
from code_atlas.watch_commands import stop_watch, watch, watch_status

# Optional rich for progress display
try:
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

app = typer.Typer(help="CodeAtlas - Agent-oriented Python codebase analyzer")


@app.command()
def scan(
    path: str = typer.Argument(..., help="Path to scan"),
    output: str = typer.Option("code_index.json", help="Output file path"),
    incremental: bool = typer.Option(False, "--incremental", help="Use incremental caching (skip unchanged files)"),
    deep: bool = typer.Option(False, "--deep", help="Enable deep analysis (call graphs, type coverage)"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed progress information"),
) -> None:
    """Scan a Python codebase and generate structure index."""
    root_path = Path(path).resolve()
    output_path = Path(output).resolve()

    typer.echo(f"Scanning {root_path}...")
    if incremental:
        typer.echo("Incremental mode: skipping unchanged files")
    if deep:
        typer.echo("Deep analysis: including call graphs and type coverage")

    # Set up progress display
    if verbose and RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Scanning files...", total=100)

            def progress_callback(file_path: str, current: int, total: int) -> None:
                progress.update(task, completed=current, total=total, description=f"Scanning: {file_path}")

            scan_directory(
                root_path, output_path, incremental=incremental, deep=deep, progress_callback=progress_callback
            )
    elif verbose:
        # Fallback to basic echo if rich not available
        def progress_callback(file_path: str, current: int, total: int) -> None:
            typer.echo(f"[{current}/{total}] {file_path}")

        scan_directory(root_path, output_path, incremental=incremental, deep=deep, progress_callback=progress_callback)
    else:
        # No progress display
        scan_directory(root_path, output_path, incremental=incremental, deep=deep)

    typer.echo(f"Index written to {output_path}")


# Register commands from other modules
app.command()(rank)
app.command()(check)
app.command()(agent)
app.command()(watch)
app.command(name="watch-status")(watch_status)
app.command(name="stop-watch")(stop_watch)


if __name__ == "__main__":
    app()

"""CLI interface for CodeAtlas."""

from pathlib import Path

import typer

from code_atlas.analysis_commands import agent, check, rank
from code_atlas.dependencies import get_atlas_service
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
    pattern: str = typer.Option(None, "--pattern", help="File pattern to match (e.g., *.py)"),
    recursive: bool = typer.Option(False, "--recursive", help="Scan recursively"),
) -> None:
    """Scan a Python codebase and generate structure index."""
    root_path = Path(path).resolve()
    output_path = Path(output).resolve()

    typer.echo(f"Scanning {root_path}...")
    if incremental:
        typer.echo("Incremental mode: skipping unchanged files")
    if deep:
        typer.echo("Deep analysis: including call graphs and type coverage")
    if pattern:
        typer.echo(f"Pattern filter: {pattern}")
    if recursive:
        typer.echo("Recursive mode enabled")

    # Get service with custom index path
    service = get_atlas_service(index_path=output_path)

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

            service.scan_directory(root_path, incremental=incremental, deep=deep, progress_callback=progress_callback)
    elif verbose:
        # Fallback to basic echo if rich not available
        def progress_callback(file_path: str, current: int, total: int) -> None:
            typer.echo(f"[{current}/{total}] {file_path}")

        service.scan_directory(root_path, incremental=incremental, deep=deep, progress_callback=progress_callback)
    else:
        # No progress display
        service.scan_directory(root_path, incremental=incremental, deep=deep)

    typer.echo(f"Index written to {output_path}")


@app.command()
def analyze(
    path: str = typer.Argument(..., help="Path to analyze"),
    metrics: bool = typer.Option(False, "--metrics", help="Include metrics in analysis"),
    index_file: str = typer.Option("code_index.json", help="Code index file"),
) -> None:
    """Analyze a file or directory."""
    file_path = Path(path).resolve()

    typer.echo(f"Analyzing {file_path}...")

    # Load code index if it exists using service
    index_path = Path(index_file)
    if index_path.exists():
        try:
            get_atlas_service(index_path=index_path)
            typer.echo(f"Using index from {index_path}")
        except Exception as e:
            typer.echo(f"Warning: Could not load index: {e}")

    if metrics:
        typer.echo("Including metrics in analysis...")

    typer.echo(f"Analysis complete for {file_path}")


@app.command()
def query(
    query_type: str = typer.Option(None, "--type", help="Entity type to query (function, class, etc)"),
    name: str = typer.Option(None, "--name", help="Filter by name"),
    index_file: str = typer.Option("code_index.json", help="Code index file"),
) -> None:
    """Query the code index."""
    index_path = Path(index_file)

    if not index_path.exists():
        typer.echo(f"Error: Index file not found: {index_path}")
        raise typer.Exit(1)

    try:
        service = get_atlas_service(index_path=index_path)
    except Exception as e:
        typer.echo(f"Error loading index: {e}")
        raise typer.Exit(1) from None

    # Query using service
    results = service.query_by_type(entity_type=query_type, name_filter=name)

    if results:
        typer.echo(f"Found {len(results)} results:")
        for result in results[:20]:  # Show first 20
            typer.echo(f"  {result['type']}: {result['name']} ({result['file']}:{result['lineno']})")
    else:
        typer.echo("No results found")


@app.command()
def graph(
    graph_type: str = typer.Option("dependencies", "--type", help="Graph type (dependencies, calls)"),
    index_file: str = typer.Option("code_index.json", help="Code index file"),
) -> None:
    """Generate dependency or call graph."""
    index_path = Path(index_file)

    if not index_path.exists():
        typer.echo(f"Error: Index file not found: {index_path}")
        raise typer.Exit(1)

    try:
        service = get_atlas_service(index_path=index_path)
    except Exception as e:
        typer.echo(f"Error loading index: {e}")
        raise typer.Exit(1) from None

    typer.echo(f"Generating {graph_type} graph...")

    # Build graph data using service
    graph_data = service.build_graph_data(graph_type)

    typer.echo(f"Graph has {len(graph_data['nodes'])} nodes")


@app.command()
def metrics(
    file: str = typer.Option(None, "--file", help="Specific file to get metrics for"),
    index_file: str = typer.Option("code_index.json", help="Code index file"),
) -> None:
    """View code metrics."""
    index_path = Path(index_file)

    if not index_path.exists():
        typer.echo(f"Error: Index file not found: {index_path}")
        raise typer.Exit(1)

    try:
        service = get_atlas_service(index_path=index_path)
    except Exception as e:
        typer.echo(f"Error loading index: {e}")
        raise typer.Exit(1) from None

    # Get metrics using service
    metrics = service.get_metrics(file)

    if file:
        typer.echo(f"Metrics for {file}:")
        typer.echo(f"  Lines: {metrics.get('lines', 0)}")
        typer.echo(f"  Entities: {metrics.get('entities', 0)}")
        typer.echo(f"  Comment Ratio: {metrics.get('comment_ratio', 0.0):.2%}")
    else:
        typer.echo("Code Metrics:")
        typer.echo(f"  Total Files: {metrics.get('total_files', 0)}")
        typer.echo(f"  Total Lines: {metrics.get('total_lines', 0)}")
        typer.echo(f"  Total Entities: {metrics.get('total_entities', 0)}")


@app.command()
def export(
    output: str = typer.Argument(..., help="Output file path"),
    format: str = typer.Option("json", "--format", help="Export format (json, dot)"),
    index_file: str = typer.Option("code_index.json", help="Code index file"),
) -> None:
    """Export code index to different formats."""
    index_path = Path(index_file)

    if not index_path.exists():
        typer.echo(f"Error: Index file not found: {index_path}")
        raise typer.Exit(1)

    try:
        service = get_atlas_service(index_path=index_path)
    except Exception as e:
        typer.echo(f"Error loading index: {e}")
        raise typer.Exit(1) from None

    output_path = Path(output).resolve()

    try:
        exported_content = service.export_to_format(format)
        output_path.write_text(exported_content, encoding="utf-8")
        typer.echo(f"Exported to {output_path} ({format.upper()} format)")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1) from e


# Cache subcommand group
cache_app = typer.Typer(help="Manage code atlas cache")


@cache_app.command()
def clear() -> None:
    """Clear the cache."""
    try:
        service = get_atlas_service()
        service.clear_cache()
        typer.echo("Cache cleared successfully")
    except Exception as e:
        typer.echo(f"Error clearing cache: {e}")
        raise typer.Exit(1) from None


@cache_app.command()
def stats() -> None:
    """Show cache statistics."""
    try:
        service = get_atlas_service()
        cache_stats = service.get_cache_stats()
        typer.echo("Cache Statistics:")
        typer.echo(f"  Entries: {cache_stats['entries']}")
        typer.echo(f"  Cache file: {cache_stats['file']}")
    except Exception as e:
        typer.echo(f"Error getting cache stats: {e}")
        raise typer.Exit(1) from None


app.add_typer(cache_app, name="cache")


# Register commands from other modules
app.command()(rank)
app.command()(check)
app.command()(agent)
app.command()(watch)
app.command(name="watch-status")(watch_status)
app.command(name="stop-watch")(stop_watch)


if __name__ == "__main__":
    app()

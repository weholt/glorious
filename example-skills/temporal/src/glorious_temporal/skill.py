"""Temporal skill - time-aware filtering."""

import typer
from rich.console import Console

app = typer.Typer(help="Temporal filtering utilities")
console = Console()


@app.command()
def parse(time_spec: str) -> None:
    """Parse time specification."""
    console.print(f"[cyan]Parsing time spec:[/cyan] {time_spec}")
    console.print("[yellow]Examples: '7d', '3h', '2025-11-14', 'last-week'[/yellow]")

    # Simple parsing examples
    import re
    from datetime import datetime, timedelta

    if match := re.match(r'(\d+)([dhm])', time_spec):
        amount, unit = match.groups()
        amount = int(amount)

        if unit == 'd':
            delta = timedelta(days=amount)
        elif unit == 'h':
            delta = timedelta(hours=amount)
        elif unit == 'm':
            delta = timedelta(minutes=amount)
        else:
            console.print("[red]Invalid unit[/red]")
            return

        target_time = datetime.utcnow() - delta
        console.print(f"[green]Resolved to:[/green] {target_time.isoformat()}")
    else:
        console.print("[yellow]Complex time specs not yet implemented[/yellow]")


@app.command()
def filter_since(since: str) -> None:
    """Show filter query for --since flag."""
    console.print(f"[cyan]Filter query for --since {since}:[/cyan]")
    console.print("  WHERE created_at >= ?")
    console.print("[dim]Use with other skills' list commands[/dim]")


@app.command()
def examples() -> None:
    """Show temporal filter examples."""
    console.print("[bold cyan]Temporal Filter Examples:[/bold cyan]\n")
    console.print("  --since 7d          Last 7 days")
    console.print("  --since 3h          Last 3 hours")
    console.print("  --since 30m         Last 30 minutes")
    console.print("  --until 2025-11-14  Before date")
    console.print("  --updated-within 3d Updated in last 3 days")
    console.print("\n[dim]These flags can be added to most skill commands[/dim]")

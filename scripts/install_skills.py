#!/usr/bin/env python3
"""Glorious Skills Installer - A magnificent TUI for installing agent skills."""

import subprocess
import sys
from pathlib import Path

try:
    from rich.align import Align
    from rich.box import DOUBLE, ROUNDED
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("Error: This script requires 'rich'. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    from rich.align import Align
    from rich.box import DOUBLE, ROUNDED
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.text import Text


console = Console()


def find_skills() -> list[tuple[str, Path, str]]:
    """Find all installable skills in the skills directory."""
    skills_dir = Path(__file__).parent.parent / "src" / "glorious_agents" / "skills"
    skills = []

    for pyproject in skills_dir.glob("*/pyproject.toml"):
        skill_dir = pyproject.parent
        skill_name = skill_dir.name

        # Read description from pyproject.toml
        description = ""
        try:
            with open(pyproject) as f:
                for line in f:
                    if line.strip().startswith("description ="):
                        description = line.split("=", 1)[1].strip().strip('"')
                        break
        except Exception:
            description = "No description available"

        skills.append((skill_name, skill_dir, description))

    return sorted(skills, key=lambda x: x[0])


def display_banner():
    """Display a glorious banner."""
    banner = Text()
    banner.append("✨ ", style="bold yellow")
    banner.append("GLORIOUS SKILLS INSTALLER", style="bold magenta")
    banner.append(" ✨", style="bold yellow")

    panel = Panel(Align.center(banner), box=DOUBLE, border_style="bright_magenta", padding=(1, 2))
    console.print()
    console.print(panel)
    console.print()


def display_skills_table(skills: list[tuple[str, Path, str]], selected: set) -> Table:
    """Create a beautiful table of available skills."""
    table = Table(
        title="📦 Available Skills",
        box=ROUNDED,
        border_style="cyan",
        header_style="bold cyan",
        show_lines=True,
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Status", width=8, justify="center")
    table.add_column("Skill Name", style="bold yellow", width=20)
    table.add_column("Description", style="white")

    for idx, (name, _, desc) in enumerate(skills, 1):
        status = "✓" if idx in selected else "○"
        status_style = "bold green" if idx in selected else "dim white"
        table.add_row(str(idx), Text(status, style=status_style), name, desc)

    return table


def get_user_selection(skills: list[tuple[str, Path, str]]) -> set:
    """Get user's skill selection through interactive prompts."""
    selected = set()

    while True:
        console.clear()
        display_banner()
        console.print(display_skills_table(skills, selected))
        console.print()

        console.print(
            Panel(
                "[cyan]Commands:[/cyan]\n"
                "• Enter [yellow]number(s)[/yellow] to toggle selection (e.g., '1 3 5' or '1-5')\n"
                "• Enter [green]'all'[/green] to select all skills\n"
                "• Enter [red]'none'[/red] to deselect all\n"
                "• Enter [magenta]'done'[/magenta] when ready to install",
                border_style="blue",
                box=ROUNDED,
            )
        )
        console.print()

        choice = Prompt.ask("[bold cyan]Your choice[/bold cyan]", default="done").strip().lower()

        if choice == "done":
            if selected:
                return selected
            console.print(
                "[yellow]⚠️  No skills selected. Please select at least one skill.[/yellow]"
            )
            console.input("\nPress Enter to continue...")
            continue

        if choice == "all":
            selected = set(range(1, len(skills) + 1))
            continue

        if choice == "none":
            selected.clear()
            continue

        # Parse number selection
        try:
            for part in choice.split():
                if "-" in part:
                    start, end = part.split("-", 1)
                    selected.update(range(int(start), int(end) + 1))
                else:
                    num = int(part)
                    if num in selected:
                        selected.remove(num)
                    else:
                        selected.add(num)
        except ValueError:
            console.print("[red]❌ Invalid input. Please enter numbers, ranges, or commands.[/red]")
            console.input("\nPress Enter to continue...")


def install_skills(skills: list[tuple[str, Path, str]], selected: set):
    """Install the selected skills with glorious progress display."""
    selected_skills = [skills[i - 1] for i in sorted(selected)]

    console.clear()
    display_banner()

    console.print(
        Panel(
            f"[bold green]Installing {len(selected_skills)} skill(s)...[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )
    console.print()

    results = []

    with Progress(
        SpinnerColumn(style="magenta"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, style="cyan", complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progress:
        overall = progress.add_task("[bold magenta]Overall Progress", total=len(selected_skills))

        for idx, (name, path, _) in enumerate(selected_skills, 1):
            task = progress.add_task(f"[yellow]{name}[/yellow]", total=100)

            try:
                # Install using uv pip install
                result = subprocess.run(
                    ["uv", "pip", "install", "-e", str(path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                progress.update(task, completed=100)

                if result.returncode == 0:
                    results.append((name, True, None))
                    progress.console.print(f"  [green]✓[/green] {name} installed successfully")
                else:
                    results.append((name, False, result.stderr))
                    progress.console.print(f"  [red]✗[/red] {name} failed to install")

            except Exception as e:
                progress.update(task, completed=100)
                results.append((name, False, str(e)))
                progress.console.print(f"  [red]✗[/red] {name} error: {e}")

            progress.update(overall, advance=1)
            progress.remove_task(task)

    # Display final results
    console.print()
    display_results(results)


def display_results(results: list[tuple[str, bool, str]]):
    """Display installation results in a glorious summary."""
    success_count = sum(1 for _, success, _ in results if success)
    fail_count = len(results) - success_count

    table = Table(
        title="📊 Installation Summary",
        box=DOUBLE,
        border_style="bright_magenta",
        header_style="bold magenta",
    )

    table.add_column("Skill", style="yellow", width=20)
    table.add_column("Status", width=12, justify="center")
    table.add_column("Details", style="dim")

    for name, success, error in results:
        if success:
            table.add_row(name, "[green]✓ SUCCESS[/green]", "")
        else:
            error_msg = error.split("\n")[-2] if error else "Unknown error"
            table.add_row(name, "[red]✗ FAILED[/red]", error_msg[:50])

    console.print(table)
    console.print()

    if success_count == len(results):
        console.print(
            Panel(
                f"[bold green]🎉 All {success_count} skill(s) installed successfully! 🎉[/bold green]",
                border_style="green",
                box=DOUBLE,
            )
        )
    elif success_count > 0:
        console.print(
            Panel(
                f"[yellow]⚠️  {success_count} succeeded, {fail_count} failed[/yellow]",
                border_style="yellow",
                box=ROUNDED,
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]❌ All installations failed[/bold red]", border_style="red", box=ROUNDED
            )
        )


def main():
    """Main entry point for the glorious installer."""
    try:
        console.clear()
        display_banner()

        # Find all available skills
        with console.status("[bold cyan]Discovering skills...", spinner="dots"):
            skills = find_skills()

        if not skills:
            console.print("[red]❌ No skills found in src/glorious_agents/skills/[/red]")
            return 1

        console.print(f"[green]✓[/green] Found {len(skills)} skill(s)\n")
        console.input("Press Enter to continue...")

        # Get user selection
        selected = get_user_selection(skills)

        # Confirm installation
        console.clear()
        display_banner()
        console.print(display_skills_table(skills, selected))
        console.print()

        if (
            not Prompt.ask(
                "[bold yellow]Proceed with installation?[/bold yellow]",
                choices=["y", "n"],
                default="y",
            )
            == "y"
        ):
            console.print("[yellow]Installation cancelled.[/yellow]")
            return 0

        # Install selected skills
        install_skills(skills, selected)

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled by user.[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())

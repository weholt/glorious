"""Rich output formatters for enhanced CLI display."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from issue_tracker.domain import Issue, IssuePriority, IssueStatus

console = Console()


def format_issue_table(issues: list[Issue], title: str = "Issues") -> Table:
    """Format issues as a rich table.

    Args:
        issues: List of issues to display
        title: Table title

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Priority", justify="center")
    table.add_column("Type", justify="center")
    table.add_column("Assignee", style="yellow")

    for issue in issues:
        status_color = get_status_color(issue.status)
        priority_emoji = get_priority_emoji(issue.priority)

        table.add_row(
            issue.id,
            issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
            f"[{status_color}]{issue.status.value}[/{status_color}]",
            priority_emoji,
            issue.type.value,
            issue.assignee or "-",
        )

    return table


def format_issue_panel(issue: Issue) -> Panel:
    """Format issue as a rich panel with details.

    Args:
        issue: Issue to display

    Returns:
        Rich Panel object
    """
    status_color = get_status_color(issue.status)
    priority_emoji = get_priority_emoji(issue.priority)

    content = Text()
    content.append("ID: ", style="bold")
    content.append(f"{issue.id}\n", style="cyan")

    content.append("Title: ", style="bold")
    content.append(f"{issue.title}\n\n", style="white")

    if issue.description:
        content.append("Description:\n", style="bold")
        content.append(f"{issue.description}\n\n", style="dim")

    content.append("Status: ", style="bold")
    content.append(f"{issue.status.value}", style=status_color)
    content.append("  Priority: ", style="bold")
    content.append(f"{priority_emoji}\n", style="white")

    content.append("Type: ", style="bold")
    content.append(f"{issue.type.value}", style="blue")

    if issue.assignee:
        content.append("  Assignee: ", style="bold")
        content.append(f"{issue.assignee}", style="yellow")

    if issue.labels:
        content.append("\n\nLabels: ", style="bold")
        content.append(f"{', '.join(issue.labels)}", style="green")

    if issue.epic_id:
        content.append("\nEpic: ", style="bold")
        content.append(f"{issue.epic_id}", style="magenta")

    return Panel(
        content,
        title=f"[bold]{issue.id}[/bold]",
        border_style=status_color,
    )


def print_issue_table(issues: list[Issue], title: str = "Issues") -> None:
    """Print issues as a rich table to console.

    Args:
        issues: List of issues to display
        title: Table title
    """
    table = format_issue_table(issues, title)
    console.print(table)


def print_issue_panel(issue: Issue) -> None:
    """Print issue as a rich panel to console.

    Args:
        issue: Issue to display
    """
    panel = format_issue_panel(issue)
    console.print(panel)


def print_success(message: str) -> None:
    """Print success message with formatting.

    Args:
        message: Success message to display
    """
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print error message with formatting.

    Args:
        message: Error message to display
    """
    console.print(f"[bold red]✗[/bold red] {message}", style="red")


def print_warning(message: str) -> None:
    """Print warning message with formatting.

    Args:
        message: Warning message to display
    """
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print info message with formatting.

    Args:
        message: Info message to display
    """
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def get_status_color(status: IssueStatus) -> str:
    """Get color for issue status.

    Args:
        status: Issue status

    Returns:
        Rich color string
    """
    color_map = {
        IssueStatus.OPEN: "green",
        IssueStatus.IN_PROGRESS: "yellow",
        IssueStatus.BLOCKED: "red",
        IssueStatus.RESOLVED: "blue",
        IssueStatus.CLOSED: "dim",
        IssueStatus.ARCHIVED: "dim",
    }
    return color_map.get(status, "white")


def get_priority_emoji(priority: IssuePriority | int) -> str:
    """Get emoji for issue priority.

    Args:
        priority: Issue priority

    Returns:
        Emoji string
    """
    priority_val = int(priority) if isinstance(priority, IssuePriority) else priority
    emoji_map = {
        0: "🔴",  # Critical
        1: "🟠",  # High
        2: "🟡",  # Medium
        3: "🟢",  # Low
        4: "⚪",  # Backlog
    }
    return emoji_map.get(priority_val, "⚪")

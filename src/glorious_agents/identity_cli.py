"""Agent identity and registry management."""

import sqlite3

import typer
from rich.console import Console
from rich.table import Table

from glorious_agents.core.db import get_agent_folder, get_master_db_path, init_master_db

app = typer.Typer(help="Agent identity management")
console = Console()


def get_active_agent_code() -> str | None:
    """Get the currently active agent code from the filesystem.

    Reads the active agent code from the 'active_agent' file in the agent
    data directory. This code identifies which agent's database and configuration
    should be used for operations.

    Returns:
        The agent code as a string if an active agent is set, None otherwise.
        The code is stripped of whitespace.

    Example:
        >>> get_active_agent_code()
        'my-agent'
    """
    active_file = get_agent_folder() / "active_agent"
    if active_file.exists():
        return active_file.read_text().strip()
    return None


def set_active_agent(code: str) -> None:
    """Set the active agent code in the filesystem.

    Writes the provided agent code to the 'active_agent' file, making it the
    currently active agent. All subsequent operations will use this agent's
    database and configuration until changed.

    Args:
        code: The agent code to set as active. Should match a registered agent
            in the master database.

    Example:
        >>> set_active_agent('my-agent')
        # 'my-agent' is now the active agent
    """
    active_file = get_agent_folder() / "active_agent"
    active_file.parent.mkdir(parents=True, exist_ok=True)
    active_file.write_text(code)


@app.command()
def register(
    name: str = typer.Option(..., help="Agent name"),
    role: str = typer.Option("", help="Agent role/purpose"),
    project_id: str = typer.Option("", help="Project ID"),
) -> None:
    """Register a new agent in the master registry.

    Creates a new agent identity with the specified name, role, and project.
    The agent code is automatically generated from the name by converting to
    lowercase and replacing spaces with hyphens. If an agent with the same
    code already exists, it will be replaced.

    Args:
        name: The display name for the agent. Required.
        role: Optional description of the agent's role or purpose.
        project_id: Optional project identifier to associate with the agent.

    Example:
        $ agent identity register --name "Code Reviewer" --role "Review PRs" --project-id "myapp"
        Agent 'Code Reviewer' registered with code: code-reviewer
    """
    init_master_db()

    # Generate code from name
    code = name.lower().replace(" ", "-")

    db_path = get_master_db_path()
    conn = sqlite3.connect(str(db_path))

    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO agents (code, name, role, project_id)
            VALUES (?, ?, ?, ?)
        """,
            (code, name, role, project_id),
        )
        conn.commit()

        console.print(f"[green]Agent '{name}' registered with code: {code}[/green]")
    finally:
        conn.close()


@app.command()
def use(code: str) -> None:
    """Switch to a different agent context.

    Changes the active agent to the one specified by the given code. All
    subsequent operations will use this agent's database, notes, and
    configuration. The agent must already be registered.

    Args:
        code: The agent code to switch to. Must match an existing registered
            agent in the master database.

    Example:
        $ agent identity use code-reviewer
        Switched to agent: Code Reviewer (code-reviewer)
    """
    init_master_db()

    # Verify agent exists
    db_path = get_master_db_path()
    conn = sqlite3.connect(str(db_path))

    try:
        cur = conn.execute("SELECT name FROM agents WHERE code = ?", (code,))
        row = cur.fetchone()

        if not row:
            console.print(f"[red]Agent '{code}' not found. Register it first.[/red]")
            return

        set_active_agent(code)
        console.print(f"[green]Switched to agent: {row[0]} ({code})[/green]")
    finally:
        conn.close()


@app.command()
def whoami() -> None:
    """Display information about the currently active agent.

    Shows the name, code, role, project, and registration date of the currently
    active agent. If no agent is active, prompts the user to register one.

    Example:
        $ agent identity whoami

        Active Agent: Code Reviewer
        Code: code-reviewer
        Role: Review PRs
        Project: myapp
        Registered: 2025-11-14 10:30:00
    """
    code = get_active_agent_code()

    if not code:
        console.print("[yellow]No active agent set. Use 'agent identity register' first.[/yellow]")
        return

    init_master_db()
    db_path = get_master_db_path()
    conn = sqlite3.connect(str(db_path))

    try:
        cur = conn.execute(
            """
            SELECT name, role, project_id, created_at
            FROM agents WHERE code = ?
        """,
            (code,),
        )
        row = cur.fetchone()

        if not row:
            console.print(f"[yellow]Active agent '{code}' not in registry.[/yellow]")
            return

        console.print(f"\n[bold cyan]Active Agent: {row[0]}[/bold cyan]")
        console.print(f"Code: {code}")
        if row[1]:
            console.print(f"Role: {row[1]}")
        if row[2]:
            console.print(f"Project: {row[2]}")
        console.print(f"[dim]Registered: {row[3]}[/dim]")
    finally:
        conn.close()


@app.command("list")
def list_agents() -> None:
    """List all registered agents in the master registry.

    Displays a formatted table showing all agents that have been registered,
    including their code, name, role, project, and whether they are currently
    active. Agents are listed in reverse chronological order (most recently
    registered first).

    Example:
        $ agent identity list
        ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
        ┃ Code          ┃ Name         ┃ Role      ┃ Project ┃ Active ┃
        ┣━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━╋━━━━━━━━┫
        ┃ code-reviewer ┃ Code Reviewer┃ Review PRs┃ myapp   ┃ ✓      ┃
        ┗━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━┻━━━━━━━━┛
    """
    init_master_db()

    db_path = get_master_db_path()
    conn = sqlite3.connect(str(db_path))

    try:
        cur = conn.execute("""
            SELECT code, name, role, project_id
            FROM agents
            ORDER BY created_at DESC
        """)

        active_code = get_active_agent_code()

        table = Table(title="Registered Agents")
        table.add_column("Code", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Role", style="yellow")
        table.add_column("Project", style="magenta")
        table.add_column("Active", style="green")

        for row in cur:
            is_active = "✓" if row[0] == active_code else ""
            table.add_row(row[0], row[1], row[2] or "-", row[3] or "-", is_active)

        console.print(table)
    finally:
        conn.close()

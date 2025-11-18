"""Automations skill - declarative event-driven automation engine.

Refactored to use modern architecture with Repository/Service patterns
while remaining discoverable as a separate installable skill.
"""

from __future__ import annotations

import json
from typing import Any

import typer
import yaml
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.search import SearchResult
from glorious_agents.core.validation import SkillInput, validate_input

from .dependencies import get_automation_service

app = typer.Typer(help="Event-driven automations")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context and register automations."""
    global _ctx
    _ctx = ctx
    # Registration happens on-demand when commands are executed
    # to avoid issues with RestrictedSkillContext during initialization


def _register_active_automations() -> None:
    """Register all active automations with the event bus."""
    if _ctx is None:
        return

    # Only register if we have a full context with event_bus
    event_bus = getattr(_ctx, "event_bus", None)
    if event_bus is None:
        return

    service = get_automation_service(event_bus=event_bus)
    with service.uow:
        service.register_all_automations()


class CreateAutomationInput(SkillInput):
    """Input validation for creating automations."""

    name: str = Field(..., min_length=1, max_length=200, description="Automation name")
    trigger_topic: str = Field(
        ..., min_length=1, max_length=200, description="Event topic to trigger on"
    )
    actions: str = Field(..., min_length=1, description="JSON array of actions")


@validate_input
def create(
    name: str, trigger_topic: str, actions: str, description: str = "", trigger_condition: str = ""
) -> str:
    """Create a new automation.

    Args:
        name: Automation name.
        trigger_topic: Event topic to listen to.
        actions: JSON array of actions to execute.
        description: Optional description.
        trigger_condition: Optional Python expression to filter events.

    Returns:
        Automation ID.
    """
    event_bus = getattr(_ctx, "event_bus", None) if _ctx else None
    service = get_automation_service(event_bus=event_bus)

    with service.uow:
        automation = service.create_automation(
            name, trigger_topic, actions, description, trigger_condition
        )
        return automation.id


def disable(automation_id: str) -> None:
    """Disable an automation.

    Args:
        automation_id: The automation ID.
    """
    service = get_automation_service()

    with service.uow:
        service.disable_automation(automation_id)


def enable(automation_id: str) -> None:
    """Enable an automation.

    Args:
        automation_id: The automation ID.
    """
    event_bus = getattr(_ctx, "event_bus", None) if _ctx else None
    service = get_automation_service(event_bus=event_bus)

    with service.uow:
        service.enable_automation(automation_id)


def delete(automation_id: str) -> None:
    """Delete an automation.

    Args:
        automation_id: The automation ID.
    """
    service = get_automation_service()

    with service.uow:
        service.delete_automation(automation_id)


@app.command(name="create")
def create_cmd(
    name: str = typer.Argument(..., help="Automation name"),
    trigger_topic: str = typer.Argument(..., help="Event topic"),
    actions: str = typer.Argument(..., help="JSON actions array"),
    description: str = typer.Option("", "--description", "-d", help="Description"),
    condition: str = typer.Option(
        "", "--condition", "-c", help="Trigger condition (Python expression)"
    ),
) -> None:
    """Create a new automation."""
    try:
        auto_id = create(name, trigger_topic, actions, description, condition)
        console.print(f"[green]Automation '{name}' created:[/green] {auto_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="create-from-file")
def create_from_file(
    file: str = typer.Argument(..., help="YAML or JSON file with automation definition"),
) -> None:
    """Create automation from file."""
    try:
        with open(file) as f:
            if file.endswith(".yaml") or file.endswith(".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        auto_id = create(
            data["name"],
            data["trigger_topic"],
            json.dumps(data["actions"]),
            data.get("description", ""),
            data.get("trigger_condition", ""),
        )
        console.print(f"[green]Automation '{data['name']}' created:[/green] {auto_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="list")
def list_cmd(
    enabled_only: bool = typer.Option(
        False, "--enabled", "-e", help="Show only enabled automations"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all automations."""
    service = get_automation_service()

    with service.uow:
        automations = service.list_automations(enabled_only)

        if json_output:
            results = [
                {
                    "id": a.id,
                    "name": a.name,
                    "trigger_topic": a.trigger_topic,
                    "enabled": a.enabled,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in automations
            ]
            console.print(json.dumps(results))
        else:
            if not automations:
                console.print("[yellow]No automations found.[/yellow]")
                return

            table = Table(title="Automations")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Trigger", style="blue")
            table.add_column("Status", style="green")

            for automation in automations:
                status = "✓ Enabled" if automation.enabled else "✗ Disabled"
                table.add_row(automation.id, automation.name, automation.trigger_topic, status)

            console.print(table)


@app.command()
def show(
    automation_id: str = typer.Argument(..., help="Automation ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show automation details."""
    service = get_automation_service()

    with service.uow:
        automation = service.get_automation(automation_id)

        if not automation:
            console.print(f"[red]Automation not found:[/red] {automation_id}")
            raise typer.Exit(1)

        if json_output:
            result = {
                "id": automation.id,
                "name": automation.name,
                "description": automation.description,
                "trigger_topic": automation.trigger_topic,
                "trigger_condition": automation.trigger_condition,
                "actions": json.loads(automation.actions),
                "enabled": automation.enabled,
                "created_at": automation.created_at.isoformat() if automation.created_at else None,
            }
            console.print(json.dumps(result))
        else:
            console.print(f"[bold]ID:[/bold] {automation.id}")
            console.print(f"[bold]Name:[/bold] {automation.name}")
            console.print(f"[bold]Description:[/bold] {automation.description or '(none)'}")
            console.print(f"[bold]Trigger:[/bold] {automation.trigger_topic}")
            console.print(f"[bold]Condition:[/bold] {automation.trigger_condition or '(none)'}")
            console.print(f"[bold]Enabled:[/bold] {'Yes' if automation.enabled else 'No'}")
            console.print("\n[bold]Actions:[/bold]")
            actions = json.loads(automation.actions)
            for i, action in enumerate(actions, 1):
                console.print(f"  {i}. {json.dumps(action, indent=2)}")


@app.command(name="disable")
def disable_cmd(automation_id: str = typer.Argument(..., help="Automation ID")) -> None:
    """Disable an automation."""
    try:
        disable(automation_id)
        console.print(f"[yellow]Automation disabled:[/yellow] {automation_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="enable")
def enable_cmd(automation_id: str = typer.Argument(..., help="Automation ID")) -> None:
    """Enable an automation."""
    try:
        enable(automation_id)
        console.print(f"[green]Automation enabled:[/green] {automation_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="delete")
def delete_cmd(automation_id: str = typer.Argument(..., help="Automation ID")) -> None:
    """Delete an automation."""
    try:
        delete(automation_id)
        console.print(f"[red]Automation deleted:[/red] {automation_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def executions(
    automation_id: str = typer.Option(None, "--automation", "-a", help="Filter by automation ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show automation execution history."""
    service = get_automation_service()

    with service.uow:
        execs = service.get_executions(automation_id, limit)

        if json_output:
            results = [
                {
                    "id": e.id,
                    "automation_id": e.automation_id,
                    "status": e.status,
                    "executed_at": e.executed_at.isoformat() if e.executed_at else None,
                }
                for e in execs
            ]
            console.print(json.dumps(results))
        else:
            if not execs:
                console.print("[yellow]No executions found.[/yellow]")
                return

            table = Table(title="Execution History")
            table.add_column("ID", style="cyan")
            table.add_column("Automation", style="white")
            table.add_column("Status", style="green")
            table.add_column("Time", style="blue")

            for execution in execs:
                status_color = "green" if execution.status == "success" else "red"
                table.add_row(
                    str(execution.id),
                    execution.automation_id,
                    f"[{status_color}]{execution.status}[/{status_color}]",
                    execution.executed_at.isoformat() if execution.executed_at else "",
                )

            console.print(table)


def search(query: str, limit: int = 10) -> list[SearchResult]:
    """Universal search API for automations.

    Searches automation names, descriptions, and trigger topics.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    service = get_automation_service()

    with service.uow:
        return service.search_automations(query, limit)

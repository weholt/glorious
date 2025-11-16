"""Automations skill - declarative event-driven automation engine."""

import json
import uuid
from datetime import datetime
from typing import Any

import typer
import yaml
from pydantic import Field
from rich.console import Console
from rich.table import Table

from glorious_agents.core.context import SkillContext
from glorious_agents.core.validation import SkillInput, validate_input

app = typer.Typer(help="Event-driven automations")
console = Console()
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context and register automations."""
    global _ctx
    _ctx = ctx
    _register_active_automations()


def _register_active_automations() -> None:
    """Register all active automations with the event bus."""
    assert _ctx is not None
    rows = _ctx.conn.execute(
        "SELECT id, name, trigger_topic, trigger_condition, actions FROM automations WHERE enabled = 1"
    ).fetchall()

    for auto_id, name, topic, condition, actions_json in rows:

        def handler(data: dict[str, Any], aid: str = auto_id, cond: str = condition, acts: str = actions_json) -> None:
            _execute_automation(aid, data, cond, acts)

        _ctx.subscribe(topic, handler)


def _execute_automation(
    automation_id: str, trigger_data: dict[str, Any], condition: str | None, actions_json: str
) -> None:
    """Execute an automation."""
    assert _ctx is not None

    if condition:
        try:
            if not eval(condition, {"data": trigger_data}):
                return
        except Exception as e:
            _ctx.conn.execute(
                "INSERT INTO automation_executions (automation_id, trigger_data, status, error) VALUES (?, ?, ?, ?)",
                (automation_id, json.dumps(trigger_data), "failed", f"Condition eval error: {e}"),
            )
            _ctx.conn.commit()
            return

    try:
        actions = json.loads(actions_json)
        results = []
        for action in actions:
            action_type = action.get("type")
            if action_type == "log":
                console.print(f"[blue]Automation log:[/blue] {action.get('message', '')}")
                results.append({"type": "log", "success": True})
            elif action_type == "publish":
                topic = action.get("topic")
                data = action.get("data", {})
                _ctx.publish(topic, data)
                results.append({"type": "publish", "topic": topic, "success": True})
            else:
                results.append({"type": action_type, "success": False, "error": "Unknown action type"})

        _ctx.conn.execute(
            "INSERT INTO automation_executions (automation_id, trigger_data, status, result) VALUES (?, ?, ?, ?)",
            (automation_id, json.dumps(trigger_data), "success", json.dumps(results)),
        )
        _ctx.conn.commit()
    except Exception as e:
        _ctx.conn.execute(
            "INSERT INTO automation_executions (automation_id, trigger_data, status, error) VALUES (?, ?, ?, ?)",
            (automation_id, json.dumps(trigger_data), "failed", str(e)),
        )
        _ctx.conn.commit()


class CreateAutomationInput(SkillInput):
    """Input validation for creating automations."""

    name: str = Field(..., min_length=1, max_length=200, description="Automation name")
    trigger_topic: str = Field(..., min_length=1, max_length=200, description="Event topic to trigger on")
    actions: str = Field(..., min_length=1, description="JSON array of actions")


@validate_input
def create(
    name: str, trigger_topic: str, actions: str, description: str = "", trigger_condition: str = ""
) -> str:
    """
    Create a new automation.

    Args:
        name: Automation name.
        trigger_topic: Event topic to listen to.
        actions: JSON array of actions to execute.
        description: Optional description.
        trigger_condition: Optional Python expression to filter events.

    Returns:
        Automation ID.
    """
    assert _ctx is not None

    try:
        json.loads(actions)
    except json.JSONDecodeError:
        raise ValueError("actions must be valid JSON array")

    auto_id = f"auto-{uuid.uuid4().hex[:8]}"
    _ctx.conn.execute(
        "INSERT INTO automations (id, name, description, trigger_topic, trigger_condition, actions) VALUES (?, ?, ?, ?, ?, ?)",
        (auto_id, name, description, trigger_topic, trigger_condition or None, actions),
    )
    _ctx.conn.commit()

    def handler(data: dict[str, Any]) -> None:
        _execute_automation(auto_id, data, trigger_condition or None, actions)

    _ctx.subscribe(trigger_topic, handler)

    return auto_id


def disable(automation_id: str) -> None:
    """
    Disable an automation.

    Args:
        automation_id: The automation ID.
    """
    assert _ctx is not None
    _ctx.conn.execute("UPDATE automations SET enabled = 0, updated_at = ? WHERE id = ?", (datetime.now(), automation_id))
    _ctx.conn.commit()


def enable(automation_id: str) -> None:
    """
    Enable an automation.

    Args:
        automation_id: The automation ID.
    """
    assert _ctx is not None
    _ctx.conn.execute("UPDATE automations SET enabled = 1, updated_at = ? WHERE id = ?", (datetime.now(), automation_id))
    _ctx.conn.commit()

    row = _ctx.conn.execute(
        "SELECT trigger_topic, trigger_condition, actions FROM automations WHERE id = ?", (automation_id,)
    ).fetchone()
    if row:
        topic, condition, actions = row

        def handler(data: dict[str, Any]) -> None:
            _execute_automation(automation_id, data, condition, actions)

        _ctx.subscribe(topic, handler)


def delete(automation_id: str) -> None:
    """
    Delete an automation.

    Args:
        automation_id: The automation ID.
    """
    assert _ctx is not None
    _ctx.conn.execute("DELETE FROM automations WHERE id = ?", (automation_id,))
    _ctx.conn.commit()


@app.command()
def create_cmd(
    name: str = typer.Argument(..., help="Automation name"),
    trigger_topic: str = typer.Argument(..., help="Event topic"),
    actions: str = typer.Argument(..., help="JSON actions array"),
    description: str = typer.Option("", "--description", "-d", help="Description"),
    condition: str = typer.Option("", "--condition", "-c", help="Trigger condition (Python expression)"),
) -> None:
    """Create a new automation."""
    try:
        auto_id = create(name, trigger_topic, actions, description, condition)
        console.print(f"[green]Automation '{name}' created:[/green] {auto_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
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


@app.command()
def list_cmd(
    enabled_only: bool = typer.Option(False, "--enabled", "-e", help="Show only enabled automations"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all automations."""
    assert _ctx is not None

    query = "SELECT id, name, trigger_topic, enabled, created_at FROM automations"
    if enabled_only:
        query += " WHERE enabled = 1"
    query += " ORDER BY created_at DESC"

    rows = _ctx.conn.execute(query).fetchall()

    if json_output:
        results = [{"id": r[0], "name": r[1], "trigger_topic": r[2], "enabled": bool(r[3]), "created_at": r[4]} for r in rows]
        console.print(json.dumps(results))
    else:
        if not rows:
            console.print("[yellow]No automations found.[/yellow]")
            return

        table = Table(title="Automations")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Trigger", style="blue")
        table.add_column("Status", style="green")

        for row in rows:
            status = "✓ Enabled" if row[3] else "✗ Disabled"
            table.add_row(row[0], row[1], row[2], status)

        console.print(table)


@app.command()
def show(
    automation_id: str = typer.Argument(..., help="Automation ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show automation details."""
    assert _ctx is not None

    row = _ctx.conn.execute(
        "SELECT id, name, description, trigger_topic, trigger_condition, actions, enabled, created_at FROM automations WHERE id = ?",
        (automation_id,),
    ).fetchone()

    if not row:
        console.print(f"[red]Automation not found:[/red] {automation_id}")
        raise typer.Exit(1)

    if json_output:
        result = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "trigger_topic": row[3],
            "trigger_condition": row[4],
            "actions": json.loads(row[5]),
            "enabled": bool(row[6]),
            "created_at": row[7],
        }
        console.print(json.dumps(result))
    else:
        console.print(f"[bold]ID:[/bold] {row[0]}")
        console.print(f"[bold]Name:[/bold] {row[1]}")
        console.print(f"[bold]Description:[/bold] {row[2] or '(none)'}")
        console.print(f"[bold]Trigger:[/bold] {row[3]}")
        console.print(f"[bold]Condition:[/bold] {row[4] or '(none)'}")
        console.print(f"[bold]Enabled:[/bold] {'Yes' if row[6] else 'No'}")
        console.print(f"\n[bold]Actions:[/bold]")
        actions = json.loads(row[5])
        for i, action in enumerate(actions, 1):
            console.print(f"  {i}. {json.dumps(action, indent=2)}")


@app.command()
def disable_cmd(automation_id: str = typer.Argument(..., help="Automation ID")) -> None:
    """Disable an automation."""
    try:
        disable(automation_id)
        console.print(f"[yellow]Automation disabled:[/yellow] {automation_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def enable_cmd(automation_id: str = typer.Argument(..., help="Automation ID")) -> None:
    """Enable an automation."""
    try:
        enable(automation_id)
        console.print(f"[green]Automation enabled:[/green] {automation_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
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
    assert _ctx is not None

    query = "SELECT id, automation_id, status, executed_at FROM automation_executions"
    params: tuple[Any, ...] = ()
    if automation_id:
        query += " WHERE automation_id = ?"
        params = (automation_id,)
    query += " ORDER BY executed_at DESC LIMIT ?"
    params = params + (limit,)

    rows = _ctx.conn.execute(query, params).fetchall()

    if json_output:
        results = [{"id": r[0], "automation_id": r[1], "status": r[2], "executed_at": r[3]} for r in rows]
        console.print(json.dumps(results))
    else:
        if not rows:
            console.print("[yellow]No executions found.[/yellow]")
            return

        table = Table(title="Execution History")
        table.add_column("ID", style="cyan")
        table.add_column("Automation", style="white")
        table.add_column("Status", style="green")
        table.add_column("Time", style="blue")

        for row in rows:
            status_color = "green" if row[2] == "success" else "red"
            table.add_row(str(row[0]), row[1], f"[{status_color}]{row[2]}[/{status_color}]", row[3])

        console.print(table)


def search(query: str, limit: int = 10) -> list["SearchResult"]:
    """Universal search API for automations.
    
    Searches automation names, descriptions, and trigger topics.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of SearchResult objects
    """
    from glorious_agents.core.search import SearchResult
    
    if _ctx is None:
        return []
    
    rows = _ctx.conn.execute(
        "SELECT id, name, description, trigger_topic, enabled, created_at FROM automations"
    ).fetchall()
    
    results = []
    query_lower = query.lower()
    
    for auto_id, name, description, trigger_topic, enabled, created_at in rows:
        score = 0.0
        matched = False
        
        if query_lower in name.lower():
            score += 0.8
            matched = True
        
        if description and query_lower in description.lower():
            score += 0.5
            matched = True
        
        if query_lower in trigger_topic.lower():
            score += 0.3
            matched = True
        
        if matched:
            score = min(1.0, score)
            
            results.append(SearchResult(
                skill="automations",
                id=auto_id,
                type="automation",
                content=f"{name}\n{description or ''}",
                metadata={
                    "trigger_topic": trigger_topic,
                    "enabled": bool(enabled),
                    "created_at": created_at,
                },
                score=score
            ))
    
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]

"""Skills management CLI - modular implementation."""

import typer

from glorious_agents.skills_cli.config import manage_skill_config
from glorious_agents.skills_cli.export import export_skills
from glorious_agents.skills_cli.list_describe import (
    check_skill,
    describe_skill,
    list_skills,
)
from glorious_agents.skills_cli.list_describe import (
    doctor as doctor,
)
from glorious_agents.skills_cli.migrate import app as migrate_app
from glorious_agents.skills_cli.reload import reload_skills

app = typer.Typer(help="Manage skills")
app.add_typer(migrate_app, name="migrate")


@app.command()
def list() -> None:
    """List all currently loaded skills."""
    list_skills()


@app.command()
def reload(
    skill_name: str | None = typer.Argument(
        None, help="Specific skill to reload (or all if not specified)"
    ),
) -> None:
    """Reload skills from disk and entry points."""
    reload_skills(skill_name)


@app.command()
def describe(skill_name: str) -> None:
    """Describe a specific skill and display its detailed information."""
    describe_skill(skill_name)


@app.command()
def export(
    format: str = typer.Option("json", help="Export format (json or md)"),
    skill_name: str | None = typer.Option(None, "--skill", help="Export specific skill only"),
) -> None:
    """Export loaded skills metadata in various formats."""
    export_skills(format, skill_name)


@app.command()
def check(skill_name: str) -> None:
    """Run health checks on a specific skill."""
    check_skill(skill_name)


@app.command(name="config")
def config(
    skill_name: str = typer.Argument(..., help="Name of the skill"),
    key: str | None = typer.Option(None, help="Configuration key to show"),
    set_value: str | None = typer.Option(None, "--set", help="Set configuration value"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults"),
) -> None:
    """Manage skill configuration."""
    manage_skill_config(skill_name, key, set_value, reset)


# Create command will be added when create.py module is completed

"""Skills export command."""

import json
import logging
from typing import Any, cast

from rich.console import Console

from glorious_agents.core.db import get_connection
from glorious_agents.core.registry import get_registry

console = Console()


def export_skills(format: str = "json", skill_name: str | None = None) -> None:
    """Export loaded skills metadata in various formats."""
    registry = get_registry()
    skills = registry.list_all()

    # Filter to specific skill if requested
    if skill_name:
        skills = [s for s in skills if s.name == skill_name]
        if not skills:
            console.print(f"[red]Skill '{skill_name}' not found.[/red]")
            return

    if format == "json":
        data = []
        for s in skills:
            skill_data = {
                "name": s.name,
                "version": s.version,
                "description": s.description,
                "origin": s.origin,
                "requires": s.requires,
                "requires_db": s.requires_db,
            }

            # Add commands
            app = registry.get_app(s.name)
            if app and hasattr(app, "registered_commands"):
                commands_list = [
                    {
                        "name": cmd.name or cmd.callback.__name__,
                        "help": (cmd.help or cmd.callback.__doc__ or "").split("\n")[0].strip(),
                    }
                    for cmd in app.registered_commands
                ]
                skill_data["commands"] = commands_list  # type: ignore[assignment]

            # Add database tables
            if s.requires_db:
                try:
                    conn = get_connection()
                    skill_table_prefix = s.name.replace("-", "_")
                    cur = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                        (f"{skill_table_prefix}%",),
                    )
                    skill_data["tables"] = [row[0] for row in cur.fetchall()]
                except Exception:
                    skill_data["tables"] = []

            # Add configuration schema
            if s.config_schema:
                skill_data["config_schema"] = cast(Any, s.config_schema)

            # Add documentation paths
            if s.path:
                skill_data["path"] = str(s.path)
                if s.internal_doc:
                    skill_data["internal_doc"] = s.internal_doc
                if s.external_doc:
                    skill_data["external_doc"] = s.external_doc

            data.append(skill_data)

        console.print(json.dumps(data, indent=2))

    elif format == "md":
        console.print("# Loaded Skills\n")
        for skill in skills:
            console.print(f"## {skill.name} (v{skill.version})")
            console.print(f"\n{skill.description}\n")
            console.print(f"**Origin:** {skill.origin}")

            if skill.requires:
                console.print(f"**Requires:** {', '.join(skill.requires)}")

            console.print(f"**Database:** {'Yes' if skill.requires_db else 'No'}")

            # Commands
            app = registry.get_app(skill.name)
            if app and hasattr(app, "registered_commands"):
                console.print("\n**Commands:**\n")
                for cmd in app.registered_commands:
                    cmd_name = cmd.name or cmd.callback.__name__
                    cmd_help = (
                        (cmd.help or cmd.callback.__doc__ or "No description")
                        .split("\n")[0]
                        .strip()
                    )
                    console.print(f"- `{cmd_name}`: {cmd_help}")

            # Database tables
            if skill.requires_db:
                try:
                    conn = get_connection()
                    skill_table_prefix = skill.name.replace("-", "_")
                    cur = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                        (f"{skill_table_prefix}%",),
                    )
                    tables = [row[0] for row in cur.fetchall()]
                    if tables:
                        console.print(f"\n**Tables:** {', '.join(tables)}")
                except Exception as e:
                    logging.debug(f"Could not query tables for {skill.name}: {e}")

            console.print()
    else:
        console.print(f"[red]Unknown format: {format}[/red]")

"""Skills configuration management."""

import tomllib
from pathlib import Path
from typing import Any

import tomli_w
from rich.console import Console

from glorious_agents.config import config as agent_config
from glorious_agents.core.registry import get_registry

console = Console()


def load_skill_config(config_file: Path) -> dict[str, Any]:
    """Load skill configuration from TOML file."""
    if not config_file.exists():
        return {}

    with open(config_file, "rb") as f:
        return tomllib.load(f)


def save_skill_config(config_file: Path, config_data: dict[str, Any]) -> None:
    """Save skill configuration to TOML file."""
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "wb") as f:
        tomli_w.dump(config_data, f)


def parse_config_value(value_str: str, schema_type: str) -> Any:
    """Parse configuration value according to schema type."""
    if schema_type == "int":
        return int(value_str)
    elif schema_type == "float":
        return float(value_str)
    elif schema_type == "bool":
        return value_str.lower() in ("true", "yes", "1")
    else:  # str is default
        return value_str


def set_nested_key(config: dict[str, Any], key: str, value: Any) -> None:
    """Set a nested configuration key using dot notation."""
    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value


def get_nested_value(config: dict[str, Any], key: str) -> tuple[Any, bool]:
    """Get a nested configuration value using dot notation.

    Returns:
        Tuple of (value, found) where found indicates if the key exists.
    """
    parts = key.split(".")
    value = config
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return (None, False)
    return (value, True)


def display_config(
    skill_name: str, manifest: Any, config_data: dict[str, Any], key: str | None
) -> None:
    """Display skill configuration."""
    if key:
        # Show specific key
        value, found = get_nested_value(config_data, key)
        if found:
            console.print(f"{key}: {value}")
        else:
            # Try schema default
            if manifest.config_schema and key in manifest.config_schema:
                default = manifest.config_schema[key].get("default")
                console.print(f"{key}: [dim]{default} (default)[/dim]")
            else:
                console.print(f"[yellow]{key}: not set[/yellow]")
    else:
        # Show all config
        if not config_data and not manifest.config_schema:
            console.print(f"[yellow]No configuration for '{skill_name}'[/yellow]")
            return

        console.print(f"[cyan]Configuration for '{skill_name}':[/cyan]\n")

        # Show schema defaults first
        if manifest.config_schema:
            console.print("[dim]Schema (defaults):[/dim]")
            for cfg_key, cfg_schema in manifest.config_schema.items():
                default = cfg_schema.get("default", "N/A")
                cfg_type = cfg_schema.get("type", "str")
                console.print(f"  {cfg_key}: {default} ({cfg_type})")
            console.print()

        # Show current values
        if config_data:
            console.print("[bold]Current values:[/bold]")
            for cfg_key, cfg_value in config_data.items():
                console.print(f"  {cfg_key}: {cfg_value}")
        else:
            console.print("[dim]No custom configuration set (using defaults)[/dim]")


def manage_skill_config(
    skill_name: str,
    key: str | None = None,
    set_value: str | None = None,
    reset: bool = False,
) -> None:
    """Manage skill configuration."""
    registry = get_registry()
    manifest = registry.get_manifest(skill_name)

    if not manifest:
        console.print(f"[red]Skill '{skill_name}' not found.[/red]")
        return

    config_dir = Path(agent_config.AGENT_FOLDER) / "config"
    config_file = config_dir / f"{skill_name}.toml"

    # Handle reset
    if reset:
        if config_file.exists():
            config_file.unlink()
            console.print(f"[green]✓ Configuration reset for '{skill_name}'[/green]")
        else:
            console.print(f"[yellow]No configuration file to reset for '{skill_name}'[/yellow]")
        return

    # Load current config
    current_config = load_skill_config(config_file)

    # Handle set
    if key and set_value is not None:
        # Parse the value based on schema type if available
        value: Any = set_value
        if manifest.config_schema and key in manifest.config_schema:
            schema_type = manifest.config_schema[key].get("type", "str")
            try:
                value = parse_config_value(set_value, schema_type)
            except ValueError:
                console.print(f"[red]Invalid value for type {schema_type}: {set_value}[/red]")
                return

        set_nested_key(current_config, key, value)
        save_skill_config(config_file, current_config)
        console.print(f"[green]✓ Set {key} = {value} for '{skill_name}'[/green]")
        return

    # Show config
    display_config(skill_name, manifest, current_config, key)

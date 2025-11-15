"""Skills reload command."""

import importlib
import sys
from pathlib import Path

from rich.console import Console

from glorious_agents.core.db import init_skill_schema
from glorious_agents.core.loader import load_all_skills, load_skill_entry
from glorious_agents.core.registry import get_registry
from glorious_agents.core.runtime import get_ctx

console = Console()


def reload_skills(skill_name: str | None = None) -> None:
    """Reload skills from disk and entry points."""
    if skill_name:
        reload_single_skill(skill_name)
    else:
        console.print("[blue]Reloading all skills...[/blue]")
        registry = get_registry()
        registry.clear()
        load_all_skills()
        console.print("[green]Skills reloaded successfully![/green]")


def reload_single_skill(skill_name: str) -> None:
    """Hot-reload a single skill module."""
    console.print(f"[blue]Reloading skill '{skill_name}'...[/blue]")

    registry = get_registry()
    manifest = registry.get_manifest(skill_name)

    if not manifest:
        console.print(f"[red]Skill '{skill_name}' not found in registry.[/red]")
        console.print("[yellow]Use 'agent skills reload' to discover new skills.[/yellow]")
        return

    try:
        # Get the module name from entry point
        module_name = manifest.entry_point.split(":")[0]

        # Reload the module if already loaded
        if module_name in sys.modules:
            module = sys.modules[module_name]
            importlib.reload(module)
            console.print(f"  ✓ Reloaded module: {module_name}")
        else:
            # Import for the first time
            importlib.import_module(module_name)
            console.print(f"  ✓ Loaded module: {module_name}")

        # Re-initialize schema (idempotent)
        if manifest.requires_db and manifest.schema_file and manifest.path:
            schema_path = Path(manifest.path) / manifest.schema_file
            if schema_path.exists():
                init_skill_schema(skill_name, schema_path)
                console.print("  ✓ Schema initialized")

        # Load the skill entry point
        app = load_skill_entry(skill_name, manifest.entry_point)

        # Re-initialize context
        try:
            ctx = get_ctx()
            init_fn_name = "init_context"
            module = sys.modules[module_name]
            if hasattr(module, init_fn_name):
                init_fn = getattr(module, init_fn_name)
                init_fn(ctx)
                console.print("  ✓ Context re-initialized")
        except Exception as e:
            console.print(f"  [yellow]⚠ Context init failed: {e}[/yellow]")

        # Update registry
        registry.add(manifest, app)
        console.print(f"[green]✓ Skill '{skill_name}' reloaded successfully![/green]")

    except Exception as e:
        console.print(f"[red]✗ Failed to reload '{skill_name}': {e}[/red]")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")

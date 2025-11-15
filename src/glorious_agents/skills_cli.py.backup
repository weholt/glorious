"""Skills management CLI commands."""

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from glorious_agents.config import config
from glorious_agents.core.loader import load_all_skills
from glorious_agents.core.registry import get_registry

app = typer.Typer(help="Manage skills")
console = Console()


@app.command()
def list() -> None:
    """List all currently loaded skills.

    Displays a formatted table showing all skills that have been discovered
    and loaded by the framework. The table includes each skill's name, version,
    origin (local or entry point), and dependencies.

    Example:
        $ agent skills list
        ┏━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
        ┃ Name  ┃ Version ┃ Origin ┃ Requires ┃
        ┣━━━━━━━╋━━━━━━━━━╋━━━━━━━━╋━━━━━━━━━━┫
        ┃ notes ┃ 0.1.0   ┃ local  ┃ -        ┃
        ┗━━━━━━━┻━━━━━━━━━┻━━━━━━━━┻━━━━━━━━━━┛
    """
    registry = get_registry()
    skills = registry.list_all()

    if not skills:
        console.print("[yellow]No skills loaded.[/yellow]")
        return

    table = Table(title="Loaded Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Origin", style="green")
    table.add_column("Requires", style="yellow")

    for skill in skills:
        requires_str = ", ".join(skill.requires) if skill.requires else "-"
        table.add_row(skill.name, skill.version, skill.origin, requires_str)

    console.print(table)


@app.command()
def reload(
    skill_name: str | None = typer.Argument(
        None, help="Specific skill to reload (or all if not specified)"
    ),
) -> None:
    """Reload skills from disk and entry points.

    Can reload all skills or a specific skill with hot-reload support.
    For single skill reload, uses importlib.reload() to refresh the module
    without restarting the entire application.

    When reloading all skills, clears the registry and re-discovers everything.
    When reloading a single skill, only that skill's module is reloaded while
    preserving the rest of the system state.

    The reload process for a single skill includes:
    1. Reloading the skill module with importlib.reload()
    2. Re-initializing database schemas (idempotent)
    3. Re-calling init_context() to re-register event handlers
    4. Updating the registry with the refreshed skill

    Note:
        This command does not restart the daemon. To reload skills in a running
        daemon, you must restart the daemon process.

    Args:
        skill_name: Optional name of specific skill to reload. If not provided,
            reloads all skills.

    Example:
        $ agent skills reload
        Reloading all skills...

        $ agent skills reload notes
        Reloading skill 'notes'...
    """
    if skill_name:
        _reload_single_skill(skill_name)
    else:
        console.print("[blue]Reloading all skills...[/blue]")
        registry = get_registry()
        registry.clear()
        load_all_skills()
        console.print("[green]Skills reloaded successfully![/green]")


def _reload_single_skill(skill_name: str) -> None:
    """Hot-reload a single skill module."""
    import importlib
    import sys

    from glorious_agents.core.db import init_skill_schema
    from glorious_agents.core.loader import load_skill_entry
    from glorious_agents.core.runtime import get_ctx

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
            from pathlib import Path

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


@app.command()
def describe(skill_name: str) -> None:
    """Describe a specific skill and display its detailed information.

    Shows comprehensive information about a skill including:
    - Metadata (name, version, description, origin)
    - Dependencies (required skills and dependent skills)
    - Available commands from the Typer app
    - Database schema tables
    - Configuration options (if defined)
    - Documentation paths
    - Usage documentation content (if available)

    Args:
        skill_name: The name of the skill to describe. Must match an existing
            loaded skill exactly.

    Example:
        $ agent skills describe cache
        cache v0.1.0
        Short-term ephemeral storage with TTL

        Origin: entrypoint
        Requires skills: None
        Required by: planner, linker

        Commands:
          • set - Store value with optional TTL
          • get - Retrieve cached value
          • list - Show all cache entries
          • delete - Remove entry
          • warmup - Pre-populate cache
          • prune - Clean up expired entries

        Database: Yes
        Tables: cache_entries

        Documentation: /path/to/skill/usage.md
    """
    from glorious_agents.core.db import get_connection

    registry = get_registry()
    manifest = registry.get_manifest(skill_name)

    if not manifest:
        console.print(f"[red]Skill '{skill_name}' not found.[/red]")
        return

    # Header
    console.print(f"[bold cyan]{manifest.name}[/bold cyan] v{manifest.version}")
    console.print(f"[dim]{manifest.description}[/dim]\n")

    # Origin
    console.print(f"[bold]Origin:[/bold] {manifest.origin}")

    # Dependencies
    if manifest.requires:
        requires_list = [f"[cyan]{req}[/cyan]" for req in manifest.requires]
        console.print(f"[bold]Requires skills:[/bold] {', '.join(requires_list)}")
    else:
        console.print("[bold]Requires skills:[/bold] None")

    # Find skills that depend on this skill
    all_skills = registry.list_all()
    dependents = [s.name for s in all_skills if skill_name in s.requires]
    if dependents:
        dependents_list = [f"[cyan]{dep}[/cyan]" for dep in dependents]
        console.print(f"[bold]Required by:[/bold] {', '.join(dependents_list)}")

    console.print()

    # Commands
    app = registry.get_app(skill_name)
    if app and hasattr(app, "registered_commands"):
        console.print("[bold]Commands:[/bold]")
        for cmd in app.registered_commands:
            cmd_name = cmd.name or cmd.callback.__name__
            cmd_help = cmd.help or cmd.callback.__doc__ or "No description"
            # Get first line of help/docstring
            cmd_help_line = cmd_help.split("\n")[0].strip()
            console.print(f"  • [cyan]{cmd_name}[/cyan] - {cmd_help_line}")
        console.print()

    # Database info
    console.print(f"[bold]Database:[/bold] {'Yes' if manifest.requires_db else 'No'}")
    if manifest.requires_db:
        try:
            conn = get_connection()
            # Query for tables related to this skill
            skill_table_prefix = skill_name.replace("-", "_")
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                (f"{skill_table_prefix}%",),
            )
            tables = [row[0] for row in cur.fetchall()]
            if tables:
                console.print(f"[bold]Tables:[/bold] {', '.join(tables)}")
            else:
                console.print("[yellow]No tables found (schema may not be initialized)[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not query database: {e}[/yellow]")
    console.print()

    # Configuration
    if manifest.config_schema:
        console.print("[bold]Configuration options:[/bold]")
        for key, schema in manifest.config_schema.items():
            cfg_type = schema.get("type", "str")
            default = schema.get("default", "N/A")
            choices = schema.get("choices")
            if choices:
                console.print(
                    f"  • [cyan]{key}[/cyan] ({cfg_type}) = {default} [choices: {choices}]"
                )
            else:
                console.print(f"  • [cyan]{key}[/cyan] ({cfg_type}) = {default}")
        console.print()

    # Documentation paths
    if manifest.path:
        console.print(f"[bold]Location:[/bold] {manifest.path}")
        if manifest.internal_doc:
            internal_path = Path(manifest.path) / manifest.internal_doc
            status = "✓" if internal_path.exists() else "✗"
            console.print(f"[bold]Internal docs:[/bold] {status} {manifest.internal_doc}")
        if manifest.external_doc:
            external_path = Path(manifest.path) / manifest.external_doc
            status = "✓" if external_path.exists() else "✗"
            console.print(f"[bold]External docs:[/bold] {status} {manifest.external_doc}")
        console.print()

    # Display usage documentation if available
    if manifest.external_doc and manifest.path:
        usage_path = Path(manifest.path) / manifest.external_doc
        if usage_path.exists():
            console.print("[bold]─── Usage Documentation ───[/bold]\n")
            console.print(usage_path.read_text())
        else:
            console.print(f"[yellow]Usage documentation not found at: {usage_path}[/yellow]")
    elif manifest.external_doc:
        console.print(f"[bold]External Docs:[/bold] {manifest.external_doc}")
    else:
        console.print("[dim]Tip: Add a usage.md file for user-friendly documentation.[/dim]")


@app.command()
def export(
    format: str = typer.Option("json", help="Export format (json or md)"),
    skill_name: str | None = typer.Option(None, "--skill", help="Export specific skill only"),
) -> None:
    """Export loaded skills metadata in various formats.

    Exports comprehensive skill information to stdout in either JSON or Markdown format.
    Includes metadata, dependencies, available commands, and database schema information.
    This is useful for documentation generation, integration with other tools, or creating
    skill catalogs.

    Args:
        format: The output format, either 'json' or 'md' (Markdown). Defaults to 'json'.
        skill_name: Optional specific skill to export. If not provided, exports all skills.

    Example:
        $ agent skills export --format json > skills.json
        $ agent skills export --format md > SKILLS.md
        $ agent skills export --format json --skill cache > cache.json
    """
    from glorious_agents.core.db import get_connection

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
                from typing import cast

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
                    # Log the exception but continue - non-critical error
                    import logging

                    logging.debug(f"Could not query tables for {skill.name}: {e}")

            console.print()
    else:
        console.print(f"[red]Unknown format: {format}[/red]")


@app.command()
def create(
    name: str,
    external: bool = typer.Option(False, "--external", help="Create external installable package"),
) -> None:
    """Create a new skill scaffold with all required files.

    Generates a complete skill directory structure with template files including:
    - skill.json: Manifest with metadata and configuration
    - skill.py: Python module with sample command and context initialization
    - schema.sql: Database schema definition
    - instructions.md: Internal documentation for agents
    - usage.md: External documentation for humans

    When --external is used, creates a standalone package with pyproject.toml
    and proper package structure for distribution via PyPI.

    Args:
        name: The name for the new skill. Will be used as the directory name
            and in the generated files. Should be a valid Python identifier.
        external: If True, creates an external package structure instead of
            a local skill.

    Example:
        $ agent skills create my-analyzer
        Skill 'my-analyzer' created successfully at /path/to/skills/my-analyzer
        Run 'agent skills reload' to load the new skill.

        $ agent skills create my-plugin --external
        Package 'my-plugin' created at ./my-plugin
        Install with: pip install -e ./my-plugin
    """
    if external:
        _create_external_skill(name)
    else:
        _create_local_skill(name)


def _create_local_skill(name: str) -> None:
    """Create a local skill in the skills directory."""
    skills_dir = config.SKILLS_DIR
    skill_dir = skills_dir / name

    if skill_dir.exists():
        console.print(f"[red]Skill '{name}' already exists![/red]")
        return

    # Create directory
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create manifest
    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": f"Skill: {name}",
        "entry_point": f"{name}.skill:app",
        "schema_file": "schema.sql",
        "requires": [],
        "requires_db": True,
        "internal_doc": "instructions.md",
        "external_doc": "usage.md",
    }
    (skill_dir / "skill.json").write_text(json.dumps(manifest, indent=2))

    # Create schema
    schema = f"""-- Schema for {name} skill
CREATE TABLE IF NOT EXISTS {name}_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
    (skill_dir / "schema.sql").write_text(schema)

    # Create skill.py
    skill_py = f'''"""Skill: {name}."""

import typer
from glorious_agents.core.context import SkillContext

app = typer.Typer(help="{name} skill")
_ctx: SkillContext | None = None


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx
    # Subscribe to events if needed
    # ctx.subscribe("some_topic", handle_event)


@app.command()
def hello(name: str = "World") -> None:
    """Say hello."""
    print(f"Hello {{name}} from {name} skill!")


# Add more commands and callable functions here
'''
    (skill_dir / "skill.py").write_text(skill_py)

    # Create docs
    (skill_dir / "instructions.md").write_text(f"# {name} - Internal Instructions\n\nFor agents.\n")
    (skill_dir / "usage.md").write_text(f"# {name} - Usage Guide\n\nFor humans.\n")

    console.print(f"[green]Skill '{name}' created successfully at {skill_dir}[/green]")
    console.print("[blue]Run 'agent skills reload' to load the new skill.[/blue]")


def _generate_pyproject_toml(name: str, package_name: str) -> str:
    """Generate pyproject.toml content for external skill."""
    return f'''[project]
name = "{name}"
version = "0.1.0"
description = "Glorious Agents skill: {name}"
readme = "README.md"
requires-python = ">=3.13"
license = {{text = "MIT"}}
authors = [
    {{name = "Your Name", email = "your.email@example.com"}}
]
dependencies = [
    "glorious-agents>=0.1.0",
]

[project.entry-points."glorious_agents.skills"]
{name} = "{package_name}.skill:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
'''


def _generate_skill_manifest(name: str, package_name: str) -> dict[str, Any]:
    """Generate skill.json manifest for external skill."""
    return {
        "name": name,
        "version": "0.1.0",
        "description": f"Skill: {name}",
        "entry_point": f"{package_name}.skill:app",
        "schema_file": "schema.sql",
        "requires": [],
        "requires_db": True,
        "internal_doc": "instructions.md",
        "external_doc": "usage.md",
    }


def _generate_skill_schema(name: str, package_name: str) -> str:
    """Generate SQL schema for external skill."""
    return f"""-- Schema for {name} skill
CREATE TABLE IF NOT EXISTS {package_name}_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _generate_skill_code(name: str) -> str:
    """Generate skill.py code for external skill."""
    return f'''"""Skill: {name}."""

import typer
from glorious_agents.core.context import SkillContext

app = typer.Typer(help="{name} skill")
_ctx: SkillContext | None = None


def init() -> None:
    """Optional initialization function called when skill is loaded.
    
    Use this to verify that the skill can run (check dependencies,
    validate configuration, test external services, etc.).
    
    Raises:
        Exception: If skill cannot run (will prevent skill from loading)
    """
    # Example: Check for required environment variables
    # import os
    # if not os.getenv("API_KEY"):
    #     raise RuntimeError("API_KEY environment variable not set")
    
    # Example: Verify external service is available
    # import requests
    # try:
    #     requests.get("https://api.example.com/health", timeout=5).raise_for_status()
    # except Exception as e:
    #     raise RuntimeError(f"Cannot reach external API: {{e}}")
    
    pass


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context."""
    global _ctx
    _ctx = ctx
    # Subscribe to events if needed
    # ctx.subscribe("some_topic", handle_event)


@app.command()
def hello(name: str = "World") -> None:
    """Say hello."""
    print(f"Hello {{name}} from {name} skill!")


# Add more commands and callable functions here
'''


def _generate_readme(name: str, package_name: str) -> str:
    """Generate README.md for external skill."""
    return f"""# {name}

Glorious Agents skill: {name}

## Installation

```bash
pip install {name}
```

Or install in development mode:

```bash
pip install -e .
```

## Usage

After installation, the skill will be automatically discovered by Glorious Agents:

```bash
agent skills list
```

See [usage.md]({package_name}/usage.md) for detailed documentation.

## Development

1. Install in editable mode: `pip install -e .`
2. Make changes to the skill
3. Test with: `agent skills reload`

## License

MIT
"""


def _generate_mit_license() -> str:
    """Generate MIT license text."""
    return """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _generate_gitignore() -> str:
    """Generate .gitignore for Python projects."""
    return """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.venv/
venv/
ENV/
"""


def _create_external_skill(name: str) -> None:
    """Create an external installable skill package."""
    from pathlib import Path

    # Use current directory
    package_dir = Path.cwd() / name
    package_name = name.replace("-", "_")

    if package_dir.exists():
        console.print(f"[red]Directory '{name}' already exists![/red]")
        return

    # Create package structure
    package_dir.mkdir(parents=True)
    src_dir = package_dir / package_name
    src_dir.mkdir()

    # Generate and write all files using helper functions
    (package_dir / "pyproject.toml").write_text(_generate_pyproject_toml(name, package_name))
    (src_dir / "skill.json").write_text(
        json.dumps(_generate_skill_manifest(name, package_name), indent=2)
    )
    (src_dir / "__init__.py").write_text(f'"""Skill package: {name}."""\n\n__version__ = "0.1.0"\n')
    (src_dir / "schema.sql").write_text(_generate_skill_schema(name, package_name))
    (src_dir / "skill.py").write_text(_generate_skill_code(name))
    (src_dir / "instructions.md").write_text(f"# {name} - Internal Instructions\n\nFor agents.\n")
    (src_dir / "usage.md").write_text(f"# {name} - Usage Guide\n\nFor humans.\n")
    (package_dir / "README.md").write_text(_generate_readme(name, package_name))
    (package_dir / "LICENSE").write_text(_generate_mit_license())
    (package_dir / ".gitignore").write_text(_generate_gitignore())

    console.print(f"[green]External package '{name}' created successfully at {package_dir}[/green]")
    console.print(f"[blue]Install with: pip install -e {package_dir}[/blue]")
    console.print("[blue]Then run 'agent skills reload' to load the skill.[/blue]")


@app.command()
def check(skill_name: str) -> None:
    """Run health checks on a specific skill.

    Performs comprehensive diagnostics including:
    - Manifest validation
    - Schema table existence
    - Dependency availability
    - Entry point accessibility
    - Documentation presence

    Args:
        skill_name: Name of the skill to check.

    Example:
        $ agent skills check notes
        ✓ notes - All checks passed
    """
    from glorious_agents.core.db import get_connection

    registry = get_registry()
    manifest = registry.get_manifest(skill_name)

    if not manifest:
        console.print(f"[red]✗ Skill '{skill_name}' not found[/red]")
        return

    issues = []
    warnings = []

    # Check 1: Manifest loaded
    console.print(f"[cyan]Checking skill: {skill_name}[/cyan]")

    # Check 2: Required dependencies loaded
    if manifest.requires:
        for dep in manifest.requires:
            if not registry.get_manifest(dep):
                issues.append(f"Missing dependency: {dep}")

    # Check 3: Schema tables exist
    if manifest.requires_db and manifest.schema_file:
        try:
            conn = get_connection()
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                (f"{skill_name.replace('-', '_')}%",),
            )
            tables = cur.fetchall()
            if not tables:
                warnings.append(f"No schema tables found for {skill_name}")
        except Exception as e:
            issues.append(f"Database check failed: {e}")

    # Check 4: Entry point accessible
    try:
        app = registry.get_app(skill_name)
        if not app:
            issues.append("Entry point not loaded")
    except Exception as e:
        issues.append(f"Entry point error: {e}")

    # Check 5: Documentation files
    if manifest.path:
        from pathlib import Path

        skill_path = Path(manifest.path)
        if manifest.internal_doc:
            if not (skill_path / manifest.internal_doc).exists():
                warnings.append(f"Missing internal docs: {manifest.internal_doc}")
        if manifest.external_doc:
            if not (skill_path / manifest.external_doc).exists():
                warnings.append(f"Missing external docs: {manifest.external_doc}")

    # Display results
    if issues:
        console.print(f"[red]✗ {skill_name} - {len(issues)} issue(s) found[/red]")
        for issue in issues:
            console.print(f"  [red]✗[/red] {issue}")
    elif warnings:
        console.print(f"[yellow]⚠ {skill_name} - {len(warnings)} warning(s)[/yellow]")
        for warning in warnings:
            console.print(f"  [yellow]⚠[/yellow] {warning}")
    else:
        console.print(f"[green]✓ {skill_name} - All checks passed[/green]")


@app.command()
def doctor() -> None:
    """Run health checks on all loaded skills.

    Performs comprehensive diagnostics on all skills in the registry,
    checking dependencies, schemas, entry points, and documentation.

    Example:
        $ agent skills doctor
        ✓ notes - OK
        ✗ planner - Missing dependency: notes
        ⚠ cache - Missing external docs
    """
    registry = get_registry()
    skills = registry.list_all()

    if not skills:
        console.print("[yellow]No skills loaded.[/yellow]")
        return

    console.print(f"[cyan]Running diagnostics on {len(skills)} skill(s)...[/cyan]\\n")

    for manifest in skills:
        check(manifest.name)


@app.command(name="config")
def _load_skill_config(config_file: Path) -> dict[str, Any]:
    """Load skill configuration from TOML file."""
    import tomllib

    if not config_file.exists():
        return {}

    with open(config_file, "rb") as f:
        return tomllib.load(f)


def _save_skill_config(config_file: Path, config_data: dict[str, Any]) -> None:
    """Save skill configuration to TOML file."""
    import tomli_w

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "wb") as f:
        tomli_w.dump(config_data, f)


def _parse_config_value(value_str: str, schema_type: str) -> Any:
    """Parse configuration value according to schema type."""
    if schema_type == "int":
        return int(value_str)
    elif schema_type == "float":
        return float(value_str)
    elif schema_type == "bool":
        return value_str.lower() in ("true", "yes", "1")
    else:  # str is default
        return value_str


def _set_nested_key(config: dict[str, Any], key: str, value: Any) -> None:
    """Set a nested configuration key using dot notation."""
    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value


def _get_nested_value(config: dict[str, Any], key: str) -> tuple[Any, bool]:
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


def _display_config(
    skill_name: str, manifest: Any, config_data: dict[str, Any], key: str | None
) -> None:
    """Display skill configuration."""
    if key:
        # Show specific key
        value, found = _get_nested_value(config_data, key)
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

        console.print(f"[cyan]Configuration for '{skill_name}':[/cyan]\\n")

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


def skill_config(
    skill_name: str = typer.Argument(..., help="Name of the skill"),
    key: str | None = typer.Option(None, help="Configuration key to show"),
    set_value: str | None = typer.Option(None, "--set", help="Set configuration value"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults"),
) -> None:
    """Manage skill configuration.

    View, set, or reset configuration for a specific skill. Configuration is stored
    in ~/.agent/config/<skill_name>.toml and validated against the skill's config_schema.

    Examples:
        $ agent skills config cache
        $ agent skills config cache --key ttl_default
        $ agent skills config cache --key ttl_default --set 7200
        $ agent skills config cache --reset
    """
    from pathlib import Path

    from glorious_agents.config import config as agent_config

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
    current_config = _load_skill_config(config_file)

    # Handle set
    if key and set_value is not None:
        # Parse the value based on schema type if available
        value: Any = set_value
        if manifest.config_schema and key in manifest.config_schema:
            schema_type = manifest.config_schema[key].get("type", "str")
            try:
                value = _parse_config_value(set_value, schema_type)
            except ValueError:
                console.print(f"[red]Invalid value for type {schema_type}: {set_value}[/red]")
                return

        _set_nested_key(current_config, key, value)
        _save_skill_config(config_file, current_config)
        console.print(f"[green]✓ Set {key} = {value} for '{skill_name}'[/green]")
        return

    # Show config
    _display_config(skill_name, manifest, current_config, key)

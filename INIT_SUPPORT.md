# Skill Init Support

Skills can now include an optional `init()` function that is called during skill loading. This allows skills to verify they can run before being registered.

## Usage

Add an `init()` function to your skill module (e.g., `skill.py`):

```python
"""My skill module."""

import os
import typer

app = typer.Typer(help="my skill")


def init() -> None:
    """Optional initialization function called when skill is loaded.
    
    Use this to verify that the skill can run (check dependencies,
    validate configuration, test external services, etc.).
    
    Raises:
        Exception: If skill cannot run (will prevent skill from loading)
    """
    # Example: Check for required environment variables
    if not os.getenv("API_KEY"):
        raise RuntimeError("API_KEY environment variable not set")
    
    # Example: Verify external service is available
    # import requests
    # try:
    #     requests.get("https://api.example.com/health", timeout=5).raise_for_status()
    # except Exception as e:
    #     raise RuntimeError(f"Cannot reach external API: {e}")
    
    print("Skill initialization successful!")


def init_context(ctx: SkillContext) -> None:
    """Initialize skill context (called after init)."""
    # ... existing context setup


@app.command()
def my_command():
    """Example command."""
    pass
```

## Behavior

- **Optional**: If no `init()` function exists, skill loading proceeds normally
- **Called Once**: `init()` is called once during skill loading, before the skill is registered
- **Failure Handling**: If `init()` raises an exception:
  - The skill is not loaded
  - The error is logged with full traceback
  - Other skills continue loading (fail-open behavior)
  - A summary shows which skills failed and why
- **Success**: If `init()` completes without exception, the skill is registered and available

## Use Cases

1. **Environment Validation**: Check for required environment variables or configuration
2. **Dependency Verification**: Verify external dependencies are installed and importable
3. **Service Health Checks**: Test connectivity to external APIs or databases
4. **License Validation**: Verify license keys or authentication tokens
5. **Resource Checks**: Ensure required files, directories, or resources exist
6. **Feature Detection**: Check if required system features are available

## Example: API Key Validation

```python
def init() -> None:
    """Verify API credentials are configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable not set. "
            "Please configure your API key before using this skill."
        )
```

## Example: Service Connectivity

```python
def init() -> None:
    """Verify database connectivity."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database="mydb",
            connect_timeout=5
        )
        conn.close()
    except Exception as e:
        raise RuntimeError(f"Cannot connect to database: {e}")
```

## Logging

When a skill's `init()` is called:
- Debug log: "Calling init() for skill 'skillname'"
- Debug log: "Skill 'skillname' init() completed successfully"
- On failure: Error log with full traceback

Loading summary shows:
```
Skill loading complete: X loaded, Y failed
Failed to load skills: skill1, skill2
```

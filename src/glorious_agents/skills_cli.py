"""Skills management CLI commands.

This module has been refactored into a package structure for better maintainability.
The original file was 1071 lines, now split into focused modules:
- list_describe.py: list, describe, check, doctor commands
- reload.py: reload command
- export.py: export command
- config.py: config command
- __init__.py: app assembly
"""

from glorious_agents.skills_cli import app

__all__ = ["app"]

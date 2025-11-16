"""CLI command modules."""

from issue_tracker.cli.commands.comments import app as comments_app
from issue_tracker.cli.commands.dependencies import app as dependencies_app
from issue_tracker.cli.commands.epics import app as epics_app
from issue_tracker.cli.commands.instructions import app as instructions_app
from issue_tracker.cli.commands.labels import app as labels_app

__all__ = ["comments_app", "dependencies_app", "epics_app", "instructions_app", "labels_app"]

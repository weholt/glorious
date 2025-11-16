from typer.testing import CliRunner
from issue_tracker.cli.app import app
import json

runner = CliRunner()

# Create issues
issue1 = runner.invoke(app, ["create", "Issue 1", "--json"])
print("Issue 1:", issue1.stdout)
issue1_id = json.loads(issue1.stdout)["id"]

issue2 = runner.invoke(app, ["create", "Issue 2", "--json"])
print("Issue 2:", issue2.stdout)
issue2_id = json.loads(issue2.stdout)["id"]

# Try dep-add with test syntax
result = runner.invoke(app, ["dependencies", "add", issue1_id, "blocks", issue2_id])
print(f"Exit code: {result.exit_code}")
print(f"Stdout: {result.stdout}")
print(f"Exception: {result.exception}")

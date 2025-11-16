from typer.testing import CliRunner

from issue_tracker.cli.app import app

runner = CliRunner()
result = runner.invoke(app, ["stale"])
print(f"Exit code: {result.exit_code}")
print(f"Stdout: {result.stdout}")
if result.exception:
    print(f"Exception: {result.exception}")
    import traceback

    traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

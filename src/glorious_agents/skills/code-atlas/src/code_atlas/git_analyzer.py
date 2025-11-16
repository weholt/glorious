"""Git metadata extraction utilities."""

import subprocess
from pathlib import Path
from typing import Any


def extract_git_metadata(path: Path) -> dict[str, Any]:
    """Extract commit count, last author, last date.

    Args:
        path: Path to file

    Returns:
        Dict with commits, last_author, last_commit (empty values if git unavailable)
    """
    empty_result = {"commits": 0, "last_author": "", "last_commit": ""}

    try:
        # Check if git is available
        check_git = subprocess.run(  # noqa: S603
            ["git", "--version"],  # noqa: S607
            capture_output=True,
            check=False,
            timeout=2,
        )
        if check_git.returncode != 0:
            return empty_result

        # Get commit count
        result = subprocess.run(  # noqa: S603
            ["git", "rev-list", "--count", "HEAD", "--", str(path)],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        commits = int(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else 0

        # Get last author
        result = subprocess.run(  # noqa: S603
            ["git", "log", "-1", "--pretty=%an", "--", str(path)],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        last_author = result.stdout.strip() if result.returncode == 0 else ""

        # Get last commit date
        result = subprocess.run(  # noqa: S603
            ["git", "log", "-1", "--pretty=%ad", "--date=short", "--", str(path)],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        last_commit = result.stdout.strip() if result.returncode == 0 else ""

        return {
            "commits": commits,
            "last_author": last_author,
            "last_commit": last_commit,
        }
    except subprocess.TimeoutExpired:
        # Git command took too long
        return empty_result
    except FileNotFoundError:
        # Git not installed
        return empty_result
    except Exception:  # noqa: S112
        # Any other error
        return empty_result

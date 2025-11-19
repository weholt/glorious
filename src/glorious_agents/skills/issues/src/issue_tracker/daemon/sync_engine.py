"""Sync engine for JSONL export/import and git operations."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

__all__ = ["SyncEngine"]

logger = logging.getLogger(__name__)


class SyncEngine:
    """Handles synchronization between database and git repository."""

    def __init__(self, workspace_path: Path, export_path: Path, git_enabled: bool = True) -> None:
        """Initialize sync engine.

        Args:
            workspace_path: Workspace root directory
            export_path: Path to JSONL export file
            git_enabled: Whether git integration is enabled
        """
        self.workspace_path = workspace_path
        self.export_path = export_path
        self.git_enabled = git_enabled
        self._last_export: dict[str, Any] = {}

    def export_to_jsonl(self, issues: list[dict[str, Any]]) -> tuple[int, int]:
        """Export issues to JSONL format.

        Args:
            issues: List of issue dictionaries

        Returns:
            Tuple of (exported_count, skipped_count)
        """
        exported = 0
        skipped = 0

        try:
            self.export_path.parent.mkdir(parents=True, exist_ok=True)

            # Collect issues that need to be written
            issues_to_write: list[dict[str, Any]] = []
            for issue in issues:
                # Check if issue changed since last export
                issue_id = issue.get("id")
                issue_hash = hash(json.dumps(issue, sort_keys=True))

                if issue_id and self._last_export.get(issue_id) == issue_hash:
                    skipped += 1
                    continue

                issues_to_write.append(issue)
                if issue_id:
                    self._last_export[issue_id] = issue_hash
                exported += 1

            # Only write file if there are changes
            if issues_to_write:
                with open(self.export_path, "w", encoding="utf-8") as f:
                    for issue in issues_to_write:
                        f.write(json.dumps(issue) + "\n")
            elif self.export_path.exists():
                # Touch file to update mtime even when all skipped
                self.export_path.touch()

            logger.info(f"Exported {exported} issues to {self.export_path} ({skipped} skipped)")
            return exported, skipped

        except Exception as e:
            logger.error(f"Failed to export issues: {e}")
            raise

    def import_from_jsonl(self) -> list[dict[str, Any]]:
        """Import issues from JSONL format.

        Returns:
            List of issue dictionaries
        """
        if not self.export_path.exists():
            logger.info(f"No export file found at {self.export_path}")
            return []

        try:
            issues = []
            with open(self.export_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        issue = json.loads(line)
                        issues.append(issue)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")

            logger.info(f"Imported {len(issues)} issues from {self.export_path}")
            return issues

        except Exception as e:
            logger.error(f"Failed to import issues: {e}")
            raise

    def git_commit(self, message: str | None = None) -> bool:
        """Commit changes to git.

        Args:
            message: Commit message (auto-generated if None)

        Returns:
            True if commit succeeded
        """
        if not self.git_enabled:
            return False

        try:
            # Check if we're in a git repo
            result = subprocess.run(  # noqa: S603, S607
                ["git", "rev-parse", "--git-dir"],  # noqa: S607
                cwd=self.workspace_path,
                capture_output=True,
                check=False,
                timeout=5,
            )
            if result.returncode != 0:
                logger.warning("Not a git repository, skipping commit")
                return False

            # Stage the JSONL file
            subprocess.run(  # noqa: S603, S607
                ["git", "add", str(self.export_path.relative_to(self.workspace_path))],  # noqa: S607
                cwd=self.workspace_path,
                check=True,
                timeout=5,
            )

            # Check if there are changes to commit
            result = subprocess.run(  # noqa: S607
                ["git", "diff", "--cached", "--quiet"],  # noqa: S607
                cwd=self.workspace_path,
                check=False,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info("No changes to commit")
                return True

            # Commit
            if message is None:
                message = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            subprocess.run(  # noqa: S603, S607
                ["git", "commit", "-m", message],  # noqa: S607
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
                timeout=10,
            )
            logger.info(f"Committed changes: {message}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Git commit timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during git commit: {e}")
            return False

    def git_pull(self) -> bool:
        """Pull changes from remote.

        Returns:
            True if pull succeeded
        """
        if not self.git_enabled:
            return False

        try:
            result = subprocess.run(  # noqa: S607
                ["git", "pull", "--rebase"],  # noqa: S607
                cwd=self.workspace_path,
                capture_output=True,
                check=False,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info("Pulled changes from remote")
                return True

            logger.warning(f"Git pull failed: {result.stderr.decode()}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("Git pull timed out")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during git pull: {e}")
            return False

    def git_push(self) -> bool:
        """Push changes to remote.

        Returns:
            True if push succeeded
        """
        if not self.git_enabled:
            return False

        try:
            result = subprocess.run(  # noqa: S607
                ["git", "push"],  # noqa: S607
                cwd=self.workspace_path,
                capture_output=True,
                check=False,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info("Pushed changes to remote")
                return True

            # Check if it's because there's no upstream
            stderr = result.stderr.decode()
            if "no upstream" in stderr.lower() or "set-upstream" in stderr.lower():
                logger.info("No upstream branch configured, skipping push")
                return True

            logger.warning(f"Git push failed: {stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("Git push timed out")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during git push: {e}")
            return False

    def sync(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Perform full sync cycle: export → commit → pull → import → push.

        Args:
            issues: Current issues from database

        Returns:
            Sync statistics
        """
        stats: dict[str, Any] = {
            "exported": 0,
            "skipped": 0,
            "imported": 0,
            "committed": False,
            "pulled": False,
            "pushed": False,
            "errors": [],
        }

        try:
            # Export current state
            exported, skipped = self.export_to_jsonl(issues)
            stats["exported"] = exported
            stats["skipped"] = skipped

            # Commit if there are changes
            if exported > 0:
                stats["committed"] = self.git_commit()

            # Pull remote changes
            stats["pulled"] = self.git_pull()

            # Import any updates
            imported_issues = self.import_from_jsonl()
            stats["imported"] = len(imported_issues)

            # Push local changes
            if stats["committed"]:
                stats["pushed"] = self.git_push()

            return stats

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            stats["errors"].append(str(e))
            return stats

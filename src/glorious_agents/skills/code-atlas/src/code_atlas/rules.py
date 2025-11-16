"""Rule engine for dynamic code analysis based on YAML configuration."""

from pathlib import Path
from typing import Any

import yaml

from code_atlas.utils import SafeExpressionEvaluator, get_avg_complexity, logger


class RuleEngine:
    """Dynamic rule engine for code quality checks."""

    def __init__(self, rules_path: str | Path) -> None:
        """Initialize rule engine from YAML file.

        Args:
            rules_path: Path to rules.yaml file

        Raises:
            FileNotFoundError: If rules file does not exist
            ValueError: If path is not a file
        """
        path = Path(rules_path)

        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Rules path is not a file: {path}")

        with open(path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def evaluate(self, file_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Evaluate rules against file data.

        Args:
            file_data: File analysis data from scanner

        Returns:
            List of rule violations with details
        """
        issues: list[dict[str, Any]] = []

        metrics = self.config.get("metrics", {})
        actions = self.config.get("actions", [])

        for action in actions:
            rule_id = action.get("id", "UNKNOWN")
            condition = action.get("condition", "")
            message = action.get("message", "")
            suggested_action = action.get("action", "")

            if self._check_condition(condition, file_data, metrics):
                issues.append(
                    {
                        "id": rule_id,
                        "message": message,
                        "action": suggested_action,
                        "file": file_data.get("path", ""),
                    }
                )

        return issues

    def _check_condition(
        self,
        condition: str,
        file_data: dict[str, Any],
        metrics: dict[str, Any],
    ) -> bool:
        """Check if condition is met.

        Args:
            condition: Condition expression to evaluate
            file_data: File analysis data
            metrics: Metrics thresholds

        Returns:
            True if condition is met
        """
        try:
            # Build evaluation context
            context = {
                "complexity": get_avg_complexity(file_data),
                "loc": file_data.get("raw", {}).get("loc", 0),
                "comment_ratio": file_data.get("comment_ratio", 0.0),
                "max_complexity": metrics.get("max_complexity", 10),
                "max_loc": metrics.get("max_loc", 500),
                "min_comment_ratio": metrics.get("min_comment_ratio", 0.1),
            }

            # Safely evaluate condition using safe evaluator
            evaluator = SafeExpressionEvaluator(context)
            return bool(evaluator.eval(condition))
        except Exception as e:
            logger.debug(f"Rule condition evaluation failed for '{condition}': {e}")
            # If evaluation fails, don't flag as violation
            return False

"""Utility functions shared across modules."""

import ast
import logging
import operator
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(name)s: %(message)s")
logger = logging.getLogger("code_atlas")


class SafeExpressionEvaluator:
    """Safe evaluator for simple expressions without using eval()."""

    # Allowed operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
        ast.Not: operator.not_,
    }

    def __init__(self, context: dict[str, Any]):
        """Initialize evaluator with context variables.

        Args:
            context: Dictionary of variable names to values
        """
        self.context = context

    def eval(self, expr_str: str) -> Any:
        """Safely evaluate an expression.

        Args:
            expr_str: Expression string to evaluate

        Returns:
            Evaluation result

        Raises:
            ValueError: If expression contains unsafe operations
        """
        try:
            tree = ast.parse(expr_str, mode="eval")
            return self._eval_node(tree.body)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {e}") from e

    def _eval_constant(self, node: ast.Constant) -> Any:
        """Evaluate constant node."""
        return node.value

    def _eval_name(self, node: ast.Name) -> Any:
        """Evaluate name (variable) node."""
        if node.id in self.context:
            return self.context[node.id]
        raise NameError(f"Undefined variable: {node.id}")

    def _eval_binop(self, node: ast.BinOp) -> Any:
        """Evaluate binary operation node."""
        left = self._eval_node(node.left)
        right = self._eval_node(node.right)
        op = self.OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(left, right)  # type: ignore[operator]

    def _eval_compare(self, node: ast.Compare) -> bool:
        """Evaluate comparison node."""
        left = self._eval_node(node.left)
        for op_node, comparator in zip(node.ops, node.comparators, strict=True):
            right = self._eval_node(comparator)
            op_func = self.OPERATORS.get(type(op_node))
            if op_func is None:
                raise ValueError(f"Unsupported comparison: {type(op_node).__name__}")
            if not op_func(left, right):  # type: ignore[operator]
                return False
            left = right
        return True

    def _eval_boolop(self, node: ast.BoolOp) -> Any:
        """Evaluate boolean operation node."""
        op_func = self.OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
        values = [self._eval_node(v) for v in node.values]
        result: Any = values[0]
        for val in values[1:]:
            result = op_func(result, val)  # type: ignore[operator]
        return result

    def _eval_unaryop(self, node: ast.UnaryOp) -> Any:
        """Evaluate unary operation node."""
        operand = self._eval_node(node.operand)
        op_func = self.OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_func(operand)  # type: ignore[operator]

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Constant):
            return self._eval_constant(node)
        elif isinstance(node, ast.Name):
            return self._eval_name(node)
        elif isinstance(node, ast.BinOp):
            return self._eval_binop(node)
        elif isinstance(node, ast.Compare):
            return self._eval_compare(node)
        elif isinstance(node, ast.BoolOp):
            return self._eval_boolop(node)
        elif isinstance(node, ast.UnaryOp):
            return self._eval_unaryop(node)
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")


# Default ignore patterns for scanning
DEFAULT_IGNORE_PATTERNS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".eggs",
    "build",
    "dist",
}

# Default test file patterns
DEFAULT_TEST_PATTERNS = [
    "tests/test_{name}.py",
    "tests/{name}_test.py",
    "test_{name}.py",
    "{name}_test.py",
    "tests/{name}/test_{name}.py",
]


def find_test_file(source_path: Path, root: Path) -> bool:
    """Check if a test file exists for the given source file.

    Args:
        source_path: Path to source file
        root: Project root directory

    Returns:
        True if a test file exists
    """
    # Get relative path and module name
    try:
        rel_path = source_path.relative_to(root)
    except ValueError:
        rel_path = source_path

    # Extract module name (filename without extension)
    module_name = source_path.stem

    # Try various test file patterns
    for pattern in DEFAULT_TEST_PATTERNS:
        test_path = root / pattern.format(name=module_name)
        if test_path.exists():
            return True

    # Also check if file is in src/ and try tests/ directory
    if "src" in rel_path.parts:
        # Convert src/package/module.py -> tests/test_module.py
        test_path = root / "tests" / f"test_{module_name}.py"
        if test_path.exists():
            return True

        # Try maintaining directory structure
        # src/package/subpackage/module.py -> tests/package/subpackage/test_module.py
        parts = list(rel_path.parts)
        if parts[0] == "src":
            parts[0] = "tests"
            parts[-1] = f"test_{module_name}.py"
            test_path = root / Path(*parts)
            if test_path.exists():
                return True

    return False


def get_avg_complexity(file_data: dict[str, Any]) -> float:
    """Get average complexity for a file.

    Args:
        file_data: File analysis data

    Returns:
        Average complexity value
    """
    complexity_list = file_data.get("complexity", [])
    if not complexity_list:
        return 0.0

    total = sum(c.get("complexity", 0) for c in complexity_list)
    return float(total / len(complexity_list))

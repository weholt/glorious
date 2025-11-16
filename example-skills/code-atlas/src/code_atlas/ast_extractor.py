"""AST extraction utilities for code analysis."""

import ast
from typing import Any


class CallVisitor(ast.NodeVisitor):
    """AST visitor to track function calls within functions."""

    def __init__(self) -> None:
        """Initialize visitor."""
        self.current_func: str | None = None
        self.calls: dict[str, list[str]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self.current_func = node.name
        self.calls[node.name] = []
        self.generic_visit(node)
        self.current_func = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self.current_func = node.name
        self.calls[node.name] = []
        self.generic_visit(node)
        self.current_func = None

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call."""
        if self.current_func:
            # Extract called function name
            if isinstance(node.func, ast.Name):
                called = node.func.id
                if called not in self.calls[self.current_func]:
                    self.calls[self.current_func].append(called)
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
                if called not in self.calls[self.current_func]:
                    self.calls[self.current_func].append(called)
        self.generic_visit(node)


def extract_entities(tree: ast.AST) -> list[dict[str, Any]]:
    """Extract all classes and functions from AST.

    Args:
        tree: Parsed AST tree

    Returns:
        List of entity dicts with type, name, lineno, end_lineno, docstring
    """
    entities: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            bases = [ast.unparse(base) for base in node.bases]
            entities.append(
                {
                    "type": "class",
                    "name": node.name,
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node),
                    "methods": methods,
                    "bases": bases,
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Only capture top-level functions, not methods
            entity_type = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            entities.append(
                {
                    "type": entity_type,
                    "name": node.name,
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node),
                }
            )

    return entities


def extract_imports(tree: ast.AST) -> list[str]:
    """Extract all import statements from AST.

    Args:
        tree: Parsed AST tree

    Returns:
        List of imported module names
    """
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports

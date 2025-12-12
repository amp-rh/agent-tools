"""Shared AST parsing utilities for code analysis tools."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, TypeVar

__all__ = ["collect_py_files", "parse_file", "analyze_with_visitor"]

T = TypeVar("T")


def collect_py_files(path: Path) -> list[Path]:
    """Collect Python files from a path, filtering pycache and hidden directories.

    Args:
        path: File or directory to collect from

    Returns:
        List of Python file paths, sorted for consistent ordering
    """
    if path.is_file():
        return [path] if path.suffix == ".py" else []

    py_files = list(path.rglob("*.py"))
    return sorted(
        f for f in py_files
        if "__pycache__" not in str(f)
        and not any(p.startswith(".") for p in f.parts)
    )


def parse_file(path: Path) -> ast.Module | None:
    """Safely parse a Python file, returning None on error.

    Args:
        path: Path to the Python file

    Returns:
        Parsed AST module or None if parsing fails
    """
    try:
        source = path.read_text()
        return ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return None


def analyze_with_visitor(
    path: Path,
    visitor: ast.NodeVisitor,
    results_attr: str = "results",
) -> list[Any]:
    """Parse file and run AST visitor, returning collected items.

    Args:
        path: Path to the Python file
        visitor: An AST visitor instance with a results attribute
        results_attr: Name of the attribute on visitor that holds results

    Returns:
        List of results from the visitor, or empty list if parsing fails
    """
    tree = parse_file(path)
    if tree is None:
        return []

    visitor.visit(tree)
    return getattr(visitor, results_attr, [])


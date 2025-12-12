"""code.complexity: Analyze code complexity metrics for Python files."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from agent_tools.code._formatters import format_header, format_section
from agent_tools.code._parsers import collect_py_files, parse_file

__all__ = ["complexity"]


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""

    name: str
    file: str
    line: int
    cyclomatic: int
    lines: int
    max_depth: int
    params: int

    @property
    def score(self) -> int:
        """Overall complexity score combining all metrics."""
        score = self.cyclomatic
        if self.lines > 20:
            score += (self.lines - 20) // 10
        if self.max_depth > 3:
            score += (self.max_depth - 3) * 2
        if self.params > 4:
            score += (self.params - 4) * 2
        return score


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor that calculates complexity metrics."""

    def __init__(self) -> None:
        self.functions: list[FunctionMetrics] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._analyze_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._analyze_function(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        cyclomatic = _calculate_cyclomatic(node)
        lines = (node.end_lineno or node.lineno) - node.lineno + 1
        max_depth = _calculate_max_depth(node)
        params = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)

        self.functions.append(
            FunctionMetrics(
                name=node.name,
                file="",  # Set by caller
                line=node.lineno,
                cyclomatic=cyclomatic,
                lines=lines,
                max_depth=max_depth,
                params=params,
            )
        )
        self.generic_visit(node)


def _calculate_cyclomatic(node: ast.AST) -> int:
    """Calculate cyclomatic complexity (McCabe complexity)."""
    complexity = 1  # Base complexity

    for child in ast.walk(node):
        if isinstance(child, ast.If | ast.While | ast.For | ast.AsyncFor):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.And | ast.Or):
            complexity += 1
        elif isinstance(child, ast.comprehension):
            complexity += 1
            if child.ifs:
                complexity += len(child.ifs)
        elif isinstance(child, ast.Assert):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 2 if len(child.values) > 2 else 0

    return complexity


def _calculate_max_depth(node: ast.AST, depth: int = 0) -> int:
    """Calculate maximum nesting depth."""
    max_depth = depth
    nesting_types = (
        ast.If, ast.While, ast.For, ast.AsyncFor,
        ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler,
    )

    for child in ast.iter_child_nodes(node):
        if isinstance(child, nesting_types):
            child_depth = _calculate_max_depth(child, depth + 1)
        else:
            child_depth = _calculate_max_depth(child, depth)
        max_depth = max(max_depth, child_depth)

    return max_depth


def _analyze_file(file_path: Path) -> list[FunctionMetrics]:
    """Analyze a single Python file for complexity."""
    tree = parse_file(file_path)
    if tree is None:
        return []

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    for func in visitor.functions:
        func.file = str(file_path)

    return visitor.functions


def _format_issues(func: FunctionMetrics) -> list[str]:
    """Format specific issues for a function."""
    issues = []
    if func.cyclomatic > 5:
        issues.append(f"cyclomatic complexity {func.cyclomatic} (target: ≤5)")
    if func.lines > 20:
        issues.append(f"{func.lines} lines (target: ≤20)")
    if func.max_depth > 3:
        issues.append(f"nesting depth {func.max_depth} (target: ≤3)")
    if func.params > 4:
        issues.append(f"{func.params} parameters (target: ≤4)")
    return issues


def _collect_metrics(path: Path) -> tuple[list[FunctionMetrics], int]:
    """Collect all function metrics from a path.

    Returns:
        Tuple of (all_functions, file_count)
    """
    py_files = collect_py_files(path)
    all_functions: list[FunctionMetrics] = []

    for py_file in py_files:
        all_functions.extend(_analyze_file(py_file))

    return all_functions, len(py_files)


def _group_by_severity(
    functions: list[FunctionMetrics], threshold: int
) -> tuple[list[FunctionMetrics], list[FunctionMetrics], list[FunctionMetrics]]:
    """Group functions by severity: high (>=10), medium (5-9), low (<5)."""
    filtered = [f for f in functions if f.score >= threshold]
    filtered.sort(key=lambda f: f.score, reverse=True)

    high = [f for f in filtered if f.score >= 10]
    medium = [f for f in filtered if 5 <= f.score < 10]
    low = [f for f in filtered if f.score < 5]

    return high, medium, low


def _format_high_complexity(functions: list[FunctionMetrics]) -> list[str]:
    """Format high complexity functions for output."""
    lines = ["These functions should be refactored as a priority:", ""]
    for func in functions:
        rel_path = Path(func.file).name
        lines.append(f"### `{func.name}` in `{rel_path}` (line {func.line})")
        lines.append(f"**Score: {func.score}**")
        lines.append("")
        issues = _format_issues(func)
        if issues:
            lines.append("Issues:")
            for issue in issues:
                lines.append(f"- {issue}")
        lines.append("")
    return lines


def _format_medium_complexity(functions: list[FunctionMetrics]) -> list[str]:
    """Format medium complexity functions for output."""
    lines = []
    for func in functions:
        rel_path = Path(func.file).name
        issues = _format_issues(func)
        issue_str = ", ".join(issues) if issues else "moderate complexity"
        lines.append(f"- `{func.name}` in `{rel_path}` (line {func.line}): {issue_str}")
    return lines


def _format_low_complexity(functions: list[FunctionMetrics]) -> list[str]:
    """Format low complexity functions for output."""
    lines = []
    for func in functions:
        rel_path = Path(func.file).name
        lines.append(f"- `{func.name}` in `{rel_path}` (line {func.line}): score {func.score}")
    return lines


def _format_recommendations(
    high: list[FunctionMetrics],
    all_filtered: list[FunctionMetrics],
) -> list[str]:
    """Generate recommendations based on found issues."""
    lines = []
    if high:
        lines.append("- **High priority**: Break down complex functions using Extract Method")
        lines.append("- Consider replacing conditionals with polymorphism or strategy pattern")
    if any(f.params > 4 for f in all_filtered):
        lines.append("- Use parameter objects or builder pattern for many parameters")
    if any(f.max_depth > 3 for f in all_filtered):
        lines.append("- Reduce nesting with early returns (guard clauses)")
    if any(f.lines > 30 for f in all_filtered):
        lines.append("- Extract helper functions to reduce function length")
    return lines


def complexity(path: str, threshold: int = None) -> str:
    """Analyze code complexity metrics for Python files.

    Args:
        path: Directory or file to analyze
        threshold: Minimum complexity score to include in results (default: 1)

    Returns:
        Functions ranked by complexity with specific recommendations.
    """
    threshold = threshold if threshold is not None else 1
    target = Path(path)

    if not target.exists():
        return f"Error: Path not found: {path}"

    all_functions, file_count = _collect_metrics(target)

    if file_count == 0:
        return f"No Python files found in {path}"

    lines = [format_header("Complexity Analysis", path, file_count, len(all_functions))]

    high, medium, low = _group_by_severity(all_functions, threshold)
    all_filtered = high + medium + low

    if not all_filtered:
        if threshold > 1:
            lines.append(f"No functions found with complexity score ≥ {threshold}.")
            lines.append("All functions are below threshold.")
        else:
            lines.append("No complexity issues found.")
        return "\n".join(lines)

    if high:
        high_content = _format_high_complexity(high)
        lines.append(format_section("High Complexity (score ≥ 10)", high_content))

    if medium:
        medium_content = _format_medium_complexity(medium)
        lines.append(format_section("Medium Complexity (score 5-9)", medium_content))

    if low and threshold < 5:
        low_content = _format_low_complexity(low)
        lines.append(format_section("Low Complexity (score < 5)", low_content))

    recommendations = _format_recommendations(high, all_filtered)
    if recommendations:
        lines.append(format_section("Recommendations", recommendations))

    return "\n".join(lines)

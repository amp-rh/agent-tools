"""code.analyze: Comprehensive code quality analysis."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from agent_tools.code._formatters import format_header, format_section
from agent_tools.code._parsers import collect_py_files, parse_file

__all__ = ["analyze"]


@dataclass
class NamingIssue:
    """A naming convention issue."""

    name: str
    file: str
    line: int
    issue_type: str
    suggestion: str


class NamingVisitor(ast.NodeVisitor):
    """AST visitor that checks naming conventions."""

    def __init__(self) -> None:
        self.issues: list[NamingIssue] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._check_function_name(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._check_function_name(node)
        self.generic_visit(node)

    def _check_function_name(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        name = node.name

        # Skip magic methods
        if name.startswith("__") and name.endswith("__"):
            return

        # Check for single-letter names
        if len(name) == 1 and name not in {"_"}:
            self.issues.append(
                NamingIssue(
                    name=name,
                    file="",
                    line=node.lineno,
                    issue_type="too_short",
                    suggestion="Use a descriptive name that explains the function's purpose",
                )
            )

        # Check for camelCase (should be snake_case in Python)
        if re.match(r"^[a-z]+[A-Z]", name) and "_" not in name:
            self.issues.append(
                NamingIssue(
                    name=name,
                    file="",
                    line=node.lineno,
                    issue_type="camel_case",
                    suggestion=f"Use snake_case: {_to_snake_case(name)}",
                )
            )


def _to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    result = re.sub(r"([A-Z])", r"_\1", name)
    return result.lower().lstrip("_")


def _analyze_naming(file_path: Path) -> list[NamingIssue]:
    """Analyze naming conventions in a Python file."""
    tree = parse_file(file_path)
    if tree is None:
        return []

    visitor = NamingVisitor()
    visitor.visit(tree)

    for issue in visitor.issues:
        issue.file = str(file_path)

    return visitor.issues


def _format_naming_report(issues: list[NamingIssue]) -> list[str]:
    """Format naming issues as markdown lines."""
    if not issues:
        return []

    lines = []
    by_type: dict[str, list[NamingIssue]] = {}
    for issue in issues:
        by_type.setdefault(issue.issue_type, []).append(issue)

    if "too_short" in by_type:
        lines.append("### Single-Letter Names")
        lines.append("")
        lines.append("Function names should be descriptive:")
        lines.append("")
        for issue in by_type["too_short"]:
            rel_path = Path(issue.file).name
            lines.append(f"- `{issue.name}` in `{rel_path}` (line {issue.line})")
        lines.append("")

    if "camel_case" in by_type:
        lines.append("### CamelCase Instead of snake_case")
        lines.append("")
        lines.append("Python conventions prefer snake_case for functions:")
        lines.append("")
        for issue in by_type["camel_case"]:
            rel_path = Path(issue.file).name
            lines.append(
                f"- `{issue.name}` in `{rel_path}` (line {issue.line}): "
                f"{issue.suggestion}"
            )
        lines.append("")

    return lines


def _run_complexity_analysis(path: str) -> tuple[str, bool, list[str]]:
    """Run complexity analysis and return (output, has_issues, recommendations)."""
    from agent_tools.code.complexity import complexity

    result = complexity(path)
    has_issues = "High Complexity" in result or "Medium Complexity" in result

    lines = []
    recommendations = []

    if has_issues:
        for line in result.split("\n"):
            if line.startswith("# ") or line.startswith("Analyzed "):
                continue
            lines.append(line)

        if "High Complexity" in result:
            recommendations.append(
                "Break down complex functions using Extract Method refactoring"
            )

    return "\n".join(lines), has_issues, recommendations


def _run_architecture_analysis(path: str) -> tuple[str, bool, list[str]]:
    """Run architecture analysis and return (output, has_issues, recommendations)."""
    from agent_tools.code.architecture import architecture

    result = architecture(path)
    has_issues = "Circular Dependencies" in result or "Layer Violations" in result

    lines = []
    recommendations = []

    if has_issues:
        for line in result.split("\n"):
            if line.startswith("# ") or line.startswith("Analyzed "):
                continue
            lines.append(line)

        if "Circular" in result:
            recommendations.append(
                "Break circular dependencies by introducing interfaces"
            )
        if "Layer Violation" in result:
            recommendations.append(
                "Apply dependency inversion to fix layer violations"
            )

    return "\n".join(lines), has_issues, recommendations


def _run_naming_analysis(py_files: list[Path]) -> tuple[list[str], bool, list[str]]:
    """Run naming analysis and return (output_lines, has_issues, recommendations)."""
    all_issues: list[NamingIssue] = []
    for py_file in py_files:
        all_issues.extend(_analyze_naming(py_file))

    lines = _format_naming_report(all_issues)
    recommendations = []

    if all_issues:
        if any(i.issue_type == "too_short" for i in all_issues):
            recommendations.append("Use descriptive names that explain purpose")
        if any(i.issue_type == "camel_case" for i in all_issues):
            recommendations.append(
                "Follow Python naming conventions (snake_case for functions)"
            )

    return lines, bool(all_issues), recommendations


def analyze(path: str, focus: str = None) -> str:
    """Comprehensive code quality analysis combining multiple analyzers.

    Args:
        path: Directory or file to analyze
        focus: Focus area: complexity, architecture, naming, or all (default: all)

    Returns:
        Comprehensive report with prioritized recommendations.
    """
    focus = focus or "all"
    target = Path(path)

    if not target.exists():
        return f"Error: Path not found: {path}"

    py_files = collect_py_files(target)

    if not py_files:
        return f"No Python files found in {path}"

    lines = [format_header("Code Analysis", path, len(py_files))]
    issues_found = False
    all_recommendations: list[str] = []

    # Run complexity analysis
    if focus in ("complexity", "all"):
        output, has_issues, recs = _run_complexity_analysis(path)
        if has_issues:
            issues_found = True
            lines.append(format_section("Complexity Analysis", [output]))
            all_recommendations.extend(recs)

    # Run architecture analysis
    if focus in ("architecture", "all"):
        output, has_issues, recs = _run_architecture_analysis(path)
        if has_issues:
            issues_found = True
            lines.append(format_section("Architecture Analysis", [output]))
            all_recommendations.extend(recs)

    # Run naming analysis
    if focus in ("naming", "all"):
        output_lines, has_issues, recs = _run_naming_analysis(py_files)
        if has_issues:
            issues_found = True
            lines.append(format_section("Naming Convention Issues", output_lines))
            all_recommendations.extend(recs)

    # Summary
    lines.append("## Summary")
    lines.append("")

    if not issues_found:
        lines.append("No major code quality issues found. The codebase looks clean!")
    else:
        lines.append("### Recommendations")
        lines.append("")
        for i, rec in enumerate(all_recommendations, 1):
            lines.append(f"{i}. {rec}")

    return "\n".join(lines)

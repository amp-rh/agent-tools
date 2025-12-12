"""code.analyze: Comprehensive code quality analysis."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

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

    def __init__(self):
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

        # Check for single-letter names (except common ones like i, j, k, x, y)
        if len(name) == 1 and name not in {"_"}:
            self.issues.append(
                NamingIssue(
                    name=name,
                    file="",  # Set by caller
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
                    suggestion=f"Use snake_case: {self._to_snake_case(name)}",
                )
            )

    def _to_snake_case(self, name: str) -> str:
        """Convert camelCase to snake_case."""
        result = re.sub(r"([A-Z])", r"_\1", name)
        return result.lower().lstrip("_")


def _analyze_naming(file_path: Path) -> list[NamingIssue]:
    """Analyze naming conventions in a Python file."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []

    visitor = NamingVisitor()
    visitor.visit(tree)

    for issue in visitor.issues:
        issue.file = str(file_path)

    return visitor.issues


def _format_naming_report(issues: list[NamingIssue]) -> list[str]:
    """Format naming issues as markdown."""
    if not issues:
        return ["No naming convention issues found."]

    lines = []
    lines.append("## Naming Convention Issues")
    lines.append("")

    by_type = {}
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


def analyze(path: str, focus: str = None) -> str:
    """
    Comprehensive code quality analysis combining multiple analyzers.

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

    # Collect all Python files
    if target.is_file():
        py_files = [target] if target.suffix == ".py" else []
    else:
        py_files = list(target.rglob("*.py"))
        py_files = [
            f for f in py_files
            if "__pycache__" not in str(f)
            and not any(p.startswith(".") for p in f.parts)
        ]

    if not py_files:
        return f"No Python files found in {path}"

    file_count = len(py_files)
    lines = [
        f"# Code Analysis: {path}",
        "",
        f"Analyzed {file_count} file{'s' if file_count != 1 else ''}.",
        "",
    ]

    issues_found = False
    recommendations = []

    # Run complexity analysis
    if focus in ("complexity", "all"):
        from agent_tools.code.complexity import complexity

        complexity_result = complexity(path)

        # Check if there are actual issues
        has_complexity_issues = (
            "High Complexity" in complexity_result
            or "Medium Complexity" in complexity_result
        )

        if has_complexity_issues:
            issues_found = True
            lines.append("## Complexity Analysis")
            lines.append("")
            # Extract just the issue sections, not the full header
            for line in complexity_result.split("\n"):
                if line.startswith("# ") or line.startswith("Analyzed "):
                    continue
                lines.append(line)
            lines.append("")

            if "High Complexity" in complexity_result:
                recommendations.append(
                    "Break down complex functions using Extract Method refactoring"
                )

    # Run architecture analysis
    if focus in ("architecture", "all"):
        from agent_tools.code.architecture import architecture

        arch_result = architecture(path)

        # Check if there are actual issues
        has_arch_issues = (
            "Circular Dependencies" in arch_result or "Layer Violations" in arch_result
        )

        if has_arch_issues:
            issues_found = True
            lines.append("## Architecture Analysis")
            lines.append("")
            for line in arch_result.split("\n"):
                if line.startswith("# ") or line.startswith("Analyzed "):
                    continue
                lines.append(line)
            lines.append("")

            if "Circular" in arch_result:
                recommendations.append(
                    "Break circular dependencies by introducing interfaces"
                )
            if "Layer Violation" in arch_result:
                recommendations.append(
                    "Apply dependency inversion to fix layer violations"
                )

    # Run naming analysis
    if focus in ("naming", "all"):
        all_naming_issues: list[NamingIssue] = []
        for py_file in py_files:
            all_naming_issues.extend(_analyze_naming(py_file))

        if all_naming_issues:
            issues_found = True
            lines.extend(_format_naming_report(all_naming_issues))

            if any(i.issue_type == "too_short" for i in all_naming_issues):
                recommendations.append(
                    "Use descriptive names that explain purpose"
                )
            if any(i.issue_type == "camel_case" for i in all_naming_issues):
                recommendations.append(
                    "Follow Python naming conventions (snake_case for functions)"
                )

    # Summary and recommendations
    lines.append("## Summary")
    lines.append("")

    if not issues_found:
        lines.append("No major code quality issues found. The codebase looks clean!")
    else:
        lines.append("### Recommendations")
        lines.append("")
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")

    return "\n".join(lines)


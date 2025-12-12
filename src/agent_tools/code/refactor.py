"""code.refactor: Comprehensive refactoring analysis chain."""
from __future__ import annotations

import ast
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["refactor"]


@dataclass
class RefactorIssue:
    """A refactoring issue with priority."""

    category: str
    priority: int  # 1=critical, 2=major, 3=minor
    title: str
    description: str
    file: str
    line: int
    recommendation: str
    details: list[str] = field(default_factory=list)


def _hash_function_body(node: ast.FunctionDef) -> str:
    """Create a hash of function body for duplicate detection."""
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]  # Skip docstring

    if not body:
        return ""

    normalized = ast.dump(ast.Module(body=body, type_ignores=[]))
    return hashlib.md5(normalized.encode()).hexdigest()[:8]


def _extract_functions(file_path: Path) -> list[dict]:
    """Extract function info from a Python file."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "file": str(file_path),
                "line": node.lineno,
                "body_hash": _hash_function_body(node),
                "num_lines": (node.end_lineno or node.lineno) - node.lineno + 1,
            })
    return functions


def _find_duplicates(functions: list[dict]) -> dict[str, list[dict]]:
    """Find functions with identical bodies across files."""
    by_hash = defaultdict(list)
    for func in functions:
        if func["body_hash"]:
            by_hash[func["body_hash"]].append(func)

    duplicates = {}
    for hash_val, funcs in by_hash.items():
        files = set(f["file"] for f in funcs)
        if len(files) > 1:
            duplicates[hash_val] = funcs

    return duplicates


def _find_same_name_functions(functions: list[dict]) -> dict[str, list[dict]]:
    """Find functions with the same name in different files."""
    by_name = defaultdict(list)
    for func in functions:
        by_name[func["name"]].append(func)

    same_name = {}
    for name, funcs in by_name.items():
        files = set(f["file"] for f in funcs)
        if len(files) > 1:
            same_name[name] = funcs

    return same_name


def _collect_py_files(path: Path) -> list[Path]:
    """Collect Python files from path, excluding __pycache__ and hidden dirs."""
    if path.is_file():
        return [path] if path.suffix == ".py" else []

    py_files = list(path.rglob("*.py"))
    return [
        f for f in py_files
        if "__pycache__" not in str(f)
        and not any(p.startswith(".") for p in f.parts)
    ]


def _analyze_duplication(
    py_files: list[Path], all_functions: list[dict]
) -> list[RefactorIssue]:
    """Analyze for code duplication issues."""
    issues = []

    duplicates = _find_duplicates(all_functions)
    for hash_val, funcs in duplicates.items():
        first = funcs[0]
        details = [
            f"`{f['name']}` in `{Path(f['file']).name}` (line {f['line']})"
            for f in funcs
        ]
        issues.append(RefactorIssue(
            category="duplication",
            priority=2,
            title=f"Duplicate function bodies (hash: {hash_val})",
            description=f"{len(funcs)} functions have identical implementations",
            file=first["file"],
            line=first["line"],
            recommendation="Extract to a shared module and import",
            details=details,
        ))

    same_name = _find_same_name_functions(all_functions)
    dup_funcs = {f["name"] for group in duplicates.values() for f in group}
    same_name = {k: v for k, v in same_name.items() if k not in dup_funcs}

    for name, funcs in same_name.items():
        first = funcs[0]
        details = [
            f"`{Path(f['file']).name}` line {f['line']} ({f['num_lines']} lines)"
            for f in funcs
        ]
        issues.append(RefactorIssue(
            category="duplication",
            priority=3,
            title=f"Same-name function: `{name}`",
            description=f"{len(funcs)} functions share this name with different impls",
            file=first["file"],
            line=first["line"],
            recommendation="Consolidate if same purpose, or rename for clarity",
            details=details,
        ))

    return issues


def _analyze_complexity(path: str) -> list[RefactorIssue]:
    """Run complexity analysis and convert to issues."""
    from agent_tools.code.complexity import complexity

    issues = []
    result = complexity(path)

    # Parse the complexity output to extract high/medium issues
    current_section = None  # "high", "medium", or None
    current_func = None
    current_file = None
    current_line = None
    current_details = []

    def save_high_complexity_issue():
        if current_func:
            issues.append(RefactorIssue(
                category="complexity",
                priority=1,
                title=f"High complexity: `{current_func}`",
                description="Function is too complex",
                file=current_file or "",
                line=current_line or 0,
                recommendation="Break down using Extract Method refactoring",
                details=current_details.copy(),
            ))

    for line in result.split("\n"):
        if "## High Complexity" in line:
            current_section = "high"
        elif "## Medium Complexity" in line:
            # Save any pending high complexity issue
            save_high_complexity_issue()
            current_section = "medium"
            current_func = None
            current_details = []
        elif "## Low Complexity" in line or "## Recommendations" in line:
            # Save any pending high complexity issue
            if current_section == "high":
                save_high_complexity_issue()
            current_section = None
            current_func = None
            current_details = []
        elif current_section == "high" and line.startswith("### "):
            # Save previous high complexity issue if any
            save_high_complexity_issue()

            # Parse: ### `func_name` in `file.py` (line N)
            current_details = []
            try:
                parts = line.replace("### `", "").split("`")
                current_func = parts[0] if parts else None
                current_file = parts[2] if len(parts) > 2 else None
                current_line = None
                if "(line " in line:
                    current_line = int(line.split("(line ")[1].split(")")[0])
            except (IndexError, ValueError):
                current_func = None
        elif current_section == "high" and line.startswith("- "):
            current_details.append(line[2:])
        elif current_section == "medium" and line.startswith("- `"):
            # Parse medium complexity: - `func` in `file` (line N): issues
            try:
                parts = line.replace("- `", "").split("`")
                func_name = parts[0] if parts else "unknown"
                file_name = parts[2] if len(parts) > 2 else ""
                line_num = 0
                if "(line " in line:
                    line_num = int(line.split("(line ")[1].split(")")[0])
                issue_text = line.split("): ")[1] if "): " in line else ""
                issues.append(RefactorIssue(
                    category="complexity",
                    priority=2,
                    title=f"Medium complexity: `{func_name}`",
                    description=issue_text or "Moderate complexity",
                    file=file_name,
                    line=line_num,
                    recommendation="Consider simplifying",
                    details=[],
                ))
            except (IndexError, ValueError):
                pass

    # Don't forget the last high-complexity function
    if current_section == "high":
        save_high_complexity_issue()

    return issues


def _analyze_architecture(path: str) -> list[RefactorIssue]:
    """Run architecture analysis and convert to issues."""
    from agent_tools.code.architecture import architecture

    issues = []
    result = architecture(path)

    if "Circular Dependencies" in result:
        # Extract circular dependency info
        in_circular = False
        for line in result.split("\n"):
            if "## Circular Dependencies" in line:
                in_circular = True
            elif line.startswith("## "):
                in_circular = False
            elif in_circular and line.startswith("- "):
                cycle = line[2:]
                issues.append(RefactorIssue(
                    category="architecture",
                    priority=1,
                    title="Circular dependency",
                    description=cycle,
                    file="",
                    line=0,
                    recommendation="Break cycle with interfaces or shared module",
                    details=[],
                ))

    if "Layer Violations" in result:
        in_violations = False
        for line in result.split("\n"):
            if "## Layer Violations" in line:
                in_violations = True
            elif line.startswith("## "):
                in_violations = False
            elif in_violations and line.startswith("- `"):
                issues.append(RefactorIssue(
                    category="architecture",
                    priority=2,
                    title="Layer violation",
                    description=line[2:],
                    file="",
                    line=0,
                    recommendation="Apply dependency inversion",
                    details=[],
                ))

    return issues


def _format_issues_by_priority(issues: list[RefactorIssue]) -> list[str]:
    """Format issues grouped by priority."""
    lines = []

    priority_names = {
        1: "Priority 1: Critical Issues",
        2: "Priority 2: Major Issues",
        3: "Priority 3: Minor Issues",
    }

    for priority in [1, 2, 3]:
        priority_issues = [i for i in issues if i.priority == priority]
        if not priority_issues:
            continue

        lines.append(f"## {priority_names[priority]}")
        lines.append("")

        # Group by category within priority
        by_category = defaultdict(list)
        for issue in priority_issues:
            by_category[issue.category].append(issue)

        for category, cat_issues in by_category.items():
            lines.append(f"### {category.title()}")
            lines.append("")

            for issue in cat_issues:
                lines.append(f"**{issue.title}**")
                if issue.description:
                    lines.append(f"  {issue.description}")
                if issue.details:
                    for detail in issue.details:
                        lines.append(f"  - {detail}")
                lines.append(f"  *Recommendation*: {issue.recommendation}")
                lines.append("")

    return lines


def _generate_action_items(issues: list[RefactorIssue]) -> list[str]:
    """Generate prioritized action items."""
    lines = ["## Recommended Actions", ""]

    actions = []

    # Count by category and priority
    critical_complexity = sum(
        1 for i in issues if i.category == "complexity" and i.priority == 1
    )
    circular_deps = sum(
        1 for i in issues if i.category == "architecture" and "Circular" in i.title
    )
    duplicates = sum(
        1 for i in issues if i.category == "duplication" and "Duplicate" in i.title
    )

    if circular_deps:
        actions.append(
            f"1. **Break {circular_deps} circular dependencies** - "
            "Introduce interfaces or move shared code"
        )
    if critical_complexity:
        actions.append(
            f"2. **Refactor {critical_complexity} high-complexity functions** - "
            "Use Extract Method to break down"
        )
    if duplicates:
        actions.append(
            f"3. **Consolidate {duplicates} duplicate function groups** - "
            "Extract to shared utilities"
        )

    if not actions:
        lines.append("No critical refactoring actions needed.")
    else:
        lines.extend(actions)

    return lines


def refactor(path: str, focus: str = None) -> str:
    """
    Comprehensive code refactoring analysis chain.

    Combines duplication, complexity, and architecture analysis to produce
    a prioritized refactoring plan.

    Args:
        path: Directory or file to analyze
        focus: 'duplication', 'complexity', 'architecture', or 'all' (default)

    Returns:
        Prioritized refactoring plan with specific recommendations.
    """
    focus = focus or "all"
    target = Path(path)

    if not target.exists():
        return f"Error: Path not found: {path}"

    py_files = _collect_py_files(target)
    if not py_files:
        return f"No Python files found in {path}"

    # Extract functions for duplication analysis
    all_functions = []
    for py_file in py_files:
        all_functions.extend(_extract_functions(py_file))

    lines = [
        f"# Refactoring Plan: {path}",
        "",
        f"Analyzed {len(py_files)} files, {len(all_functions)} functions.",
        "",
    ]

    all_issues: list[RefactorIssue] = []

    # Run analyses based on focus
    if focus in ("duplication", "all"):
        all_issues.extend(_analyze_duplication(py_files, all_functions))

    if focus in ("complexity", "all"):
        all_issues.extend(_analyze_complexity(path))

    if focus in ("architecture", "all"):
        all_issues.extend(_analyze_architecture(path))

    if not all_issues:
        lines.append("No refactoring opportunities found.")
        lines.append("")
        lines.append("The codebase looks clean!")
        return "\n".join(lines)

    # Sort by priority
    all_issues.sort(key=lambda i: (i.priority, i.category))

    # Format output
    lines.extend(_format_issues_by_priority(all_issues))
    lines.extend(_generate_action_items(all_issues))

    return "\n".join(lines)

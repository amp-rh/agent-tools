"""code.refactor: Analyze code for refactoring opportunities and generate a plan."""
from __future__ import annotations

import ast
import hashlib
from collections import defaultdict
from pathlib import Path

__all__ = ["refactor"]


def _hash_function_body(node: ast.FunctionDef) -> str:
    """Create a hash of function body for duplicate detection."""
    # Normalize: strip docstrings and dump AST
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]  # Skip docstring

    if not body:
        return ""

    # Create a normalized string representation
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
        if func["body_hash"]:  # Skip empty functions
            by_hash[func["body_hash"]].append(func)

    # Only keep hashes that appear in multiple files
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

    # Only keep names that appear in multiple files
    same_name = {}
    for name, funcs in by_name.items():
        files = set(f["file"] for f in funcs)
        if len(files) > 1:
            same_name[name] = funcs

    return same_name


def refactor(path: str, focus: str = None) -> str:
    """
    Analyze code for refactoring opportunities and generate a refactoring plan.

    Args:
        path: Directory or file to analyze for refactoring
        focus: Specific focus area: 'duplication', 'complexity', 'dead-code', or 'all'

    Returns:
        Structured refactoring plan with specific recommendations.
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
        # Exclude __pycache__ and hidden dirs
        py_files = [
            f for f in py_files
            if "__pycache__" not in str(f)
            and not any(p.startswith(".") for p in f.parts)
        ]

    if not py_files:
        return f"No Python files found in {path}"

    # Extract all functions
    all_functions = []
    for py_file in py_files:
        all_functions.extend(_extract_functions(py_file))

    lines = [
        f"# Refactoring Analysis: {path}",
        "",
        f"Analyzed {len(py_files)} files, found {len(all_functions)} functions.",
        "",
    ]

    issues_found = False

    # Check for duplicates
    if focus in ("duplication", "all"):
        duplicates = _find_duplicates(all_functions)
        same_name = _find_same_name_functions(all_functions)

        if duplicates:
            issues_found = True
            lines.append("## Duplicate Function Bodies")
            lines.append("")
            lines.append(
                "These functions have identical implementations and should be consolidated:"
            )
            lines.append("")

            for hash_val, funcs in duplicates.items():
                lines.append(f"### Duplicate group (hash: {hash_val})")
                for f in funcs:
                    rel_path = Path(f["file"]).name
                    lines.append(f"- `{f['name']}` in `{rel_path}` (line {f['line']})")
                lines.append("")
                lines.append("**Recommendation**: Extract to a shared module and import.")
                lines.append("")

        if same_name:
            # Filter out ones already caught as duplicates
            dup_funcs = {f["name"] for group in duplicates.values() for f in group}
            same_name = {k: v for k, v in same_name.items() if k not in dup_funcs}

            if same_name:
                issues_found = True
                lines.append("## Same-Name Functions (Different Implementations)")
                lines.append("")
                lines.append(
                    "These functions share names but have different implementations. Consider:"
                )
                lines.append("- If they do the same thing: consolidate")
                lines.append("- If they're intentionally different: rename for clarity")
                lines.append("")

                for name, funcs in same_name.items():
                    lines.append(f"### `{name}`")
                    for f in funcs:
                        rel_path = Path(f["file"]).name
                        lines.append(f"- `{rel_path}` line {f['line']} ({f['num_lines']} lines)")
                    lines.append("")

    if not issues_found:
        lines.append("No refactoring opportunities found for the specified focus.")

    return "\n".join(lines)

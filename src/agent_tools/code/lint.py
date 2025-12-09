"""code.lint: Lint and auto-fix code issues in Python files."""
from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = ["lint"]


def lint(path: str = None, fix: bool = None) -> str:
    """
    Lint and auto-fix code issues in Python files.

    Args:
        path: File or directory to lint (defaults to current directory)
        fix: Auto-fix issues (default: true)

    Returns:
        Summary of issues found, fixed, and any remaining errors.
    """
    fix = fix if fix is not None else True
    target = path or "."

    # Verify path exists
    target_path = Path(target)
    if not target_path.exists():
        return f"Error: Path not found: {target}"

    # Build ruff command
    cmd = ["ruff", "check", target]
    if fix:
        cmd.extend(["--fix", "--unsafe-fixes"])

    # Run ruff
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    output_lines = []

    # Parse output
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode == 0:
        if "Fixed" in stdout or "fixed" in stdout:
            output_lines.append("## Linting Complete")
            output_lines.append("")
            output_lines.append(stdout)
            output_lines.append("")
            output_lines.append("**Status**: Fixed issues automatically")
        elif stdout == "All checks passed!":
            output_lines.append("## Linting Complete")
            output_lines.append("")
            output_lines.append("**Status**: Clean - no issues found")
        else:
            output_lines.append("## Linting Complete")
            output_lines.append("")
            output_lines.append("**Status**: Clean - no issues found")
    else:
        output_lines.append("## Linting Results")
        output_lines.append("")
        if stdout:
            output_lines.append(stdout)
        if stderr:
            output_lines.append(stderr)
        output_lines.append("")

        if fix:
            output_lines.append("**Status**: Some issues remain that require manual fixes")
        else:
            output_lines.append("**Status**: Issues found (run with fix=true to auto-fix)")

    return "\n".join(output_lines)

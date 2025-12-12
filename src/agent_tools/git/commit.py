"""git.commit: Commit changes to git with a conventional commit message."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

__all__ = ["commit"]


@dataclass
class CommitResult:
    """Result of a git commit operation."""

    success: bool
    message: str
    commit_hash: str = ""
    stdout: str = ""


def _build_commit_message(message: str, commit_type: str, scope: str | None) -> str:
    """Build a conventional commit message."""
    if scope:
        return f"{commit_type}({scope}): {message}"
    return f"{commit_type}: {message}"


def _parse_file_list(files: str | None) -> list[str]:
    """Parse a comma or space separated file list."""
    if not files:
        return []
    return [f.strip() for f in files.replace(",", " ").split() if f.strip()]


def _stage_files(files: str | None) -> tuple[bool, str]:
    """Stage files for commit.

    Returns:
        Tuple of (success, error_message)
    """
    file_list = _parse_file_list(files)

    if file_list:
        cmd = ["git", "add", "--"] + file_list
    else:
        cmd = ["git", "add", "-A"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            return False, f"Error staging files: {stderr}"
        return False, f"Error staging files (exit code {result.returncode})"

    return True, ""


def _execute_commit(full_message: str) -> CommitResult:
    """Execute the git commit command."""
    result = subprocess.run(
        ["git", "commit", "-m", full_message],
        capture_output=True,
        text=True,
    )

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        combined = f"{stdout} {stderr}".lower()
        if "nothing to commit" in combined or "no changes" in combined:
            return CommitResult(False, "Nothing to commit - working tree clean")
        if "not a git repository" in combined:
            return CommitResult(False, "Error: Not a git repository")
        return CommitResult(False, f"Error: {stderr or stdout or 'Unknown git error'}")

    commit_hash = _extract_commit_hash(stdout)
    return CommitResult(True, full_message, commit_hash, stdout)


def _extract_commit_hash(stdout: str) -> str:
    """Extract commit hash from git output like '[main abc1234] message'."""
    if not stdout or "]" not in stdout:
        return ""

    bracket_content = stdout.split("]")[0]
    parts = bracket_content.strip("[").split()
    if len(parts) >= 2:
        return parts[-1]
    return ""


def _format_success_output(result: CommitResult) -> str:
    """Format successful commit output."""
    lines = ["## Committed", ""]
    lines.append(f"**Message**: `{result.message}`")
    if result.commit_hash:
        lines.append(f"**Hash**: `{result.commit_hash}`")
    lines.extend(["", "```", result.stdout, "```"])
    return "\n".join(lines)


def commit(message: str, type: str = None, scope: str = None, files: str = None) -> str:
    """Commit changes to git with a conventional commit message.

    Stages files (all if not specified) and commits with format: <type>(<scope>): <message>

    Args:
        message: The commit message description (required)
        type: Commit type: feat, fix, refactor, docs, test, chore (default: feat)
        scope: Scope for conventional commit (e.g., registry, server, docs)
        files: Specific files to stage (space or comma separated). Default: all changes (-A)

    Returns:
        Result message describing what was done.
    """
    commit_type = type or "feat"
    full_message = _build_commit_message(message, commit_type, scope)

    # Stage files
    success, error = _stage_files(files)
    if not success:
        return error

    # Execute commit
    result = _execute_commit(full_message)
    if not result.success:
        return result.message

    return _format_success_output(result)

"""git.commit: Commit changes to git with a conventional commit message."""
from __future__ import annotations

import subprocess

__all__ = ["commit"]


def commit(message: str, type: str = None, scope: str = None, files: str = None) -> str:
    """
    Commit changes to git with a conventional commit message.

    Stages files (all if not specified) and commits with format: <type>(<scope>): <message>

    The agent should analyze changes and provide an appropriate message.
    This tool executes the commit.

    Args:
        message: The commit message description (required)
        type: Commit type: feat, fix, refactor, docs, test, chore (default: feat)
        scope: Scope for conventional commit (e.g., registry, server, docs)
        files: Specific files to stage (space or comma separated). Default: all changes (-A)

    Returns:
        Result message describing what was done.
    """
    commit_type = type or "feat"

    # Build conventional commit message
    if scope:
        full_message = f"{commit_type}({scope}): {message}"
    else:
        full_message = f"{commit_type}: {message}"

    # Stage files
    if files:
        # Parse files (comma or space separated)
        file_list = [f.strip() for f in files.replace(",", " ").split() if f.strip()]
        stage_cmd = ["git", "add", "--"] + file_list
    else:
        stage_cmd = ["git", "add", "-A"]

    stage_result = subprocess.run(
        stage_cmd,
        capture_output=True,
        text=True,
    )

    if stage_result.returncode != 0:
        stderr = stage_result.stderr.strip()
        if stderr:
            return f"Error staging files: {stderr}"
        return f"Error staging files (exit code {stage_result.returncode})"

    # Commit
    commit_cmd = ["git", "commit", "-m", full_message]
    commit_result = subprocess.run(
        commit_cmd,
        capture_output=True,
        text=True,
    )

    stdout = commit_result.stdout.strip()
    stderr = commit_result.stderr.strip()

    if commit_result.returncode != 0:
        # Check for "nothing to commit"
        combined = f"{stdout} {stderr}".lower()
        if "nothing to commit" in combined or "no changes" in combined:
            return "Nothing to commit - working tree clean"
        if "not a git repository" in combined:
            return "Error: Not a git repository"
        return f"Error: {stderr or stdout or 'Unknown git error'}"

    # Extract commit hash from output like "[main abc1234] message"
    commit_hash = ""
    if stdout:
        # Parse "[branch hash] message" format
        if "]" in stdout:
            bracket_content = stdout.split("]")[0]
            parts = bracket_content.strip("[").split()
            if len(parts) >= 2:
                commit_hash = parts[-1]

    lines = ["## Committed"]
    lines.append("")
    lines.append(f"**Message**: `{full_message}`")
    if commit_hash:
        lines.append(f"**Hash**: `{commit_hash}`")
    lines.append("")
    lines.append("```")
    lines.append(stdout)
    lines.append("```")

    return "\n".join(lines)

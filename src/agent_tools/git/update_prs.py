"""git.update-prs: Create or update a PR for the current branch."""
from __future__ import annotations

import subprocess

__all__ = ["update_prs"]


def update_prs(
    base: str = None,
    title: str = None,
    body: str = None,
    draft: bool = None,
) -> str:
    """
    Create or update a PR for the current branch.

    Pushes the current branch and creates or updates its associated PR using GitHub CLI.
    Requires `gh` CLI to be installed and authenticated.

    Args:
        base: Base branch for the PR (default: dev)
        title: PR title. If not provided, uses the branch name.
        body: PR body/description. Optional.
        draft: Create as draft PR (default: false)

    Returns:
        Summary of PR status and URL.
    """
    base = base or "dev"

    # Get current branch name
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Error: Could not determine current branch: {result.stderr}"

    branch = result.stdout.strip()
    if not branch:
        return "Error: Not on a branch (detached HEAD?)"

    # Push the branch
    push_result = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        capture_output=True,
        text=True,
    )
    if push_result.returncode != 0:
        stderr = push_result.stderr.strip()
        return f"Error pushing branch: {stderr}"

    # Check if PR already exists
    try:
        pr_view = subprocess.run(
            ["gh", "pr", "view", branch, "--json", "url", "--jq", ".url"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return "Error: `gh` CLI not found. Install it from https://cli.github.com/"

    if pr_view.returncode == 0 and pr_view.stdout.strip():
        # PR exists
        pr_url = pr_view.stdout.strip()
        lines = ["## PR Updated", "", f"**Branch**: `{branch}`", f"**URL**: {pr_url}", ""]
        lines.append("Pushed latest changes.")
        return "\n".join(lines)

    # Create new PR
    pr_title = title or branch.replace("-", " ").replace("/", ": ").title()
    cmd = ["gh", "pr", "create", "--base", base, "--title", pr_title]

    if body:
        cmd.extend(["--body", body])
    else:
        cmd.append("--fill")

    if draft:
        cmd.append("--draft")

    try:
        create_result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return "Error: `gh` CLI not found. Install it from https://cli.github.com/"

    if create_result.returncode != 0:
        stderr = create_result.stderr.strip()
        return f"Error creating PR: {stderr}"

    pr_url = create_result.stdout.strip()

    lines = [
        "## PR Created",
        "",
        f"**Branch**: `{branch}`",
        f"**Base**: `{base}`",
        f"**Title**: {pr_title}",
    ]

    if draft:
        lines.append("**Status**: Draft")

    lines.append(f"\n**URL**: {pr_url}")

    return "\n".join(lines)

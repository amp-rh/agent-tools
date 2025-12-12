"""git.update-prs: Create or update a PR for the current branch."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

__all__ = ["update_prs"]


@dataclass
class BranchInfo:
    """Information about the current branch."""

    name: str
    error: str = ""


@dataclass
class PRInfo:
    """Information about a PR."""

    url: str
    is_new: bool
    title: str = ""
    base: str = ""
    is_draft: bool = False


def _get_current_branch() -> BranchInfo:
    """Get the current git branch name."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return BranchInfo("", f"Could not determine current branch: {result.stderr}")

    branch = result.stdout.strip()
    if not branch:
        return BranchInfo("", "Not on a branch (detached HEAD?)")

    return BranchInfo(branch)


def _push_branch(branch: str) -> tuple[bool, str]:
    """Push the branch to origin.

    Returns:
        Tuple of (success, error_message)
    """
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, f"Error pushing branch: {result.stderr.strip()}"
    return True, ""


def _check_existing_pr(branch: str) -> tuple[str | None, str | None]:
    """Check if a PR already exists for the branch.

    Returns:
        Tuple of (pr_url or None, error or None)
    """
    try:
        result = subprocess.run(
            ["gh", "pr", "view", branch, "--json", "url", "--jq", ".url"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None, "Error: `gh` CLI not found. Install it from https://cli.github.com/"

    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip(), None

    return None, None


def _create_pr(
    branch: str,
    base: str,
    title: str | None,
    body: str | None,
    draft: bool,
) -> tuple[str | None, str | None]:
    """Create a new PR.

    Returns:
        Tuple of (pr_url or None, error or None)
    """
    pr_title = title or branch.replace("-", " ").replace("/", ": ").title()
    cmd = ["gh", "pr", "create", "--base", base, "--title", pr_title]

    if body:
        cmd.extend(["--body", body])
    else:
        cmd.append("--fill")

    if draft:
        cmd.append("--draft")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return None, "Error: `gh` CLI not found. Install it from https://cli.github.com/"

    if result.returncode != 0:
        return None, f"Error creating PR: {result.stderr.strip()}"

    return result.stdout.strip(), None


def _format_pr_updated(branch: str, url: str) -> str:
    """Format output for an updated PR."""
    lines = ["## PR Updated", "", f"**Branch**: `{branch}`", f"**URL**: {url}", ""]
    lines.append("Pushed latest changes.")
    return "\n".join(lines)


def _format_pr_created(pr: PRInfo, branch: str) -> str:
    """Format output for a newly created PR."""
    lines = [
        "## PR Created",
        "",
        f"**Branch**: `{branch}`",
        f"**Base**: `{pr.base}`",
        f"**Title**: {pr.title}",
    ]
    if pr.is_draft:
        lines.append("**Status**: Draft")
    lines.append(f"\n**URL**: {pr.url}")
    return "\n".join(lines)


def update_prs(
    base: str = None,
    title: str = None,
    body: str = None,
    draft: bool = None,
) -> str:
    """Create or update a PR for the current branch.

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

    # Get current branch
    branch_info = _get_current_branch()
    if branch_info.error:
        return f"Error: {branch_info.error}"

    branch = branch_info.name

    # Push branch
    success, error = _push_branch(branch)
    if not success:
        return error

    # Check for existing PR
    existing_url, gh_error = _check_existing_pr(branch)
    if gh_error:
        return gh_error
    if existing_url:
        return _format_pr_updated(branch, existing_url)

    # Create new PR
    pr_url, create_error = _create_pr(branch, base, title, body, draft or False)
    if create_error:
        return create_error

    pr_title = title or branch.replace("-", " ").replace("/", ": ").title()
    pr_info = PRInfo(
        url=pr_url or "",
        is_new=True,
        title=pr_title,
        base=base,
        is_draft=draft or False,
    )

    return _format_pr_created(pr_info, branch)

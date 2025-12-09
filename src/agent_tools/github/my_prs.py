"""github.my-prs: List your open pull requests across all repositories."""
from __future__ import annotations

import json
import os

from agent_tools.mcp.call import call_external_sync

__all__ = ["my_prs"]


def my_prs(state: str = None, limit: int = None) -> str:
    """
    List your open pull requests across all repositories.

    Requires GITHUB_USERNAME environment variable to be set.

    Args:
        state: PR state: 'open' (default), 'closed', or 'all'
        limit: Maximum number of PRs to return (default: 20)

    Returns:
        Formatted list of PRs.
    """
    username = os.environ.get("GITHUB_USERNAME")
    if not username:
        return "Error: GITHUB_USERNAME environment variable is not set."

    state = state or "open"
    limit = limit or 20

    query = f"is:pr is:{state} author:{username}"

    # Call the external github server
    result = call_external_sync("github", "search_issues", q=query)

    if result.startswith("Error"):
        return result

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return f"Error parsing response: {result[:200]}"

    total = data.get("total_count", 0)
    items = data.get("items", [])[:limit]

    if not items:
        return f"No {state} PRs found for {username}."

    lines = [
        f"## Your {state.title()} PRs ({total} total)",
        "",
    ]

    for pr in items:
        title = pr.get("title", "Untitled")
        url = pr.get("html_url", "")
        repo_url = pr.get("repository_url", "")
        repo = "/".join(repo_url.split("/")[-2:]) if repo_url else "unknown"
        created = pr.get("created_at", "")[:10]
        draft = " [DRAFT]" if pr.get("draft") else ""

        lines.append(f"### [{title}]({url}){draft}")
        lines.append(f"- **Repo**: {repo}")
        lines.append(f"- **Created**: {created}")
        lines.append("")

    return "\n".join(lines)

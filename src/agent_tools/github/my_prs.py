"""github.my-prs: List your open pull requests across all repositories."""
from __future__ import annotations

import json
import os

from agent_tools.mcp.call import call_external_sync

__all__ = ["my_prs"]

# GitHub username - can be overridden via env var
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "amp-rh")


def my_prs(state: str = None, limit: int = None) -> str:
    """
    List your open pull requests across all repositories.

    Args:
        state: PR state: 'open' (default), 'closed', or 'all'
        limit: Maximum number of PRs to return (default: 20)

    Returns:
        Formatted list of PRs.
    """
    state = state or "open"
    limit = limit or 20

    # Build search query
    query = f"is:pr is:{state} author:{GITHUB_USERNAME}"

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
        return f"No {state} PRs found for {GITHUB_USERNAME}."

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

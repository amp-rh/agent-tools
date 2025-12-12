"""Shared markdown formatting utilities for code analysis reports."""
from __future__ import annotations

from typing import Any

__all__ = ["format_header", "format_section", "format_issue_list", "group_by_severity"]


def format_header(
    title: str,
    path: str,
    file_count: int | None = None,
    func_count: int | None = None,
) -> str:
    """Format a report header with title and stats.

    Args:
        title: Report title (e.g., "Complexity Analysis")
        path: Path being analyzed
        file_count: Number of files analyzed
        func_count: Number of functions found

    Returns:
        Formatted markdown header
    """
    lines = [f"# {title}: {path}", ""]

    if file_count is not None:
        file_word = "file" if file_count == 1 else "files"
        stats = f"Analyzed {file_count} {file_word}"
        if func_count is not None:
            func_word = "function" if func_count == 1 else "functions"
            stats += f", found {func_count} {func_word}"
        stats += "."
        lines.append(stats)
        lines.append("")

    return "\n".join(lines)


def group_by_severity(
    items: list[dict[str, Any]],
    score_key: str = "score",
    high_threshold: int = 10,
    medium_threshold: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """Group items by severity based on score.

    Args:
        items: List of items with score values
        score_key: Key to use for score lookup
        high_threshold: Score >= this is "high"
        medium_threshold: Score >= this is "medium", else "low"

    Returns:
        Dict with "high", "medium", "low" keys containing grouped items
    """
    result: dict[str, list[dict[str, Any]]] = {"high": [], "medium": [], "low": []}

    for item in items:
        score = item.get(score_key, 0)
        if score >= high_threshold:
            result["high"].append(item)
        elif score >= medium_threshold:
            result["medium"].append(item)
        else:
            result["low"].append(item)

    return result


def format_section(
    heading: str,
    items: list[str],
    description: str | None = None,
    level: int = 2,
) -> str:
    """Format a markdown section with heading and items.

    Args:
        heading: Section heading text
        items: Lines to include in the section
        description: Optional description after heading
        level: Heading level (default: 2 for ##)

    Returns:
        Formatted markdown section, or empty string if no items
    """
    if not items:
        return ""

    prefix = "#" * level
    lines = [f"{prefix} {heading}", ""]

    if description:
        lines.append(description)
        lines.append("")

    lines.extend(items)
    lines.append("")

    return "\n".join(lines)


def format_issue_list(issues: list[str], prefix: str = "- ") -> str:
    """Format a list of issues as markdown bullet points.

    Args:
        issues: List of issue strings
        prefix: Prefix for each item (default: "- ")

    Returns:
        Formatted list, or empty string if no issues
    """
    if not issues:
        return ""

    return "\n".join(f"{prefix}{issue}" for issue in issues)


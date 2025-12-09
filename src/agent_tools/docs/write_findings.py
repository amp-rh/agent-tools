"""docs.write-findings: Create a structured findings document."""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["write_findings"]


def write_findings(
    path: str,
    topic: str,
    problem: str,
    attempts: str,
    insights: str,
    recommendations: str,
) -> str:
    """
    Create a structured findings document from an experiment or investigation.

    Args:
        path: Output file path (e.g., 'docs/my-findings.md')
        topic: Title/topic of the findings
        problem: Problem statement - what were you trying to solve?
        attempts: JSON array of attempts: [{"name": "...", "result": "..."}]
        insights: JSON array of insight strings
        recommendations: JSON array of recommendation strings

    Returns:
        Path to the created file.
    """
    attempts_list = json.loads(attempts)
    insights_list = json.loads(insights)
    recommendations_list = json.loads(recommendations)

    lines = [
        f"# {topic}",
        "",
        "## Problem",
        "",
        problem,
        "",
        "## What We Tried",
        "",
    ]

    for attempt in attempts_list:
        lines.append(f"### {attempt['name']}")
        lines.append("")
        lines.append(f"**Result**: {attempt['result']}")
        lines.append("")

    lines.append("## Key Insights")
    lines.append("")
    for insight in insights_list:
        lines.append(f"- {insight}")
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    for rec in recommendations_list:
        lines.append(f"- {rec}")
    lines.append("")

    content = "\n".join(lines)

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    return f"Created: {path}"

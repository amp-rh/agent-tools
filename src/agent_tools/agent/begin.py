"""agent.begin: ALWAYS call this first with the task you're about to do."""
from __future__ import annotations

from typing import Any

from agent_tools import _core

__all__ = ["begin", "analyze_repeatability"]

REPEATABLE_SIGNALS = [
    "create", "write", "generate", "build", "make",
    "format", "convert", "transform", "parse",
    "validate", "check", "verify", "test",
    "deploy", "publish", "release",
    "setup", "initialize", "configure",
    "report", "summarize", "document",
    "every", "always", "whenever", "each time",
]

ONE_OFF_SIGNALS = [
    "fix this", "debug this", "investigate",
    "figure out", "understand", "explore",
    "once", "just this", "only this",
    "specific", "particular",
]

CORE_NAMESPACES = {"registry", "agent"}


def _is_tier1(name: str, config: dict[str, Any]) -> bool:
    """Determine if a tool is Tier 1 (directly callable)."""
    if "tier" in config:
        return config["tier"] == 1
    if "." in name:
        namespace = name.split(".", 1)[0]
        if namespace in CORE_NAMESPACES:
            return True
    return False


def _format_tools_by_tier(tools: list[dict[str, Any]]) -> str:
    """Format tools showing tier separation."""
    tier1: dict[str, list[tuple[str, str]]] = {}
    tier2: dict[str, list[tuple[str, str]]] = {}

    for tool in tools:
        name = tool.get("name", "")
        desc = tool.get("description", "").split("\n")[0][:50]

        if "." in name:
            ns, tool_name = name.split(".", 1)
        else:
            ns, tool_name = "root", name

        target = tier1 if _is_tier1(name, tool) else tier2
        target.setdefault(ns, []).append((tool_name, desc))

    lines = []

    if tier1:
        lines.append("### Tier 1 (call directly)")
        for ns in sorted(tier1.keys()):
            lines.append(f"  {ns}:")
            for tool_name, desc in sorted(tier1[ns]):
                lines.append(f"    {tool_name}: {desc}")

    if tier2:
        lines.append("")
        lines.append("### Tier 2 (via registry-execute)")
        for ns in sorted(tier2.keys()):
            lines.append(f"  {ns}:")
            for tool_name, desc in sorted(tier2[ns]):
                lines.append(f"    {tool_name}: {desc}")
        lines.append("")
        lines.append("To call Tier 2: `registry-execute(name=\"ns.tool\", params='{...}')`")

    return "\n".join(lines)


def analyze_repeatability(task: str) -> tuple[str, str]:
    """Analyze if a task is likely repeatable."""
    task_lower = task.lower()

    repeatable_matches = [s for s in REPEATABLE_SIGNALS if s in task_lower]
    one_off_matches = [s for s in ONE_OFF_SIGNALS if s in task_lower]

    if one_off_matches and not repeatable_matches:
        return "one-off", f"Signals: {', '.join(one_off_matches)}"
    elif repeatable_matches:
        return "repeatable", f"Signals: {', '.join(repeatable_matches)}"
    else:
        return "unclear", "No strong signals either way"


def begin(task: str) -> str:
    """
    Analyze a task and recommend an approach.

    Args:
        task: What you're about to do

    Returns:
        Analysis and recommendation.
    """
    registry = _core.load_registry()
    tools = registry.get("tools", [])
    tools_output = _format_tools_by_tier(tools)
    repeatability, reason = analyze_repeatability(task)

    lines = [
        "## Task Analysis",
        "",
        f"**Task**: {task}",
        "",
        f"**Repeatability**: {repeatability}",
        f"  {reason}",
        "",
        "## Available Tools",
        "",
        tools_output,
        "",
        "## Recommendation",
        "",
    ]

    if repeatability == "repeatable":
        lines.extend([
            "This task appears **repeatable**. Before doing it manually:",
            "",
            "1. Check if an existing tool above fits",
            "2. If not, **choose the right MCP primitive**:",
            "",
            "   | Primitive | Use When |",
            "   |-----------|----------|",
            "   | **Tool** | Needs code execution, variable inputs |",
            "   | **Prompt** | Workflow guidance, templates, structured thinking |",
            "   | **Resource** | Read-only data, reference info |",
            "",
            "3. Create the primitive, then use it",
            "",
            "Don't default to tools! Prompts and resources are often better fits.",
        ])
    elif repeatability == "one-off":
        lines.extend([
            "This task appears **one-off**. Proceed manually.",
            "",
            "If you find yourself doing something similar later, reconsider making a tool.",
        ])
    else:
        lines.extend([
            "**Unclear** if this is repeatable. Ask yourself:",
            "",
            "- Will I or another agent do this again?",
            "- Is there a pattern here worth capturing?",
            "",
            "If yes → create the right primitive (tool/prompt/resource).",
            "If no → proceed manually.",
        ])

    return "\n".join(lines)

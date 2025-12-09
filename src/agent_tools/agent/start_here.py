"""agent.start-here: ALWAYS call this first before attempting any task."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

__all__ = ["start_here"]


def _load_registry() -> dict[str, Any]:
    """Load the registry YAML file."""
    registry_file = Path(__file__).parent.parent.parent.parent / "agent-tools.yaml"
    with registry_file.open() as f:
        return yaml.safe_load(f)


def _format_tools() -> str:
    """Format all tools for display."""
    registry = _load_registry()
    tools = registry.get("tools", [])

    # Organize by namespace
    namespaces: dict[str, list[tuple[str, str]]] = {}
    for tool in tools:
        name = tool.get("name", "")
        desc = tool.get("description", "").split("\n")[0][:55]

        if "." in name:
            ns, tool_name = name.split(".", 1)
        else:
            ns, tool_name = "root", name

        namespaces.setdefault(ns, []).append((tool_name, desc))

    lines = []
    for ns in sorted(namespaces.keys()):
        lines.append(f"  {ns}:")
        for tool_name, desc in sorted(namespaces[ns]):
            lines.append(f"    {tool_name}: {desc}")

    return "\n".join(lines)


def start_here() -> str:
    """
    ALWAYS call this first before attempting any task.

    Returns workflow guidance and lists all available tools.
    """
    tools_output = _format_tools()

    return f"""## Workflow

If a tool exists for your task, use it.
If no tool exists and the task is repeatable, create one with `registry-add` first, then use it.

Every repeatable process becomes a tool. Your job is to think. Tools do the work.

## Available Tools

{tools_output}

## How to Call Tools

Use `registry-execute` to invoke any tool:

```
registry-execute(
  name="namespace.tool-name",
  params='{{"param1": "value1", "param2": "value2"}}'
)
```

## Quick Reference

| Action | Tool |
|--------|------|
| Create new tool | `registry-execute(name="registry.add", params='{{...}}')` |
| List all tools | `registry-execute(name="registry.list", params='{{}}')` |
| Analyze task | `registry-execute(name="agent.begin", params='{{"task": "..."}}')` |
"""

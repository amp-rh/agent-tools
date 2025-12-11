"""registry.reload: Clear module cache and reload tool definitions."""
from __future__ import annotations

import sys

__all__ = ["reload"]


def reload() -> str:
    """
    Clear Python module cache and reload tool definitions.

    Use after modifying tool implementations to pick up changes
    without restarting the MCP server.

    Returns:
        Summary of modules cleared and tools reloaded.
    """
    # Find all agent_tools modules to clear (except core infrastructure)
    preserve = {
        "agent_tools",
        "agent_tools._core",
        "agent_tools.server",
        "agent_tools.registry",
        "agent_tools.mcp_client",
    }

    to_clear = [
        name for name in sys.modules
        if name.startswith("agent_tools") and name not in preserve
    ]

    # Clear the modules
    for name in to_clear:
        del sys.modules[name]

    # Also clear any cached bytecode by touching __pycache__ would be overkill
    # The import system will re-import fresh on next tool call

    lines = [
        "## Module Cache Cleared",
        "",
        f"Cleared {len(to_clear)} modules from cache.",
        "",
    ]

    if to_clear:
        lines.append("Modules cleared:")
        for name in sorted(to_clear)[:10]:  # Show first 10
            lines.append(f"  - {name}")
        if len(to_clear) > 10:
            lines.append(f"  - ... and {len(to_clear) - 10} more")
        lines.append("")

    lines.append("Next tool calls will use fresh code from disk.")

    return "\n".join(lines)

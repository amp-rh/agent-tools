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
        Summary of modules cleared and configs reloaded.
    """
    lines = ["## Cache Cleared", ""]

    # === 1. Clear Python module cache for local tools ===
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

    for name in to_clear:
        del sys.modules[name]

    lines.append(f"**Local tools**: Cleared {len(to_clear)} Python modules.")
    if to_clear:
        sample = sorted(to_clear)[:5]
        lines.append(f"  Examples: {', '.join(m.split('.')[-1] for m in sample)}")
    lines.append("")

    # === 2. Reload external MCP server configs ===
    external_status = _reload_external_configs()
    lines.append(f"**External servers**: {external_status}")
    lines.append("")

    lines.append("Next tool calls will use fresh code/configs.")
    lines.append("")
    lines.append("**Note**: External MCP server code changes require `mcp.disconnect` + `mcp.connect`.")

    return "\n".join(lines)


def _reload_external_configs() -> str:
    """Reload external MCP server configurations from disk."""
    try:
        from agent_tools.mcp.connect import get_manager
        manager = get_manager()
        manager.reload_configs()
        servers = manager.get_configured_servers()
        return f"Reloaded configs ({len(servers)} servers configured)"
    except Exception:
        # No manager available (running outside MCP server context)
        return "No active manager (standalone mode)"

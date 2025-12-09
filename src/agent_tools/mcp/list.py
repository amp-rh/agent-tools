"""mcp.list: List all configured external MCP servers."""
from __future__ import annotations

import agent_tools._core as _core

__all__ = ["list_servers"]


def list_servers() -> str:
    """
    List all configured external MCP servers.

    Returns:
        YAML-formatted list of configured servers.
    """
    registry = _core.load_registry()
    mcp_servers = registry.get("mcp_servers", {})

    if not mcp_servers:
        return "No external MCP servers configured.\n\nUse mcp.add to add one."

    lines = ["## External MCP Servers", ""]

    for name, config in mcp_servers.items():
        command = config.get("command", "")
        args = config.get("args", [])
        env = config.get("env", {})

        lines.append(f"### {name}")
        lines.append(f"Command: `{command} {' '.join(args)}`")
        if env:
            env_keys = ", ".join(env.keys())
            lines.append(f"Environment: {env_keys}")
        lines.append("")

    return "\n".join(lines)

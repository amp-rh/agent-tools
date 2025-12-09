"""mcp.remove: Remove an external MCP server reference."""
from __future__ import annotations

import agent_tools._core as _core

__all__ = ["remove"]


def remove(name: str) -> str:
    """
    Remove an external MCP server reference.

    Args:
        name: Name of the server to remove

    Returns:
        Result message describing what was done.
    """
    servers_dir = _core.TOOL_DEFS_DIR / "_servers"
    server_file = servers_dir / f"{name}.yaml"

    if not server_file.exists():
        # List available servers
        available = []
        if servers_dir.exists():
            available = [f.stem for f in servers_dir.glob("*.yaml")]
        available_str = ", ".join(available) if available else "none"
        return f"Error: MCP server '{name}' not found. Available: {available_str}"

    # Remove server file
    server_file.unlink()

    return f"""Removed MCP server: {name}

Server config deleted from: tool_defs/_servers/{name}.yaml
"""

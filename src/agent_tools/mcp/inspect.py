"""mcp.inspect: Launch MCP Inspector to interactively test an MCP server."""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["inspect"]


def inspect(server: str = None, command: str = None) -> str:
    """
    Launch MCP Inspector to interactively test an MCP server.

    Runs the MCP Inspector (via npx) and returns the connection URL.
    Can inspect a server from mcp.json by name or run a direct command.

    Args:
        server: Server name from .cursor/mcp.json to inspect
        command: Direct command to run (e.g., 'uv run agent-tools server')

    Returns:
        Command and instructions for running MCP Inspector.
    """
    # Determine the command to inspect
    if command:
        # Direct command provided
        target_command = command
        server_name = "custom"
    elif server:
        # Look up server from mcp.json
        mcp_json_path = Path.cwd() / ".cursor" / "mcp.json"
        if not mcp_json_path.exists():
            return f"Error: .cursor/mcp.json not found. Server '{server}' cannot be looked up."

        try:
            config = json.loads(mcp_json_path.read_text())
        except json.JSONDecodeError as e:
            return f"Error: Invalid mcp.json: {e}"

        servers = config.get("mcpServers", {})
        if server not in servers:
            available = ", ".join(servers.keys()) if servers else "(none)"
            return f"Error: Server '{server}' not found in mcp.json. Available: {available}"

        server_config = servers[server]
        cmd = server_config.get("command", "")
        args = server_config.get("args", [])
        target_command = f"{cmd} {' '.join(args)}".strip()
        server_name = server
    else:
        # Default: agent-tools
        target_command = "uv run agent-tools server"
        server_name = "agent-tools"

    # Build inspector command
    inspector_cmd = f"npx -y @modelcontextprotocol/inspector {target_command}"

    # Return instructions
    lines = [
        f"## MCP Inspector for {server_name}",
        "",
        "Run this command to start the inspector:",
        "",
        "```bash",
        inspector_cmd,
        "```",
        "",
        "The inspector will start at: `http://localhost:6274`",
        "",
        "### Available Tabs",
        "- **Resources**: Browse and read server resources",
        "- **Prompts**: Test prompt templates",
        "- **Tools**: Execute tools with custom inputs",
        "- **Notifications**: View server logs",
    ]

    return "\n".join(lines)

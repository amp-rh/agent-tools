"""mcp.add: Add an external MCP server reference to tool_defs/_servers/."""
from __future__ import annotations

import json

import yaml

import agent_tools._core as _core

__all__ = ["add"]


def add(name: str, command: str, args: str, env: str = None) -> str:
    """
    Add an external MCP server reference.

    Args:
        name: Unique name for this server (e.g., 'github', 'filesystem')
        command: Command to run the server (e.g., 'npx', 'uvx', 'node')
        args: JSON array of command arguments
        env: JSON object of environment variables (optional)

    Returns:
        Result message describing what was done.
    """
    # Parse args
    try:
        args_list = json.loads(args) if args else []
    except json.JSONDecodeError as e:
        return f"Error: Invalid args JSON: {e}"

    # Parse env
    env_dict = None
    if env:
        try:
            env_dict = json.loads(env)
        except json.JSONDecodeError as e:
            return f"Error: Invalid env JSON: {e}"

    # Check for duplicate
    servers_dir = _core.TOOL_DEFS_DIR / "_servers"
    server_file = servers_dir / f"{name}.yaml"

    if server_file.exists():
        return f"Error: MCP server '{name}' already exists. Use mcp.remove first."

    # Build server entry
    server_entry = {
        "command": command,
        "args": args_list,
    }
    if env_dict:
        server_entry["env"] = env_dict

    # Ensure _servers directory exists
    servers_dir.mkdir(parents=True, exist_ok=True)

    # Save server definition
    with server_file.open("w") as f:
        yaml.dump(server_entry, f, default_flow_style=False, sort_keys=False)

    return f"""Added MCP server: {name}

Command: {command} {' '.join(args_list)}
{f"Environment: {', '.join(env_dict.keys())}" if env_dict else ""}

Server config saved to: tool_defs/_servers/{name}.yaml
Use mcp.connect to start using it immediately.
"""

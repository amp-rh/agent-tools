"""
Command-line interface for agent-tools.

Commands:
    init     - Initialize agent-tools.yaml in current directory
    server   - Run the MCP server
    list     - List all registered tools
    validate - Validate the registry
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

__all__ = ["main"]

# Package's default registry
PACKAGE_DIR = Path(__file__).parent
DEFAULT_REGISTRY = PACKAGE_DIR.parent.parent / "agent-tools.yaml"

# User config locations
USER_CONFIG_DIR = Path.home() / ".config" / "agent-tools"
LOCAL_CONFIG = Path.cwd() / "agent-tools.yaml"


def get_default_registry_path() -> Path:
    """Get path to the package's default registry."""
    # Try package location first
    if DEFAULT_REGISTRY.exists():
        return DEFAULT_REGISTRY

    # Try installed location
    import importlib.resources
    try:
        with importlib.resources.files("agent_tools").joinpath("../agent-tools.yaml") as p:
            if p.exists():
                return Path(p)
    except Exception:
        pass

    # Fallback: look in share directory
    share_path = Path(sys.prefix) / "share" / "agent-tools" / "agent-tools.yaml"
    if share_path.exists():
        return share_path

    return DEFAULT_REGISTRY


def find_registry() -> Path | None:
    """Find the registry file, checking local then user config."""
    # Check current directory first
    if LOCAL_CONFIG.exists():
        return LOCAL_CONFIG

    # Check user config directory
    user_config = USER_CONFIG_DIR / "agent-tools.yaml"
    if user_config.exists():
        return user_config

    return None


def cmd_init(args: list[str]) -> int:
    """Initialize agent-tools.yaml in current directory."""
    target = LOCAL_CONFIG
    force = "--force" in args

    if target.exists() and not force:
        print(f"Error: {target} already exists. Use --force to overwrite.")
        return 1

    # Copy default registry
    default = get_default_registry_path()
    if not default.exists():
        print(f"Error: Default registry not found at {default}")
        return 1

    shutil.copy(default, target)
    print(f"Created {target}")
    print()
    print("Next steps:")
    print("  1. Add tools with: agent-tools add <name> <description>")
    print("  2. Or use MCP: registry-add in your AI assistant")
    print()
    print("MCP server config (add to .cursor/mcp.json):")
    print(f'''
{{
  "mcpServers": {{
    "agent-tools": {{
      "command": "agent-tools-server",
      "args": ["{target}"]
    }}
  }}
}}
''')
    return 0


def cmd_server(args: list[str]) -> int:
    """Run the MCP server."""
    from agent_tools.server import main as server_main

    # If no args, try to find registry
    if not args:
        registry = find_registry()
        if registry:
            sys.argv = ["agent-tools-server", str(registry)]
        else:
            print("Error: No agent-tools.yaml found.")
            print("Run 'agent-tools init' to create one.")
            return 1

    server_main()
    return 0


def cmd_list(args: list[str]) -> int:
    """List all registered tools."""
    from agent_tools import _core, registry
    from agent_tools.registry import list_tools

    # Find and use registry
    registry_path = find_registry()
    if not registry_path:
        print("Error: No agent-tools.yaml found.")
        print("Run 'agent-tools init' to create one.")
        return 1

    # Temporarily point to found registry's tool_defs
    original = _core.TOOL_DEFS_DIR
    _core.TOOL_DEFS_DIR = registry_path.parent / "tool_defs" if registry_path.name == "agent-tools.yaml" else registry_path
    registry._reset_manager()

    try:
        print(list_tools())
    finally:
        _core.TOOL_DEFS_DIR = original
        registry._reset_manager()

    return 0


def cmd_validate(args: list[str]) -> int:
    """Validate the registry."""
    from agent_tools import _core, registry
    from agent_tools.registry import validate_registry

    registry_path = find_registry()
    if not registry_path:
        print("Error: No agent-tools.yaml found.")
        return 1

    # Temporarily point to found registry's tool_defs
    original = _core.TOOL_DEFS_DIR
    _core.TOOL_DEFS_DIR = registry_path.parent / "tool_defs" if registry_path.name == "agent-tools.yaml" else registry_path
    registry._reset_manager()

    try:
        print(validate_registry())
    finally:
        _core.TOOL_DEFS_DIR = original
        registry._reset_manager()

    return 0


def cmd_help(args: list[str]) -> int:
    """Show help message."""
    print("""agent-tools - Self-modifying tool registry for AI agents

Usage: agent-tools <command> [options]

Commands:
    init       Initialize agent-tools.yaml in current directory
    server     Run the MCP server (or use: agent-tools-server)
    list       List all registered tools
    validate   Validate the registry for errors
    help       Show this help message

Installation from GitHub:
    uv add git+https://github.com/amp-rh/agent-tools.git

    # Or with pip
    pip install git+https://github.com/amp-rh/agent-tools.git

Quick Start:
    1. agent-tools init
    2. Add MCP config to .cursor/mcp.json
    3. Restart your AI assistant
    4. Use registry-add to create tools

Philosophy:
    Every repeatable process becomes a tool.
    Your job is to think. Tools do the work.
""")
    return 0


COMMANDS = {
    "init": cmd_init,
    "server": cmd_server,
    "list": cmd_list,
    "validate": cmd_validate,
    "help": cmd_help,
    "--help": cmd_help,
    "-h": cmd_help,
}


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    if not args:
        cmd_help([])
        sys.exit(0)

    cmd = args[0]
    cmd_args = args[1:]

    if cmd in COMMANDS:
        sys.exit(COMMANDS[cmd](cmd_args))
    else:
        print(f"Unknown command: {cmd}")
        print("Run 'agent-tools help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()

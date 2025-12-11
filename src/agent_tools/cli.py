"""
Command-line interface for agent-tools.

Commands:
    init     - Initialize tool_defs in current directory
    server   - Run the MCP server
    list     - List all registered tools
    validate - Check registry for errors
    commands - Generate Cursor slash commands
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

    # If args provided, pass them through
    if args:
        sys.argv = ["agent-tools-server", *args]
    else:
        # Try local registry first, otherwise let server find bundled tools
        registry = find_registry()
        if registry:
            sys.argv = ["agent-tools-server", str(registry)]
        else:
            sys.argv = ["agent-tools-server"]

    server_main()
    return 0


def _with_registry(func):
    """Run a function with the registry temporarily pointed to the found config."""
    from contextlib import contextmanager

    from agent_tools import _core, registry

    @contextmanager
    def _use_registry(registry_path: Path):
        original = _core.TOOL_DEFS_DIR
        _core.TOOL_DEFS_DIR = (
            registry_path.parent / "tool_defs"
            if registry_path.name == "agent-tools.yaml"
            else registry_path
        )
        registry._reset_manager()
        try:
            yield
        finally:
            _core.TOOL_DEFS_DIR = original
            registry._reset_manager()

    registry_path = find_registry()
    if not registry_path:
        print("Error: No agent-tools.yaml found.")
        print("Run 'agent-tools init' to create one.")
        return 1

    with _use_registry(registry_path):
        print(func())

    return 0


def cmd_list(args: list[str]) -> int:
    """List all registered tools."""
    from agent_tools.registry import list_tools

    return _with_registry(list_tools)


def cmd_validate(args: list[str]) -> int:
    """Validate the registry."""
    from agent_tools.registry import validate_registry

    return _with_registry(validate_registry)


def cmd_commands(args: list[str]) -> int:
    """Generate Cursor slash commands from tool definitions."""
    from agent_tools.registry import generate_commands

    # Parse arguments
    output_dir = None
    sync = "--sync" in args

    for i, arg in enumerate(args):
        if arg == "--output" and i + 1 < len(args):
            output_dir = Path(args[i + 1])
        elif arg.startswith("--output="):
            output_dir = Path(arg.split("=", 1)[1])

    # Default to .cursor/commands in current directory
    if output_dir is None:
        output_dir = Path.cwd() / ".cursor" / "commands"

    def _generate():
        return generate_commands(output_dir, sync=sync)

    return _with_registry(_generate)


def cmd_help(args: list[str]) -> int:
    """Show help message."""
    print("""agent-tools - A self-modifying tool registry that lets AI agents create
and manage their own tools via the Model Context Protocol (MCP).

Usage: agent-tools <command> [options]

Commands:
    init       Initialize tool_defs in current directory
    server     Run the MCP server (or use: agent-tools-server)
    list       List all registered tools
    validate   Check registry for errors
    commands   Generate Cursor slash commands from tools
    help       Show this help message

What It Does:
    Exposes tools to AI assistants (like Claude in Cursor) that let them:
    - Create new tools on the fly with registry.add
    - Execute tools dynamically with registry.execute
    - Manage the registry (list, update, remove, validate)

Quick Start:
    1. agent-tools init
       Creates: tool_defs/, src/agent_tools/, tests/

    2. Add to .cursor/mcp.json:
       {
         "mcpServers": {
           "agent-tools": {
             "command": "agent-tools-server",
             "args": ["/path/to/your/tool_defs"]
           }
         }
       }

    3. Restart your AI assistant - tools are now available

Installation:
    uv add git+https://github.com/amp-rh/agent-tools.git
    pip install git+https://github.com/amp-rh/agent-tools.git
""")
    return 0


COMMANDS = {
    "init": cmd_init,
    "server": cmd_server,
    "list": cmd_list,
    "validate": cmd_validate,
    "commands": cmd_commands,
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

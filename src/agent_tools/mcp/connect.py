"""mcp.connect: Connect to an external MCP server and discover its tools."""
from __future__ import annotations

import asyncio
import atexit

from agent_tools._async_helpers import run_async_in_thread
from agent_tools.mcp_client import ExternalServerManager

__all__ = ["connect", "get_manager", "cleanup"]

# Global manager instance (shared with server.py when running)
_manager: ExternalServerManager | None = None
_cleanup_registered: bool = False


def _cleanup_sync() -> None:
    """Synchronous cleanup for atexit."""
    global _manager
    if _manager is not None:
        try:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_manager.stop_all())
            finally:
                loop.close()
        except Exception:
            pass  # Best effort cleanup
        _manager = None


def get_manager() -> ExternalServerManager:
    """Get existing manager or create a new one with cleanup registered."""
    global _manager, _cleanup_registered
    if _manager is None:
        _manager = ExternalServerManager()
        if not _cleanup_registered:
            atexit.register(_cleanup_sync)
            _cleanup_registered = True
    return _manager


def set_manager(manager: ExternalServerManager) -> None:
    """Set the manager instance (used by server.py to share its manager)."""
    global _manager
    _manager = manager


async def cleanup() -> None:
    """Cleanup all external servers."""
    global _manager
    if _manager is not None:
        await _manager.stop_all()
        _manager = None


async def _connect_async(name: str) -> str:
    """Async implementation of connect."""
    manager = get_manager()
    manager.reload_configs()

    configured = manager.get_configured_servers()
    if name not in configured:
        return f"Error: Server '{name}' not configured. Use mcp.add first."

    success = await manager.start_server(name)
    if not success:
        return f"Error: Failed to start server '{name}'. Check command and configuration."

    server = manager.get_server(name)
    if not server:
        return f"Error: Server '{name}' started but not accessible."

    tools = server.get_tools()
    if not tools:
        return f"Connected to {name}, but no tools discovered."

    return _format_connection_result(name, tools)


def _format_connection_result(name: str, tools: list[dict]) -> str:
    """Format the connection result as markdown."""
    lines = [
        f"## Connected to {name}",
        "",
        f"Discovered {len(tools)} tools:",
        "",
    ]

    for tool in tools:
        tool_name = tool.get("name", "unknown")
        desc = tool.get("description", "No description")[:60]
        lines.append(f"- `{tool_name}`: {desc}")

    lines.extend([
        "",
        "Call these tools via registry-execute:",
        f'  `registry-execute(name="{name}.<tool>", params=\'{{...}}\')`',
    ])

    return "\n".join(lines)


def connect(name: str) -> str:
    """Connect to an external MCP server and discover its tools.

    Args:
        name: Name of the server to connect to

    Returns:
        List of available tools from the server.
    """
    try:
        return run_async_in_thread(_connect_async(name))
    except TimeoutError:
        return "Error: Connection timed out"
    except Exception as e:
        return f"Error connecting to {name}: {e}"

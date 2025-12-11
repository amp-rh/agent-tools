"""mcp.connect: Connect to an external MCP server and discover its tools."""
from __future__ import annotations

import asyncio
import atexit

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
        # Register cleanup on process exit
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

    # Reload configs to pick up any newly added servers
    manager.reload_configs()

    configured = manager.get_configured_servers()
    if name not in configured:
        return f"Error: Server '{name}' not configured. Use mcp.add first."

    # Try to start the server
    success = await manager.start_server(name)
    if not success:
        return f"Error: Failed to start server '{name}'. Check command and configuration."

    # Get the server and list its tools
    server = manager.get_server(name)
    if not server:
        return f"Error: Server '{name}' started but not accessible."

    tools = server.get_tools()
    if not tools:
        return f"Connected to {name}, but no tools discovered."

    # Format tool list
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

    lines.append("")
    lines.append("Call these tools via registry-execute:")
    lines.append(f'  `registry-execute(name="{name}.<tool>", params=\'{{...}}\')`')

    return "\n".join(lines)


def _run_in_thread(coro):
    """Run async coroutine in a separate thread with its own event loop."""
    import threading

    result = [None]
    error = [None]

    def _execute_in_loop():
        try:
            # Create a completely fresh event loop in this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result[0] = new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        except Exception as e:
            error[0] = e

    thread = threading.Thread(target=_execute_in_loop)
    thread.start()
    thread.join(timeout=120)

    if thread.is_alive():
        return "Error: Connection timed out"
    if error[0]:
        raise error[0]
    return result[0]


def connect(name: str) -> str:
    """
    Connect to an external MCP server and discover its tools.

    Args:
        name: Name of the server to connect to

    Returns:
        List of available tools from the server.
    """
    try:
        return _run_in_thread(_connect_async(name))
    except Exception as e:
        return f"Error connecting to {name}: {e}"

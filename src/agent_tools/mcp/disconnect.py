"""mcp.disconnect: Disconnect from external MCP servers."""
from __future__ import annotations

import asyncio

from agent_tools.mcp.connect import get_manager

__all__ = ["disconnect"]


async def _disconnect_async(name: str | None) -> str:
    """Async implementation of disconnect."""
    manager = get_manager()

    if name:
        # Disconnect specific server
        server = manager.get_server(name)
        if not server:
            return f"Server '{name}' is not connected."

        await server.stop()
        # Remove from manager's internal dict
        if hasattr(manager, "_servers") and name in manager._servers:
            del manager._servers[name]

        return f"Disconnected from {name}."
    else:
        # Disconnect all servers
        await manager.stop_all()
        return "Disconnected from all external MCP servers."


def disconnect(name: str = None) -> str:
    """
    Disconnect from an external MCP server and stop it.

    Args:
        name: Name of the server to disconnect (optional, disconnects all if not provided)

    Returns:
        Status message.
    """
    try:
        # Check if we're already in an async context
        try:
            asyncio.get_running_loop()
            # We're in an async context - run in thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(_disconnect_async(name))
                )
                return future.result(timeout=30)
        except RuntimeError:
            # No running loop - safe to create one
            return asyncio.run(_disconnect_async(name))
    except Exception as e:
        return f"Error disconnecting: {e}"

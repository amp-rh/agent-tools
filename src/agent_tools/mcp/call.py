"""Utility for calling external MCP server tools from wrapper tools."""
from __future__ import annotations

from agent_tools._async_helpers import run_async_in_thread
from agent_tools.mcp.connect import get_manager

__all__ = ["call_external", "call_external_sync"]


async def call_external(server: str, tool: str, **kwargs) -> str:
    """Call an external MCP server tool (async version).

    Args:
        server: Name of the external server (e.g., 'github')
        tool: Name of the tool on that server (e.g., 'search_issues')
        **kwargs: Arguments to pass to the tool

    Returns:
        Tool result as string.

    Example:
        result = await call_external('github', 'search_issues', q='is:pr is:open')
    """
    manager = get_manager()

    # Ensure server is started
    if not manager.get_server(server):
        manager.reload_configs()
        if not await manager.start_server(server):
            return f"Error: Could not start server '{server}'"

    return await manager.call_tool(server, tool, kwargs)


def call_external_sync(server: str, tool: str, **kwargs) -> str:
    """Call an external MCP server tool (sync version).

    Use this from synchronous tool implementations.

    Args:
        server: Name of the external server (e.g., 'github')
        tool: Name of the tool on that server (e.g., 'search_issues')
        **kwargs: Arguments to pass to the tool

    Returns:
        Tool result as string.

    Example:
        result = call_external_sync('github', 'search_issues', q='is:pr is:open')
    """
    try:
        return run_async_in_thread(call_external(server, tool, **kwargs))
    except TimeoutError:
        return "Error: Call timed out"
    except Exception as e:
        return f"Error: {e}"

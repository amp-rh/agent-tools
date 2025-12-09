"""
MCP client for managing external MCP servers.

This module handles spawning, connecting to, and proxying calls to external
MCP servers configured in tool_defs/_servers/.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

__all__ = ["ExternalServer", "ExternalServerManager"]


def _expand_env_vars(env: dict[str, str]) -> dict[str, str]:
    """Expand ${VAR} syntax in environment variable values."""
    result = {}
    for key, value in env.items():
        if isinstance(value, str) and "${" in value:
            # Simple expansion: ${VAR} -> os.environ.get(VAR, "")
            import re

            def replace(match):
                var_name = match.group(1)
                return os.environ.get(var_name, "")

            value = re.sub(r"\$\{(\w+)\}", replace, value)
        result[key] = value
    return result


@dataclass
class ExternalServer:
    """Manages lifecycle of one external MCP server."""

    name: str
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)

    _session: ClientSession | None = field(default=None, repr=False)
    _tools: list[Tool] = field(default_factory=list, repr=False)
    _read: Any = field(default=None, repr=False)
    _write: Any = field(default=None, repr=False)
    _cm: Any = field(default=None, repr=False)  # Context manager

    async def start(self) -> bool:
        """
        Start the external server and establish connection.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Expand environment variables
            expanded_env = _expand_env_vars(self.env) if self.env else {}

            # Merge with current environment
            full_env = {**os.environ, **expanded_env}

            # Create server parameters
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=full_env,
            )

            # Start the client connection
            self._cm = stdio_client(server_params)
            self._read, self._write = await self._cm.__aenter__()

            # Create and initialize session
            self._session = ClientSession(self._read, self._write)
            await self._session.__aenter__()
            await self._session.initialize()

            # Discover tools
            tools_result = await self._session.list_tools()
            self._tools = tools_result.tools

            print(
                f"Connected to {self.name}: {len(self._tools)} tools available",
                file=sys.stderr,
            )
            return True

        except Exception as e:
            print(f"Failed to start {self.name}: {e}", file=sys.stderr)
            await self.stop()
            return False

    async def stop(self) -> None:
        """Stop the external server and cleanup."""
        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None
            if self._cm:
                await self._cm.__aexit__(None, None, None)
                self._cm = None
        except Exception as e:
            print(f"Error stopping {self.name}: {e}", file=sys.stderr)

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get tools from this server, prefixed with server name.

        Returns:
            List of tool configs with prefixed names.
        """
        tools = []
        for tool in self._tools:
            # Prefix tool name with server name
            prefixed_name = f"{self.name}.{tool.name}"
            tools.append(
                {
                    "name": prefixed_name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema,
                    "_external": True,
                    "_server": self.name,
                    "_original_name": tool.name,
                }
            )
        return tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """
        Call a tool on this external server.

        Args:
            tool_name: Original tool name (without prefix)
            arguments: Tool arguments

        Returns:
            Tool result as string.
        """
        if not self._session:
            return f"Error: Server {self.name} not connected"

        try:
            result = await self._session.call_tool(tool_name, arguments)

            # Extract text from result
            if result.content:
                texts = []
                for item in result.content:
                    if hasattr(item, "text"):
                        texts.append(item.text)
                    else:
                        texts.append(str(item))
                return "\n".join(texts)
            return ""

        except Exception as e:
            return f"Error calling {self.name}.{tool_name}: {e}"


class ExternalServerManager:
    """Manages all external MCP servers."""

    def __init__(self):
        self._servers: dict[str, ExternalServer] = {}
        self._configs: dict[str, dict[str, Any]] = {}

    def set_configs(self, mcp_servers: dict[str, dict[str, Any]]) -> None:
        """
        Store server configurations for lazy loading.

        Args:
            mcp_servers: Server configs from agent-tools.yaml
        """
        self._configs = mcp_servers.copy()

    def reload_configs(self) -> None:
        """Reload configurations from registry file."""
        import agent_tools._core as _core

        registry = _core.load_registry()
        self._configs = registry.get("mcp_servers", {})

    async def start_server(self, name: str) -> bool:
        """
        Start a specific server by name.

        Args:
            name: Server name from config

        Returns:
            True if successful.
        """
        if name in self._servers:
            return True  # Already running

        config = self._configs.get(name)
        if not config:
            # Reload configs in case it was just added
            self.reload_configs()
            config = self._configs.get(name)

        if not config:
            return False

        server = ExternalServer(
            name=name,
            command=config.get("command", ""),
            args=config.get("args", []),
            env=config.get("env", {}),
        )

        if await server.start():
            self._servers[name] = server
            return True
        return False

    async def start_all(self, mcp_servers: dict[str, dict[str, Any]]) -> None:
        """
        Start all configured external servers.

        Args:
            mcp_servers: Server configs from agent-tools.yaml
        """
        self.set_configs(mcp_servers)
        for name in mcp_servers:
            await self.start_server(name)

    async def stop_all(self) -> None:
        """Stop all external servers."""
        for server in self._servers.values():
            await server.stop()
        self._servers.clear()

    def get_all_tools(self) -> list[dict[str, Any]]:
        """
        Get all tools from all running external servers.

        Returns:
            List of tool configs with prefixed names.
        """
        tools = []
        for server in self._servers.values():
            tools.extend(server.get_tools())
        return tools

    def get_configured_servers(self) -> list[str]:
        """Get names of all configured (not necessarily running) servers."""
        self.reload_configs()
        return list(self._configs.keys())

    def get_server(self, name: str) -> ExternalServer | None:
        """Get a running server by name."""
        return self._servers.get(name)

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """
        Call a tool on a specific external server.

        Lazily starts the server if not already running.

        Args:
            server_name: Name of the external server
            tool_name: Original tool name (without prefix)
            arguments: Tool arguments

        Returns:
            Tool result as string.
        """
        # Lazy start: if server not running, try to start it
        if server_name not in self._servers:
            if not await self.start_server(server_name):
                return f"Error: External server '{server_name}' not found or failed to start"

        server = self._servers.get(server_name)
        if not server:
            return f"Error: External server '{server_name}' not available"

        return await server.call_tool(tool_name, arguments)


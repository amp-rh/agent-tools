"""MCP server that exposes agent-tools as callable functions."""
from __future__ import annotations

import asyncio
import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptMessage,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)

import agent_tools._core as _core
from agent_tools._core import ToolDefinition, ToolParameter, ToolRegistry
from agent_tools.mcp_client import ExternalServerManager

__all__ = ["AgentToolsServer", "main"]

ENTRY_POINT_TOOLS = frozenset({
    "agent.start-here",
    "registry.execute",
    "registry.reload",
    "observe.log",
    "observe.trace-call",
    "observe.session",
})

WORKFLOW_PROMPT = """\
I should check what tools are available before attempting this task.
Let me call `registry-list` first.

If a tool exists, I'll use it.
If not and this task is repeatable, I'll create one with `registry-add` first.

Every repeatable process becomes a tool. My job is to think. Tools do the work."""


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for the agent-tools MCP server."""

    tool_defs_path: Path
    project_root: Path = field(default_factory=Path.cwd)

    @classmethod
    def from_path(cls, tool_defs_path: Path) -> ServerConfig:
        return cls(
            tool_defs_path=tool_defs_path,
            project_root=tool_defs_path.parent,
        )


class InputSchemaBuilder:
    """Builds JSON schema for tool parameters."""

    @staticmethod
    def build(parameters: list[ToolParameter]) -> dict[str, Any]:
        properties = {}
        required = []

        for param in parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {"type": "object", "properties": properties, "required": required}


class ToolExecutor:
    """Executes tool functions by importing their modules."""

    @staticmethod
    def execute(tool: ToolDefinition, arguments: dict[str, Any]) -> str:
        if not tool.module or not tool.function:
            return f"Error: Tool '{tool.name}' missing module or function"

        try:
            module = importlib.import_module(tool.module)
            func = getattr(module, tool.function)
            return str(func(**arguments))
        except ImportError as e:
            return f"Error importing {tool.module}: {e}"
        except AttributeError:
            return f"Error: Function '{tool.function}' not found in {tool.module}"
        except Exception as e:
            return f"Error executing {tool.name}: {e}"


class ToolNameConverter:
    """Converts between MCP tool names and registry names."""

    @staticmethod
    def to_mcp(registry_name: str) -> str:
        return registry_name.replace(".", "-")

    @staticmethod
    def to_registry(mcp_name: str) -> str:
        return mcp_name.replace("-", ".", 1)


class AgentToolsServer:
    """MCP server exposing agent-tools as callable functions."""

    def __init__(self, config: ServerConfig):
        self._config = config
        self._server = Server("agent-tools")
        self._tools: dict[str, ToolDefinition] = {}
        self._external_manager: ExternalServerManager | None = None
        self._register_handlers()

    def _register_handlers(self) -> None:
        self._server.list_tools()(self._list_tools)
        self._server.call_tool()(self._call_tool)
        self._server.list_prompts()(self._list_prompts)
        self._server.get_prompt()(self._get_prompt)
        self._server.list_resources()(self._list_resources)
        self._server.read_resource()(self._read_resource)

    async def _list_tools(self) -> list[Tool]:
        tools = []
        for name, tool in self._tools.items():
            if name not in ENTRY_POINT_TOOLS:
                continue

            tools.append(
                Tool(
                    name=ToolNameConverter.to_mcp(name),
                    description=tool.description,
                    inputSchema=InputSchemaBuilder.build(tool.parameters),
                )
            )
        return tools

    async def _list_prompts(self) -> list[Prompt]:
        return [
            Prompt(
                name="agent-tools-workflow",
                description="Agent's thought process: check tools first, create if needed",
            )
        ]

    async def _get_prompt(
        self, name: str, arguments: dict[str, str] | None
    ) -> GetPromptResult:
        if name == "agent-tools-workflow":
            return GetPromptResult(
                description="Agent's thought process: check tools first, create if needed",
                messages=[
                    PromptMessage(
                        role="assistant",
                        content=TextContent(type="text", text=WORKFLOW_PROMPT),
                    )
                ],
            )
        raise ValueError(f"Unknown prompt: {name}")

    async def _list_resources(self) -> list[Resource]:
        return [
            Resource(
                uri="agent-tools://registry",
                name="Tool Registry",
                description="All available tools organized by namespace",
                mimeType="text/yaml",
            ),
        ]

    async def _read_resource(self, uri: str) -> list[TextResourceContents]:
        import yaml

        if uri == "agent-tools://registry":
            # Build registry summary
            namespaces: dict[str, list[dict[str, str]]] = {}
            for name, tool in self._tools.items():
                ns = tool.namespace
                namespaces.setdefault(ns, []).append({
                    "name": tool.tool_name,
                    "description": tool.short_description,
                })

            content = yaml.dump(namespaces, default_flow_style=False, sort_keys=True)
            return [TextResourceContents(uri=uri, mimeType="text/yaml", text=content)]

        raise ValueError(f"Unknown resource: {uri}")

    def _find_tool(self, mcp_name: str) -> ToolDefinition | None:
        registry_name = ToolNameConverter.to_registry(mcp_name)

        if registry_name in self._tools:
            return self._tools[registry_name]

        if mcp_name in self._tools:
            return self._tools[mcp_name]

        for key, tool in self._tools.items():
            if ToolNameConverter.to_mcp(key) == mcp_name:
                return tool

        return None

    async def _try_external_tool(
        self, registry_name: str, arguments: dict[str, Any]
    ) -> str | None:
        if not self._external_manager or "." not in registry_name:
            return None

        server_name, tool_name = registry_name.split(".", 1)
        configured_servers = self._external_manager.get_configured_servers()

        if server_name in configured_servers:
            return await self._external_manager.call_tool(
                server_name, tool_name, arguments
            )

        return None

    async def _call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        tool = self._find_tool(name)

        if not tool:
            registry_name = ToolNameConverter.to_registry(name)
            external_result = await self._try_external_tool(registry_name, arguments)
            if external_result is not None:
                return [TextContent(type="text", text=external_result)]
            return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

        if tool.is_external:
            if self._external_manager and tool.external_server and tool.original_name:
                result = await self._external_manager.call_tool(
                    tool.external_server, tool.original_name, arguments
                )
                return [TextContent(type="text", text=result)]
            return [TextContent(type="text", text="Error: External server not available")]

        result = ToolExecutor.execute(tool, arguments)
        return [TextContent(type="text", text=result)]

    def _add_src_to_path(self) -> None:
        src_path = self._config.project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

    async def _load_tools(self) -> None:
        registry_data = _core.load_registry(self._config.tool_defs_path)
        registry = ToolRegistry.from_dict(registry_data)

        for tool in registry.tools:
            self._tools[tool.name] = tool

        print(
            f"Loaded {len(self._tools)} tools from {self._config.tool_defs_path}",
            file=sys.stderr,
        )

    async def _start_external_servers(
        self, mcp_servers: dict[str, dict[str, Any]]
    ) -> None:
        if not mcp_servers:
            return

        self._external_manager = ExternalServerManager()

        try:
            from agent_tools.mcp.connect import set_manager

            set_manager(self._external_manager)
        except ImportError:
            pass

        await self._external_manager.start_all(mcp_servers)

        for tool_dict in self._external_manager.get_all_tools():
            tool = ToolDefinition.from_dict(tool_dict)
            self._tools[tool.name] = tool

        print(
            f"Loaded {len(self._external_manager.get_all_tools())} external tools "
            f"from {len(mcp_servers)} MCP servers",
            file=sys.stderr,
        )

    async def _cleanup(self) -> None:
        if self._external_manager:
            await self._external_manager.stop_all()

    async def run(self) -> None:
        self._add_src_to_path()
        await self._load_tools()

        registry_data = _core.load_registry(self._config.tool_defs_path)
        await self._start_external_servers(registry_data.get("mcp_servers", {}))

        try:
            async with stdio_server() as (read_stream, write_stream):
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options(),
                )
        finally:
            await self._cleanup()


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        config_path = _core.find_tool_defs()
    else:
        config_path = Path(sys.argv[1])
        if not config_path.exists():
            print(f"Error: Tool defs not found: {config_path}", file=sys.stderr)
            sys.exit(1)

    # If given agent-tools.yaml, use the sibling tool_defs directory
    if config_path and config_path.name == "agent-tools.yaml":
        tool_defs_dir = config_path.parent / "tool_defs"
        if tool_defs_dir.exists():
            config_path = tool_defs_dir

    if config_path:
        print(f"Using tool_defs: {config_path}", file=sys.stderr)
        server_config = ServerConfig.from_path(config_path)
    else:
        print("No tool_defs/ found, starting with empty registry.", file=sys.stderr)
        print("Run 'agent-tools init' to create one.", file=sys.stderr)
        server_config = ServerConfig(tool_defs_path=Path.cwd(), project_root=Path.cwd())

    agent_server = AgentToolsServer(server_config)
    asyncio.run(agent_server.run())


if __name__ == "__main__":
    main()

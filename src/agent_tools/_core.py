"""Core data models and registry operations for agent-tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "PROJECT_ROOT",
    "TOOL_DEFS_DIR",
    "SRC_DIR",
    "TESTS_DIR",
    "ToolParameter",
    "ToolDefinition",
    "ToolRegistry",
    "load_registry",
    "load_tool",
    "save_tool",
    "delete_tool",
    "find_tool_defs",
]

PROJECT_ROOT = Path(__file__).parent.parent.parent
TOOL_DEFS_DIR = PROJECT_ROOT / "tool_defs"
SRC_DIR = Path(__file__).parent
TESTS_DIR = PROJECT_ROOT / "tests"
USER_CONFIG_DIR = Path.home() / ".config" / "agent-tools"


@dataclass(frozen=True)
class ToolParameter:
    """A single parameter for a tool."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolParameter:
        return cls(
            name=data.get("name", ""),
            type=data.get("type", "string"),
            description=data.get("description", ""),
            required=data.get("required", True),
            default=data.get("default"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            result["default"] = self.default
        return result

    @property
    def python_type(self) -> str:
        type_map = {"string": "str", "integer": "int", "boolean": "bool", "number": "float"}
        return type_map.get(self.type, "str")


@dataclass
class ToolDefinition:
    """Definition of a tool including its metadata and implementation location."""

    name: str
    description: str = ""
    module: str = ""
    function: str = ""
    parameters: list[ToolParameter] = field(default_factory=list)
    is_external: bool = False
    external_server: str = ""
    original_name: str = ""

    @property
    def namespace(self) -> str:
        return self.name.split(".", 1)[0] if "." in self.name else "root"

    @property
    def tool_name(self) -> str:
        return self.name.split(".", 1)[1] if "." in self.name else self.name

    @property
    def function_name(self) -> str:
        return self.tool_name.replace("-", "_")

    @property
    def class_name(self) -> str:
        return "".join(word.capitalize() for word in self.tool_name.split("-"))

    @property
    def short_description(self) -> str:
        return self.description.split("\n")[0][:60]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolDefinition:
        parameters = [
            ToolParameter.from_dict(p) if isinstance(p, dict) else p
            for p in data.get("parameters", [])
        ]
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            module=data.get("module", ""),
            function=data.get("function", ""),
            parameters=parameters,
            is_external=data.get("_external", False),
            external_server=data.get("_server", ""),
            original_name=data.get("_original_name", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "module": self.module,
            "function": self.function,
            "parameters": [p.to_dict() for p in self.parameters],
        }
        if self.is_external:
            result["_external"] = True
            result["_server"] = self.external_server
            result["_original_name"] = self.original_name
        return result


@dataclass
class ToolRegistry:
    """Collection of tool definitions and MCP server configurations."""

    tools: list[ToolDefinition] = field(default_factory=list)
    mcp_servers: dict[str, dict[str, Any]] = field(default_factory=dict)

    def find_tool(self, name: str) -> ToolDefinition | None:
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def has_tool(self, name: str) -> bool:
        return self.find_tool(name) is not None

    def add_tool(self, tool: ToolDefinition) -> None:
        if self.has_tool(tool.name):
            raise ValueError(f"Tool '{tool.name}' already exists")
        self.tools.append(tool)

    def remove_tool(self, name: str) -> bool:
        for i, tool in enumerate(self.tools):
            if tool.name == name:
                self.tools.pop(i)
                return True
        return False

    def tools_by_namespace(self) -> dict[str, list[ToolDefinition]]:
        namespaces: dict[str, list[ToolDefinition]] = {}
        for tool in self.tools:
            namespaces.setdefault(tool.namespace, []).append(tool)
        return namespaces

    def to_dict(self) -> dict[str, Any]:
        return {
            "tools": [t.to_dict() for t in self.tools],
            "mcp_servers": self.mcp_servers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolRegistry:
        tools = [ToolDefinition.from_dict(t) for t in data.get("tools", [])]
        return cls(tools=tools, mcp_servers=data.get("mcp_servers", {}))


class ToolPath:
    """Handles conversion between tool names and file paths."""

    @staticmethod
    def to_name(path: Path, base_dir: Path) -> str:
        rel_path = path.relative_to(base_dir)
        parts = list(rel_path.parts)
        parts[-1] = parts[-1].replace(".yaml", "")
        return ".".join(parts)

    @staticmethod
    def to_path(name: str, base_dir: Path) -> Path:
        parts = name.split(".")
        if len(parts) < 2:
            raise ValueError(f"Tool name must have namespace: {name}")
        namespace = parts[0]
        tool_name = ".".join(parts[1:])
        return base_dir / namespace / f"{tool_name}.yaml"


def _path_to_tool_name(path: Path, base_dir: Path) -> str:
    return ToolPath.to_name(path, base_dir)


def _tool_name_to_path(name: str, base_dir: Path) -> Path:
    return ToolPath.to_path(name, base_dir)


def load_tool(path: Path) -> dict[str, Any] | None:
    """Load a single tool definition from a YAML file."""
    if not path.exists():
        return None
    with path.open() as f:
        return yaml.safe_load(f)


def save_tool(name: str, tool_def: dict[str, Any], base_dir: Path | None = None) -> Path:
    """Save a tool definition to the appropriate YAML file."""
    base = base_dir or TOOL_DEFS_DIR
    path = ToolPath.to_path(name, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    tool_def["name"] = name

    with path.open("w") as f:
        yaml.dump(tool_def, f, default_flow_style=False, sort_keys=False)

    return path


def delete_tool(name: str, base_dir: Path | None = None) -> bool:
    """Delete a tool definition file."""
    base = base_dir or TOOL_DEFS_DIR
    path = ToolPath.to_path(name, base)

    if path.exists():
        path.unlink()
        return True
    return False


def find_tool_defs(base_dir: Path | None = None) -> Path | None:
    """Find the tool_defs directory by searching standard locations."""
    import sys

    if base_dir and base_dir.exists():
        return base_dir

    if TOOL_DEFS_DIR.exists():
        return TOOL_DEFS_DIR

    local = Path.cwd() / "tool_defs"
    if local.exists():
        return local

    user_config = USER_CONFIG_DIR / "tool_defs"
    if user_config.exists():
        return user_config

    # Check installed package share directory
    share_path = Path(sys.prefix) / "share" / "agent-tools" / "tool_defs"
    if share_path.exists():
        return share_path

    return None


def _load_tools_from_directory(base_dir: Path) -> list[dict[str, Any]]:
    """Load all tool definitions from a directory."""
    tools = []
    for yaml_file in sorted(base_dir.rglob("*.yaml")):
        if "_servers" in yaml_file.parts:
            continue

        tool_def = load_tool(yaml_file)
        if tool_def:
            expected_name = ToolPath.to_name(yaml_file, base_dir)
            if "name" not in tool_def:
                tool_def["name"] = expected_name
            elif tool_def["name"] != expected_name:
                print(
                    f"Warning: Tool name mismatch in {yaml_file}: "
                    f"'{tool_def['name']}' != '{expected_name}'"
                )
            tools.append(tool_def)
    return tools


def _load_mcp_servers(base_dir: Path) -> dict[str, dict[str, Any]]:
    """Load MCP server configurations from _servers directory."""
    servers: dict[str, dict[str, Any]] = {}
    servers_dir = base_dir / "_servers"

    if servers_dir.exists():
        for yaml_file in sorted(servers_dir.glob("*.yaml")):
            server_def = load_tool(yaml_file)
            if server_def:
                servers[yaml_file.stem] = server_def

    return servers


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load the tool registry from tool_defs/ directory.

    Returns a dictionary for backward compatibility. Use ToolRegistry.from_dict()
    to convert to the typed dataclass.
    """
    base_dir = path or find_tool_defs() or TOOL_DEFS_DIR

    if not base_dir.exists():
        return {"tools": [], "mcp_servers": {}}

    return {
        "tools": _load_tools_from_directory(base_dir),
        "mcp_servers": _load_mcp_servers(base_dir),
    }

"""Registry operations for managing tool definitions."""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path

import agent_tools._core as _core
from agent_tools._core import ToolDefinition, ToolParameter, ToolRegistry
from agent_tools._template import COMMAND_TEMPLATE, INIT_TEMPLATE, STUB_TEMPLATE, TEST_TEMPLATE

__all__ = [
    "CommandGenerator",
    "StubGenerator",
    "ToolManager",
    "add_tool",
    "remove_tool",
    "update_tool",
    "list_tools",
    "validate_registry",
    "execute_tool",
    "generate_commands",
]


@dataclass
class StubGenerator:
    """Generates Python module and test stubs for new tools."""

    src_dir: Path
    tests_dir: Path

    def _typed_params(self, parameters: list[ToolParameter]) -> str:
        if not parameters:
            return ""

        parts = []
        for param in parameters:
            signature = f"{param.name}: {param.python_type}"
            if not param.required:
                signature += " = None"
            parts.append(signature)
        return ", ".join(parts)

    def _param_docs(self, parameters: list[ToolParameter]) -> str:
        if not parameters:
            return "        None"
        return "\n".join(
            f"        {p.name}: {p.description or 'No description'}" for p in parameters
        )

    def _test_args(self, parameters: list[ToolParameter]) -> str:
        if not parameters:
            return ""

        type_defaults = {
            "string": lambda p: f'"{p.name}_value"',
            "integer": lambda _: "0",
            "boolean": lambda _: "False",
        }
        return ", ".join(
            type_defaults.get(p.type, lambda _: '""')(p) for p in parameters
        )

    def _ensure_namespace_init(self, namespace_dir: Path, namespace: str) -> None:
        init_file = namespace_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(INIT_TEMPLATE.format(namespace=namespace))

    def create_module(self, tool: ToolDefinition) -> Path:
        namespace_dir = self.src_dir / tool.namespace
        namespace_dir.mkdir(exist_ok=True)
        self._ensure_namespace_init(namespace_dir, tool.namespace)

        content = STUB_TEMPLATE.format(
            namespace=tool.namespace,
            tool_name=tool.tool_name,
            short_description=tool.short_description,
            function_name=tool.function_name,
            typed_params=self._typed_params(tool.parameters),
            description=tool.description.strip(),
            param_docs=self._param_docs(tool.parameters),
        )

        module_file = namespace_dir / f"{tool.function_name}.py"
        module_file.write_text(content)
        return module_file

    def create_test(self, tool: ToolDefinition) -> Path:
        test_namespace_dir = self.tests_dir / f"test_{tool.namespace}"
        test_namespace_dir.mkdir(exist_ok=True)

        init_file = test_namespace_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""Tests for {tool.namespace} tools."""\n')

        content = TEST_TEMPLATE.format(
            namespace=tool.namespace,
            tool_name=tool.tool_name,
            module_name=tool.function_name,
            function_name=tool.function_name,
            class_name=tool.class_name,
            test_args=self._test_args(tool.parameters),
        )

        test_file = test_namespace_dir / f"test_{tool.function_name}.py"
        test_file.write_text(content)
        return test_file


@dataclass
class CommandGenerator:
    """Generates Cursor command files from tool definitions."""

    output_dir: Path

    def _format_title(self, tool: ToolDefinition) -> str:
        """Convert tool name to human-readable title."""
        # Convert 'think.about' to 'Think About', 'github.my-prs' to 'Github My PRs'
        # Special acronyms that should be styled specifically
        acronyms = {"prs": "PRs", "api": "API", "url": "URL", "id": "ID"}
        words = tool.name.replace(".", "-").replace("-", " ").split()
        return " ".join(acronyms.get(word.lower(), word.capitalize()) for word in words)

    def _format_parameters(self, tool: ToolDefinition) -> str:
        """Format parameters as markdown list."""
        if not tool.parameters:
            return "None"

        lines = []
        for param in tool.parameters:
            required = "required" if param.required else "optional"
            desc = param.description or "No description"
            lines.append(f"- **{param.name}** ({required}): {desc}")
        return "\n".join(lines)

    def _format_example(self, tool: ToolDefinition) -> str:
        """Generate a simple usage example."""
        if not tool.parameters:
            return ""
        # Generate example based on first required parameter or first optional
        required_params = [p for p in tool.parameters if p.required]
        if required_params:
            command_name = tool.name.replace(".", "-").replace("-", " ")
            return f'\n\nExample: "Run {command_name} with {required_params[0].name}"'
        return ""

    def generate_command(self, tool: ToolDefinition) -> str:
        """Generate markdown content for a single tool."""
        return COMMAND_TEMPLATE.format(
            title=self._format_title(tool),
            description=tool.description.strip(),
            parameters=self._format_parameters(tool),
            tool_name=tool.name,
            example=self._format_example(tool),
        )

    def generate_one(self, tool: ToolDefinition) -> Path:
        """Generate command file for a single tool."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        content = self.generate_command(tool)
        command_file = self.output_dir / f"{tool.name.replace('.', '-')}.md"
        command_file.write_text(content)
        return command_file

    def generate_all(self, tools: list[ToolDefinition]) -> list[Path]:
        """Generate command files for all tools."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        created = []
        for tool in tools:
            path = self.generate_one(tool)
            created.append(path)
        return created

    def sync(self, tools: list[ToolDefinition]) -> dict[str, list[Path]]:
        """Sync command files: create missing, remove stale."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track expected files
        expected_files = {f"{tool.name.replace('.', '-')}.md" for tool in tools}

        # Generate all commands
        created = self.generate_all(tools)

        # Find and remove stale files
        removed = []
        if self.output_dir.exists():
            for existing in self.output_dir.glob("*.md"):
                if existing.name not in expected_files:
                    existing.unlink()
                    removed.append(existing)

        return {"created": created, "removed": removed}


@dataclass
class ValidationResult:
    """Result of registry validation."""

    tool_count: int
    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def format(self) -> str:
        lines = [f"Validated {self.tool_count} tools"]

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            lines.extend(f"  ✗ {err}" for err in self.errors)

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            lines.extend(f"  ⚠ {warn}" for warn in self.warnings)

        if not self.errors and not self.warnings:
            lines.append("\n✓ No issues found")

        return "\n".join(lines)


class ToolManager:
    """Manages tool CRUD operations and validation."""

    def __init__(
        self,
        stub_generator: StubGenerator | None = None,
        tool_defs_dir: Path | None = None,
        commands_dir: Path | None = None,
    ):
        self._stub_generator = stub_generator or StubGenerator(_core.SRC_DIR, _core.TESTS_DIR)
        self._tool_defs_dir = tool_defs_dir or _core.TOOL_DEFS_DIR
        self._commands_dir = commands_dir

    def _load_registry(self) -> ToolRegistry:
        data = _core.load_registry(self._tool_defs_dir)
        return ToolRegistry.from_dict(data)

    def _parse_parameters(self, parameters_json: str) -> list[ToolParameter]:
        if not parameters_json:
            return []
        params_list = json.loads(parameters_json)
        return [ToolParameter.from_dict(p) for p in params_list]

    def add(self, name: str, description: str, parameters: str) -> str:
        if "." not in name:
            return f"Error: Tool name must include namespace: 'namespace.tool-name', got '{name}'"

        try:
            params = self._parse_parameters(parameters)
        except json.JSONDecodeError as e:
            return f"Error: Invalid parameters JSON: {e}"

        registry = self._load_registry()
        if registry.has_tool(name):
            return f"Error: Tool '{name}' already exists. Use registry.update to modify."

        tool = ToolDefinition(
            name=name,
            description=description,
            module=f"agent_tools.{name.split('.')[0]}.{name.split('.', 1)[1].replace('-', '_')}",
            function=name.split(".", 1)[1].replace("-", "_"),
            parameters=params,
        )

        module_file = self._stub_generator.create_module(tool)
        test_file = self._stub_generator.create_test(tool)
        tool_def_file = _core.save_tool(name, tool.to_dict(), self._tool_defs_dir)

        # Generate Cursor command if commands_dir is configured
        command_file = None
        if self._commands_dir:
            cmd_gen = CommandGenerator(self._commands_dir)
            command_file = cmd_gen.generate_one(tool)

        files_created = [
            f"  {tool_def_file.relative_to(_core.PROJECT_ROOT)}  ← Tool definition",
            f"  {module_file.relative_to(_core.PROJECT_ROOT)}  ← Implement here",
            f"  {test_file.relative_to(_core.PROJECT_ROOT)}  ← Add tests",
        ]
        if command_file:
            files_created.append(f"  {command_file.relative_to(_core.PROJECT_ROOT)}  ← Cursor command")

        return f"""Created tool: {name}

Files created:
{chr(10).join(files_created)}

Next steps:
  1. Implement the function in {tool.function_name}.py
  2. Run: uv run pytest {test_file.relative_to(_core.PROJECT_ROOT)}
  3. Restart MCP server to use the tool
"""

    def remove(self, name: str) -> str:
        registry = self._load_registry()
        if not registry.has_tool(name):
            return f"Error: Tool '{name}' not found in registry."

        if _core.delete_tool(name, self._tool_defs_dir):
            return f"""Removed tool: {name}

Note: Python module and tests were NOT deleted.
To fully remove, delete the files manually if needed.
"""
        return f"Error: Could not delete tool definition for '{name}'."

    def update(self, name: str, description: str = "", parameters: str = "") -> str:
        registry = self._load_registry()
        tool = registry.find_tool(name)

        if not tool:
            return f"Error: Tool '{name}' not found. Use registry.add for new tools."

        updated_fields = []
        tool_dict = tool.to_dict()

        if description:
            tool_dict["description"] = description
            updated_fields.append("description")

        if parameters:
            try:
                tool_dict["parameters"] = json.loads(parameters)
                updated_fields.append("parameters")
            except json.JSONDecodeError as e:
                return f"Error: Invalid parameters JSON: {e}"

        if not updated_fields:
            return "No fields to update. Provide description or parameters."

        _core.save_tool(name, tool_dict, self._tool_defs_dir)

        return f"""Updated tool: {name}

Fields updated: {', '.join(updated_fields)}

Note: Python module was NOT modified.
Update the implementation manually if the interface changed.
"""

    def list(self) -> str:
        registry = self._load_registry()
        namespaces = registry.tools_by_namespace()

        output_lines = ["tools:"]
        for ns in sorted(namespaces.keys()):
            output_lines.append(f"  {ns}:")
            for tool in sorted(namespaces[ns], key=lambda t: t.tool_name):
                output_lines.append(f"    {tool.tool_name}: {tool.short_description}")

        return "\n".join(output_lines)

    def validate(self) -> ValidationResult:
        registry = self._load_registry()
        errors: list[str] = []
        warnings: list[str] = []
        seen_names: set[str] = set()

        for i, tool in enumerate(registry.tools):
            if not tool.name:
                errors.append(f"Tool {i}: Missing 'name' field")
                continue

            if not tool.description:
                warnings.append(f"{tool.name}: Missing description")

            if not tool.module:
                errors.append(f"{tool.name}: Missing 'module' field")

            if tool.name in seen_names:
                errors.append(f"{tool.name}: Duplicate tool name")
            seen_names.add(tool.name)

            if tool.module and not tool.module.startswith("agent_tools.registry"):
                parts = tool.module.replace("agent_tools.", "").split(".")
                if parts:
                    module_file = _core.SRC_DIR / "/".join(parts[:-1]) / f"{parts[-1]}.py"
                    if not module_file.exists():
                        rel_path = module_file.relative_to(_core.PROJECT_ROOT)
                        warnings.append(f"{tool.name}: Module not found: {rel_path}")

            for param in tool.parameters:
                if not param.name:
                    errors.append(f"{tool.name}: Parameter missing 'name' field")

        return ValidationResult(len(registry.tools), errors, warnings)

    def execute(self, name: str, params: str) -> str:
        registry = self._load_registry()
        tool = registry.find_tool(name)

        if not tool:
            return f"Error: Tool '{name}' not found. Use registry-list to see available tools."

        if not tool.module or not tool.function:
            return f"Error: Tool '{name}' has invalid configuration (missing module or function)."

        try:
            params_dict = json.loads(params) if params else {}
        except json.JSONDecodeError as e:
            return f"Error: Invalid params JSON: {e}"

        try:
            module = importlib.import_module(tool.module)
            func = getattr(module, tool.function)
            return str(func(**params_dict))
        except ImportError as e:
            return f"Error importing {tool.module}: {e}"
        except AttributeError:
            return f"Error: Function '{tool.function}' not found in {tool.module}"
        except TypeError as e:
            return f"Error: Invalid parameters for {name}: {e}"
        except Exception as e:
            return f"Error executing {name}: {e}"


_default_manager: ToolManager | None = None


def _get_manager() -> ToolManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = ToolManager()
    return _default_manager


def _reset_manager() -> None:
    """Reset the default manager (used in testing)."""
    global _default_manager
    _default_manager = None


def add_tool(name: str, description: str, parameters: str) -> str:
    """Add a new tool to the registry."""
    return _get_manager().add(name, description, parameters)


def remove_tool(name: str) -> str:
    """Remove a tool from the registry."""
    return _get_manager().remove(name)


def update_tool(name: str, description: str = "", parameters: str = "") -> str:
    """Update an existing tool's definition."""
    return _get_manager().update(name, description, parameters)


def list_tools() -> str:
    """List all tools in the registry, organized by namespace."""
    return _get_manager().list()


def validate_registry() -> str:
    """Validate the registry for common errors."""
    return _get_manager().validate().format()


def execute_tool(name: str, params: str) -> str:
    """Execute any tool by name."""
    return _get_manager().execute(name, params)


def generate_commands(output_dir: Path | str | None = None, sync: bool = False) -> str:
    """Generate Cursor command files for all tools.

    Args:
        output_dir: Directory to write commands to (default: .cursor/commands)
        sync: If True, remove stale command files

    Returns:
        Summary of generated commands.
    """
    if output_dir is None:
        output_dir = Path.cwd() / ".cursor" / "commands"
    elif isinstance(output_dir, str):
        output_dir = Path(output_dir)

    manager = _get_manager()
    registry = manager._load_registry()
    generator = CommandGenerator(output_dir)

    if sync:
        result = generator.sync(registry.tools)
        created = result["created"]
        removed = result["removed"]
        lines = [f"Generated {len(created)} commands to {output_dir}"]
        if removed:
            lines.append(f"Removed {len(removed)} stale commands")
    else:
        created = generator.generate_all(registry.tools)
        lines = [f"Generated {len(created)} commands to {output_dir}"]

    # List created files
    if created:
        lines.append("\nCommands:")
        for path in sorted(created):
            lines.append(f"  /{path.stem}")

    return "\n".join(lines)

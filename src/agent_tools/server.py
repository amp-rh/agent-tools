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
    "registry.list",
    "registry.reload",
    "observe.log",
    "observe.trace-call",
    "observe.session",
    "think.about",
})

WORKFLOW_PROMPT = """\
I should check what tools are available before attempting this task.
Let me call `registry-list` first.

If a tool exists, I'll use it.
If not and this task is repeatable, I'll create one with `registry-add` first.

Every repeatable process becomes a tool. My job is to think. Tools do the work."""

MCP_FROM_COMMANDS_PROMPT = """\
## Extract MCP Tools from Cursor Commands

Scan commands in `.cursor/commands/` or `~/.cursor/commands/` and extract those that \
aren't yet MCP tools.

### Identification

Commands that are NOT yet MCP tools have detailed instructions instead of:
```
Use the `namespace.tool` MCP tool.
```

### Extraction Workflow (per command)

1. **Analyze**: Read command file, understand what it does
2. **Design**: Determine namespace, tool name, parameters
3. **Create**: `registry.add(name, description, parameters)`
4. **Test**: Write tests FIRST (TDD) in `tests/test_<namespace>/`
5. **Implement**: Code the tool in generated stub
6. **Verify**: `uv run pytest tests/test_<namespace>/test_<tool>.py`
7. **Lint**: `uv run ruff check --fix`
8. **Update command**: Change to "Use the `namespace.tool` MCP tool."
9. **Sync**: Copy to `~/.cursor/commands/`

### Namespace Guidelines

| Domain | Namespace | Examples |
|--------|-----------|----------|
| Git operations | `git` | commit, update-prs |
| Cursor IDE | `cursor` | create-command, sync-commands |
| MCP operations | `mcp` | inspect, connect |
| Agent notes | `notes` | todo |
| Code operations | `code` | lint, refactor |

### Common Patterns

- **CLI tools**: Use `subprocess.run()` with `capture_output=True, text=True`
- **File operations**: Use `Path.cwd()` / `Path.home()`, mock in tests
- **Config files**: Parse with `json.loads()`, handle errors gracefully
- **Output**: Return structured markdown with `## Headers`

### After All Extractions

Update `.cursor/discovery/mcp-from-commands.md` with status."""

REFACTOR_FUNCTION_PROMPT = """\
## Refactor Function Workflow

Step-by-step guide for refactoring a specific function to improve quality.

### 1. Analyze the Function

Run `code.complexity` on the file to get metrics:
- Cyclomatic complexity (target: <= 5)
- Lines of code (target: <= 20)
- Nesting depth (target: <= 3)
- Parameter count (target: <= 4)

### 2. Identify Issues

Common problems to look for:
- **Too long**: Extract smaller functions with clear names
- **Too complex**: Simplify conditionals, use early returns
- **Too many params**: Use parameter objects or builder pattern
- **Deep nesting**: Use guard clauses to flatten

### 3. Apply Refactoring Patterns

| Issue | Pattern | Example |
|-------|---------|---------|
| Long function | Extract Method | Move code blocks to named functions |
| Complex conditionals | Replace Conditional with Polymorphism | Use strategy pattern |
| Deep nesting | Guard Clauses | Return early for edge cases |
| Many parameters | Parameter Object | Group related params into a class |
| Duplicate code | Extract and Share | Create utility function |

### 4. Verify Changes

After refactoring:
1. Run tests to ensure behavior unchanged
2. Run `code.complexity` again to verify improvement
3. Run `code.lint` to fix any style issues

### 5. Document

Add/update docstrings explaining:
- What the function does
- Parameters and return value
- Any important behavior"""

EXTRACT_RESPONSIBILITY_PROMPT = """\
## Extract Responsibility Workflow

Apply Single Responsibility Principle (SRP) by extracting mixed responsibilities.

### 1. Identify Mixed Responsibilities

Signs a class/module has too many responsibilities:
- Multiple unrelated public methods
- Methods that don't use the same instance variables
- "And" in the class description (e.g., "parses AND validates AND saves")
- Large file size (> 300 lines often indicates multiple concerns)

### 2. Group Related Functionality

For each responsibility:
1. List the methods that belong together
2. Identify shared state they use
3. Name the responsibility clearly

### 3. Plan the Extraction

Create a plan with:
- New module/class name (noun describing the responsibility)
- Methods to move
- State to move
- Interface between old and new code

### 4. Execute Extraction

Step by step:
1. Create new module/class with the extracted methods
2. Update imports in the original module
3. Replace direct calls with delegation or dependency injection
4. Run tests after each change

### 5. Verify with Architecture Analysis

Run `code.architecture` to check:
- No circular dependencies introduced
- Proper layer boundaries maintained
- Dependency direction is correct (outer depends on inner)

### Example

Before:
```python
class UserService:
    def create_user(self, data): ...      # Business logic
    def validate_email(self, email): ...  # Validation
    def send_welcome_email(self, user): ...  # Email sending
    def save_to_database(self, user): ...    # Persistence
```

After:
```python
class UserService:           # Just business logic
class EmailValidator:        # Validation concern
class EmailSender:          # Email concern
class UserRepository:       # Persistence concern
```"""

CLEAN_ARCHITECTURE_REVIEW_PROMPT = """\
## Clean Architecture Review Checklist

Use this checklist to verify a codebase follows clean architecture principles.

### Layer Structure

Verify the codebase has clear layers:

- [ ] **Domain/Entities**: Core business objects and rules
  - No framework dependencies
  - No database/external service dependencies
  - Pure Python classes

- [ ] **Application/Use Cases**: Business operations
  - Orchestrates domain objects
  - Defines interfaces for external dependencies
  - No direct infrastructure imports

- [ ] **Interface/Adapters**: Controllers, presenters, gateways
  - Implements interfaces defined in application layer
  - Converts between external and internal formats

- [ ] **Infrastructure**: Frameworks, DB, external services
  - Implements interfaces from inner layers
  - Contains all framework-specific code

### Dependency Direction

Run `code.architecture` and verify:

- [ ] No circular dependencies
- [ ] Domain layer has NO imports from other layers
- [ ] Application layer only imports from domain
- [ ] Infrastructure imports from all inner layers (allowed)

### Interface Segregation

- [ ] Interfaces are small and focused
- [ ] Clients don't depend on methods they don't use
- [ ] Abstract base classes define clear contracts

### Dependency Inversion

- [ ] High-level modules don't import low-level modules
- [ ] Both depend on abstractions (interfaces)
- [ ] Abstractions live in inner layers

### Common Violations

| Violation | Fix |
|-----------|-----|
| Domain imports database | Create repository interface |
| Use case calls HTTP directly | Inject HTTP client interface |
| Controller has business logic | Move to use case |
| Entity depends on framework | Create pure domain model |

### After Review

Document findings in `.cursor/discovery/architecture-review.md`:
- Current state assessment
- Violations found
- Remediation plan with priority"""

CLEAN_CODE_RESOURCE = """\
# Clean Code Principles Reference

## SOLID Principles

### Single Responsibility (SRP)
A class should have only one reason to change.
- One class = one responsibility
- If you can't describe it without "and", split it

### Open/Closed (OCP)
Open for extension, closed for modification.
- Use inheritance or composition for new behavior
- Don't modify existing working code

### Liskov Substitution (LSP)
Subtypes must be substitutable for their base types.
- Override methods should honor base contract
- Don't throw unexpected exceptions

### Interface Segregation (ISP)
Many specific interfaces > one general interface.
- Clients shouldn't depend on unused methods
- Split large interfaces into focused ones

### Dependency Inversion (DIP)
Depend on abstractions, not concretions.
- High-level modules don't import low-level
- Both depend on interfaces

## Function Design

### Size
- Keep functions small (< 20 lines ideal)
- Do one thing well
- One level of abstraction per function

### Naming
- Use descriptive names
- Verb for actions: `calculate_total`, `send_email`
- Noun for getters: `get_user`, `find_orders`

### Parameters
- Fewer is better (0-2 ideal, 3 max)
- Use parameter objects for many params
- Avoid boolean flags (split into two functions)

### Return Values
- Return early for edge cases
- Single return type (don't mix None/value)
- Use exceptions for errors, not return codes

## Naming Conventions

### Variables
- Descriptive and pronounceable
- Avoid abbreviations except common ones (id, url)
- Scope-appropriate length (loop: i, class: user_repository)

### Functions
- Verb + noun: `validate_email`, `create_order`
- Question for booleans: `is_valid`, `has_permission`

### Classes
- Noun or noun phrase: `UserService`, `OrderProcessor`
- Avoid generic names: Manager, Processor, Data, Info

## Complexity Guidelines

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Cyclomatic complexity | <= 5 | 6-10 | > 10 |
| Function lines | <= 20 | 21-40 | > 40 |
| Nesting depth | <= 3 | 4 | > 4 |
| Parameters | <= 3 | 4-5 | > 5 |
| Class methods | <= 10 | 11-20 | > 20 |"""

REFACTORING_PATTERNS_RESOURCE = """\
# Common Refactoring Patterns

## Extract Method
**When**: Long function or duplicate code blocks
**How**: Move code to a new function with descriptive name

Before:
```python
def process_order(order):
    # validate
    if not order.items:
        raise ValueError("Empty order")
    if order.total < 0:
        raise ValueError("Invalid total")
    # process
    for item in order.items:
        inventory.reserve(item)
    payment.charge(order.total)
```

After:
```python
def process_order(order):
    validate_order(order)
    reserve_inventory(order)
    charge_payment(order)
```

## Replace Conditional with Polymorphism
**When**: Switch/if-else on type to determine behavior
**How**: Create subclasses or strategy objects

Before:
```python
def calculate_shipping(order):
    if order.type == "standard":
        return order.weight * 1.0
    elif order.type == "express":
        return order.weight * 2.5
    elif order.type == "overnight":
        return order.weight * 5.0
```

After:
```python
class ShippingStrategy:
    def calculate(self, order): ...

class StandardShipping(ShippingStrategy):
    def calculate(self, order):
        return order.weight * 1.0
```

## Introduce Parameter Object
**When**: Multiple parameters that travel together
**How**: Create a class to hold related parameters

Before:
```python
def create_user(name, email, street, city, zip_code, country):
    ...
```

After:
```python
@dataclass
class Address:
    street: str
    city: str
    zip_code: str
    country: str

def create_user(name, email, address: Address):
    ...
```

## Replace Magic Numbers with Constants
**When**: Literal values with unclear meaning
**How**: Extract to named constants

Before:
```python
if user.age >= 18:
    if user.orders > 10:
        discount = 0.15
```

After:
```python
LEGAL_AGE = 18
LOYAL_CUSTOMER_ORDERS = 10
LOYAL_CUSTOMER_DISCOUNT = 0.15

if user.age >= LEGAL_AGE:
    if user.orders > LOYAL_CUSTOMER_ORDERS:
        discount = LOYAL_CUSTOMER_DISCOUNT
```

## Guard Clauses (Replace Nested Conditionals)
**When**: Deep nesting from multiple conditions
**How**: Return early for edge cases

Before:
```python
def get_payment(order):
    if order:
        if order.is_paid:
            if order.payment:
                return order.payment
            else:
                return None
        else:
            return None
    else:
        return None
```

After:
```python
def get_payment(order):
    if not order:
        return None
    if not order.is_paid:
        return None
    return order.payment
```

## Decompose Conditional
**When**: Complex boolean expressions
**How**: Extract conditions to named functions/variables

Before:
```python
if (user.subscription == "premium" and
    user.orders > 5 and
    user.account_age > 365 and
    not user.has_violations):
    apply_discount()
```

After:
```python
def is_eligible_for_loyalty_discount(user):
    return (
        user.subscription == "premium" and
        user.orders > 5 and
        user.account_age > 365 and
        not user.has_violations
    )

if is_eligible_for_loyalty_discount(user):
    apply_discount()
```

## Replace Temp with Query
**When**: Temporary variable used once after calculation
**How**: Extract calculation to a method

Before:
```python
base_price = quantity * item_price
if base_price > 1000:
    return base_price * 0.95
return base_price
```

After:
```python
def base_price(self):
    return self.quantity * self.item_price

if self.base_price() > 1000:
    return self.base_price() * 0.95
return self.base_price()
```"""


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
        self._server.list_resource_templates()(self._list_resource_templates)

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
            ),
            Prompt(
                name="mcp-from-commands",
                description="Workflow for extracting MCP tools from Cursor command files",
            ),
            Prompt(
                name="refactor-function",
                description="Step-by-step guide for refactoring a function",
            ),
            Prompt(
                name="extract-responsibility",
                description="Workflow for applying Single Responsibility Principle",
            ),
            Prompt(
                name="clean-architecture-review",
                description="Checklist for reviewing clean architecture compliance",
            ),
        ]

    async def _get_prompt(
        self, name: str, arguments: dict[str, str] | None
    ) -> GetPromptResult:
        prompts = {
            "agent-tools-workflow": (
                "Agent's thought process: check tools first, create if needed",
                WORKFLOW_PROMPT,
            ),
            "mcp-from-commands": (
                "Workflow for extracting MCP tools from Cursor commands",
                MCP_FROM_COMMANDS_PROMPT,
            ),
            "refactor-function": (
                "Step-by-step guide for refactoring a function",
                REFACTOR_FUNCTION_PROMPT,
            ),
            "extract-responsibility": (
                "Workflow for applying Single Responsibility Principle",
                EXTRACT_RESPONSIBILITY_PROMPT,
            ),
            "clean-architecture-review": (
                "Checklist for reviewing clean architecture compliance",
                CLEAN_ARCHITECTURE_REVIEW_PROMPT,
            ),
        }

        if name in prompts:
            description, text = prompts[name]
            return GetPromptResult(
                description=description,
                messages=[
                    PromptMessage(
                        role="assistant",
                        content=TextContent(type="text", text=text),
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
            Resource(
                uri="agent-tools://clean-code",
                name="Clean Code Principles",
                description="SOLID principles, function design, naming conventions",
                mimeType="text/markdown",
            ),
            Resource(
                uri="agent-tools://refactoring-patterns",
                name="Refactoring Patterns",
                description="Common refactoring patterns with examples",
                mimeType="text/markdown",
            ),
        ]

    async def _list_resource_templates(self) -> list:
        """Return empty list - we don't have resource templates."""
        return []

    async def _read_resource(self, uri: str) -> list[TextResourceContents]:
        import yaml

        uri_str = str(uri)

        if uri_str == "agent-tools://registry":
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

        if uri_str == "agent-tools://clean-code":
            return [
                TextResourceContents(
                    uri=uri, mimeType="text/markdown", text=CLEAN_CODE_RESOURCE
                )
            ]

        if uri_str == "agent-tools://refactoring-patterns":
            return [
                TextResourceContents(
                    uri=uri, mimeType="text/markdown", text=REFACTORING_PATTERNS_RESOURCE
                )
            ]

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

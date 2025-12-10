# agent-tools

A self-modifying tool registry that lets AI agents create and manage their own tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=agent-tools&config=eyJjb21tYW5kIjoidXZ4IGdpdCtodHRwczovL2dpdGh1Yi5jb20vYW1wLXJoL2FnZW50LXRvb2xzLmdpdCBzZXJ2ZXIifQ%3D%3D)

## What It Does

agent-tools exposes a set of tools to AI assistants (like Claude in Cursor) that let them:

- **Create new tools** on the fly with `registry.add`
- **Execute tools** dynamically with `registry.execute`
- **Manage the registry** (list, update, remove, validate)

When an agent creates a tool, it generates:
- A YAML definition in `tool_defs/`
- A Python module stub ready for implementation
- A test stub

After implementing and restarting the MCP server, the new tool is available to the agent.

## Installation

```bash
# Using uv (recommended)
uv add git+https://github.com/amp-rh/agent-tools.git

# Using pip
pip install git+https://github.com/amp-rh/agent-tools.git
```

## Quick Start

```bash
# Initialize in your project directory
agent-tools init

# This creates:
#   tool_defs/           - YAML tool definitions
#   src/agent_tools/     - Python implementations
#   tests/               - Test stubs
```

Then add to your MCP config (e.g., `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "agent-tools": {
      "command": "agent-tools-server",
      "args": ["/path/to/your/tool_defs"]
    }
  }
}
```

Restart your AI assistant and the tools are available.

## Architecture

```
tool_defs/
├── _servers/              # External MCP server configs
│   └── github.yaml
├── registry/              # Built-in registry tools
│   ├── add.yaml
│   ├── remove.yaml
│   └── ...
└── mytools/               # Your custom tools
    └── my-tool.yaml

src/agent_tools/
├── _core.py               # Dataclasses: ToolParameter, ToolDefinition, ToolRegistry
├── registry.py            # StubGenerator, ToolManager, ValidationResult
├── server.py              # AgentToolsServer (MCP server)
└── mytools/
    └── my_tool.py         # Your implementation
```

### Key Classes

- **`ToolDefinition`** - Dataclass representing a tool with name, description, module, function, parameters
- **`ToolRegistry`** - Collection of tools with `find_tool()`, `has_tool()`, `tools_by_namespace()`
- **`StubGenerator`** - Creates Python module and test stubs from tool definitions
- **`ToolManager`** - CRUD operations for tool definitions
- **`AgentToolsServer`** - MCP server that exposes tools to AI assistants

## Creating Tools Manually

1. Create a YAML definition in `tool_defs/namespace/tool-name.yaml`:

```yaml
name: mytools.greet
description: Greet a user by name
module: agent_tools.mytools.greet
function: greet
parameters:
  - name: name
    type: string
    description: The name to greet
    required: true
```

2. Create the Python module at `src/agent_tools/mytools/greet.py`:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

3. Restart the MCP server.

## CLI Commands

| Command | Description |
|---------|-------------|
| `agent-tools init` | Initialize tool_defs in current directory |
| `agent-tools server` | Run the MCP server |
| `agent-tools list` | List all registered tools |
| `agent-tools validate` | Check registry for errors |

## Built-in Tools

| Namespace | Tools | Purpose |
|-----------|-------|---------|
| `registry` | add, remove, update, list, validate, execute | Manage the tool registry |
| `agent` | start-here, begin | Workflow guidance for agents |
| `mcp` | add, connect, disconnect, list, remove | Manage external MCP servers |
| `code` | lint, refactor | Code quality tools |
| `docs` | write-findings | Documentation generation |
| `think` | about | Structured thinking |

## External MCP Servers

You can proxy other MCP servers through agent-tools. Add a config to `tool_defs/_servers/`:

```yaml
# tool_defs/_servers/github.yaml
command: npx
args:
  - -y
  - '@modelcontextprotocol/server-github'
env:
  GITHUB_PERSONAL_ACCESS_TOKEN: ${GITHUB_PAT}
```

The server starts lazily when a tool from that namespace is called.

## Development

```bash
git clone https://github.com/amp-rh/agent-tools.git
cd agent-tools

uv sync           # Install dependencies
uv run pytest     # Run tests (79 tests)
uv run ruff check # Lint
```

## How It Works Internally

1. **Server startup**: `AgentToolsServer` loads all YAML files from `tool_defs/`
2. **Tool discovery**: Each YAML becomes a `ToolDefinition` in the `ToolRegistry`
3. **MCP exposure**: Only entry-point tools (`agent.start-here`, `registry.execute`) are directly exposed
4. **Tool execution**: `registry.execute` can invoke any tool by name, importing its module dynamically
5. **Tool creation**: `registry.add` uses `StubGenerator` to create YAML + Python + test files

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

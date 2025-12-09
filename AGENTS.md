# agent-tools

**Core principle**: Every repeatable process becomes a tool. Your job is to think. Tools do the work.

## Before Doing Anything

Ask: *"Will I or another agent ever do this again?"*
- **Yes** → Create a tool first, then use it
- **No** → Do it manually (rare)

## Quick Start

```bash
uv sync              # Install dependencies
uv run pytest        # Run tests
```

## How It Works

1. Tools are defined in `agent-tools.yaml`
2. MCP server exposes them as callable functions
3. Use `registry.*` tools to add/modify tools
4. New tools available after MCP restart

## Creating a Tool

One command creates everything:

```
registry.add(
  name="namespace.tool-name",
  description="What it does (be detailed - this shapes agent understanding)",
  parameters='[{"name": "param1", "type": "string", "description": "...", "required": true}]'
)
```

This creates:
- YAML entry in `agent-tools.yaml`
- Module stub at `src/agent_tools/namespace/tool_name.py`
- Test stub at `tests/test_namespace/test_tool_name.py`

Then: implement the function, run tests, restart MCP.

## Key Insights

**Tool descriptions ARE the interface.** Agents only know what descriptions tell them.

**But descriptions don't guarantee behavior.** Even "ALWAYS call this first" won't trigger if the agent is task-focused. See [docs/discovery-problem.md](docs/discovery-problem.md) for the full analysis.

Write descriptions as if they're the only documentation. Include:
- What the tool does
- When to use it
- What it returns
- Edge cases or limitations

## Files

| File | Purpose |
|------|---------|
| `agent-tools.yaml` | Tool registry (single source of truth) |
| `src/agent_tools/registry.py` | Meta-tool implementation |
| `src/agent_tools/server.py` | MCP server |
| `src/agent_tools/_template.py` | Stub template reference |

## Registry Tools

| Tool | Purpose |
|------|---------|
| `registry.add` | Add new tool (creates YAML + stubs) |
| `registry.remove` | Remove tool from registry |
| `registry.update` | Update existing tool definition |
| `registry.list` | List all tools (hierarchical YAML) |
| `registry.validate` | Check for errors in registry |

## Namespace Convention

Use dot notation: `namespace.tool-name`

```
jira.create-issue    → src/agent_tools/jira/create_issue.py
git.commit           → src/agent_tools/git/commit.py
file.read-json       → src/agent_tools/file/read_json.py
```

## Workflow

```
Think: "Is this repeatable?"
    ↓ yes
registry.add(...)
    ↓
Implement stub
    ↓
uv run pytest
    ↓
Restart MCP
    ↓
Use tool
```

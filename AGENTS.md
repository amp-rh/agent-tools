# agent-tools

**Core principle**: Every repeatable process becomes a tool. Your job is to think. Tools do the work.

## Project Structure

This project uses **focused contexts** to keep agent context windows small and relevant. Each directory has its own `AGENTS.md` that serves as an entry point.

| Context | Description | Key Files |
|---------|-------------|-----------|
| @.cursor/discovery | Research and findings (local-only) | Analysis, patterns discovered |
| @.cursor/remediation | Fixes and improvements (local-only) | Action items, implementation guides |
| @.cursor/inventory | Data and tracking (local-only) | CSVs, structured data |
| @.cursor/resources | Reference materials (local-only) | External docs, guides |
| @docs | Existing documentation | discovery-problem.md |

---

## 📝 Agent Scratchpad: `.cursor/`

**Use `.cursor/` as your working memory.** This directory is gitignored and persists across sessions.

| Use For | Example Files |
|---------|---------------|
| Scratchpad notes | `.cursor/notes.md`, `.cursor/scratch.txt` |
| Task tracking | `.cursor/todos.md`, `.cursor/progress.md` |
| Learnings & insights | `.cursor/learnings.md`, `.cursor/patterns.md` |
| Investigation logs | `.cursor/discovery/*.md` |
| Data & inventories | `.cursor/inventory/*.csv` |

**Rules:**
- ✅ Create any files you need in `.cursor/`
- ✅ Use for drafts, experiments, temporary work
- ✅ Track progress across sessions
- ❌ **Never commit** - the directory is gitignored
- ❌ Don't reference in code that gets committed

> **Tip**: Start complex tasks by creating a plan in `.cursor/plan.md`, update as you go.

---

## Quick Start

```bash
uv sync              # Install dependencies
uv run pytest        # Run tests
```

## Before Doing Anything

Ask: *"Will I or another agent ever do this again?"*
- **Yes** → Create the right primitive first, then use it
- **No** → Do it manually (rare)

## 🎯 Choose the Right MCP Primitive

**Don't default to tools!** MCP has three primitives - pick the right one:

| Primitive | Use When | Examples |
|-----------|----------|----------|
| **Tool** | Needs code execution, has variable inputs, returns computed results | `git.commit`, `code.lint`, `cursor.create-command` |
| **Prompt** | Provides workflow guidance, structured thinking, reusable templates | `mcp-from-commands`, `agent-tools-workflow` |
| **Resource** | Exposes read-only data, reference info, computed summaries | `agent-tools://registry` |

### Decision Tree

```
Is it guidance/workflow/template?
    → YES → Create a PROMPT (in server.py)
    → NO ↓

Is it read-only data or reference info?
    → YES → Create a RESOURCE (in server.py)
    → NO ↓

Does it need to execute code with variable inputs?
    → YES → Create a TOOL (via registry.add)
```

### Where to Add Each

| Primitive | Location |
|-----------|----------|
| Tool | `registry.add(...)` → creates YAML + Python |
| Prompt | Edit `src/agent_tools/server.py` → `_list_prompts()` + `_get_prompt()` |
| Resource | Edit `src/agent_tools/server.py` → `_list_resources()` + `_read_resource()` |

---

## How It Works

1. Tools are defined in `tool_defs/` (YAML files)
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
- YAML entry in `tool_defs/namespace/tool-name.yaml`
- Module stub at `src/agent_tools/namespace/tool_name.py`
- Test stub at `tests/test_namespace/test_tool_name.py`

Then: implement the function, run tests, restart MCP.

## Key Insights

**Tool descriptions ARE the interface.** Agents only know what descriptions tell them.

**But descriptions don't guarantee behavior.** Even "ALWAYS call this first" won't trigger if the agent is task-focused. See @docs/discovery-problem.md for the full analysis.

Write descriptions as if they're the only documentation. Include:
- What the tool does
- When to use it
- What it returns
- Edge cases or limitations

## Files

| File | Purpose |
|------|---------|
| `tool_defs/` | Tool definitions (YAML, single source of truth) |
| `src/agent_tools/registry/` | Registry tools (add, remove, reload, etc.) |
| `src/agent_tools/server.py` | MCP server (tools, prompts, resources) |
| `src/agent_tools/_template.py` | Stub template reference |

## Registry Tools

| Tool | Purpose |
|------|---------|
| `registry.add` | Add new tool (creates YAML + stubs) |
| `registry.remove` | Remove tool from registry |
| `registry.update` | Update existing tool definition |
| `registry.list` | List all tools (hierarchical YAML) |
| `registry.validate` | Check for errors in registry |
| `registry.execute` | Execute any tool by name |
| `registry.reload` | Clear module cache (hot-reload tools) |

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
git checkout -b tool/<namespace>-<name>
    ↓
registry.add(...)
    ↓
Implement stub
    ↓
uv run pytest
    ↓
git commit & push
    ↓
Create PR
```

See @CONTRIBUTING.md for branch naming conventions and PR process.

---

## Agent Notes

### 🔴 CRITICAL: Always Update Inventory Files

**Every chat session starts fresh.** When you discover new findings or verify existing ones, you MUST update the inventory files immediately. This is the source of truth for the project.

**When you find something new or verify/refute existing findings:**

1. **Update `.cursor/inventory/*.csv`** - Add/modify data entries
2. **Update `.cursor/discovery/*.md`** - Update findings and status
3. **Update this file (`AGENTS.md`)** - Update summary counts and lists

**Never assume the user will ask you to update files** - do it automatically as part of completing the task.

### Quick Links

- **Contribution guide**: @CONTRIBUTING.md - Branching, code style, PR process
- **Discovery details**: @.cursor/discovery/AGENTS.md
- **Remediation guide**: @.cursor/remediation/AGENTS.md
- **Inventory data**: @.cursor/inventory/AGENTS.md
- **Reference materials**: @.cursor/resources/AGENTS.md
- **Analysis docs**: @docs/discovery-problem.md

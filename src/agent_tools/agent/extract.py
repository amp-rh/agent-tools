"""agent.extract: Extract potential tools from conversation patterns."""
from __future__ import annotations

__all__ = ["extract"]


def extract(summary: str, context: str = "") -> str:
    """
    Analyze conversation patterns and generate prompts to extract a new tool.

    Args:
        summary: What was accomplished in the conversation
        context: Optional code snippets, patterns, or examples from the conversation

    Returns:
        Structured prompts guiding tool extraction.
    """
    context_section = ""
    if context:
        context_section = f"""
### Provided Context

```
{context}
```

"""

    return f"""## Extract Reusable Pattern

**Summary**: {summary}
{context_section}
---

### 1. What's Repeatable?

Answer these questions about the pattern:

- What specific action was performed?
- Would you or another agent do this again?
- What inputs vary each time? (these become parameters)
- What stays the same? (this is the logic)

### 2. Tool, Prompt, or Resource?

| **Tool** | **Prompt** | **Resource** |
|----------|------------|--------------|
| Needs code execution | Guides thinking/workflow | Exposes data for reading |
| Has variable inputs | Static text, no params | Static or computed data |
| Returns computed results | Reusable starting point | Reference information |
| Example: `code.refactor` | Example: `agent-tools-workflow` | Example: `agent-tools://registry` |

---

## Option A: Create a Tool

**Name**: `namespace.tool-name`
- Use existing namespace if it fits: agent, code, docs, think, github, mcp
- Or create a new namespace for a new domain

**Description** (1-2 sentences):
> What does this tool do? When should an agent use it?

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| param1 | string | yes | What this parameter is for |
| param2 | string | no | Optional parameter |

**Registry Command**:
```
registry-execute(
  name="registry.add",
  params='{{"name": "namespace.tool-name", "description": "Your description here", "parameters": [{{"name": "param1", "type": "string", "description": "What it does", "required": true}}]}}'
)
```

After creating:
1. Implement stub at `src/agent_tools/<namespace>/<tool_name>.py`
2. Run tests: `uv run pytest tests/test_<namespace>/test_<tool_name>.py`
3. Restart MCP server

---

## Option B: Create an MCP Prompt

MCP prompts are reusable text templates that guide agent behavior without code.

**To add a prompt**, edit `src/agent_tools/server.py`:

1. Add to `_list_prompts()`:
```python
Prompt(
    name="your-prompt-name",
    description="When to use this prompt",
)
```

2. Add to `_get_prompt()`:
```python
if name == "your-prompt-name":
    return GetPromptResult(
        description="...",
        messages=[
            PromptMessage(
                role="assistant",  # or "user"
                content=TextContent(type="text", text=YOUR_PROMPT_TEXT),
            )
        ],
    )
```

**Note**: Prompts are only used when explicitly requested by the client. They don't auto-inject.

---

## Option C: Create an MCP Resource

MCP resources expose data that agents can read. Use for reference data, configs, or computed summaries.

**To add a resource**, edit `src/agent_tools/server.py`:

1. Add to `_list_resources()`:
```python
Resource(
    uri="agent-tools://your-resource",
    name="Your Resource Name",
    description="What this resource contains",
    mimeType="text/yaml",  # or text/plain, application/json
)
```

2. Add to `_read_resource()`:
```python
if uri == "agent-tools://your-resource":
    content = "your content here"
    return [TextResourceContents(uri=uri, mimeType="text/yaml", text=content)]
```

**Note**: Resources are read-only data. Use tools for actions, prompts for guidance, resources for data.

---
*Extract what's reusable. Tool = code. Prompt = guidance. Resource = data.*
"""

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

### 2. Tool or Prompt?

| Create a **Tool** when... | Create a **Prompt** when... |
|---------------------------|----------------------------|
| Needs code execution | Just guides thinking/workflow |
| Has variable inputs (parameters) | Static text, no parameters |
| Returns computed results | Provides a reusable starting point |
| Example: `code.refactor` | Example: `agent-tools-workflow` |

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
*Extract what's reusable. Tool = code. Prompt = guidance. One job each.*
"""

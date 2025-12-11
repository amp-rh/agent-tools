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

    return f"""## Extract Tool from Conversation

**Summary**: {summary}
{context_section}
---

### 1. What's Repeatable?

Answer these questions about the pattern:

- What specific action was performed?
- Would you or another agent do this again?
- What inputs vary each time? (these become parameters)
- What stays the same? (this is the tool's logic)

### 2. Tool Specification

Fill in this template:

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

### 3. Registry Command

Once you've filled in the specification, use this format:

```
registry-execute(
  name="registry.add",
  params='{{"name": "namespace.tool-name", "description": "Your description here", "parameters": [{{"name": "param1", "type": "string", "description": "What it does", "required": true}}]}}'
)
```

### 4. Implementation Notes

After creating the tool stub:

1. The stub will be at `src/agent_tools/<namespace>/<tool_name>.py`
2. Implement the function body (replace `raise NotImplementedError`)
3. Run tests: `uv run pytest tests/test_<namespace>/test_<tool_name>.py`
4. Restart MCP server to use the new tool

---
*Extract what's reusable. Keep it simple. One tool = one job.*
"""

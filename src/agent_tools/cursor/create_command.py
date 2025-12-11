"""cursor.create-command: Create a new Cursor slash command file."""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["create_command"]


def create_command(
    name: str,
    description: str,
    mcp_tool_name: str = None,
    parameters: str = None,
) -> str:
    """
    Create a new Cursor slash command file.

    Creates a .md file in .cursor/commands/ that defines a slash command for Cursor.
    If mcp_tool_name is provided, the command will reference that MCP tool.
    Otherwise, creates a standalone command with instructions.

    Args:
        name: Command name in kebab-case (e.g., 'my-command')
        description: What the command does
        mcp_tool_name: MCP tool name to wrap (e.g., 'git.commit'). If provided,
            command references this tool.
        parameters: JSON array of parameter definitions: [{name, description, required}].

    Returns:
        Result message describing what was done.
    """
    # Convert kebab-case to Title Case
    title = " ".join(word.capitalize() for word in name.split("-"))

    # Build parameters section
    params_section = ""
    if parameters:
        try:
            params_list = json.loads(parameters)
            param_lines = []
            for p in params_list:
                req = "required" if p.get("required") else "optional"
                param_lines.append(f"- **{p['name']}** ({req}): {p.get('description', '')}")
            params_section = "\n".join(param_lines)
        except (json.JSONDecodeError, KeyError):
            params_section = "- (parameters not specified)"
    else:
        params_section = "- (none)"

    # Build usage section
    if mcp_tool_name:
        usage_section = f"Use the `{mcp_tool_name}` MCP tool."
    else:
        usage_section = "When invoked, the agent should:\n1. (implement behavior here)"

    # Build command file content
    content = f"""# {title}

{description}

## Parameters

{params_section}

## Usage

{usage_section}
"""

    # Write file
    commands_dir = Path.cwd() / ".cursor" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    file_path = commands_dir / f"{name}.md"
    file_path.write_text(content)

    return f"Created command: `/{name}` at `.cursor/commands/{name}.md`"

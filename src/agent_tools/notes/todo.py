"""notes.todo: Add a todo item to the agent notes file."""
from __future__ import annotations

from pathlib import Path

__all__ = ["todo"]


def todo(item: str, details: str = None) -> str:
    """
    Add a todo item to the agent notes file (.cursor/notes.md).

    Appends a todo item to the TODOs section, creating the file and section if needed.
    Persists across sessions for tracking work.

    Args:
        item: The todo item to add
        details: Additional context or sub-items (optional)

    Returns:
        Confirmation message.
    """
    notes_path = Path.cwd() / ".cursor" / "notes.md"

    # Ensure directory exists
    notes_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content or create default
    if notes_path.exists():
        content = notes_path.read_text()
    else:
        content = "# Agent Notes\n\n"

    # Build the todo entry
    todo_entry = f"- [ ] {item}\n"
    if details:
        todo_entry += f"  - {details}\n"

    # Find or create TODOs section
    if "## TODOs" in content:
        # Insert after the ## TODOs line
        parts = content.split("## TODOs", 1)
        after_header = parts[1]

        # Find where to insert (after any existing todos, before next section)
        lines = after_header.split("\n")
        insert_idx = 1  # Start after the header line

        for i, line in enumerate(lines[1:], start=1):
            if line.startswith("## "):
                # Hit next section
                break
            if line.strip() == "" and i > 1:
                # Empty line after content
                continue
            insert_idx = i + 1

        lines.insert(insert_idx, todo_entry.rstrip())
        parts[1] = "\n".join(lines)
        content = "## TODOs".join(parts)
    else:
        # Add TODOs section at the end
        if not content.endswith("\n"):
            content += "\n"
        content += "\n## TODOs\n\n"
        content += todo_entry

    notes_path.write_text(content)

    return f"Added todo: `{item}` to `.cursor/notes.md`"

"""cursor.sync-commands: Sync Cursor commands between project and user directories."""
from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path

__all__ = ["sync_commands"]


def sync_commands(direction: str = None, filter: str = None) -> str:
    """
    Synchronize Cursor commands between project and user directories.

    Copies command files between .cursor/commands/ (project) and
    ~/.cursor/commands/ (user). User commands are available in all workspaces.

    Args:
        direction: Sync direction: 'to-user' (default) or 'to-project'
        filter: Only sync commands matching this pattern (e.g., 'agent-*')

    Returns:
        Summary of synced files.
    """
    direction = direction or "to-user"

    project_commands = Path.cwd() / ".cursor" / "commands"
    user_commands = Path.home() / ".cursor" / "commands"

    if direction == "to-user":
        src = project_commands
        dest = user_commands
        desc = "project → user"
    elif direction == "to-project":
        src = user_commands
        dest = project_commands
        desc = "user → project"
    else:
        return f"Error: Invalid direction '{direction}'. Use 'to-user' or 'to-project'."

    if not src.exists():
        return f"Error: Source directory does not exist: {src}"

    # Ensure destination exists
    dest.mkdir(parents=True, exist_ok=True)

    # Get list of .md files
    md_files = list(src.glob("*.md"))
    if filter:
        md_files = [f for f in md_files if fnmatch.fnmatch(f.name, filter)]

    if not md_files:
        return f"No commands found to sync ({desc})"

    copied = []
    skipped = []

    for src_file in md_files:
        dest_file = dest / src_file.name

        # Check if identical
        if dest_file.exists():
            if src_file.read_text() == dest_file.read_text():
                skipped.append(src_file.name)
                continue

        # Copy file
        shutil.copy2(src_file, dest_file)
        copied.append(src_file.name)

    # Build summary
    lines = [f"## Commands Synced ({desc})", ""]

    if copied:
        lines.append(f"**Copied ({len(copied)}):**")
        for name in copied:
            lines.append(f"- {name}")
        lines.append("")

    if skipped:
        lines.append(f"**Skipped ({len(skipped)} identical):**")
        for name in skipped:
            lines.append(f"- {name}")

    return "\n".join(lines)

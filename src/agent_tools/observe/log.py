"""observe.log: Append structured observation entries to a trace log file."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["log"]


def log(file: str, category: str, message: str, metadata: str = None) -> str:
    """
    Append a structured observation entry to a trace log file.

    Args:
        file: Path to the trace log file (created if missing)
        category: Event category (e.g., 'decision', 'tool_call', 'error', 'checkpoint')
        message: Human-readable description of the event
        metadata: Optional JSON string of structured data to include

    Returns:
        JSON string with logged status, file path, and entry count.
    """
    path = Path(file)
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "message": message,
    }

    if metadata:
        try:
            entry["metadata"] = json.loads(metadata) if isinstance(metadata, str) else metadata
        except json.JSONDecodeError:
            entry["metadata"] = {"raw": metadata}

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    entry_count = sum(1 for _ in path.open("r", encoding="utf-8"))

    return json.dumps({
        "logged": True,
        "file": str(path),
        "entry_count": entry_count,
    })

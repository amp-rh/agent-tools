"""observe.session: Capture session checkpoints with current state."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["session"]


def session(checkpoint_dir: str, checkpoint_name: str, state: str) -> str:
    """
    Capture a session checkpoint with current state.

    Args:
        checkpoint_dir: Directory to save checkpoint files
        checkpoint_name: Name for this checkpoint (used in filename)
        state: JSON string of current state to capture

    Returns:
        JSON string with checkpoint name, file path, and timestamp.
    """
    dir_path = Path(checkpoint_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in checkpoint_name)
    filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{safe_name}.json"
    file_path = dir_path / filename

    try:
        state_data = json.loads(state) if isinstance(state, str) else state
    except json.JSONDecodeError:
        state_data = {"raw": state}

    checkpoint = {
        "checkpoint": checkpoint_name,
        "timestamp": timestamp.isoformat(),
        "state": state_data,
    }

    file_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    return json.dumps({
        "checkpoint": checkpoint_name,
        "file": str(file_path),
        "timestamp": timestamp.isoformat(),
    })

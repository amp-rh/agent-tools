"""observe.trace-call: Record tool calls with timing information."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["trace_call"]

_active_traces: dict[str, datetime] = {}


def trace_call(
    file: str,
    tool_name: str,
    phase: str,
    data: str = None,
    trace_id: str = None,
) -> str:
    """
    Record a tool call with timing information.

    Args:
        file: Path to the trace log file
        tool_name: Name of the tool being traced
        phase: Either 'start' or 'end'
        data: JSON string of parameters (start) or result summary (end)
        trace_id: Required for phase='end' - the trace_id from the start call

    Returns:
        JSON string with trace_id, phase, and duration_ms (for end phase).
    """
    path = Path(file)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    if phase == "start":
        new_trace_id = str(uuid.uuid4())[:8]
        _active_traces[new_trace_id] = now

        entry = {
            "timestamp": now.isoformat(),
            "trace_id": new_trace_id,
            "tool": tool_name,
            "phase": "start",
        }

        if data:
            try:
                entry["params"] = json.loads(data) if isinstance(data, str) else data
            except json.JSONDecodeError:
                entry["params"] = {"raw": data}

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return json.dumps({"trace_id": new_trace_id, "phase": "start"})

    elif phase == "end":
        if not trace_id:
            return json.dumps({"error": "trace_id required for phase='end'"})

        start_time = _active_traces.pop(trace_id, None)
        duration_ms = None
        if start_time:
            duration_ms = int((now - start_time).total_seconds() * 1000)

        entry = {
            "timestamp": now.isoformat(),
            "trace_id": trace_id,
            "tool": tool_name,
            "phase": "end",
            "duration_ms": duration_ms,
        }

        if data:
            try:
                entry["result"] = json.loads(data) if isinstance(data, str) else data
            except json.JSONDecodeError:
                entry["result"] = {"raw": data}

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return json.dumps({
            "trace_id": trace_id,
            "phase": "end",
            "duration_ms": duration_ms,
        })

    else:
        return json.dumps({"error": f"Invalid phase: {phase}. Use 'start' or 'end'."})

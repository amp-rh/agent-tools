"""observe.log tests."""
import json
from pathlib import Path

import pytest

from agent_tools.observe.log import log


class TestLog:
    """Tests for log."""

    def test_log_creates_file(self, tmp_path: Path):
        """Log creates file if it doesn't exist."""
        log_file = tmp_path / "trace.jsonl"
        result = json.loads(log(str(log_file), "test", "Test message"))

        assert result["logged"] is True
        assert log_file.exists()

    def test_log_appends_entry(self, tmp_path: Path):
        """Log appends entries to file."""
        log_file = tmp_path / "trace.jsonl"

        log(str(log_file), "decision", "First entry")
        log(str(log_file), "tool_call", "Second entry")

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        assert entry1["category"] == "decision"
        assert entry1["message"] == "First entry"

    def test_log_includes_timestamp(self, tmp_path: Path):
        """Log entries include ISO timestamp."""
        log_file = tmp_path / "trace.jsonl"
        log(str(log_file), "test", "Message")

        entry = json.loads(log_file.read_text().strip())
        assert "timestamp" in entry
        assert "T" in entry["timestamp"]

    def test_log_with_metadata(self, tmp_path: Path):
        """Log accepts optional metadata."""
        log_file = tmp_path / "trace.jsonl"
        metadata = json.dumps({"key": "value", "count": 42})
        log(str(log_file), "checkpoint", "With metadata", metadata)

        entry = json.loads(log_file.read_text().strip())
        assert entry["metadata"]["key"] == "value"
        assert entry["metadata"]["count"] == 42

    def test_log_returns_entry_count(self, tmp_path: Path):
        """Log returns current entry count."""
        log_file = tmp_path / "trace.jsonl"

        result1 = json.loads(log(str(log_file), "test", "First"))
        assert result1["entry_count"] == 1

        result2 = json.loads(log(str(log_file), "test", "Second"))
        assert result2["entry_count"] == 2

    def test_log_creates_parent_dirs(self, tmp_path: Path):
        """Log creates parent directories if needed."""
        log_file = tmp_path / "deep" / "nested" / "trace.jsonl"
        log(str(log_file), "test", "Message")

        assert log_file.exists()

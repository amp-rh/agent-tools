"""observe.session tests."""
import json
from pathlib import Path

import pytest

from agent_tools.observe.session import session


class TestSession:
    """Tests for session."""

    def test_creates_checkpoint_file(self, tmp_path: Path):
        """Session creates a checkpoint file."""
        state = json.dumps({"goal": "test"})
        result = json.loads(session(str(tmp_path), "test_checkpoint", state))

        assert result["checkpoint"] == "test_checkpoint"
        assert Path(result["file"]).exists()

    def test_checkpoint_contains_state(self, tmp_path: Path):
        """Checkpoint file contains provided state."""
        state = json.dumps({"goal": "complete task", "progress": 50})
        result = json.loads(session(str(tmp_path), "progress", state))

        checkpoint = json.loads(Path(result["file"]).read_text())
        assert checkpoint["state"]["goal"] == "complete task"
        assert checkpoint["state"]["progress"] == 50

    def test_checkpoint_includes_timestamp(self, tmp_path: Path):
        """Checkpoint includes ISO timestamp."""
        state = json.dumps({})
        result = json.loads(session(str(tmp_path), "test", state))

        checkpoint = json.loads(Path(result["file"]).read_text())
        assert "timestamp" in checkpoint
        assert "T" in checkpoint["timestamp"]

    def test_checkpoint_name_in_filename(self, tmp_path: Path):
        """Checkpoint name appears in filename."""
        state = json.dumps({})
        result = json.loads(session(str(tmp_path), "my_checkpoint", state))

        assert "my_checkpoint" in result["file"]

    def test_sanitizes_checkpoint_name(self, tmp_path: Path):
        """Special characters in checkpoint name are sanitized."""
        state = json.dumps({})
        result = json.loads(session(str(tmp_path), "bad/name:here", state))

        filename = Path(result["file"]).name
        assert "/" not in filename
        assert ":" not in filename

    def test_creates_checkpoint_dir(self, tmp_path: Path):
        """Creates checkpoint directory if it doesn't exist."""
        new_dir = tmp_path / "deep" / "checkpoints"
        state = json.dumps({"test": True})

        result = json.loads(session(str(new_dir), "test", state))

        assert new_dir.exists()
        assert Path(result["file"]).exists()

    def test_multiple_checkpoints(self, tmp_path: Path):
        """Multiple checkpoints create separate files."""
        session(str(tmp_path), "first", json.dumps({"n": 1}))
        session(str(tmp_path), "second", json.dumps({"n": 2}))

        files = list(tmp_path.glob("*.json"))
        assert len(files) == 2

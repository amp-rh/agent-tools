"""notes.todo tests."""
from __future__ import annotations

from unittest.mock import patch

from agent_tools.notes.todo import todo


class TestTodo:
    """Tests for todo."""

    def test_adds_todo_to_existing_file(self, tmp_path):
        """Adds todo to existing notes file."""
        notes_file = tmp_path / ".cursor" / "notes.md"
        notes_file.parent.mkdir(parents=True)
        notes_file.write_text("# Notes\n\n## TODOs\n\n- [ ] Existing item\n")

        with patch("agent_tools.notes.todo.Path.cwd", return_value=tmp_path):
            todo("New todo item")

        content = notes_file.read_text()
        assert "- [ ] New todo item" in content
        assert "Existing item" in content

    def test_creates_file_if_missing(self, tmp_path):
        """Creates notes.md if it doesn't exist."""
        with patch("agent_tools.notes.todo.Path.cwd", return_value=tmp_path):
            todo("First todo")

        notes_file = tmp_path / ".cursor" / "notes.md"
        assert notes_file.exists()
        content = notes_file.read_text()
        assert "## TODOs" in content
        assert "- [ ] First todo" in content

    def test_creates_todos_section_if_missing(self, tmp_path):
        """Creates TODOs section if file exists but section doesn't."""
        notes_file = tmp_path / ".cursor" / "notes.md"
        notes_file.parent.mkdir(parents=True)
        notes_file.write_text("# Notes\n\nSome content here.\n")

        with patch("agent_tools.notes.todo.Path.cwd", return_value=tmp_path):
            todo("New item")

        content = notes_file.read_text()
        assert "## TODOs" in content
        assert "- [ ] New item" in content

    def test_adds_details_as_subitems(self, tmp_path):
        """Details are added as indented sub-items."""
        notes_file = tmp_path / ".cursor" / "notes.md"
        notes_file.parent.mkdir(parents=True)
        notes_file.write_text("# Notes\n\n## TODOs\n")

        with patch("agent_tools.notes.todo.Path.cwd", return_value=tmp_path):
            todo("Main item", details="Sub-detail here")

        content = notes_file.read_text()
        assert "- [ ] Main item" in content
        assert "  - Sub-detail here" in content

    def test_returns_success_message(self, tmp_path):
        """Returns confirmation message."""
        notes_file = tmp_path / ".cursor" / "notes.md"
        notes_file.parent.mkdir(parents=True)
        notes_file.write_text("## TODOs\n")

        with patch("agent_tools.notes.todo.Path.cwd", return_value=tmp_path):
            result = todo("My task")

        assert "Added" in result or "todo" in result.lower()

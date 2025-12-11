"""cursor.create-command tests."""
from __future__ import annotations

from unittest.mock import patch

from agent_tools.cursor.create_command import create_command


class TestCreateCommand:
    """Tests for create_command."""

    def test_creates_basic_command(self, tmp_path):
        """Create a basic command without MCP tool."""
        with patch("agent_tools.cursor.create_command.Path.cwd", return_value=tmp_path):
            commands_dir = tmp_path / ".cursor" / "commands"
            commands_dir.mkdir(parents=True)

            create_command("my-test", "Test command description")

        expected_file = commands_dir / "my-test.md"
        assert expected_file.exists()
        content = expected_file.read_text()
        assert "# My Test" in content
        assert "Test command description" in content

    def test_creates_mcp_wrapped_command(self, tmp_path):
        """Create a command that wraps an MCP tool."""
        with patch("agent_tools.cursor.create_command.Path.cwd", return_value=tmp_path):
            commands_dir = tmp_path / ".cursor" / "commands"
            commands_dir.mkdir(parents=True)

            create_command(
                "commit",
                "Commit changes with conventional message",
                mcp_tool_name="git.commit",
            )

        expected_file = commands_dir / "commit.md"
        assert expected_file.exists()
        content = expected_file.read_text()
        assert "git.commit" in content
        assert "MCP tool" in content

    def test_creates_command_with_parameters(self, tmp_path):
        """Create a command with parameters."""
        with patch("agent_tools.cursor.create_command.Path.cwd", return_value=tmp_path):
            commands_dir = tmp_path / ".cursor" / "commands"
            commands_dir.mkdir(parents=True)

            params = '[{"name": "file", "description": "File to process", "required": true}]'
            create_command("process-file", "Process a file", parameters=params)

        expected_file = commands_dir / "process-file.md"
        assert expected_file.exists()
        content = expected_file.read_text()
        assert "**file**" in content
        assert "required" in content.lower()

    def test_converts_kebab_to_title_case(self, tmp_path):
        """Kebab-case name becomes Title Case heading."""
        with patch("agent_tools.cursor.create_command.Path.cwd", return_value=tmp_path):
            commands_dir = tmp_path / ".cursor" / "commands"
            commands_dir.mkdir(parents=True)

            create_command("my-awesome-command", "Does awesome things")

        content = (commands_dir / "my-awesome-command.md").read_text()
        assert "# My Awesome Command" in content

    def test_creates_commands_directory_if_missing(self, tmp_path):
        """Creates .cursor/commands/ if it doesn't exist."""
        with patch("agent_tools.cursor.create_command.Path.cwd", return_value=tmp_path):
            create_command("new-cmd", "New command")

        expected_dir = tmp_path / ".cursor" / "commands"
        assert expected_dir.exists()
        assert (expected_dir / "new-cmd.md").exists()

    def test_returns_success_message(self, tmp_path):
        """Returns success message with file path."""
        with patch("agent_tools.cursor.create_command.Path.cwd", return_value=tmp_path):
            (tmp_path / ".cursor" / "commands").mkdir(parents=True)
            result = create_command("test-cmd", "Test")

        assert "Created" in result or "test-cmd" in result

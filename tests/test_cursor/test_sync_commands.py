"""cursor.sync-commands tests."""
from __future__ import annotations

from unittest.mock import patch

from agent_tools.cursor.sync_commands import sync_commands


class TestSyncCommands:
    """Tests for sync_commands."""

    def test_sync_to_user_default(self, tmp_path):
        """Default syncs from project to user directory."""
        project_commands = tmp_path / "project" / ".cursor" / "commands"
        user_commands = tmp_path / "user" / ".cursor" / "commands"
        project_commands.mkdir(parents=True)
        user_commands.mkdir(parents=True)

        # Create a command in project
        (project_commands / "my-cmd.md").write_text("# My Command\nTest")

        with (
            patch("agent_tools.cursor.sync_commands.Path.cwd", return_value=tmp_path / "project"),
            patch("agent_tools.cursor.sync_commands.Path.home", return_value=tmp_path / "user"),
        ):
            result = sync_commands()

        # Should have been copied
        assert (user_commands / "my-cmd.md").exists()
        assert "my-cmd" in result

    def test_sync_to_project(self, tmp_path):
        """Sync from user to project directory."""
        project_commands = tmp_path / "project" / ".cursor" / "commands"
        user_commands = tmp_path / "user" / ".cursor" / "commands"
        project_commands.mkdir(parents=True)
        user_commands.mkdir(parents=True)

        # Create a command in user
        (user_commands / "user-cmd.md").write_text("# User Command\nTest")

        with (
            patch("agent_tools.cursor.sync_commands.Path.cwd", return_value=tmp_path / "project"),
            patch("agent_tools.cursor.sync_commands.Path.home", return_value=tmp_path / "user"),
        ):
            sync_commands(direction="to-project")

        # Should have been copied
        assert (project_commands / "user-cmd.md").exists()

    def test_sync_with_filter(self, tmp_path):
        """Filter limits which commands are synced."""
        project_commands = tmp_path / "project" / ".cursor" / "commands"
        user_commands = tmp_path / "user" / ".cursor" / "commands"
        project_commands.mkdir(parents=True)
        user_commands.mkdir(parents=True)

        # Create commands
        (project_commands / "agent-begin.md").write_text("# Agent Begin")
        (project_commands / "git-commit.md").write_text("# Git Commit")

        with (
            patch("agent_tools.cursor.sync_commands.Path.cwd", return_value=tmp_path / "project"),
            patch("agent_tools.cursor.sync_commands.Path.home", return_value=tmp_path / "user"),
        ):
            sync_commands(filter="agent-*")

        # Only agent-* should be synced
        assert (user_commands / "agent-begin.md").exists()
        assert not (user_commands / "git-commit.md").exists()

    def test_sync_skips_identical(self, tmp_path):
        """Identical files are skipped."""
        project_commands = tmp_path / "project" / ".cursor" / "commands"
        user_commands = tmp_path / "user" / ".cursor" / "commands"
        project_commands.mkdir(parents=True)
        user_commands.mkdir(parents=True)

        # Create identical files in both
        content = "# Same Command\nIdentical content"
        (project_commands / "same.md").write_text(content)
        (user_commands / "same.md").write_text(content)

        with (
            patch("agent_tools.cursor.sync_commands.Path.cwd", return_value=tmp_path / "project"),
            patch("agent_tools.cursor.sync_commands.Path.home", return_value=tmp_path / "user"),
        ):
            result = sync_commands()

        assert "skipped" in result.lower() or "identical" in result.lower() or "0" in result

    def test_sync_creates_dest_dir(self, tmp_path):
        """Creates destination directory if it doesn't exist."""
        project_commands = tmp_path / "project" / ".cursor" / "commands"
        project_commands.mkdir(parents=True)
        (project_commands / "new-cmd.md").write_text("# New")

        user_home = tmp_path / "user"
        user_home.mkdir(parents=True)
        # Don't create .cursor/commands

        with (
            patch("agent_tools.cursor.sync_commands.Path.cwd", return_value=tmp_path / "project"),
            patch("agent_tools.cursor.sync_commands.Path.home", return_value=user_home),
        ):
            sync_commands()

        user_commands = user_home / ".cursor" / "commands"
        assert user_commands.exists()
        assert (user_commands / "new-cmd.md").exists()

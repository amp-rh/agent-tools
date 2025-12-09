"""Tests for CLI commands."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from agent_tools import cli


@pytest.fixture
def tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change to a temporary directory for testing."""
    monkeypatch.chdir(tmp_path)
    # Patch LOCAL_CONFIG to use the temp directory
    monkeypatch.setattr(cli, "LOCAL_CONFIG", tmp_path / "agent-tools.yaml")
    return tmp_path


class TestCmdInit:
    """Tests for the init command."""

    def test_init_creates_registry_file(self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch):
        """Verify init creates agent-tools.yaml in current directory."""
        # Mock get_default_registry_path to return a valid file
        default_registry = tmp_cwd / "default.yaml"
        default_registry.write_text("tools: {}\n")
        monkeypatch.setattr(cli, "get_default_registry_path", lambda: default_registry)

        result = cli.cmd_init([])

        assert result == 0
        assert (tmp_cwd / "agent-tools.yaml").exists()

    def test_init_refuses_overwrite_without_force(
        self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify init refuses to overwrite existing file without --force."""
        (tmp_cwd / "agent-tools.yaml").write_text("existing: true\n")

        result = cli.cmd_init([])

        assert result == 1
        assert (tmp_cwd / "agent-tools.yaml").read_text() == "existing: true\n"

    def test_init_overwrites_with_force(self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch):
        """Verify init overwrites existing file with --force."""
        (tmp_cwd / "agent-tools.yaml").write_text("existing: true\n")

        default_registry = tmp_cwd / "default.yaml"
        default_registry.write_text("tools: {}\n")
        monkeypatch.setattr(cli, "get_default_registry_path", lambda: default_registry)

        result = cli.cmd_init(["--force"])

        assert result == 0
        assert (tmp_cwd / "agent-tools.yaml").read_text() == "tools: {}\n"

    def test_init_fails_if_default_missing(self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch):
        """Verify init fails if default registry not found."""
        monkeypatch.setattr(cli, "get_default_registry_path", lambda: tmp_cwd / "nonexistent.yaml")

        result = cli.cmd_init([])

        assert result == 1


class TestCmdList:
    """Tests for the list command."""

    def test_list_succeeds_with_registry(
        self,
        tmp_registry: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ):
        """Verify list succeeds when registry is found and displays tools."""
        from agent_tools.registry import add_tool

        add_tool(name="test.tool", description="A test tool", parameters="[]")

        # Point CLI to the temp registry's tool_defs
        monkeypatch.setattr(cli, "find_registry", lambda: tmp_registry / "tool_defs")

        result = cli.cmd_list([])

        assert result == 0
        captured = capsys.readouterr()
        assert "test:" in captured.out
        assert "tool:" in captured.out

    def test_list_fails_without_registry(
        self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify list fails when no registry found."""
        monkeypatch.setattr(cli, "find_registry", lambda: None)

        result = cli.cmd_list([])

        assert result == 1


class TestCmdValidate:
    """Tests for the validate command."""

    def test_validate_succeeds_with_registry(
        self,
        tmp_registry: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ):
        """Verify validate succeeds with a valid registry."""
        from agent_tools.registry import add_tool

        add_tool(name="test.tool", description="A test tool", parameters="[]")

        # Point CLI to the temp registry's tool_defs
        monkeypatch.setattr(cli, "find_registry", lambda: tmp_registry / "tool_defs")

        result = cli.cmd_validate([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Validated" in captured.out

    def test_validate_fails_without_registry(
        self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify validate fails when no registry found."""
        monkeypatch.setattr(cli, "find_registry", lambda: None)

        result = cli.cmd_validate([])

        assert result == 1


class TestCmdHelp:
    """Tests for the help command."""

    def test_help_output_contains_commands(self, capsys: pytest.CaptureFixture[str]):
        """Verify help command succeeds and lists available commands."""
        result = cli.cmd_help([])

        assert result == 0
        captured = capsys.readouterr()
        for cmd in ["init", "server", "list", "validate"]:
            assert cmd in captured.out


class TestCmdServer:
    """Tests for the server command."""

    def test_server_uses_bundled_tools_without_registry(
        self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify server falls back to bundled tools when no local registry found."""
        monkeypatch.setattr(cli, "find_registry", lambda: None)

        # Mock server_main to avoid actually starting the server
        server_called = []

        def mock_server_main():
            server_called.append(True)

        monkeypatch.setattr("agent_tools.server.main", mock_server_main)

        result = cli.cmd_server([])

        assert result == 0
        assert server_called, "Server main should have been called"


class TestFindRegistry:
    """Tests for registry discovery."""

    def test_find_registry_returns_local_first(
        self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify find_registry prefers local config."""
        local = tmp_cwd / "agent-tools.yaml"
        local.write_text("local: true\n")
        monkeypatch.setattr(cli, "LOCAL_CONFIG", local)

        result = cli.find_registry()

        assert result == local

    def test_find_registry_returns_none_when_missing(
        self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify find_registry returns None when no config found."""
        monkeypatch.setattr(cli, "LOCAL_CONFIG", tmp_cwd / "nonexistent.yaml")
        monkeypatch.setattr(cli, "USER_CONFIG_DIR", tmp_cwd / "user_config")

        result = cli.find_registry()

        assert result is None

    def test_find_registry_falls_back_to_user_config(
        self, tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify find_registry checks user config directory."""
        user_config_dir = tmp_cwd / "user_config"
        user_config_dir.mkdir()
        user_config = user_config_dir / "agent-tools.yaml"
        user_config.write_text("user: true\n")

        monkeypatch.setattr(cli, "LOCAL_CONFIG", tmp_cwd / "nonexistent.yaml")
        monkeypatch.setattr(cli, "USER_CONFIG_DIR", user_config_dir)

        result = cli.find_registry()

        assert result == user_config


class TestMain:
    """Tests for main entry point."""

    def test_main_no_args_shows_help(self, monkeypatch: pytest.MonkeyPatch):
        """Verify main with no args shows help and exits 0."""
        monkeypatch.setattr(sys, "argv", ["agent-tools"])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 0

    def test_main_unknown_command_exits_1(self, monkeypatch: pytest.MonkeyPatch):
        """Verify main with unknown command exits 1."""
        monkeypatch.setattr(sys, "argv", ["agent-tools", "unknown-command"])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 1

    @pytest.mark.parametrize("help_arg", ["help", "--help", "-h"])
    def test_main_dispatches_help(self, monkeypatch: pytest.MonkeyPatch, help_arg: str):
        """Verify main handles help command and flags."""
        monkeypatch.setattr(sys, "argv", ["agent-tools", help_arg])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 0


class TestGetDefaultRegistryPath:
    """Tests for default registry path resolution."""

    def test_returns_package_default_if_exists(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ):
        """Verify returns package default when it exists."""
        default_reg = tmp_path / "agent-tools.yaml"
        default_reg.write_text("tools: {}\n")
        monkeypatch.setattr(cli, "DEFAULT_REGISTRY", default_reg)

        result = cli.get_default_registry_path()

        assert result == default_reg

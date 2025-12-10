"""Functional tests that run the CLI via uvx."""
from __future__ import annotations

import base64
import json
import re
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run agent-tools CLI via uvx from the local project."""
    return subprocess.run(
        ["uvx", "--from", str(PROJECT_ROOT), "agent-tools", *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.slow
class TestUvxFunctional:
    """Functional tests using uvx to install and run agent-tools."""

    def test_list_shows_tools(self):
        """Verify 'agent-tools list' shows registered tools."""
        result = run_cli("list")

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "tools:" in result.stdout
        assert "registry:" in result.stdout

    def test_help_shows_usage(self):
        """Verify 'agent-tools help' shows usage information."""
        result = run_cli("help")

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "agent-tools" in result.stdout
        assert "init" in result.stdout
        assert "list" in result.stdout
        assert "validate" in result.stdout

    def test_validate_succeeds(self):
        """Verify 'agent-tools validate' runs without errors."""
        result = run_cli("validate")
<<<<<<< Current (Your changes)
=======

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Validated" in result.stdout


class TestMcpInstallLink:
    """Tests for the MCP install link in README."""

    def test_readme_has_install_link(self):
        """Verify README contains a valid MCP install link."""
        readme = (PROJECT_ROOT / "README.md").read_text()

        # Extract the install link
        pattern = r'cursor://anysphere\.cursor-deeplink/mcp/install\?name=([^&]+)&config=([^"]+)'
        match = re.search(pattern, readme)

        assert match, "README must contain MCP install link"
        name, config_b64 = match.groups()

        assert name == "agent-tools", f"Server name should be 'agent-tools', got '{name}'"

    def test_install_link_config_is_valid_json(self):
        """Verify the base64 config decodes to valid JSON."""
        readme = (PROJECT_ROOT / "README.md").read_text()

        pattern = r'cursor://anysphere\.cursor-deeplink/mcp/install\?name=([^&]+)&config=([^"]+)'
        match = re.search(pattern, readme)
        assert match, "README must contain MCP install link"

        _, config_b64 = match.groups()
        config_json = base64.b64decode(config_b64).decode("utf-8")
        config = json.loads(config_json)

        assert "command" in config, "Config must have 'command' field"
        assert "args" in config, "Config must have 'args' field"
        assert isinstance(config["args"], list), "'args' must be a list"

    def test_install_link_command_is_uvx(self):
        """Verify the install link uses uvx."""
        readme = (PROJECT_ROOT / "README.md").read_text()

        pattern = r'cursor://anysphere\.cursor-deeplink/mcp/install\?name=([^&]+)&config=([^"]+)'
        match = re.search(pattern, readme)
        assert match, "README must contain MCP install link"

        _, config_b64 = match.groups()
        config = json.loads(base64.b64decode(config_b64))

        assert config["command"] == "uvx", f"Command should be 'uvx', got '{config['command']}'"
        assert "--from" in config["args"], "Args should contain '--from'"
        assert "agent-tools-server" in config["args"], "Args should contain 'agent-tools-server'"

    @pytest.mark.slow
    def test_install_link_command_executes(self):
        """Verify the command from the install link actually runs."""
        readme = (PROJECT_ROOT / "README.md").read_text()

        pattern = r'cursor://anysphere\.cursor-deeplink/mcp/install\?name=([^&]+)&config=([^"]+)'
        match = re.search(pattern, readme)
        assert match, "README must contain MCP install link"

        _, config_b64 = match.groups()
        config = json.loads(base64.b64decode(config_b64))

        # Run the command with a timeout - it should start and load tools
        result = subprocess.run(
            [config["command"], *config["args"]],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=PROJECT_ROOT,
        )
>>>>>>> Incoming (Background Agent changes)

        # Server runs until killed, so we check stderr for successful startup
        assert "Loaded" in result.stderr or "tool" in result.stderr.lower(), (
            f"Server should load tools. stderr: {result.stderr}"
        )


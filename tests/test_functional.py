"""Functional tests that run the CLI via uvx."""
from __future__ import annotations

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

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Validated" in result.stdout

    def test_uvx_local_server_command(self):
        """Verify 'uvx <local-path> server' works like the README's remote command.

        The README uses: uvx git+https://github.com/amp-rh/agent-tools.git server
        This tests the equivalent local command: uvx <project-path> server
        """
        # Server starts and waits for MCP input - we send EOF to make it exit
        result = subprocess.run(
            ["uvx", str(PROJECT_ROOT), "server"],
            capture_output=True,
            text=True,
            timeout=10,
            input="",  # Send EOF immediately
        )

        # Server should start successfully and show it loaded tool_defs
        assert "Using tool_defs:" in result.stderr or result.returncode == 0, (
            f"Command failed: {result.stderr}"
        )

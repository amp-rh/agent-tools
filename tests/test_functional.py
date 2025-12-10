"""Functional tests that run the CLI via uvx."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class TestUvxFunctional:
    """Functional tests using uvx to install and run agent-tools."""

    @pytest.mark.slow
    def test_uvx_list_shows_tools(self):
        """Verify 'uvx agent-tools list' shows registered tools.

        This test installs the package from the local project directory
        using uvx and verifies the list command works end-to-end.

        Note: To test from GitHub, push changes first then use:
            uvx --from git+https://github.com/amp-rh/agent-tools.git agent-tools list
        """
        result = subprocess.run(
            ["uvx", "--from", str(PROJECT_ROOT), "agent-tools", "list"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "tools:" in result.stdout
        assert "registry:" in result.stdout
        assert "add:" in result.stdout or "list:" in result.stdout

    @pytest.mark.slow
    def test_uvx_help_shows_usage(self):
        """Verify 'uvx agent-tools help' shows usage information."""
        result = subprocess.run(
            ["uvx", "--from", str(PROJECT_ROOT), "agent-tools", "help"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "agent-tools" in result.stdout
        assert "init" in result.stdout
        assert "list" in result.stdout
        assert "validate" in result.stdout

    @pytest.mark.slow
    def test_uvx_validate_succeeds(self):
        """Verify 'uvx agent-tools validate' runs without errors."""
        result = subprocess.run(
            ["uvx", "--from", str(PROJECT_ROOT), "agent-tools", "validate"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Validated" in result.stdout


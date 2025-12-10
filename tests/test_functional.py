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


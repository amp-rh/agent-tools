"""Tests for MCP client functionality."""
from __future__ import annotations

import pytest

from agent_tools.mcp_client import ExternalServer, ExternalServerManager, _expand_env_vars


class TestExpandEnvVars:
    """Tests for environment variable expansion."""

    def test_expands_simple_var(self, monkeypatch):
        """Verify ${VAR} is expanded."""
        monkeypatch.setenv("TEST_VAR", "hello")
        result = _expand_env_vars({"KEY": "${TEST_VAR}"})
        assert result["KEY"] == "hello"

    def test_expands_multiple_vars(self, monkeypatch):
        """Verify multiple vars in one value are expanded."""
        monkeypatch.setenv("A", "foo")
        monkeypatch.setenv("B", "bar")
        result = _expand_env_vars({"KEY": "${A}_${B}"})
        assert result["KEY"] == "foo_bar"

    def test_missing_var_becomes_empty(self, monkeypatch):
        """Verify missing vars become empty string."""
        monkeypatch.delenv("NONEXISTENT", raising=False)
        result = _expand_env_vars({"KEY": "${NONEXISTENT}"})
        assert result["KEY"] == ""

    def test_no_expansion_without_syntax(self):
        """Verify regular strings are unchanged."""
        result = _expand_env_vars({"KEY": "plain_value"})
        assert result["KEY"] == "plain_value"


class TestExternalServer:
    """Tests for ExternalServer class."""

    def test_init(self):
        """Verify ExternalServer initializes correctly."""
        server = ExternalServer(
            name="test",
            command="echo",
            args=["hello"],
            env={"VAR": "value"},
        )
        assert server.name == "test"
        assert server.command == "echo"
        assert server.args == ["hello"]
        assert server.env == {"VAR": "value"}

    def test_get_tools_empty_before_start(self):
        """Verify get_tools returns empty before start."""
        server = ExternalServer(name="test", command="echo", args=[])
        assert server.get_tools() == []


class TestExternalServerManager:
    """Tests for ExternalServerManager class."""

    def test_init(self):
        """Verify manager initializes correctly."""
        manager = ExternalServerManager()
        assert manager.get_all_tools() == []

    def test_get_server_not_found(self):
        """Verify get_server returns None for unknown server."""
        manager = ExternalServerManager()
        assert manager.get_server("nonexistent") is None

    @pytest.mark.asyncio
    async def test_call_tool_unknown_server(self):
        """Verify call_tool handles unknown server."""
        manager = ExternalServerManager()
        result = await manager.call_tool("unknown", "tool", {})
        assert "not found" in result


"""mcp.inspect tests."""
from __future__ import annotations

import json
from unittest.mock import patch

from agent_tools.mcp.inspect import inspect


class TestInspect:
    """Tests for inspect."""

    def test_inspect_with_command(self):
        """Direct command is used for inspector."""
        result = inspect(command="uv run agent-tools server")

        assert "npx" in result or "MCP Inspector" in result
        assert "agent-tools" in result

    def test_inspect_with_server_name(self, tmp_path):
        """Server name is looked up from mcp.json."""
        mcp_json = {
            "mcpServers": {
                "my-server": {
                    "command": "uvx",
                    "args": ["my-package", "serve"],
                }
            }
        }
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()
        (cursor_dir / "mcp.json").write_text(json.dumps(mcp_json))

        with patch("agent_tools.mcp.inspect.Path.cwd", return_value=tmp_path):
            result = inspect(server="my-server")

        assert "my-server" in result.lower() or "uvx" in result or "my-package" in result

    def test_inspect_default_agent_tools(self):
        """Default uses agent-tools server."""
        result = inspect()

        assert "agent-tools" in result or "MCP Inspector" in result

    def test_inspect_server_not_found(self, tmp_path):
        """Error when server not found in mcp.json."""
        mcp_json = {"mcpServers": {}}
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()
        (cursor_dir / "mcp.json").write_text(json.dumps(mcp_json))

        with patch("agent_tools.mcp.inspect.Path.cwd", return_value=tmp_path):
            result = inspect(server="nonexistent")

        assert "not found" in result.lower() or "error" in result.lower()

    def test_inspect_returns_command_info(self):
        """Result includes command to run."""
        result = inspect(command="uv run my-server")

        # Should include the inspector command
        assert "npx" in result or "@modelcontextprotocol/inspector" in result

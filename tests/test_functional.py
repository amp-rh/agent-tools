"""Functional tests that run the CLI via uvx."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class MCPClient:
    """Helper class for MCP JSON-RPC communication."""

    def __init__(self):
        self._request_id = 0

    def request(self, method: str, params: dict | None = None) -> str:
        """Create a JSON-RPC request."""
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }
        return json.dumps(msg)

    def notification(self, method: str, params: dict | None = None) -> str:
        """Create a JSON-RPC notification (no id)."""
        msg = {"jsonrpc": "2.0", "method": method}
        if params:
            msg["params"] = params
        return json.dumps(msg)

    def initialize(self) -> str:
        """Create an initialize request."""
        return self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

    @staticmethod
    def parse_responses(stdout: str) -> list[dict]:
        """Parse JSON-RPC responses from stdout."""
        responses = []
        for line in stdout.strip().split("\n"):
            if line.strip():
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return responses

    @staticmethod
    def find_response(responses: list[dict], request_id: int) -> dict | None:
        """Find a response by request id."""
        for resp in responses:
            if resp.get("id") == request_id:
                return resp
        return None


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run agent-tools CLI via uvx from the local project."""
    return subprocess.run(
        ["uvx", "--from", str(PROJECT_ROOT), "agent-tools", *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def run_server(
    input_data: str = "", cwd: Path | None = None, timeout: int = 30
) -> subprocess.CompletedProcess[str]:
    """Run the MCP server via uvx."""
    return subprocess.run(
        ["uvx", str(PROJECT_ROOT), "server"],
        capture_output=True,
        text=True,
        timeout=timeout,
        input=input_data,
        cwd=cwd,
    )


@pytest.mark.slow
class TestUvxCli:
    """Tests for CLI commands via uvx."""

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
        for cmd in ["agent-tools", "init", "list", "validate"]:
            assert cmd in result.stdout

    def test_validate_succeeds(self):
        """Verify 'agent-tools validate' runs without errors."""
        result = run_cli("validate")

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Validated" in result.stdout


@pytest.mark.slow
class TestUvxServer:
    """Tests for MCP server via uvx."""

    def test_server_responds_to_initialize(self, tmp_path: Path):
        """Verify server responds to MCP initialize request."""
        client = MCPClient()
        mcp_input = client.initialize() + "\n"

        result = run_server(input_data=mcp_input, cwd=tmp_path)
        responses = client.parse_responses(result.stdout)

        assert len(responses) >= 1, f"Expected response, got: {result.stdout}"

        init_response = client.find_response(responses, 1)
        assert init_response is not None, f"No init response: {responses}"
        assert "result" in init_response
        assert "protocolVersion" in init_response["result"]

    def test_server_lists_tools(self, tmp_path: Path):
        """Verify server returns tools via tools/list request."""
        client = MCPClient()
        mcp_input = "\n".join([
            client.initialize(),
            client.notification("notifications/initialized"),
            client.request("tools/list"),
        ]) + "\n"

        result = run_server(input_data=mcp_input, cwd=tmp_path)
        responses = client.parse_responses(result.stdout)

        # Find tools/list response (request id 2)
        tools_response = client.find_response(responses, 2)
        assert tools_response is not None, f"No tools/list response: {responses}"
        assert "result" in tools_response
        assert "tools" in tools_response["result"]

        tools = tools_response["result"]["tools"]
        assert len(tools) > 0, (
            f"Expected at least one tool. Response: {tools_response}. "
            f"Stderr: {result.stderr}"
        )

        # Verify tool structure
        tool = tools[0]
        assert "name" in tool
        assert "description" in tool

        # Verify entry-point tools
        tool_names = [t["name"] for t in tools]
        assert any(
            name in tool_names for name in ["agent-start-here", "registry-execute"]
        ), f"Expected entry-point tools, got: {tool_names}"

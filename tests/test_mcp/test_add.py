"""mcp.add tests."""
from pathlib import Path

import yaml

from agent_tools.mcp.add import add


class TestAdd:
    """Tests for add."""

    def test_add_creates_server_entry(self, tmp_registry: Path):
        """Verify add creates entry in _servers directory."""
        result = add(
            name="github",
            command="npx",
            args='["-y", "@modelcontextprotocol/server-github"]',
        )

        assert "Added MCP server: github" in result

        server_file = tmp_registry / "tool_defs" / "_servers" / "github.yaml"
        assert server_file.exists()

        with server_file.open() as f:
            config = yaml.safe_load(f)

        assert config["command"] == "npx"
        assert config["args"] == ["-y", "@modelcontextprotocol/server-github"]

    def test_add_with_env(self, tmp_registry: Path):
        """Verify add handles environment variables."""
        result = add(
            name="github",
            command="npx",
            args='["-y", "@modelcontextprotocol/server-github"]',
            env='{"GITHUB_TOKEN": "xxx"}',
        )

        assert "Added MCP server: github" in result
        assert "GITHUB_TOKEN" in result

        server_file = tmp_registry / "tool_defs" / "_servers" / "github.yaml"
        with server_file.open() as f:
            config = yaml.safe_load(f)

        assert "env" in config
        assert config["env"]["GITHUB_TOKEN"] == "xxx"

    def test_add_rejects_duplicate(self, tmp_registry: Path):
        """Verify add rejects duplicate server names."""
        add(name="github", command="npx", args="[]")
        result = add(name="github", command="uvx", args="[]")

        assert "Error" in result
        assert "already exists" in result

    def test_add_invalid_args_json(self, tmp_registry: Path):
        """Verify add handles invalid args JSON."""
        result = add(name="test", command="npx", args="not json")

        assert "Error" in result
        assert "Invalid args JSON" in result

    def test_add_invalid_env_json(self, tmp_registry: Path):
        """Verify add handles invalid env JSON."""
        result = add(name="test", command="npx", args="[]", env="not json")

        assert "Error" in result
        assert "Invalid env JSON" in result

"""mcp.list tests."""
from pathlib import Path

from agent_tools.mcp.add import add
from agent_tools.mcp.list import list_servers


class TestListServers:
    """Tests for list_servers."""

    def test_list_empty(self, tmp_registry: Path):
        """Verify list handles no servers configured."""
        result = list_servers()

        assert "No external MCP servers configured" in result

    def test_list_shows_servers(self, tmp_registry: Path):
        """Verify list shows configured servers."""
        add(name="github", command="npx", args='["-y", "server-github"]')
        add(name="filesystem", command="npx", args='["server-fs"]')

        result = list_servers()

        assert "github" in result
        assert "filesystem" in result
        assert "npx" in result

    def test_list_shows_env_keys(self, tmp_registry: Path):
        """Verify list shows environment variable names."""
        add(
            name="github",
            command="npx",
            args="[]",
            env='{"GITHUB_TOKEN": "secret"}',
        )

        result = list_servers()

        assert "GITHUB_TOKEN" in result
        # Should NOT show the actual value
        assert "secret" not in result

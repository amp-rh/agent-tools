"""mcp.remove tests."""
from pathlib import Path

from agent_tools.mcp.add import add
from agent_tools.mcp.remove import remove


class TestRemove:
    """Tests for remove."""

    def test_remove_deletes_server(self, tmp_registry: Path):
        """Verify remove deletes server file."""
        add(name="github", command="npx", args="[]")
        result = remove(name="github")

        assert "Removed MCP server: github" in result

        server_file = tmp_registry / "tool_defs" / "_servers" / "github.yaml"
        assert not server_file.exists()

    def test_remove_not_found(self, tmp_registry: Path):
        """Verify remove handles missing server."""
        result = remove(name="nonexistent")

        assert "Error" in result
        assert "not found" in result

    def test_remove_cleans_empty_dict(self, tmp_registry: Path):
        """Verify remove deletes the file."""
        add(name="github", command="npx", args="[]")
        remove(name="github")

        server_file = tmp_registry / "tool_defs" / "_servers" / "github.yaml"
        assert not server_file.exists()

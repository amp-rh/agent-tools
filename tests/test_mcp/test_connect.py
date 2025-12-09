"""mcp.connect tests."""
from pathlib import Path

from agent_tools.mcp.connect import connect


class TestConnect:
    """Tests for connect."""

    def test_connect_not_configured(self, tmp_registry: Path):
        """Returns error for non-configured server."""
        result = connect("nonexistent")

        assert "Error" in result
        assert "not configured" in result

    def test_connect_needs_mcp_add_first(self, tmp_registry: Path):
        """Verify connect requires mcp.add first."""
        result = connect("github")

        assert "Error" in result
        # Should indicate server isn't configured
        assert "not configured" in result or "mcp.add" in result

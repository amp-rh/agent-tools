"""mcp.disconnect tests."""
from pathlib import Path

from agent_tools.mcp.disconnect import disconnect


class TestDisconnect:
    """Tests for disconnect."""

    def test_disconnect_not_connected(self, tmp_registry: Path):
        """Handles disconnecting a server that isn't connected."""
        result = disconnect("nonexistent")

        assert "not connected" in result.lower() or "not found" in result.lower()

    def test_disconnect_all_when_none(self, tmp_registry: Path):
        """Handles disconnecting all when none connected."""
        result = disconnect()

        # Should succeed gracefully even with no servers
        assert "Disconnected" in result or "disconnect" in result.lower()
